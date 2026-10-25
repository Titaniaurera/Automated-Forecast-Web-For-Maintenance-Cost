import pandas as pd
import numpy as np


# ============================================================
# KONFIGURASI
# ============================================================

TARGET_COLUMN = "Amount in doc. curr."
DATE_COLUMN = "Document Date"
PO_COLUMN = "Purchasing Document"


# ============================================================
# 1. VALIDASI KOLOM DASAR
# ============================================================

def validate_required_columns(
    df: pd.DataFrame
):
    """
    Memastikan kolom yang dibutuhkan tersedia.
    """

    required_columns = [
        DATE_COLUMN,
        TARGET_COLUMN,
        PO_COLUMN
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Kolom berikut tidak ditemukan: "
            + ", ".join(missing_columns)
        )


# ============================================================
# 2. SIAPKAN DATA DASAR
# ============================================================

def prepare_base_data(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Menyiapkan data transaksi sebelum agregasi event.

    Unit event:
        Document Date + Purchasing Document
    """

    if df is None:

        raise ValueError(
            "DataFrame tidak boleh None."
        )

    if df.empty:

        raise ValueError(
            "DataFrame kosong."
        )

    validate_required_columns(df)

    data = df.copy()

    # --------------------------------------------------------
    # TANGGAL
    # --------------------------------------------------------

    data[DATE_COLUMN] = pd.to_datetime(
        data[DATE_COLUMN],
        errors="coerce"
    )

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    data[TARGET_COLUMN] = (
        data[TARGET_COLUMN]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    data[TARGET_COLUMN] = pd.to_numeric(
        data[TARGET_COLUMN],
        errors="coerce"
    )

    # Nilai amount dijadikan absolut

    data[TARGET_COLUMN] = (
        data[TARGET_COLUMN]
        .abs()
    )

    # --------------------------------------------------------
    # PO
    # --------------------------------------------------------

    data[PO_COLUMN] = (
        data[PO_COLUMN]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    # --------------------------------------------------------
    # HAPUS DATA TIDAK VALID
    # --------------------------------------------------------

    data = data.dropna(
        subset=[
            DATE_COLUMN,
            TARGET_COLUMN,
            PO_COLUMN
        ]
    ).copy()

    # Jangan gunakan string kosong sebagai PO

    data = data[
        data[PO_COLUMN].str.strip() != ""
    ].copy()

    # Nama internal PO

    data = data.rename(
        columns={
            PO_COLUMN: "PO_KEY"
        }
    )

    return data


# ============================================================
# 3. AGREGASI EVENT TANGGAL + PO
# ============================================================

def aggregate_po_events(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Mengubah transaksi menjadi event.

    Satu event =
        Document Date + PO_KEY

    Target event:
        total_amount

    Jumlah transaksi:
        jumlah_transaksi_po
    """

    data = prepare_base_data(df)

    base_data = (
        data
        .groupby(
            [
                DATE_COLUMN,
                "PO_KEY"
            ]
        )
        .agg(
            total_amount=(
                TARGET_COLUMN,
                "sum"
            ),

            jumlah_transaksi_po=(
                TARGET_COLUMN,
                "count"
            )
        )
        .reset_index()
        .sort_values(
            [
                DATE_COLUMN,
                "PO_KEY"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return base_data


# ============================================================
# 4. FITUR WAKTU DASAR
# ============================================================

def create_time_features(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Membuat fitur kalender berdasarkan Document Date.
    """

    data = data.copy()

    data[DATE_COLUMN] = pd.to_datetime(
        data[DATE_COLUMN],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Fitur waktu
    # --------------------------------------------------------

    data["tahun"] = (
        data[DATE_COLUMN].dt.year
    )

    data["bulan"] = (
        data[DATE_COLUMN].dt.month
    )

    data["hari"] = (
        data[DATE_COLUMN].dt.day
    )

    data["weekday"] = (
        data[DATE_COLUMN].dt.weekday
    )

    data["weekofyear"] = (
        data[DATE_COLUMN]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    data["quarter"] = (
        data[DATE_COLUMN].dt.quarter
    )

    data["is_month_start"] = (
        data[DATE_COLUMN]
        .dt.is_month_start
        .astype(int)
    )

    data["is_month_end"] = (
        data[DATE_COLUMN]
        .dt.is_month_end
        .astype(int)
    )

    return data


# ============================================================
# 5. FITUR RIWAYAT PO
# ============================================================

def create_po_features(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Membuat fitur historis berdasarkan PO.

    Seluruh lag menggunakan data sebelumnya
    agar tidak mengambil informasi masa depan.
    """

    data = data.copy()

    data = data.sort_values(
        [
            DATE_COLUMN,
            "PO_KEY"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # JARAK HARI EVENT PO SEBELUMNYA
    # --------------------------------------------------------

    data[
        "jarak_hari_po_sebelumnya"
    ] = (
        data
        .groupby("PO_KEY")[DATE_COLUMN]
        .diff()
        .dt.days
        .fillna(0)
    )

    # --------------------------------------------------------
    # EVENT KE BERAPA UNTUK PO TERSEBUT
    # --------------------------------------------------------

    data[
        "po_event_ke"
    ] = (
        data
        .groupby("PO_KEY")
        .cumcount()
    )

    # --------------------------------------------------------
    # LAG PO
    # --------------------------------------------------------

    for lag in [1, 2, 3, 4, 5]:

        data[
            f"po_lag_{lag}"
        ] = (
            data
            .groupby("PO_KEY")[
                "total_amount"
            ]
            .shift(lag)
        )

    # --------------------------------------------------------
    # ROLLING MEAN + STD PO
    # --------------------------------------------------------

    for window in [3, 5, 10]:

        data[
            f"po_rolling_{window}_mean"
        ] = (
            data
            .groupby("PO_KEY")[
                "total_amount"
            ]
            .transform(
                lambda x:
                    x.shift(1)
                    .rolling(
                        window,
                        min_periods=1
                    )
                    .mean()
            )
        )

        data[
            f"po_rolling_{window}_std"
        ] = (
            data
            .groupby("PO_KEY")[
                "total_amount"
            ]
            .transform(
                lambda x:
                    x.shift(1)
                    .rolling(
                        window,
                        min_periods=2
                    )
                    .std()
            )
        )

    return data


# ============================================================
# 6. FITUR GLOBAL
# ============================================================

def create_global_features(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Membuat lag dan rolling berdasarkan seluruh
    event, bukan berdasarkan PO tertentu.
    """

    data = data.copy()

    data = data.sort_values(
        [
            DATE_COLUMN,
            "PO_KEY"
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # GLOBAL LAG
    # --------------------------------------------------------

    for lag in [1, 2, 3]:

        data[
            f"global_lag_{lag}"
        ] = (
            data["total_amount"]
            .shift(lag)
        )

    # --------------------------------------------------------
    # GLOBAL ROLLING
    # --------------------------------------------------------

    for window in [3, 5, 10]:

        data[
            f"global_rolling_{window}_mean"
        ] = (
            data["total_amount"]
            .shift(1)
            .rolling(
                window,
                min_periods=1
            )
            .mean()
        )

    return data


# ============================================================
# 7. FITUR MUSIMAN
# ============================================================

def create_seasonal_features(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Fitur musiman yang digunakan dalam eksperimen
    model Rutin.
    """

    data = data.copy()

    # --------------------------------------------------------
    # SEMESTER
    # --------------------------------------------------------

    data["semester"] = np.where(
        data["bulan"] <= 6,
        1,
        2
    )

    # --------------------------------------------------------
    # POSISI TAHUN
    # --------------------------------------------------------

    data["awal_tahun"] = (
        data["bulan"]
        .isin([1, 2, 3])
        .astype(int)
    )

    data["tengah_tahun"] = (
        data["bulan"]
        .isin([4, 5, 6, 7, 8, 9])
        .astype(int)
    )

    data["akhir_tahun"] = (
        data["bulan"]
        .isin([10, 11, 12])
        .astype(int)
    )

    # --------------------------------------------------------
    # POSISI BULAN
    # --------------------------------------------------------

    data["awal_bulan"] = (
        data["hari"] <= 10
    ).astype(int)

    data["tengah_bulan"] = (
        (
            data["hari"] > 10
        )
        &
        (
            data["hari"] <= 20
        )
    ).astype(int)

    data["akhir_bulan"] = (
        data["hari"] > 20
    ).astype(int)

    # --------------------------------------------------------
    # WEEKEND
    # --------------------------------------------------------

    data["is_weekend"] = (
        data["weekday"] >= 5
    ).astype(int)

    # --------------------------------------------------------
    # CYCLICAL MONTH
    # --------------------------------------------------------

    data["bulan_sin"] = (
        np.sin(
            2
            * np.pi
            * data["bulan"]
            / 12
        )
    )

    data["bulan_cos"] = (
        np.cos(
            2
            * np.pi
            * data["bulan"]
            / 12
        )
    )

    # --------------------------------------------------------
    # CYCLICAL WEEK
    # --------------------------------------------------------

    data["week_sin"] = (
        np.sin(
            2
            * np.pi
            * data["weekofyear"]
            / 52
        )
    )

    data["week_cos"] = (
        np.cos(
            2
            * np.pi
            * data["weekofyear"]
            / 52
        )
    )

    return data


# ============================================================
# 8. ROLLING MEDIAN PO
# ============================================================

def create_po_rolling_median(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Rolling median historis per PO.
    """

    data = data.copy()

    for window in [3, 5, 10, 20]:

        data[
            f"po_rolling_{window}_median"
        ] = (
            data
            .groupby("PO_KEY")[
                "total_amount"
            ]
            .transform(
                lambda x:
                    x.shift(1)
                    .rolling(
                        window,
                        min_periods=1
                    )
                    .median()
            )
        )

    return data


# ============================================================
# 9. LAG PANJANG PO
# ============================================================

def create_long_po_lags(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Lag panjang berdasarkan histori PO.
    """

    data = data.copy()

    for lag in [10, 15, 20]:

        data[
            f"po_lag_{lag}"
        ] = (
            data
            .groupby("PO_KEY")[
                "total_amount"
            ]
            .shift(lag)
        )

    return data


# ============================================================
# 10. FITUR TREND
# ============================================================

def create_trend_features(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Fitur trend global berdasarkan urutan event
    dan jarak hari sejak event pertama.
    """

    data = data.copy()

    data = data.sort_values(
        [
            DATE_COLUMN,
            "PO_KEY"
        ]
    ).reset_index(
        drop=True
    )

    data["trend_event"] = (
        np.arange(
            len(data)
        )
    )

    data["trend_hari"] = (
        data[DATE_COLUMN]
        - data[DATE_COLUMN].min()
    ).dt.days

    return data


# ============================================================
# 11. TARGET LOG
# ============================================================

def create_target(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Membuat target log1p.

    Target:
        total_amount

    Target model:
        target_log
    """

    data = data.copy()

    data["total_amount"] = pd.to_numeric(
        data["total_amount"],
        errors="coerce"
    )

    data["total_amount"] = (
        data["total_amount"]
        .fillna(0)
        .clip(lower=0)
    )

    data["target_log"] = (
        np.log1p(
            data["total_amount"]
        )
    )

    return data


# ============================================================
# 12. DAFTAR FITUR MODEL
# ============================================================

def get_model_features(
    include_seasonal=True,
    include_median=True,
    include_long_lag=True,
    include_trend=True
):
    """
    Mengembalikan daftar fitur numerik yang digunakan model.
    """

    features = [

        # ----------------------------------------------------
        # WAKTU
        # ----------------------------------------------------

        "tahun",
        "bulan",
        "hari",
        "weekday",
        "weekofyear",
        "quarter",
        "is_month_start",
        "is_month_end",

        # ----------------------------------------------------
        # EVENT PO
        # ----------------------------------------------------

        "jumlah_transaksi_po",
        "jarak_hari_po_sebelumnya",
        "po_event_ke",

        # ----------------------------------------------------
        # PO LAG
        # ----------------------------------------------------

        "po_lag_1",
        "po_lag_2",
        "po_lag_3",
        "po_lag_4",
        "po_lag_5",

        # ----------------------------------------------------
        # PO ROLLING
        # ----------------------------------------------------

        "po_rolling_3_mean",
        "po_rolling_3_std",

        "po_rolling_5_mean",
        "po_rolling_5_std",

        "po_rolling_10_mean",
        "po_rolling_10_std",

        # ----------------------------------------------------
        # GLOBAL
        # ----------------------------------------------------

        "global_lag_1",
        "global_lag_2",
        "global_lag_3",

        "global_rolling_3_mean",
        "global_rolling_5_mean",
        "global_rolling_10_mean",
    ]

    # --------------------------------------------------------
    # MUSIMAN
    # --------------------------------------------------------

    if include_seasonal:

        features.extend(
            [

                "semester",

                "awal_tahun",
                "tengah_tahun",
                "akhir_tahun",

                "awal_bulan",
                "tengah_bulan",
                "akhir_bulan",

                "is_weekend",

                "bulan_sin",
                "bulan_cos",

                "week_sin",
                "week_cos",
            ]
        )

    # --------------------------------------------------------
    # ROLLING MEDIAN
    # --------------------------------------------------------

    if include_median:

        features.extend(
            [

                "po_rolling_3_median",
                "po_rolling_5_median",
                "po_rolling_10_median",
                "po_rolling_20_median",
            ]
        )

    # --------------------------------------------------------
    # LAG PANJANG
    # --------------------------------------------------------

    if include_long_lag:

        features.extend(
            [

                "po_lag_10",
                "po_lag_15",
                "po_lag_20",
            ]
        )

    # --------------------------------------------------------
    # TREND
    # --------------------------------------------------------

    if include_trend:

        features.extend(
            [

                "trend_event",
                "trend_hari",
            ]
        )

    return features


# ============================================================
# 13. BERSIHKAN FEATURE
# ============================================================

def clean_features(
    data: pd.DataFrame,
    feature_columns=None
) -> pd.DataFrame:
    """
    Membersihkan nilai NaN dan infinite pada fitur.
    """

    data = data.copy()

    if feature_columns is None:

        feature_columns = (
            get_model_features()
        )

    existing_features = [
        column
        for column in feature_columns
        if column in data.columns
    ]

    for column in existing_features:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data[existing_features] = (
        data[existing_features]
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )

    return data


# ============================================================
# 14. PIPELINE UTAMA
# ============================================================

def build_features(
    df: pd.DataFrame,
    include_seasonal=True,
    include_median=True,
    include_long_lag=True,
    include_trend=True
):
    """
    Pipeline Feature Engineering.

    Alur:

        Raw transaksi
             ↓
        Document Date + PO
             ↓
        Event aggregation
             ↓
        Time features
             ↓
        PO features
             ↓
        Global features
             ↓
        Seasonal features
             ↓
        Rolling median
             ↓
        Long lag
             ↓
        Trend
             ↓
        target_log
             ↓
        clean features

    Return:
        data_features
        feature_columns
    """

    print(
        "\n========================================"
    )

    print(
        "FEATURE ENGINEERING"
    )

    print(
        "EVENT-BASED PO FORECASTING"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # 1. EVENT
    # --------------------------------------------------------

    print(
        "\n[1] Membuat event Document Date + PO..."
    )

    data = aggregate_po_events(
        df
    )

    print(
        "Jumlah event:",
        len(data)
    )

    # --------------------------------------------------------
    # 2. TIME
    # --------------------------------------------------------

    print(
        "\n[2] Membuat fitur waktu..."
    )

    data = create_time_features(
        data
    )

    # --------------------------------------------------------
    # 3. PO
    # --------------------------------------------------------

    print(
        "\n[3] Membuat fitur historis PO..."
    )

    data = create_po_features(
        data
    )

    # --------------------------------------------------------
    # 4. GLOBAL
    # --------------------------------------------------------

    print(
        "\n[4] Membuat fitur global..."
    )

    data = create_global_features(
        data
    )

    # --------------------------------------------------------
    # 5. SEASONAL
    # --------------------------------------------------------

    if include_seasonal:

        print(
            "\n[5] Membuat fitur musiman..."
        )

        data = create_seasonal_features(
            data
        )

    # --------------------------------------------------------
    # 6. MEDIAN
    # --------------------------------------------------------

    if include_median:

        print(
            "\n[6] Membuat rolling median..."
        )

        data = create_po_rolling_median(
            data
        )

    # --------------------------------------------------------
    # 7. LONG LAG
    # --------------------------------------------------------

    if include_long_lag:

        print(
            "\n[7] Membuat lag panjang..."
        )

        data = create_long_po_lags(
            data
        )

    # --------------------------------------------------------
    # 8. TREND
    # --------------------------------------------------------

    if include_trend:

        print(
            "\n[8] Membuat trend features..."
        )

        data = create_trend_features(
            data
        )

    # --------------------------------------------------------
    # 9. TARGET
    # --------------------------------------------------------

    print(
        "\n[9] Membuat target_log..."
    )

    data = create_target(
        data
    )

    # --------------------------------------------------------
    # 10. MODEL FEATURES
    # --------------------------------------------------------

    feature_columns = get_model_features(
        include_seasonal=include_seasonal,
        include_median=include_median,
        include_long_lag=include_long_lag,
        include_trend=include_trend
    )

    # --------------------------------------------------------
    # 11. CLEAN FEATURES
    # --------------------------------------------------------

    print(
        "\n[10] Membersihkan feature..."
    )

    data = clean_features(
        data,
        feature_columns
    )

    print(
        "\n========================================"
    )

    print(
        "FEATURE ENGINEERING SELESAI"
    )

    print(
        "========================================"
    )

    print(
        "Jumlah event:",
        len(data)
    )

    print(
        "Jumlah fitur numerik:",
        len(feature_columns)
    )

    return data, feature_columns


# ============================================================
# 15. TARGET MODEL
# ============================================================

def get_target_column():
    """
    Target yang digunakan model.
    """

    return "target_log"


# ============================================================
# 16. TARGET ASLI
# ============================================================

def get_original_target_column():
    """
    Target dalam skala rupiah/asli.
    """

    return "total_amount"