import re
import unicodedata

import pandas as pd


# ============================================================
# KONFIGURASI
# ============================================================

CLASSIFICATION_COLUMN = "Klasifikasi"
SHORT_TEXT_COLUMN = "Short Text"

# Kategori yang disimpan di database
VALID_CLASSIFICATIONS = [
    "Rutin",
    "Non Rutin",
    "OVH",
]


# ============================================================
# 1. NORMALISASI KLASIFIKASI (tahan segala variasi tulisan)
# ============================================================

def normalize_classification(value):
    """
    Mengubah teks apa pun menjadi salah satu dari:
        Rutin | Non Rutin | OVH
    atau None jika kosong / tidak dikenali.

    Cara kerja:
        1. Samakan bentuk karakter (fullwidth, spasi NBSP) + huruf besar
        2. Buang SEMUA karakter selain huruf dan angka
           (spasi, -, _, +, /, titik, kurung, dst)
        3. Cek kata kunci pada teks yang sudah "dipadatkan"

    Contoh:
        rutin, RUTIN, "Rutin 2024"            -> Rutin
        non rutin, NON-RUTIN, nonrutin        -> Non Rutin
        ovh, OVH 2019, OVH FM 2021, O.V.H     -> OVH
        overhaul 2025                         -> OVH
        "Non Rutin + OVH" (memuat keduanya)   -> OVH
        kosong / "Preventif" / typo           -> None

    Tidak menebak: nilai asing dikembalikan None agar ditolak
    dan dilaporkan, bukan masuk database dengan label salah.
    """

    if value is None:
        return None

    if not isinstance(value, str) and pd.isna(value):
        return None

    text = unicodedata.normalize(
        "NFKC",
        str(value)
    ).upper()

    compact = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    if compact == "":
        return None

    has_ovh = (
        "OVH" in compact
        or "OVERHAUL" in compact
        or "OVERHOUL" in compact
    )

    has_non_rutin = (
        re.search(
            r"NON(RUTIN|ROUTINE?|RUTINE)",
            compact
        )
        is not None
    )

    # Urutan penting: OVH dan Non Rutin dicek SEBELUM Rutin,
    # karena "NONRUTIN" mengandung kata "RUTIN".
    if has_ovh:
        return "OVH"

    if has_non_rutin:
        return "Non Rutin"

    if compact.startswith(
        ("RUTIN", "ROUTINE", "RUTINE")
    ):
        return "Rutin"

    return None


# ============================================================
# 2. NORMALISASI SELURUH KOLOM KLASIFIKASI
# ============================================================

def normalize_classification_column(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Menormalisasi kolom Klasifikasi.

    Jika ada nilai kosong / tidak dikenali, proses DITOLAK
    dan error menyebut nilai aslinya beserta nomor baris
    di Excel (baris 1 = header).

    Pengecekan dilakukan di sini karena hanya di sini
    nilai asli masih tersedia sebelum ditimpa.
    """

    df = df.copy()

    if CLASSIFICATION_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{CLASSIFICATION_COLUMN}' "
            "tidak ditemukan."
        )

    original = df[CLASSIFICATION_COLUMN]

    normalized = original.apply(
        normalize_classification
    )

    bad_mask = normalized.isna()

    if bad_mask.any():

        bad_count = int(bad_mask.sum())

        bad_values = (
            original[bad_mask]
            .fillna("(kosong)")
            .astype(str)
            .str.strip()
            .replace("", "(kosong)")
            .unique()
            .tolist()
        )

        # nomor baris Excel = posisi + 2 (header di baris 1)
        bad_rows = [
            int(position) + 2
            for position in
            pd.Series(range(len(df)))[
                bad_mask.to_numpy()
            ]
        ]

        shown_values = bad_values[:10]
        shown_rows = bad_rows[:10]

        raise ValueError(
            f"Terdapat {bad_count} baris dengan "
            "Klasifikasi kosong / tidak dikenali.\n"
            f"Nilai: {shown_values}\n"
            f"Baris Excel: {shown_rows}"
            + (" ..." if bad_count > 10 else "")
            + "\n\nGunakan hanya: "
            "Rutin, Non Rutin, atau OVH "
            "(boleh ada tahun, mis. 'OVH 2024')."
        )

    df[CLASSIFICATION_COLUMN] = normalized

    return df


# ============================================================
# 3. BERSIHKAN SHORT TEXT
# ============================================================

def validate_short_text(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Membersihkan Short Text (strip spasi, kosong -> "").

    Short Text kosong TIDAK menghapus transaksi.
    Short Text TIDAK lagi dipakai untuk mengisi klasifikasi:
    klasifikasi kosong akan ditolak oleh
    normalize_classification_column().
    """

    df = df.copy()

    if SHORT_TEXT_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{SHORT_TEXT_COLUMN}' "
            "tidak ditemukan."
        )

    df[SHORT_TEXT_COLUMN] = (
        df[SHORT_TEXT_COLUMN]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    empty_count = int(
        (df[SHORT_TEXT_COLUMN] == "").sum()
    )

    if empty_count > 0:
        print(
            f"[INFO] {empty_count} baris dengan "
            "Short Text kosong tetap dipertahankan."
        )

    return df


# ============================================================
# 4. VALIDASI AKHIR KLASIFIKASI
# ============================================================

def validate_classification(
    df: pd.DataFrame
):
    """
    Pengaman akhir: memastikan semua baris sudah berisi
    salah satu dari Rutin / Non Rutin / OVH.
    (Pesan error detail ada di
    normalize_classification_column.)
    """

    if CLASSIFICATION_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{CLASSIFICATION_COLUMN}' "
            "tidak ditemukan."
        )

    invalid_mask = ~df[
        CLASSIFICATION_COLUMN
    ].isin(VALID_CLASSIFICATIONS)

    if invalid_mask.any():

        invalid_values = (
            df.loc[invalid_mask, CLASSIFICATION_COLUMN]
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "Klasifikasi tidak valid: "
            f"{invalid_values}. "
            "Gunakan hanya: Rutin, Non Rutin, OVH."
        )

    return True


# ============================================================
# 5-8. SPLIT DATA
# ============================================================

def _filter_by_classification(
    df: pd.DataFrame,
    labels: list
) -> pd.DataFrame:

    if CLASSIFICATION_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{CLASSIFICATION_COLUMN}' "
            "tidak ditemukan."
        )

    return (
        df[df[CLASSIFICATION_COLUMN].isin(labels)]
        .copy()
        .reset_index(drop=True)
    )


def get_rutin_data(df: pd.DataFrame) -> pd.DataFrame:
    """Hanya data Rutin."""
    return _filter_by_classification(df, ["Rutin"])


def get_non_rutin_data(df: pd.DataFrame) -> pd.DataFrame:
    """Hanya data Non Rutin."""
    return _filter_by_classification(df, ["Non Rutin"])


def get_ovh_data(df: pd.DataFrame) -> pd.DataFrame:
    """Hanya data OVH."""
    return _filter_by_classification(df, ["OVH"])


def get_non_rutin_ovh_data(df: pd.DataFrame) -> pd.DataFrame:
    """Non Rutin + OVH digabung (dataset model Non Rutin + OVH)."""
    return _filter_by_classification(df, ["Non Rutin", "OVH"])


# ============================================================
# 9. SPLIT DATA UNTUK DUA MODEL
# ============================================================

def split_forecasting_data(
    df: pd.DataFrame
) -> dict:
    """
    Hasil:
        {"rutin": DataFrame, "non_rutin_ovh": DataFrame}
    """

    validate_classification(df)

    return {
        "rutin": get_rutin_data(df),
        "non_rutin_ovh": get_non_rutin_ovh_data(df),
    }


# ============================================================
# 10. SUMMARY KLASIFIKASI
# ============================================================

def get_classification_summary(
    df: pd.DataFrame
) -> pd.DataFrame:

    if CLASSIFICATION_COLUMN not in df.columns:
        raise ValueError(
            f"Kolom '{CLASSIFICATION_COLUMN}' "
            "tidak ditemukan."
        )

    return (
        df[CLASSIFICATION_COLUMN]
        .value_counts()
        .rename_axis("Klasifikasi")
        .reset_index(name="Jumlah Data")
    )


# ============================================================
# 11. SUMMARY AMOUNT
# ============================================================

def get_classification_amount_summary(
    df: pd.DataFrame,
    target_column: str = "Amount in doc. curr."
) -> pd.DataFrame:
    """
    Ringkasan jumlah transaksi dan total amount per klasifikasi.
    Amount hanya untuk ringkasan, BUKAN untuk menentukan klasifikasi.
    """

    for column in [CLASSIFICATION_COLUMN, target_column]:
        if column not in df.columns:
            raise ValueError(
                f"Kolom '{column}' tidak ditemukan."
            )

    temp = df.copy()

    temp[target_column] = pd.to_numeric(
        temp[target_column],
        errors="coerce"
    )

    return (
        temp
        .groupby(CLASSIFICATION_COLUMN, dropna=False)
        .agg(
            jumlah_data=(target_column, "count"),
            total_amount=(target_column, "sum"),
        )
        .reset_index()
    )


# ============================================================
# 12. INFO DISTRIBUSI
# ============================================================

def validate_classification_distribution(
    df: pd.DataFrame
):
    """Hanya menampilkan distribusi; kategori kosong bukan error."""

    summary = get_classification_summary(df)

    print("\n" + "=" * 40)
    print("DISTRIBUSI KLASIFIKASI")
    print("=" * 40)

    for _, row in summary.iterrows():
        print(
            f"{row['Klasifikasi']}: "
            f"{row['Jumlah Data']} data"
        )

    print("=" * 40)

    return summary


# ============================================================
# 13. PIPELINE CLASSIFICATION
# ============================================================

def process_classification(
    df: pd.DataFrame
) -> dict:
    """
    Alur:
        Data Excel
            -> Normalisasi klasifikasi (tolak jika asing / kosong)
            -> Bersihkan Short Text
            -> Validasi akhir
            -> Split: Rutin | Non Rutin + OVH

    Untuk upload ke database, pakai result["all_data"].
    """

    if df is None:
        raise ValueError("DataFrame tidak boleh None.")

    if df.empty:
        raise ValueError("DataFrame kosong.")

    print("\n" + "=" * 40)
    print("CLASSIFICATION VALIDATION")
    print("=" * 40)
    print(f"Jumlah data awal: {len(df)}")

    print("\n[1/4] Normalisasi klasifikasi...")
    df = normalize_classification_column(df)

    print("[2/4] Membersihkan Short Text...")
    df = validate_short_text(df)

    print("[3/4] Validasi klasifikasi...")
    validate_classification(df)

    print("[4/4] Memisahkan dataset...")
    split_data = split_forecasting_data(df)

    rutin = split_data["rutin"]
    non_rutin_ovh = split_data["non_rutin_ovh"]

    summary = get_classification_summary(df)

    amount_summary = (
        get_classification_amount_summary(df)
        if "Amount in doc. curr." in df.columns
        else None
    )

    print("\n" + "=" * 40)
    print("HASIL CLASSIFICATION")
    print("=" * 40)
    print(f"Total data       : {len(df)}")
    print(f"Rutin            : {len(rutin)}")
    print(f"Non Rutin + OVH  : {len(non_rutin_ovh)}")
    print("\nDistribusi:")
    print(summary.to_string(index=False))
    print("=" * 40)

    return {
        "all_data": df,
        "rutin": rutin,
        "non_rutin_ovh": non_rutin_ovh,
        "summary": summary,
        "amount_summary": amount_summary,
    }


# ============================================================
# 14. CEK DATA SIAP FORECASTING
# ============================================================

def validate_forecasting_ready(
    df: pd.DataFrame
):
    """Validasi akhir sebelum preprocessing / feature engineering."""

    required_columns = [
        "Document Date",
        "Posting Date",
        "Amount in doc. curr.",
        "Purchasing Document",
        "Short Text",
        "Klasifikasi",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Data belum siap forecasting.\n"
            "Kolom yang hilang:\n"
            + "\n".join(f"- {column}" for column in missing)
        )

    if df.empty:
        raise ValueError("Dataset kosong.")

    amount = pd.to_numeric(
        df["Amount in doc. curr."],
        errors="coerce"
    )

    if amount.isna().all():
        raise ValueError(
            "Amount in doc. curr. "
            "tidak memiliki nilai numerik."
        )

    validate_classification(df)

    return True


# ============================================================
# 15. TEST LANGSUNG
# ============================================================

if __name__ == "__main__":

    contoh_data = pd.DataFrame({
        "Document Date": ["2026-01-05"] * 6,
        "Posting Date": ["2026-01-06"] * 6,
        "Amount in doc. curr.": [1000000, 2500000, 5000000, 3000000, 7000000, 100],
        "Purchasing Document": [f"45000000{i}" for i in range(1, 7)],
        "Short Text": ["A", "B", "C", "D", "", "F"],
        "Klasifikasi": [
            "Rutin", "RUTIN", "Non-Rutin", "ovh", "OVH 2019", "Non Rutin + OVH"
        ],
    })

    result = process_classification(contoh_data)

    print("\nDATA RUTIN:")
    print(result["rutin"].to_string(index=False))

    print("\nDATA NON RUTIN + OVH:")
    print(result["non_rutin_ovh"].to_string(index=False))

    # Tes penolakan: nilai asing + kosong
    print("\nTES PENOLAKAN:")
    bad = contoh_data.copy()
    bad.loc[1, "Klasifikasi"] = "Preventif"
    bad.loc[3, "Klasifikasi"] = None
    try:
        process_classification(bad)
    except ValueError as error:
        print(error)

    print("\nTEST SELESAI.")
