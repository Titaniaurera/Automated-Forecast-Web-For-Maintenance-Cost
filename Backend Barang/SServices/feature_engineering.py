import pandas as pd



# =====================================================
# FEATURE ENGINEERING
# =====================================================

def feature_engineering(df):


    print("=" * 60)
    print("STEP 5 : FEATURE ENGINEERING")
    print("=" * 60)



    # =====================================================
    # VALIDASI INPUT
    # =====================================================

    required_columns = [

        "Material",

        "Material Description",

        "Bulan",

        "Qty"

    ]


    missing_columns = [

        col

        for col in required_columns

        if col not in df.columns

    ]


    if missing_columns:

        raise ValueError(

            f"Kolom berikut tidak ditemukan: {missing_columns}"

        )




    df = df.copy()



    # =====================================================
    # KONVERSI TIPE DATA
    # =====================================================


    df["Bulan"] = pd.to_datetime(

        df["Bulan"],

        errors="coerce"

    )


    df["Qty"] = pd.to_numeric(

        df["Qty"],

        errors="coerce"

    ).fillna(0)



    df = df.dropna(

        subset=["Bulan"]

    )



    # =====================================================
    # SORT DATA TIME SERIES
    # =====================================================


    df = (

        df

        .sort_values(

            [

                "Material",

                "Bulan"

            ]

        )

        .reset_index(drop=True)

    )



    print(

        "Jumlah data setelah sorting:",

        len(df)

    )





    # =====================================================
    # LAG FEATURES
    #
    # Mengambil histori konsumsi sebelumnya
    #
    # Contoh:
    #
    # Bulan Jan Qty 100
    # Bulan Feb Lag_1 = 100
    #
    # =====================================================


    df["Lag_1"] = (

        df

        .groupby("Material")["Qty"]

        .shift(1)

    )



    df["Lag_2"] = (

        df

        .groupby("Material")["Qty"]

        .shift(2)

    )



    df["Lag_3"] = (

        df

        .groupby("Material")["Qty"]

        .shift(3)

    )





    # =====================================================
    # ROLLING MEAN
    #
    # Rata-rata konsumsi 3 periode sebelumnya
    #
    # =====================================================


    df["Rolling_Mean_3"] = (

        df

        .groupby("Material")["Qty"]

        .transform(

            lambda x:

            x.shift(1)

            .rolling(

                window=3,

                min_periods=1

            )

            .mean()

        )

    )





    # =====================================================
    # ROLLING STANDARD DEVIATION
    #
    # Mengukur variasi konsumsi
    #
    # =====================================================


    df["Rolling_STD_3"] = (

        df

        .groupby("Material")["Qty"]

        .transform(

            lambda x:

            x.shift(1)

            .rolling(

                window=3,

                min_periods=2

            )

            .std()

        )

    )





    # =====================================================
    # EXPONENTIAL MOVING AVERAGE
    #
    # Memberikan bobot lebih besar
    # pada data terbaru
    #
    # =====================================================


    df["EMA_3"] = (

        df

        .groupby("Material")["Qty"]

        .transform(

            lambda x:

            x.shift(1)

            .ewm(

                span=3,

                adjust=False

            )

            .mean()

        )

    )





    # =====================================================
    # CALENDAR FEATURES
    # =====================================================


    df["Month"] = (

        df["Bulan"]

        .dt.month

    )



    df["Quarter"] = (

        df["Bulan"]

        .dt.quarter

    )



    df["Year"] = (

        df["Bulan"]

        .dt.year

    )





    # =====================================================
    # HANDLE MISSING VALUE
    #
    # Awal histori tidak memiliki lag.
    #
    # Contoh:
    #
    # Bulan pertama:
    # Lag_1 = kosong
    #
    # Diganti menggunakan histori terdekat.
    #
    # =====================================================


    feature_columns = [

        "Lag_1",

        "Lag_2",

        "Lag_3",

        "Rolling_Mean_3",

        "Rolling_STD_3",

        "EMA_3"

    ]



    for col in feature_columns:


        df[col] = (

            df

            .groupby("Material")[col]

            .transform(

                lambda x:

                x.bfill()

                .ffill()

            )

        )



    df = df.fillna(0)





    # =====================================================
    # DEBUG OUTPUT
    # =====================================================


    print("\nFEATURE OUTPUT")

    print(

        df.head()

    )



    print("\nCOLUMN OUTPUT")

    print(

        df.columns.tolist()

    )



    print("\nSHAPE DATA")

    print(

        df.shape

    )




    print("=" * 60)
    print("FEATURE ENGINEERING SELESAI")
    print("=" * 60)



    return df