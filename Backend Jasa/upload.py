from fastapi import UploadFile

import io
import os
from pathlib import Path

import pandas as pd
import mysql.connector
from mysql.connector import errorcode

from dotenv import load_dotenv

from Classification import (
    normalize_classification_column,
    validate_short_text,
    validate_classification,
)
from row_hash import make_row_hash


# ============================================================
# LOAD ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# KONFIGURASI MYSQL
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "jasa_database"),

    # Supaya koneksi tidak menggantung kalau MySQL mati
    "connection_timeout": 5,
}

TABLE_NAME = "data_jasa"
HASH_COLUMN = "row_hash"
HASH_INDEX_NAME = "uq_data_jasa_row_hash"


# ============================================================
# KOLOM WAJIB EXCEL
# ============================================================

REQUIRED_COLUMNS = [
    "Company Code",
    "Customer",
    "G/L Account",
    "Document Number",
    "Document Type",
    "Reference",
    "Invoice reference",
    "Document Date",
    "Posting Date",
    "Quantity",
    "Amount in local currency",
    "Local Currency",
    "Document currency",
    "Amount in doc. curr.",
    "Document Header Text",
    "Text",
    "Purchasing Document",
    "Vendor",
    "User Name",
    "Assignment",
    "Cost Center",
    "Tahun",
    "Short Text",
    "Klasifikasi",
]


# ============================================================
# ATURAN DUPLIKAT
# ============================================================
# Baris dianggap duplikat jika SEMUA kolom (setelah distandarkan
# dan klasifikasi dinormalisasi) sama.
#
# Kolom "Klasifikasi" diisi manual (bukan dari SAP). Jika diisi
# True, transaksi yang sama tapi diberi label berbeda dianggap
# data baru. Jika False, duplikat tertangkap apa pun labelnya.

INCLUDE_KLASIFIKASI_IN_HASH = True


# ============================================================
# CLEAN COLUMN NAME
# ============================================================

def clean_column_names(df: pd.DataFrame):

    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    unnamed_columns = [
        column
        for column in df.columns
        if str(column).startswith("Unnamed:")
    ]

    if unnamed_columns:
        df = df.drop(columns=unnamed_columns)

    return df


# ============================================================
# VALIDASI KOLOM
# ============================================================

def validate_columns(df: pd.DataFrame):

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Kolom berikut tidak ditemukan:\n"
            + "\n".join(
                f"- {column}"
                for column in missing_columns
            )
        )


# ============================================================
# VALIDASI TANGGAL / ANGKA
# ============================================================

def validate_dates(df):
    """
    Tanggal diparse satu per satu supaya campuran format
    ("2025-03-05" dan "2025-03-05 00:00:00") tidak diam-diam
    menjadi NaT. Tanggal yang terisi tapi tidak bisa dibaca
    ditolak beserta nomor baris Excel-nya.
    """

    for column in ["Document Date", "Posting Date"]:

        if column not in df.columns:
            continue

        original = df[column]

        parsed = original.apply(
            lambda value: pd.to_datetime(value, errors="coerce")
        )

        failed = parsed.isna() & original.notna() & (
            original.astype(str).str.strip() != ""
        )

        if failed.any():

            rows = [
                int(position) + 2
                for position in
                pd.Series(range(len(df)))[failed.to_numpy()]
            ]

            samples = (
                original[failed].astype(str).unique().tolist()[:5]
            )

            raise ValueError(
                f"Kolom '{column}' berisi tanggal yang tidak "
                f"bisa dibaca: {samples} "
                f"(baris Excel: {rows[:10]})"
            )

        df[column] = pd.to_datetime(parsed, errors="coerce")


def validate_amount(df):

    if "Amount in doc. curr." not in df.columns:
        return

    df["Amount in doc. curr."] = pd.to_numeric(
        df["Amount in doc. curr."],
        errors="coerce"
    )


def validate_quantity(df):

    if "Quantity" not in df.columns:
        return

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce"
    )


def validate_year(df):

    if "Tahun" not in df.columns:
        return

    df["Tahun"] = pd.to_numeric(
        df["Tahun"],
        errors="coerce"
    )


# ============================================================
# CLEAN NaN
# ============================================================

def clean_nan(df):

    df = df.copy()

    df = df.where(
        pd.notna(df),
        None
    )

    return df


# ============================================================
# HASH BARIS (deteksi duplikat)
# ============================================================

def add_row_hash(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menambah kolom row_hash dari semua kolom yang sudah
    distandarkan. Harus dipanggil SETELAH klasifikasi
    dinormalisasi.
    """

    df = df.copy()

    exclude = (
        set()
        if INCLUDE_KLASIFIKASI_IN_HASH
        else {"Klasifikasi"}
    )

    df[HASH_COLUMN] = [
        make_row_hash(row, exclude)
        for row in df.to_dict(orient="records")
    ]

    return df


# ============================================================
# PERSIAPAN DATA (tanpa database, mudah dites)
# ============================================================

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel mentah -> DataFrame bersih siap insert:
        nama kolom -> cek kolom wajib -> tipe data
        -> klasifikasi (tolak jika kosong / asing)
        -> Short Text -> hash baris
    """

    df = clean_column_names(df)

    if df.empty:
        raise ValueError("Excel tidak memiliki data.")

    validate_columns(df)

    validate_dates(df)
    validate_amount(df)
    validate_quantity(df)
    validate_year(df)

    df = normalize_classification_column(df)
    df = validate_short_text(df)
    validate_classification(df)

    df = add_row_hash(df)

    df = clean_nan(df)

    return df


# ============================================================
# MENENTUKAN TIPE DATA MYSQL
# ============================================================

def determine_mysql_type(series: pd.Series):

    if pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"

    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"

    if pd.api.types.is_float_dtype(series):
        return "DOUBLE"

    return "TEXT"


# ============================================================
# CEK KOLOM DATABASE
# ============================================================

def get_table_columns(cursor):

    cursor.execute(f"DESCRIBE `{TABLE_NAME}`")

    return [row[0] for row in cursor.fetchall()]


# ============================================================
# PASTIKAN KOLOM row_hash + UNIQUE INDEX ADA
# ============================================================

def ensure_hash_column(cursor):
    """
    Membuat kolom row_hash dan UNIQUE index jika belum ada.
    (ALTER TABLE di MySQL otomatis commit, jadi dilakukan
    sebelum insert.)
    """

    if HASH_COLUMN not in get_table_columns(cursor):

        cursor.execute(
            f"""
            ALTER TABLE `{TABLE_NAME}`
            ADD COLUMN `{HASH_COLUMN}` CHAR(64) NULL
            """
        )

    cursor.execute(
        f"""
        SHOW INDEX FROM `{TABLE_NAME}`
        WHERE Key_name = %s
        """,
        (HASH_INDEX_NAME,)
    )

    if not cursor.fetchall():

        cursor.execute(
            f"""
            ALTER TABLE `{TABLE_NAME}`
            ADD UNIQUE INDEX `{HASH_INDEX_NAME}`
            (`{HASH_COLUMN}`)
            """
        )


# ============================================================
# TAMBAHKAN KOLOM BARU
# ============================================================

def ensure_table_columns(cursor, df):

    existing_columns = get_table_columns(cursor)

    for column in df.columns:

        if column in existing_columns:
            continue

        mysql_type = determine_mysql_type(df[column])

        cursor.execute(
            f"""
            ALTER TABLE `{TABLE_NAME}`
            ADD COLUMN `{column}` {mysql_type}
            """
        )

    return get_table_columns(cursor)


# ============================================================
# KONVERSI NILAI MYSQL
# ============================================================

def prepare_mysql_value(value):

    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, float):
        return float(value)

    return value


# ============================================================
# INSERT DATA KE MYSQL (duplikat ditolak oleh UNIQUE index)
# ============================================================

def insert_rows(cursor, df, table_columns):
    """
    Duplikat (row_hash sama) dilewati oleh MySQL lewat
    ON DUPLICATE KEY UPDATE yang tidak mengubah apa pun.

    Sengaja TIDAK memakai INSERT IGNORE: IGNORE juga
    menelan error lain (data terpotong, tipe salah) tanpa
    memberi tahu.
    """

    usable_columns = [
        column
        for column in df.columns
        if column in table_columns
    ]

    if not usable_columns:
        raise ValueError(
            "Tidak ada kolom yang sesuai dengan database."
        )

    column_names = ", ".join(
        f"`{column}`"
        for column in usable_columns
    )

    placeholders = ", ".join(["%s"] * len(usable_columns))

    insert_sql = f"""
        INSERT INTO `{TABLE_NAME}`
        ({column_names})
        VALUES
        ({placeholders})
        ON DUPLICATE KEY UPDATE `{HASH_COLUMN}` = `{HASH_COLUMN}`
    """

    data = [
        tuple(
            prepare_mysql_value(row[column])
            for column in usable_columns
        )
        for _, row in df.iterrows()
    ]

    if data:
        cursor.executemany(insert_sql, data)


def count_rows(cursor):

    cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_NAME}`")

    return cursor.fetchone()[0]


# ============================================================
# AUTO-CREATE DATABASE + TABEL
# ============================================================

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `{HASH_COLUMN}` CHAR(64) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY `{HASH_INDEX_NAME}` (`{HASH_COLUMN}`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def create_database_if_missing():
    """
    Membuat database kalau belum ada.
    Butuh hak CREATE pada user MySQL.
    """

    config = {
        key: value
        for key, value in DB_CONFIG.items()
        if key != "database"
    }

    safe_name = DB_CONFIG["database"].replace("`", "")

    connection = mysql.connector.connect(**config)

    try:

        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{safe_name}` "
            "CHARACTER SET utf8mb4"
        )

        connection.commit()

        cursor.close()

    finally:

        connection.close()


def connect_with_auto_create():
    """
    Membuka koneksi ke database data_jasa.
    Kalau database belum ada, dibuat dulu.
    """

    try:

        return mysql.connector.connect(**DB_CONFIG)

    except mysql.connector.Error as error:

        if error.errno != errorcode.ER_BAD_DB_ERROR:
            raise

        create_database_if_missing()

        return mysql.connector.connect(**DB_CONFIG)


def ensure_table(cursor):
    """
    Membuat tabel data_jasa kalau belum ada.

    Tabel baru hanya berisi id + row_hash (CHAR(64) dengan
    UNIQUE index). Kolom lain ditambahkan otomatis oleh
    ensure_table_columns() sesuai isi Excel.
    """

    cursor.execute(CREATE_TABLE_SQL)


# ============================================================
# PROSES UPLOAD EXCEL
# ============================================================

async def process_upload(file: UploadFile):

    if file is None:
        raise ValueError("File tidak ditemukan.")

    filename = file.filename or ""

    extension = Path(filename).suffix.lower()

    # ========================================================
    # VALIDASI EXTENSION
    # ========================================================

    if extension not in [".xlsx", ".xls"]:
        raise ValueError("File harus berupa Excel.")

    # ========================================================
    # BACA FILE
    # ========================================================

    file_bytes = await file.read()

    if not file_bytes:
        raise ValueError("File kosong.")

    try:
        df = pd.read_excel(io.BytesIO(file_bytes))

    except Exception as error:
        raise ValueError(f"Gagal membaca Excel: {error}")

    # ========================================================
    # BERSIHKAN + VALIDASI + HASH
    # ========================================================

    df = prepare_dataframe(df)

    # ========================================================
    # DATABASE
    # ========================================================

    connection = None
    cursor = None

    try:

        connection = connect_with_auto_create()

        cursor = connection.cursor()

        # ----------------------------------------------------
        # BUAT TABEL KALAU BELUM ADA (upload pertama)
        # ----------------------------------------------------

        ensure_table(cursor)

        # ----------------------------------------------------
        # PASTIKAN row_hash + UNIQUE INDEX, LALU KOLOM LAIN
        # ----------------------------------------------------

        ensure_hash_column(cursor)

        table_columns = ensure_table_columns(cursor, df)

        # ----------------------------------------------------
        # INSERT (duplikat dilewati oleh database)
        # ----------------------------------------------------

        total_before = count_rows(cursor)

        insert_rows(cursor, df, table_columns)

        total_after = count_rows(cursor)

        connection.commit()

        inserted_count = total_after - total_before
        duplicate_count = len(df) - inserted_count

        # ----------------------------------------------------
        # PERINGATAN: baris lama tanpa hash tidak bisa
        # dideteksi sebagai duplikat
        # ----------------------------------------------------

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM `{TABLE_NAME}`
            WHERE `{HASH_COLUMN}` IS NULL
            """
        )

        rows_without_hash = cursor.fetchone()[0]

        warnings = []

        if rows_without_hash:
            warnings.append(
                f"{rows_without_hash} baris lama belum punya "
                "row_hash sehingga tidak bisa dideteksi "
                "sebagai duplikat. Kosongkan tabel lalu "
                "upload ulang data awal."
            )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "status": "success",

            "message": "Upload berhasil. "
                       "Data masuk historical database.",

            "filename": filename,

            # Dipakai app.py untuk memutuskan perlu retrain atau tidak
            "inserted_count": inserted_count,
            "duplicate_count": duplicate_count,

            "upload_summary": {
                "rows_in_file": len(df),
                "rows_inserted": inserted_count,
                "rows_duplicate": duplicate_count,
            },

            "database": {
                "table": TABLE_NAME,
                "total_rows": total_after,
            },

            "warnings": warnings,

            "next_step": "Jika ada baris baru, forecast dihitung "
                         "ulang di background.",
        }

    except Exception:

        if connection is not None:
            connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("upload.py ready")
