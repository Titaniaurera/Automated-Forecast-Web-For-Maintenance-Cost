import json
import math
import os
import threading
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv


# ============================================================
# LOAD ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# KONFIGURASI
# ============================================================

# Cache memakai server MySQL yang sama dengan data_jasa.
# Kalau ingin schema terpisah, cukup isi CACHE_DB_NAME di .env
# (contoh: CACHE_DB_NAME=jasa_cache). Kalau kosong, memakai DB_NAME.

CACHE_DB_NAME = (
    os.getenv("CACHE_DB_NAME")
    or os.getenv("DB_NAME", "jasa_database")
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": CACHE_DB_NAME,
    "connection_timeout": 5,
}

TABLE_NAME = "forecast_cache"

DEFAULT_SCOPE = "jasa"

# Jumlah riwayat yang disimpan per scope.
KEEP_READY = 5
KEEP_FAILED = 3

# Training yang lebih lama dari ini dianggap macet.
STALE_TRAINING_MINUTES = 30

# Menunggu lock paling lama (detik) saat start_training().
LOCK_WAIT_SECONDS = 5


# ============================================================
# STATUS
# ============================================================

STATUS_TRAINING = "training"
STATUS_READY = "ready"
STATUS_FAILED = "failed"

STATE_EMPTY = "empty"


# ============================================================
# DDL
# ============================================================

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scope VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    result_json LONGTEXT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    trained_at DATETIME NULL,
    data_rows INT NULL,
    data_max_date DATE NULL,
    error_message TEXT NULL,
    PRIMARY KEY (id),
    KEY idx_scope_status_id (scope, status, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


# ============================================================
# KONEKSI + AUTO CREATE
# ============================================================

_table_ready = False
_table_lock = threading.Lock()


def _create_database_if_missing():
    """
    Membuat schema cache kalau belum ada.
    Butuh hak CREATE pada user MySQL.
    """

    config = {
        key: value
        for key, value in DB_CONFIG.items()
        if key != "database"
    }

    connection = mysql.connector.connect(**config)

    try:

        cursor = connection.cursor()

        safe_name = CACHE_DB_NAME.replace("`", "")

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{safe_name}` "
            "CHARACTER SET utf8mb4"
        )

        connection.commit()

        cursor.close()

    finally:

        connection.close()


def ensure_table():
    """
    Membuat schema + tabel forecast_cache kalau belum ada.
    Hanya dijalankan sekali per proses.
    """

    global _table_ready

    if _table_ready:
        return

    with _table_lock:

        if _table_ready:
            return

        try:

            connection = mysql.connector.connect(**DB_CONFIG)

        except mysql.connector.Error as error:

            if error.errno != errorcode.ER_BAD_DB_ERROR:
                raise

            _create_database_if_missing()

            connection = mysql.connector.connect(**DB_CONFIG)

        try:

            cursor = connection.cursor()

            cursor.execute(CREATE_TABLE_SQL)

            connection.commit()

            cursor.close()

        finally:

            connection.close()

        _table_ready = True


@contextmanager
def _connection():
    """
    Koneksi singkat per operasi. Selalu ditutup di akhir.
    """

    ensure_table()

    connection = mysql.connector.connect(**DB_CONFIG)

    try:

        yield connection

    finally:

        connection.close()


# ============================================================
# SERIALISASI JSON
# ============================================================

def _sanitize(value: Any) -> Any:
    """
    Mengubah hasil forecast (bisa berisi numpy, pandas, Decimal,
    NaN, tanggal) menjadi struktur yang aman untuk JSON.

    NaN / Infinity diganti None karena bukan JSON valid dan
    akan membuat JSON.parse di browser gagal.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, Decimal):
        number = float(value)
        return number if math.isfinite(number) else None

    if isinstance(value, (datetime, date)):

        # pandas.NaT
        if value != value:
            return None

        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_sanitize(item) for item in value]

    # numpy scalar / array, pandas Series
    if hasattr(value, "tolist"):
        return _sanitize(value.tolist())

    return str(value)


def _dump(result: Any) -> str:

    return json.dumps(
        _sanitize(result),
        ensure_ascii=False,
        allow_nan=False,
    )


def _iso(value: Any) -> Optional[str]:

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return str(value)


# ============================================================
# LOCK / STATUS TRAINING
# ============================================================

def _expire_stale(cursor, scope: str):
    """
    Training yang macet (misalnya server mati di tengah jalan)
    ditandai gagal supaya lock tidak menggantung selamanya.
    """

    cursor.execute(
        f"""
        UPDATE `{TABLE_NAME}`
        SET status = %s,
            error_message = %s
        WHERE scope = %s
          AND status = %s
          AND TIMESTAMPDIFF(MINUTE, started_at, NOW()) >= %s
        """,
        (
            STATUS_FAILED,
            "Training berhenti tidak normal "
            "(melewati batas waktu).",
            scope,
            STATUS_TRAINING,
            STALE_TRAINING_MINUTES,
        ),
    )


def is_training(scope: str = DEFAULT_SCOPE) -> bool:
    """
    True kalau ada training yang sedang berjalan.
    """

    with _connection() as connection:

        cursor = connection.cursor()

        _expire_stale(cursor, scope)

        connection.commit()

        cursor.execute(
            f"""
            SELECT 1
            FROM `{TABLE_NAME}`
            WHERE scope = %s AND status = %s
            LIMIT 1
            """,
            (scope, STATUS_TRAINING),
        )

        running = cursor.fetchone() is not None

        cursor.close()

        return running


def start_training(scope: str = DEFAULT_SCOPE) -> Optional[int]:
    """
    Menandai training dimulai dan mengambil lock.

    Return:
        run_id  -> boleh lanjut training
        None    -> sudah ada training lain yang berjalan

    Pengecekan + insert dilindungi GET_LOCK() MySQL, jadi dua
    request bersamaan (upload + POST manual) tidak bisa lolos
    berdua.
    """

    lock_name = f"{TABLE_NAME}:{scope}"

    with _connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            "SELECT GET_LOCK(%s, %s)",
            (lock_name, LOCK_WAIT_SECONDS),
        )

        acquired = cursor.fetchone()[0]

        if acquired != 1:

            cursor.close()

            return None

        try:

            _expire_stale(cursor, scope)

            cursor.execute(
                f"""
                SELECT id
                FROM `{TABLE_NAME}`
                WHERE scope = %s AND status = %s
                LIMIT 1
                """,
                (scope, STATUS_TRAINING),
            )

            if cursor.fetchone() is not None:

                connection.commit()

                return None

            cursor.execute(
                f"""
                INSERT INTO `{TABLE_NAME}` (scope, status)
                VALUES (%s, %s)
                """,
                (scope, STATUS_TRAINING),
            )

            run_id = cursor.lastrowid

            connection.commit()

            return run_id

        finally:

            try:

                cursor.execute(
                    "SELECT RELEASE_LOCK(%s)",
                    (lock_name,),
                )

                cursor.fetchone()

            except mysql.connector.Error:
                pass

            cursor.close()


# ============================================================
# SIMPAN HASIL
# ============================================================

def _prune(cursor, scope: str, status: str, keep: int):
    """
    Menghapus riwayat lama, menyisakan `keep` baris terbaru
    untuk status tersebut. Baris "training" tidak pernah dihapus.
    """

    cursor.execute(
        f"""
        SELECT id
        FROM `{TABLE_NAME}`
        WHERE scope = %s AND status = %s
        ORDER BY id DESC
        LIMIT 18446744073709551615 OFFSET %s
        """,
        (scope, status, keep),
    )

    old_ids = [row[0] for row in cursor.fetchall()]

    if not old_ids:
        return

    placeholders = ",".join(["%s"] * len(old_ids))

    cursor.execute(
        f"DELETE FROM `{TABLE_NAME}` WHERE id IN ({placeholders})",
        tuple(old_ids),
    )


def save_success(
    run_id: int,
    result: Any,
    data_rows: Optional[int] = None,
    data_max_date: Any = None,
    scope: str = DEFAULT_SCOPE,
):
    """
    Menyimpan hasil forecast yang berhasil.
    Baris training berubah jadi "ready", lalu riwayat lama dipangkas.

    Kalau result tidak bisa diserialisasi, error dilempar dan
    baris training tetap ada -> panggil save_failure().
    """

    payload = _dump(result)

    with _connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            f"""
            UPDATE `{TABLE_NAME}`
            SET status = %s,
                result_json = %s,
                trained_at = NOW(),
                data_rows = %s,
                data_max_date = %s,
                error_message = NULL
            WHERE id = %s
            """,
            (
                STATUS_READY,
                payload,
                data_rows,
                _iso(data_max_date),
                run_id,
            ),
        )

        _prune(cursor, scope, STATUS_READY, KEEP_READY)

        connection.commit()

        cursor.close()


def save_failure(
    run_id: int,
    error: Any,
    scope: str = DEFAULT_SCOPE,
):
    """
    Mencatat training gagal. Hasil "ready" sebelumnya
    tidak disentuh sama sekali.
    """

    message = str(error)[:2000]

    with _connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            f"""
            UPDATE `{TABLE_NAME}`
            SET status = %s,
                error_message = %s
            WHERE id = %s
            """,
            (STATUS_FAILED, message, run_id),
        )

        _prune(cursor, scope, STATUS_FAILED, KEEP_FAILED)

        connection.commit()

        cursor.close()


# ============================================================
# BACA HASIL
# ============================================================

def get_latest_ready(
    scope: str = DEFAULT_SCOPE,
) -> Optional[Dict[str, Any]]:
    """
    Hasil forecast "ready" terbaru, atau None kalau belum ada.
    """

    with _connection() as connection:

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            f"""
            SELECT id, result_json, trained_at,
                   data_rows, data_max_date
            FROM `{TABLE_NAME}`
            WHERE scope = %s AND status = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (scope, STATUS_READY),
        )

        row = cursor.fetchone()

        cursor.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "result": json.loads(row["result_json"]),
        "trained_at": _iso(row["trained_at"]),
        "data_rows": row["data_rows"],
        "data_max_date": _iso(row["data_max_date"]),
    }


def get_status(scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    """
    Status ringan untuk polling frontend (tidak membaca JSON hasil).

    state:
        "training" -> sedang dihitung
        "ready"    -> ada hasil, tidak sedang training
        "failed"   -> belum ada hasil dan training terakhir gagal
        "empty"    -> belum pernah ada training

    last_error terisi kalau training terakhir gagal DAN lebih baru
    dari hasil ready terakhir (hasil lama tetap bisa dipakai).
    """

    with _connection() as connection:

        cursor = connection.cursor(dictionary=True)

        _expire_stale(cursor, scope)

        connection.commit()

        cursor.execute(
            f"""
            SELECT id, trained_at, data_rows, data_max_date
            FROM `{TABLE_NAME}`
            WHERE scope = %s AND status = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (scope, STATUS_READY),
        )

        ready = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT id, error_message
            FROM `{TABLE_NAME}`
            WHERE scope = %s AND status = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (scope, STATUS_FAILED),
        )

        failed = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT 1
            FROM `{TABLE_NAME}`
            WHERE scope = %s AND status = %s
            LIMIT 1
            """,
            (scope, STATUS_TRAINING),
        )

        training = cursor.fetchone() is not None

        cursor.close()

    has_result = ready is not None

    last_error = None

    if failed is not None and (
        not has_result or failed["id"] > ready["id"]
    ):
        last_error = failed["error_message"]

    if training:
        state = STATUS_TRAINING
    elif has_result:
        state = STATUS_READY
    elif last_error is not None:
        state = STATUS_FAILED
    else:
        state = STATE_EMPTY

    return {
        "state": state,
        "is_training": training,
        "has_result": has_result,
        "trained_at": _iso(ready["trained_at"]) if ready else None,
        "data_rows": ready["data_rows"] if ready else None,
        "data_max_date": (
            _iso(ready["data_max_date"]) if ready else None
        ),
        "last_error": last_error,
    }


def get_cache(scope: str = DEFAULT_SCOPE) -> Dict[str, Any]:
    """
    Paket lengkap untuk GET /forecast:
    status + hasil terbaru (kalau ada).

    Hasil lama tetap dikirim walau sedang training ulang,
    jadi halaman tidak pernah kosong selama pernah ada hasil.
    """

    status = get_status(scope)

    latest = (
        get_latest_ready(scope)
        if status["has_result"]
        else None
    )

    return {
        **status,
        "result": latest["result"] if latest else None,
    }


# ============================================================
# CEK MANUAL
# ============================================================
# Jalankan:  python forecast_cache.py
# Hanya membuat tabel (kalau belum ada) dan menampilkan status.

if __name__ == "__main__":

    ensure_table()

    print(f"Tabel `{TABLE_NAME}` siap di schema `{CACHE_DB_NAME}`.")
    print(json.dumps(get_status(), indent=2, default=str))
