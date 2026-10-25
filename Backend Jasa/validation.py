import pandas as pd


# ============================================================
# KOLOM WAJIB
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
# VALIDASI NAMA KOLOM
# ============================================================

def validate_columns(df: pd.DataFrame):
    """
    Memastikan semua kolom yang dibutuhkan tersedia.
    """

    # Bersihkan spasi pada nama kolom
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Kolom berikut tidak ditemukan dalam file upload:\n"
            + "\n".join(
                f"- {column}"
                for column in missing_columns
            )
        )

    return True


# ============================================================
# VALIDASI DATA KOSONG
# ============================================================

def validate_empty_data(df: pd.DataFrame):
    """
    Memastikan file tidak kosong.
    """

    if df.empty:
        raise ValueError(
            "File upload tidak memiliki data."
        )

    return True


# ============================================================
# VALIDASI POSTING DATE
# ============================================================

def validate_posting_date(df: pd.DataFrame):
    """
    Memastikan Posting Date dapat dibaca sebagai tanggal.
    """

    if "Posting Date" not in df.columns:
        raise ValueError(
            "Kolom 'Posting Date' tidak ditemukan."
        )

    converted_date = pd.to_datetime(
        df["Posting Date"],
        errors="coerce"
    )

    invalid_count = converted_date.isna().sum()

    if invalid_count > 0:
        raise ValueError(
            f"Ditemukan {invalid_count} baris "
            "dengan Posting Date yang tidak valid."
        )

    return True


# ============================================================
# VALIDASI AMOUNT
# ============================================================

def validate_amount(df: pd.DataFrame):
    """
    Memastikan Amount in doc. curr. dapat digunakan
    sebagai nilai numerik.
    """

    column = "Amount in doc. curr."

    if column not in df.columns:
        raise ValueError(
            f"Kolom '{column}' tidak ditemukan."
        )

    amount = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    invalid_count = amount.isna().sum()

    if invalid_count > 0:
        raise ValueError(
            f"Ditemukan {invalid_count} baris "
            f"dengan nilai '{column}' yang tidak valid."
        )

    return True


# ============================================================
# VALIDASI KLASIFIKASI
# ============================================================

def validate_classification(df: pd.DataFrame):
    """
    Memastikan nilai Klasifikasi sesuai dengan
    klasifikasi yang sudah dilakukan sebelumnya.

    Klasifikasi tidak dibuat oleh backend.
    Backend hanya memvalidasi hasil klasifikasi.
    """

    column = "Klasifikasi"

    if column not in df.columns:
        raise ValueError(
            "Kolom 'Klasifikasi' tidak ditemukan."
        )

    # Hilangkan spasi berlebih
    values = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Nilai kosong
    empty_count = (
        values == ""
    ).sum()

    if empty_count > 0:
        raise ValueError(
            f"Ditemukan {empty_count} baris "
            "dengan Klasifikasi kosong."
        )

    # Nilai yang diperbolehkan
    allowed_values = {
        "Rutin",
        "Non Rutin",
        "OVH",
    }

    invalid_values = sorted(
        set(values.unique())
        - allowed_values
    )

    if invalid_values:
        raise ValueError(
            "Ditemukan nilai Klasifikasi "
            "yang tidak dikenali:\n"
            + "\n".join(
                f"- {value}"
                for value in invalid_values
            )
        )

    return True


# ============================================================
# VALIDASI DUPLIKAT
# ============================================================

def check_duplicates(
    df: pd.DataFrame
):
    """
    Mengecek kemungkinan data transaksi duplikat.

    Untuk sementara hanya memberikan informasi,
    tidak langsung menghapus data.
    """

    duplicate_columns = [
        column
        for column in [
            "Document Number",
            "Posting Date",
            "Amount in doc. curr.",
        ]
        if column in df.columns
    ]

    if not duplicate_columns:
        return {
            "duplicate_count": 0
        }

    duplicate_count = df.duplicated(
        subset=duplicate_columns,
        keep=False
    ).sum()

    return {
        "duplicate_count": int(
            duplicate_count
        )
    }


# ============================================================
# VALIDASI KESELURUHAN
# ============================================================

def validate_data(df: pd.DataFrame):
    """
    Menjalankan seluruh proses validasi
    terhadap data upload.
    """

    print("\n========================================")
    print("DATA VALIDATION")
    print("========================================")

    # 1. File tidak boleh kosong
    validate_empty_data(df)

    print("✓ Data tidak kosong")

    # 2. Validasi kolom
    validate_columns(df)

    print("✓ Semua kolom tersedia")

    # 3. Validasi tanggal
    validate_posting_date(df)

    print("✓ Posting Date valid")

    # 4. Validasi amount
    validate_amount(df)

    print("✓ Amount in doc. curr. valid")

    # 5. Validasi klasifikasi
    validate_classification(df)

    print("✓ Klasifikasi valid")

    # 6. Cek duplikat
    duplicate_info = check_duplicates(df)

    print(
        f"✓ Pemeriksaan duplikat selesai "
        f"({duplicate_info['duplicate_count']} baris terdeteksi)"
    )

    print("========================================")
    print("VALIDATION BERHASIL")
    print("========================================")

    return {
        "valid": True,
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_count": duplicate_info[
            "duplicate_count"
        ],
    }