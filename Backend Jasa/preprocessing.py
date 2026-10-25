import pandas as pd
import numpy as np


# ============================================================
# KONFIGURASI
# ============================================================

TARGET_COLUMN = "Amount in doc. curr."

LOWER_PERCENTILE = 0.5
UPPER_PERCENTILE = 95.0


# ============================================================
# 1. MEMBERSIHKAN NAMA KOLOM
# ============================================================

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan nama kolom agar konsisten.

    Contoh:
        ' Amount in doc. curr. ' -> 'Amount in doc. curr.'
    """

    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


# ============================================================
# 2. MEMBERSIHKAN DATA NUMERIK
# ============================================================

def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan kolom numerik yang dibutuhkan untuk forecasting.
    """

    df = df.copy()

    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{TARGET_COLUMN}' tidak ditemukan."
        )

    # Pastikan target berupa numerik
    df[TARGET_COLUMN] = pd.to_numeric(
        df[TARGET_COLUMN],
        errors="coerce"
    )

    # Quantity jika tersedia
    if "Quantity" in df.columns:

        df["Quantity"] = pd.to_numeric(
            df["Quantity"],
            errors="coerce"
        )

    # Amount local currency jika tersedia
    if "Amount in local currency" in df.columns:

        df["Amount in local currency"] = pd.to_numeric(
            df["Amount in local currency"],
            errors="coerce"
        )

    return df


# ============================================================
# 3. MEMBERSIHKAN TANGGAL
# ============================================================

def clean_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mengubah kolom tanggal menjadi format datetime.

    Posting Date menjadi tanggal utama untuk forecasting
    pembayaran bulanan.
    """

    df = df.copy()

    if "Posting Date" in df.columns:

        df["Posting Date"] = pd.to_datetime(
            df["Posting Date"],
            errors="coerce"
        )

    if "Document Date" in df.columns:

        df["Document Date"] = pd.to_datetime(
            df["Document Date"],
            errors="coerce"
        )

    return df


# ============================================================
# 4. MEMBERSIHKAN KLASIFIKASI
# ============================================================

def clean_classification(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menyeragamkan nilai Klasifikasi.

    Kategori yang digunakan:
        Rutin
        Non Rutin
        OVH

    Catatan:
    Jika OVH pada dataset ternyata sudah termasuk Non Rutin,
    fungsi ini tetap mempertahankan nilai aslinya.
    """

    df = df.copy()

    if "Klasifikasi" not in df.columns:
        raise ValueError(
            "Kolom 'Klasifikasi' tidak ditemukan."
        )

    df["Klasifikasi"] = (
        df["Klasifikasi"]
        .astype("string")
        .str.strip()
    )

    # Menyamakan variasi penulisan
    df["Klasifikasi"] = df["Klasifikasi"].replace(
        {
            "rutin": "Rutin",
            "RUTIN": "Rutin",

            "non rutin": "Non Rutin",
            "NON RUTIN": "Non Rutin",
            "non-rutin": "Non Rutin",
            "NON-RUTIN": "Non Rutin",

            "ovh": "OVH",
            "Ovh": "OVH",
        }
    )

    return df


# ============================================================
# 5. MEMBERSIHKAN SHORT TEXT
# ============================================================

def clean_short_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan Short Text.

    Short Text tidak digunakan untuk menentukan target,
    tetapi tetap dipertahankan untuk analisis kontribusi jasa.
    """

    df = df.copy()

    if "Short Text" in df.columns:

        df["Short Text"] = (
            df["Short Text"]
            .astype("string")
            .str.strip()
        )

    return df


# ============================================================
# 6. MEMBUAT PERIODE BULANAN
# ============================================================

def create_period_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membuat informasi waktu untuk forecasting bulanan.

    Menggunakan Posting Date sebagai dasar periode pembayaran.
    """

    df = df.copy()

    if "Posting Date" not in df.columns:
        raise ValueError(
            "Kolom 'Posting Date' diperlukan "
            "untuk forecasting bulanan."
        )

    # Tahun
    df["Posting Year"] = (
        df["Posting Date"].dt.year
    )

    # Bulan
    df["Posting Month"] = (
        df["Posting Date"].dt.month
    )

    # Nama bulan
    df["Posting Month Name"] = (
        df["Posting Date"].dt.strftime("%B")
    )

    # Periode YYYY-MM
    df["Period"] = (
        df["Posting Date"]
        .dt.to_period("M")
        .astype(str)
    )

    return df


# ============================================================
# 7. MENGHAPUS DATA INVALID
# ============================================================

def remove_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghapus baris yang tidak dapat digunakan untuk training.

    Data dengan target kosong tidak digunakan dalam training.

    Catatan:
    Data asli di MySQL TIDAK dihapus.
    """

    df = df.copy()

    before = len(df)

    # Target kosong tidak dapat digunakan untuk training
    df = df[
        df[TARGET_COLUMN].notna()
    ].copy()

    # Posting Date kosong tidak dapat digunakan
    # untuk forecasting bulanan
    if "Posting Date" in df.columns:

        df = df[
            df["Posting Date"].notna()
        ].copy()

    after = len(df)

    print(
        f"[PREPROCESSING] "
        f"Baris sebelum cleaning : {before}"
    )

    print(
        f"[PREPROCESSING] "
        f"Baris setelah cleaning : {after}"
    )

    print(
        f"[PREPROCESSING] "
        f"Baris tidak digunakan  : {before - after}"
    )

    return df


# ============================================================
# 8. WINSORIZING
# ============================================================

def winsorize_target(
    df: pd.DataFrame,
    lower_percentile: float = LOWER_PERCENTILE,
    upper_percentile: float = UPPER_PERCENTILE,
) -> pd.DataFrame:
    """
    Melakukan winsorizing pada Amount in doc. curr.

    Batas:
        Lower : 0.5 percentile
        Upper : 95 percentile

    Nilai di bawah lower bound akan dinaikkan ke lower bound.

    Nilai di atas upper bound akan diturunkan ke upper bound.

    Data asli tidak diubah.
    """

    df = df.copy()

    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{TARGET_COLUMN}' tidak ditemukan."
        )

    if df.empty:
        return df

    values = df[TARGET_COLUMN].dropna()

    if values.empty:
        return df

    lower_bound = np.percentile(
        values,
        lower_percentile
    )

    upper_bound = np.percentile(
        values,
        upper_percentile
    )

    print("\n========================================")
    print("WINSORIZING")
    print("========================================")

    print(
        f"Target              : {TARGET_COLUMN}"
    )

    print(
        f"Lower percentile    : "
        f"{lower_percentile}%"
    )

    print(
        f"Upper percentile    : "
        f"{upper_percentile}%"
    )

    print(
        f"Lower bound         : "
        f"{lower_bound:,.2f}"
    )

    print(
        f"Upper bound         : "
        f"{upper_bound:,.2f}"
    )

    # Hitung jumlah outlier sebelum dicapping
    lower_outliers = (
        df[TARGET_COLUMN] < lower_bound
    ).sum()

    upper_outliers = (
        df[TARGET_COLUMN] > upper_bound
    ).sum()

    # Buat kolom hasil preprocessing
    df["Amount in doc. curr. original"] = (
        df[TARGET_COLUMN]
    )

    # Winsorizing
    df[TARGET_COLUMN] = (
        df[TARGET_COLUMN]
        .clip(
            lower=lower_bound,
            upper=upper_bound
        )
    )

    print(
        f"Outlier bawah      : "
        f"{lower_outliers}"
    )

    print(
        f"Outlier atas       : "
        f"{upper_outliers}"
    )

    print("Winsorizing selesai.")

    return df


# ============================================================
# 9. PIPELINE PREPROCESSING UTAMA
# ============================================================

def preprocess_data(
    df: pd.DataFrame,
    apply_winsorizing: bool = True,
) -> pd.DataFrame:
    """
    Pipeline preprocessing lengkap.

    Urutan:

    1. Clean column names
    2. Clean numeric columns
    3. Clean dates
    4. Clean classification
    5. Clean Short Text
    6. Create monthly period
    7. Remove invalid rows
    8. Winsorizing
    """

    print("\n========================================")
    print("START PREPROCESSING")
    print("========================================")

    if df is None:
        raise ValueError(
            "DataFrame tidak boleh None."
        )

    if df.empty:
        raise ValueError(
            "DataFrame kosong."
        )

    # Jangan mengubah dataframe asli
    processed = df.copy()

    # --------------------------------------------------------
    # 1. Nama kolom
    # --------------------------------------------------------

    processed = clean_column_names(
        processed
    )

    # --------------------------------------------------------
    # 2. Numeric
    # --------------------------------------------------------

    processed = clean_numeric_columns(
        processed
    )

    # --------------------------------------------------------
    # 3. Date
    # --------------------------------------------------------

    processed = clean_date_columns(
        processed
    )

    # --------------------------------------------------------
    # 4. Classification
    # --------------------------------------------------------

    processed = clean_classification(
        processed
    )

    # --------------------------------------------------------
    # 5. Short Text
    # --------------------------------------------------------

    processed = clean_short_text(
        processed
    )

    # --------------------------------------------------------
    # 6. Period
    # --------------------------------------------------------

    processed = create_period_features(
        processed
    )

    # --------------------------------------------------------
    # 7. Remove invalid rows
    # --------------------------------------------------------

    processed = remove_invalid_rows(
        processed
    )

    # --------------------------------------------------------
    # 8. Winsorizing
    # --------------------------------------------------------

    if apply_winsorizing:

        processed = winsorize_target(
            processed,
            lower_percentile=LOWER_PERCENTILE,
            upper_percentile=UPPER_PERCENTILE,
        )

    print("\n========================================")
    print("PREPROCESSING SELESAI")
    print("========================================")

    print(
        f"Total data hasil preprocessing: "
        f"{len(processed)}"
    )

    return processed


# ============================================================
# 10. MEMISAHKAN DATA RUTIN DAN NON RUTIN + OVH
# ============================================================

def split_classification(
    df: pd.DataFrame,
):
    """
    Memisahkan dataset menjadi:

        1. Rutin
        2. Non Rutin + OVH

    Data asli tidak diubah.

    Catatan:
    OVH sementara digabung dengan Non Rutin.
    Jika ternyata definisi OVH di dataset berbeda,
    bagian ini dapat disesuaikan.
    """

    df = df.copy()

    if "Klasifikasi" not in df.columns:
        raise ValueError(
            "Kolom 'Klasifikasi' tidak ditemukan."
        )

    rutin = df[
        df["Klasifikasi"] == "Rutin"
    ].copy()

    non_rutin_ovh = df[
        df["Klasifikasi"].isin(
            [
                "Non Rutin",
                "OVH",
            ]
        )
    ].copy()

    print("\n========================================")
    print("PEMISAHAN KLASIFIKASI")
    print("========================================")

    print(
        f"Data Rutin              : "
        f"{len(rutin)}"
    )

    print(
        f"Data Non Rutin + OVH    : "
        f"{len(non_rutin_ovh)}"
    )

    return rutin, non_rutin_ovh


# ============================================================
# 11. TEST
# ============================================================

if __name__ == "__main__":

    print(
        "preprocessing.py siap digunakan."
    )