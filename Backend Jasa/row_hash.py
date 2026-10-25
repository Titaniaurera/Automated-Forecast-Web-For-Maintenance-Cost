"""
Hash baris untuk deteksi duplikat (semua kolom sama = duplikat).
Nilai distandarkan dulu supaya 1000 / 1000.0 / "1000.00", tanggal dengan
atau tanpa jam, dan spasi berlebih tidak membuat baris yang sama
dianggap berbeda.
"""
import hashlib
import re
from decimal import Decimal, InvalidOperation

import pandas as pd

# Semua kolom yang ikut dihitung (sama dengan REQUIRED_COLUMNS di upload.py)
HASH_COLUMNS = [
    "Company Code", "Customer", "G/L Account", "Document Number",
    "Document Type", "Reference", "Invoice reference", "Document Date",
    "Posting Date", "Quantity", "Amount in local currency",
    "Local Currency", "Document currency", "Amount in doc. curr.",
    "Document Header Text", "Text", "Purchasing Document", "Vendor",
    "User Name", "Assignment", "Cost Center", "Tahun", "Short Text",
    "Klasifikasi",
]

DATE_COLUMNS = {"Document Date", "Posting Date"}
NUMBER_COLUMNS = {"Quantity", "Amount in local currency",
                  "Amount in doc. curr.", "Tahun"}


def _is_empty(value):
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _std_date(value):
    ts = pd.to_datetime(value, errors="coerce")
    return "" if pd.isna(ts) else ts.strftime("%Y-%m-%d")


def _std_number(value):
    try:
        d = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return re.sub(r"\s+", " ", str(value).strip())
    return f"{d:.4f}"


def _std_text(value):
    text = str(value)
    # angka bulat yang terbaca float: 1234.0 -> 1234
    if isinstance(value, float) and value.is_integer():
        text = str(int(value))
    text = re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()
    # "4900001234.0" (teks hasil konversi Excel) -> "4900001234"
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".")[0]
    return text


def standardize_value(column, value):
    if _is_empty(value):
        return ""
    if column in DATE_COLUMNS:
        return _std_date(value)
    if column in NUMBER_COLUMNS:
        return _std_number(value)
    return _std_text(value)


def make_row_hash(row, exclude=()):
    """
    row: dict / Series yang Klasifikasinya SUDAH dinormalisasi.
    exclude: nama kolom yang tidak ikut dihash (mis. {"Klasifikasi"}).
    """
    columns = [c for c in HASH_COLUMNS if c not in exclude]
    parts = [standardize_value(c, row.get(c)) for c in columns]
    raw = "\x1f".join(parts)          # pemisah yang tidak muncul di data
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
