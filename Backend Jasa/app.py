# ============================================================
# app.py
# JASA FORECASTING API
# ============================================================

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
)

from fastapi.middleware.cors import CORSMiddleware

import os
import logging

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import mysql.connector

from dotenv import load_dotenv

# Cache forecast di MySQL (tabel forecast_cache)
import forecast_cache as cache_store


# ============================================================
# 1. BASE DIRECTORY & ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

# Log berstempel waktu untuk semua modul (app, forecasting, dst.)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ============================================================
# 2. DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "..."),
    "port": int(os.getenv("DB_PORT", "...")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "..."),

    # Timeout koneksi database
    "connection_timeout": 5,
}

TABLE_NAME = "data_jasa"


# ============================================================
# 3. FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Jasa Forecasting API",
    description="API untuk dashboard forecasting jasa",
    version="2.2.0",
)


# ============================================================
# 4. CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 5. FORECAST CACHE (MySQL)
# ============================================================
#
# Cache disimpan di tabel `forecast_cache` lewat forecast_cache.py,
# bukan di memori. Jadi:
#
#   - hasil tidak hilang saat server restart / reload
#   - semua worker membaca hasil yang sama
#   - lock training memakai GET_LOCK() MySQL, bukan threading.Lock
#
# Status yang dikirim GET /forecast:
#
#   - success  : ada hasil forecast
#   - training : sedang dihitung (hasil lama tetap dikirim)
#   - empty    : belum pernah ada hasil
#
# Kalau training gagal, hasil "ready" sebelumnya TIDAK disentuh.
# ============================================================


# ============================================================
# 6. DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Membuat koneksi ke database MySQL.
    """

    return mysql.connector.connect(
        **DB_CONFIG
    )


# ============================================================
# 7. VALUE CONVERTER
# ============================================================

def convert_value(value):
    """
    Mengubah tipe data yang tidak JSON-serializable
    menjadi tipe yang bisa dikirim oleh FastAPI.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


# ============================================================
# 8. ROW CONVERTER
# ============================================================

def convert_rows(rows):
    """
    Mengubah seluruh value pada hasil query
    agar aman dikembalikan sebagai JSON.
    """

    for row in rows:
        for key in row:
            row[key] = convert_value(row[key])

    return rows


# ============================================================
# 11. LOAD DATA FROM DATABASE
# ============================================================

def load_database_dataframe():
    """
    Mengambil seluruh data dari tabel data_jasa
    dan mengubahnya menjadi pandas DataFrame.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT *
            FROM `{TABLE_NAME}`
            """
        )

        rows = cursor.fetchall()

        if not rows:
            raise ValueError(
                "Database data_jasa kosong."
            )

        df = pd.DataFrame(rows)

        return df

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 12. NORMALIZE CLASSIFICATION
# ============================================================

def normalize_classification(value):
    """
    Menyamakan berbagai variasi penulisan klasifikasi
    menjadi dua kategori utama:

        Rutin

        Non Rutin + OVH
    """

    if value is None:
        return ""

    text = str(value).strip().upper()

    # --------------------------------------------
    # RUTIN
    # --------------------------------------------

    if text == "RUTIN":
        return "Rutin"

    # --------------------------------------------
    # NON RUTIN + OVH
    # --------------------------------------------

    if text in [
        "NON RUTIN",
        "NON-RUTIN",
        "NON RUTIN + OVH",
        "NON-RUTIN + OVH",
        "NON RUTIN OVH",
        "NON-RUTIN OVH",
    ]:
        return "Non Rutin + OVH"

    # --------------------------------------------
    # Variasi yang diawali OVH
    # --------------------------------------------

    if text.startswith("OVH"):
        return "Non Rutin + OVH"

    # --------------------------------------------
    # Selain itu, pertahankan nilai asli
    # --------------------------------------------

    return str(value).strip()


# ============================================================
# 13. BUILD FORECAST RESPONSE FROM CACHE
# ============================================================

def build_forecast_response_from_cache():
    """
    Membentuk response GET /forecast dari tabel forecast_cache.

    Status:

        success  -> ada hasil, tidak sedang training
        training -> sedang training (hasil lama ikut dikirim
                    kalau ada)
        empty    -> belum pernah ada hasil

    Isi hasil forecast (rutin, non_rutin_ovh, dst.) diletakkan
    di level atas response, sama seperti response GET /forecast
    sebelum ada cache.
    """

    cache = cache_store.get_cache()

    result = cache["result"]

    if cache["is_training"]:
        status = "training"
    elif cache["has_result"]:
        status = "success"
    else:
        status = "empty"

    response = dict(result) if result else {}

    response.update({
        "status": status,
        "training_status": cache["state"],
        "training_error": cache["last_error"],
        "trained_at": cache["trained_at"],
        "updated_at": cache["trained_at"],
        "data_rows": cache["data_rows"],
        "data_max_date": cache["data_max_date"],
    })

    return response


    # ============================================================
# 14. ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    """
    Endpoint utama untuk mengecek API.
    """

    return {
        "status": "success",
        "message": "Jasa Forecasting API is running.",
        "database": DB_CONFIG["database"],
        "table": TABLE_NAME,
    }


# ============================================================
# 15. HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    """
    Mengecek koneksi database dan kondisi forecast cache.
    """

    connection = None
    cursor = None

    try:
        # --------------------------------------------
        # Cek koneksi database
        # --------------------------------------------

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM `{TABLE_NAME}`
            """
        )

        result = cursor.fetchone()

        total = result[0] if result else 0

        # --------------------------------------------
        # Ambil status forecast
        # --------------------------------------------

        cache = cache_store.get_status()

        return {

            "status": "success",

            "database": "connected",

            "total_data": total,

            "forecast_status": cache["state"],

            "training_status": cache["state"],

            "training_error": cache["last_error"],

            "forecast_updated_at": cache["trained_at"],
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 16. GET ALL DATA
# ============================================================

@app.get("/data")
def get_data():
    """
    Mengambil seluruh data dari tabel data_jasa.
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT *
            FROM `{TABLE_NAME}`
            """
        )

        rows = cursor.fetchall()

        rows = convert_rows(rows)

        return {
            "status": "success",
            "total": len(rows),
            "data": rows,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 17. SUMMARY
# ============================================================

@app.get("/summary")
def get_summary():
    """
    Mengambil ringkasan data jasa.

    Informasi:
    - total rows
    - total amount
    - tahun minimum
    - tahun maksimum
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS total_rows,

                COALESCE(
                    SUM(
                        ABS(
                            `Amount in doc. curr.`
                        )
                    ),
                    0
                ) AS total_amount,

                MIN(
                    YEAR(`Posting Date`)
                ) AS min_year,

                MAX(
                    YEAR(`Posting Date`)
                ) AS max_year

            FROM `{TABLE_NAME}`
            """
        )

        row = cursor.fetchone()

        if row is None:
            row = {
                "total_rows": 0,
                "total_amount": 0,
                "min_year": None,
                "max_year": None,
            }

        row = convert_rows([row])[0]

        return {
            "status": "success",
            **row,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 18. BY MONTH
# ============================================================

@app.get("/by-month")
def get_by_month():
    """
    Mengambil jumlah data dan total amount
    berdasarkan tahun dan bulan.
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT
                YEAR(`Posting Date`) AS tahun,
                MONTH(`Posting Date`) AS bulan,

                COUNT(*) AS count,

                COALESCE(
                    SUM(
                        ABS(
                            `Amount in doc. curr.`
                        )
                    ),
                    0
                ) AS total_amount

            FROM `{TABLE_NAME}`

            GROUP BY
                YEAR(`Posting Date`),
                MONTH(`Posting Date`)

            ORDER BY
                tahun,
                bulan
            """
        )

        rows = cursor.fetchall()

        rows = convert_rows(rows)

        return {
            "status": "success",
            "data": rows,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 19. CLASSIFICATION
# ============================================================

@app.get("/classification")
def get_classification():
    """
    Mengambil distribusi data berdasarkan Klasifikasi.

    Menampilkan:
    - jumlah data
    - total amount
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT
                `Klasifikasi` AS classification,

                COUNT(*) AS count,

                COALESCE(
                    SUM(
                        ABS(
                            `Amount in doc. curr.`
                        )
                    ),
                    0
                ) AS total_amount

            FROM `{TABLE_NAME}`

            GROUP BY
                `Klasifikasi`

            ORDER BY
                total_amount DESC
            """
        )

        rows = cursor.fetchall()

        rows = convert_rows(rows)

        return {
            "status": "success",
            "data": rows,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 20. MONTHLY CLASSIFICATION
# ============================================================

@app.get("/monthly-classification")
def get_monthly_classification():
    """
    Mengambil distribusi klasifikasi berdasarkan bulan.
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            f"""
            SELECT
                YEAR(`Posting Date`) AS tahun,
                MONTH(`Posting Date`) AS bulan,

                `Klasifikasi` AS classification,

                COUNT(*) AS count,

                COALESCE(
                    SUM(
                        ABS(
                            `Amount in doc. curr.`
                        )
                    ),
                    0
                ) AS total_amount

            FROM `{TABLE_NAME}`

            GROUP BY
                YEAR(`Posting Date`),
                MONTH(`Posting Date`),
                `Klasifikasi`

            ORDER BY
                tahun,
                bulan,
                classification
            """
        )

        rows = cursor.fetchall()

        rows = convert_rows(rows)

        return {
            "status": "success",
            "data": rows,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 21. MONTHLY DETAILS
# ============================================================

@app.get("/monthly-details")
def get_monthly_details(
    tahun: int,
    bulan: int,
):
    """
    Mengambil detail data jasa untuk bulan tertentu.

    Parameter:
        tahun
        bulan

    Data dikelompokkan berdasarkan:
        Short Text
        Klasifikasi

    Kemudian diambil 10 data dengan
    total amount terbesar.
    """

    connection = None
    cursor = None

    try:

        # --------------------------------------------
        # Validasi bulan
        # --------------------------------------------

        if bulan < 1 or bulan > 12:
            raise HTTPException(
                status_code=400,
                detail="Bulan harus berada antara 1 sampai 12.",
            )

        # --------------------------------------------
        # Database connection
        # --------------------------------------------

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # --------------------------------------------
        # Query
        # --------------------------------------------

        cursor.execute(
            f"""
            SELECT
                `Short Text` AS short_text,

                `Klasifikasi` AS classification,

                COUNT(*) AS count,

                COALESCE(
                    SUM(
                        ABS(
                            `Amount in doc. curr.`
                        )
                    ),
                    0
                ) AS total_amount

            FROM `{TABLE_NAME}`

            WHERE
                YEAR(`Posting Date`) = %s
                AND MONTH(`Posting Date`) = %s

            GROUP BY
                `Short Text`,
                `Klasifikasi`

            ORDER BY
                total_amount DESC

            LIMIT 10
            """,
            (
                tahun,
                bulan,
            ),
        )

        rows = cursor.fetchall()

        rows = convert_rows(rows)

        return {
            "status": "success",
            "tahun": tahun,
            "bulan": bulan,
            "data": rows,
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

            # ============================================================
# 22. POST /upload
# ============================================================

@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload data ke database.

    Setelah process_upload() berhasil:

        inserted_count > 0
            -> retraining dijadwalkan di background

        inserted_count == 0
            -> tidak ada data baru,
               sehingga retraining tidak diperlukan.

    process_upload() TIDAK memanggil app.py.
    Retraining sepenuhnya dikendalikan oleh app.py.
    """

    # --------------------------------------------------------
    # Import process_upload
    # --------------------------------------------------------

    try:

        from upload import process_upload

    except ImportError as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "upload.py tidak dapat di-import. "
                f"Detail: {error}"
            ),
        )

    # --------------------------------------------------------
    # Jalankan proses upload
    # --------------------------------------------------------

    try:

        result = await process_upload(file)

        # ----------------------------------------------------
        # Validasi hasil process_upload()
        # ----------------------------------------------------

        if result is None:
            raise RuntimeError(
                "process_upload() menghasilkan None."
            )

        if not isinstance(result, dict):
            raise RuntimeError(
                "Hasil process_upload() harus berupa dictionary. "
                f"Tipe hasil: {type(result).__name__}"
            )

        # ----------------------------------------------------
        # inserted_count WAJIB tersedia
        # ----------------------------------------------------

        if "inserted_count" not in result:
            raise RuntimeError(
                "Hasil process_upload() tidak memiliki "
                "field 'inserted_count'."
            )

        try:

            inserted_count = int(
                result["inserted_count"]
            )

        except (TypeError, ValueError):

            raise RuntimeError(
                "Field 'inserted_count' harus berupa angka."
            )

        # ----------------------------------------------------
        # Pastikan tidak negatif
        # ----------------------------------------------------

        if inserted_count < 0:
            raise RuntimeError(
                "Field 'inserted_count' tidak boleh negatif."
            )

        # ----------------------------------------------------
        # Kalau ada data baru
        # ----------------------------------------------------

        if inserted_count > 0:

            background_tasks.add_task(
                background_retrain_forecast
            )

            result["forecast_retrain"] = {
                "scheduled": True,
                "message": (
                    f"{inserted_count} baris baru berhasil "
                    "dimasukkan. Forecast akan dihitung ulang "
                    "di background."
                ),
            }

        # ----------------------------------------------------
        # Kalau tidak ada data baru
        # ----------------------------------------------------

        else:

            result["forecast_retrain"] = {
                "scheduled": False,
                "message": (
                    "Tidak ada baris baru yang masuk. "
                    "Semua data upload merupakan duplikat, "
                    "sehingga retraining dilewati."
                ),
            }

        # ----------------------------------------------------
        # Response upload
        # ----------------------------------------------------

        return result

    except HTTPException:
        raise

    except ValueError as error:

        # Error validasi Excel (kolom kurang, tanggal salah, dst.)
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# 23. RUN FORECAST ENGINE
# ============================================================

def run_forecast_engine(
    df,
    classification,
):
    """
    Menjalankan fungsi run_forecast() dari forecasting.py.

    Tetap mempertahankan kompatibilitas dengan dua kemungkinan
    signature:

        run_forecast(df, classification=...)

    atau:

        run_forecast(df)
    """

    # --------------------------------------------------------
    # Import forecasting engine
    # --------------------------------------------------------

    try:

        from forecasting import run_forecast

    except ImportError as error:

        raise RuntimeError(
            "forecasting.py tidak dapat di-import. "
            f"Detail: {error}"
        )

    # --------------------------------------------------------
    # Jalankan forecast
    # --------------------------------------------------------

    # run_forecast() menerima classification. Tidak ada fallback
    # TypeError: error asli dari training harus muncul apa adanya
    # dan training tidak boleh dijalankan dua kali.

    result = run_forecast(
        df,
        classification=classification,
    )

    # --------------------------------------------------------
    # Validasi hasil
    # --------------------------------------------------------

    if result is None:

        raise RuntimeError(
            f"Forecast {classification} menghasilkan None."
        )

    return result


# ============================================================
# 24. COMPUTE FORECAST
# ============================================================

def compute_forecast():
    """
    Menghitung forecast berdasarkan seluruh data terbaru
    di database.

    Fungsi ini merupakan isi utama dari logic forecast lama.

    PERBEDAAN DENGAN GET /forecast LAMA:

        - tidak langsung menjadi HTTP response
        - tidak menggunakan HTTPException sebagai output utama
        - hanya menghitung dan mengembalikan dictionary hasil

    Fungsi ini nantinya dipanggil oleh:

        POST /forecast

    dan:

        background_retrain_forecast()
    """

    print(
        "[FORECAST] Mulai menghitung forecast..."
    )

    # ========================================================
    # 24.1 LOAD DATABASE
    # ========================================================

    df = load_database_dataframe()

    print(
        f"[FORECAST] Total data dari database: {len(df)}"
    )

    # ========================================================
    # 24.2 VALIDASI KOLOM
    # ========================================================

    required_columns = [
        "Posting Date",
        "Amount in doc. curr.",
        "Klasifikasi",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Kolom yang dibutuhkan untuk forecast "
            f"tidak ditemukan: {missing_columns}"
        )

    # ========================================================
    # 24.3 CLEAN KLASIFIKASI
    # ========================================================

    df["Klasifikasi"] = (
        df["Klasifikasi"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # ========================================================
    # 24.4 NORMALISASI KLASIFIKASI
    # ========================================================

    df["_Klasifikasi_Normalized"] = (
        df["Klasifikasi"]
        .apply(normalize_classification)
    )

    # ========================================================
    # 24.5 PISAHKAN RUTIN
    # ========================================================

    df_rutin = df[
        df["_Klasifikasi_Normalized"] == "Rutin"
    ].copy()

    # ========================================================
    # 24.6 PISAHKAN NON RUTIN + OVH
    # ========================================================

    df_non_rutin = df[
        df["_Klasifikasi_Normalized"]
        == "Non Rutin + OVH"
    ].copy()

    # ========================================================
    # 24.7 NORMALISASI NILAI KLASIFIKASI
    # ========================================================

    if not df_rutin.empty:

        df_rutin["Klasifikasi"] = "Rutin"

    if not df_non_rutin.empty:

        df_non_rutin["Klasifikasi"] = (
            "Non Rutin + OVH"
        )

    # ========================================================
    # 24.8 LOG JUMLAH DATA
    # ========================================================

    print(
        "[FORECAST] Data Rutin:",
        len(df_rutin),
    )

    print(
        "[FORECAST] Data Non Rutin + OVH:",
        len(df_non_rutin),
    )

    # ========================================================
    # 24.9 VALIDASI DATA RUTIN
    # ========================================================

    if df_rutin.empty:

        raise ValueError(
            "Tidak terdapat data dengan klasifikasi Rutin. "
            "Forecast tidak dapat dihitung."
        )

    # ========================================================
    # 24.10 FORECAST RUTIN
    # ========================================================

    print(
        "[FORECAST] Menjalankan forecast Rutin..."
    )

    rutin_result = run_forecast_engine(
        df_rutin,
        "Rutin",
    )

    # ========================================================
    # 24.11 FORECAST NON RUTIN + OVH
    # ========================================================

    if not df_non_rutin.empty:

        print(
            "[FORECAST] Menjalankan forecast "
            "Non Rutin + OVH..."
        )

        non_rutin_result = run_forecast_engine(
            df_non_rutin,
            "Non Rutin + OVH",
        )

    else:

        print(
            "[FORECAST] Tidak ada data "
            "Non Rutin + OVH."
        )

        non_rutin_result = {
            "forecast": 0,
            "model": None,
            "metrics": {},
            "historical": [],
            "series": [],
            "contributors": [],
        }

    # ========================================================
    # 24.12 VALIDASI HASIL FORECAST
    # ========================================================

    if not isinstance(rutin_result, dict):

        raise RuntimeError(
            "Hasil forecast Rutin harus berupa dictionary."
        )

    if not isinstance(
        non_rutin_result,
        dict,
    ):

        raise RuntimeError(
            "Hasil forecast Non Rutin + OVH "
            "harus berupa dictionary."
        )

    # ========================================================
    # 24.13 AMBIL NILAI FORECAST
    # ========================================================

    rutin_forecast = float(
        rutin_result.get(
            "forecast",
            0,
        )
        or 0
    )

    non_rutin_forecast = float(
        non_rutin_result.get(
            "forecast",
            0,
        )
        or 0
    )

    total_forecast = (
        rutin_forecast
        + non_rutin_forecast
    )

    # ========================================================
    # 24.14 FORECAST MONTH
    # ========================================================

    forecast_month = (
        rutin_result.get("forecast_month")
        or non_rutin_result.get("forecast_month")
    )

    forecast_month_label = (
        rutin_result.get("forecast_month_label")
        or non_rutin_result.get(
            "forecast_month_label"
        )
    )

    # ========================================================
    # 24.15 SERIES
    # ========================================================

    rutin_series = rutin_result.get(
        "series",
        [],
    )

    non_rutin_series = non_rutin_result.get(
        "series",
        [],
    )

    # ========================================================
    # 24.16 HISTORICAL
    # ========================================================

    rutin_historical = rutin_result.get(
        "historical",
        [],
    )

    # ========================================================
    # 24.17 CONTRIBUTORS
    # ========================================================

    rutin_contributors = rutin_result.get(
        "contributors",
        [],
    )

    non_rutin_contributors = (
        non_rutin_result.get(
            "contributors",
            [],
        )
    )

    # ========================================================
    # 24.18 BUILD RESPONSE
    # ========================================================

    response = {
        "status": "success",

        "forecast_month": forecast_month,

        "forecast_month_label": (
            forecast_month_label
        ),

        "total_forecast": total_forecast,

        "rutin": {
            "forecast": rutin_forecast,

            "model": rutin_result.get(
                "model"
            ),

            "metrics": rutin_result.get(
                "metrics",
                {},
            ),

            "historical": rutin_historical,

            "series": rutin_series,

            "contributors": (
                rutin_contributors
            ),
        },

        "non_rutin_ovh": {
            "forecast": non_rutin_forecast,

            "model": non_rutin_result.get(
                "model"
            ),

            "metrics": non_rutin_result.get(
                "metrics",
                {},
            ),

            "historical": (
                non_rutin_result.get(
                    "historical",
                    [],
                )
            ),

            "series": non_rutin_series,

            "contributors": (
                non_rutin_contributors
            ),
        },

        # --------------------------------------------
        # Backward compatibility
        # --------------------------------------------

        "historical": rutin_historical,

        "series": rutin_series,

        "contributors": (
            rutin_contributors
        ),

        # --------------------------------------------
        # Data information
        # --------------------------------------------

        "data_info": {
            "total_rows": len(df),

            "rutin_rows": len(df_rutin),

            "non_rutin_ovh_rows": (
                len(df_non_rutin)
            ),
        },
    }

    # ========================================================
    # 24.19 LOG SUCCESS
    # ========================================================

    print(
        "[FORECAST] Forecast berhasil dihitung."
    )

    print(
        f"[FORECAST] Forecast Rutin: "
        f"{rutin_forecast}"
    )

    print(
        f"[FORECAST] Forecast Non Rutin + OVH: "
        f"{non_rutin_forecast}"
    )

    print(
        f"[FORECAST] Total forecast: "
        f"{total_forecast}"
    )

    # ========================================================
    # 24.20 RETURN
    # ========================================================

    return response

# ============================================================
# 25. STATISTIK DATA (disimpan bersama hasil forecast)
# ============================================================

def get_data_stats():
    """
    Jumlah baris dan tanggal posting terbaru di data_jasa.
    Disimpan di cache supaya terlihat hasil forecast ini dihitung
    dari data sampai kapan. Gagal membaca -> (None, None), tidak
    menggagalkan training.
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT COUNT(*), MAX(`Posting Date`)
            FROM `{TABLE_NAME}`
            """
        )

        row = cursor.fetchone()

        if not row:
            return None, None

        max_date = row[1]

        if hasattr(max_date, "date"):
            max_date = max_date.date()

        return row[0], max_date

    except Exception as error:

        print(f"[FORECAST] Gagal membaca statistik data: {error}")

        return None, None

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# 26. RUN TRAINING (dipakai upload di background + POST /forecast)
# ============================================================

def run_training(source):
    """
    Menghitung forecast lalu menyimpannya ke cache MySQL.

    Return:
        dict  -> training sukses (result + run_id)
        None  -> sudah ada training lain yang berjalan

    Kalau training gagal:
        - kegagalan dicatat (status failed + alasan)
        - hasil "ready" sebelumnya TIDAK ditimpa
        - exception dilempar lagi ke pemanggil
    """

    run_id = cache_store.start_training()

    if run_id is None:

        print(
            f"[FORECAST] Training ({source}) dilewati: "
            "sudah ada training yang berjalan."
        )

        return None

    print(f"[FORECAST] Training ({source}) dimulai, run_id={run_id}")

    try:

        result = compute_forecast()

        if not isinstance(result, dict):

            raise RuntimeError(
                "compute_forecast() harus menghasilkan dictionary."
            )

        data_rows, data_max_date = get_data_stats()

        cache_store.save_success(
            run_id,
            result,
            data_rows=data_rows,
            data_max_date=data_max_date,
        )

        print(f"[FORECAST] Training ({source}) berhasil.")

        return {"run_id": run_id, "result": result}

    except Exception as error:

        print(f"[FORECAST] Training ({source}) gagal: {error}")

        try:

            cache_store.save_failure(run_id, error)

        except Exception as save_error:

            print(
                "[FORECAST] Gagal mencatat kegagalan training: "
                f"{save_error}"
            )

        raise


# ============================================================
# 27. BACKGROUND RETRAIN FORECAST
# ============================================================

def background_retrain_forecast():
    """
    Dijalankan lewat BackgroundTasks setelah upload sukses.

    Tidak melempar exception (tidak ada yang menangkapnya di
    background). Kegagalan sudah dicatat di forecast_cache dan
    muncul di GET /forecast sebagai training_error.
    """

    try:

        run_training("upload")

    except Exception:

        # sudah dicatat dan di-log oleh run_training()
        pass


# ============================================================
# 28. GET /forecast
# ============================================================

@app.get("/forecast")
def get_forecast():
    """
    Membaca forecast dari cache MySQL.

    Endpoint ini TIDAK melakukan training.
    """

    try:

        return build_forecast_response_from_cache()

    except mysql.connector.Error as error:

        raise HTTPException(
            status_code=503,
            detail=f"Database tidak dapat diakses: {error}",
        )


# ============================================================
# 29. POST /forecast
# ============================================================

@app.post("/forecast")
def post_forecast():
    """
    Retrain manual tanpa upload.

    Jalan sinkron: response baru dikirim setelah training selesai.

    409 -> sudah ada training yang berjalan
    500 -> training gagal (hasil lama tetap aman di cache)
    """

    try:

        outcome = run_training("manual")

    except Exception as error:

        try:
            previous = cache_store.get_status()["has_result"]
        except Exception:
            previous = False

        raise HTTPException(
            status_code=500,
            detail={
                "status": "failed",
                "message": "Forecast gagal dihitung ulang.",
                "error": str(error),
                "previous_result_available": previous,
            },
        )

    if outcome is None:

        raise HTTPException(
            status_code=409,
            detail={
                "status": "training",
                "message": (
                    "Forecast sedang dalam proses training. "
                    "Silakan tunggu sampai proses selesai."
                ),
            },
        )

    return build_forecast_response_from_cache()


# ============================================================
# 30. STARTUP
# ============================================================

@app.on_event("startup")
def prepare_forecast_cache():
    """
    Membuat tabel forecast_cache saat server naik, supaya masalah
    koneksi / hak akses MySQL ketahuan sejak awal. Kalau gagal,
    server tetap jalan dan tabel dicoba lagi saat dipakai.
    """

    try:

        cache_store.ensure_table()

        print("[FORECAST] Tabel forecast_cache siap.")

    except Exception as error:

        print(f"[FORECAST] Tabel forecast_cache belum siap: {error}")


# ============================================================
# 31. RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
