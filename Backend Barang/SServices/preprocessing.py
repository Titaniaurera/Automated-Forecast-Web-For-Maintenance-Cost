import pandas as pd



def preprocessing(df):


    print("=" * 60)
    print("STEP 1 : PREPROCESSING")
    print("=" * 60)



    # =====================================================
    # COPY DATA
    # =====================================================

    df = df.copy()



    # =====================================================
    # 1. CLEAN COLUMN NAME
    # =====================================================

    df.columns = (

        df.columns

        .astype(str)

        .str.replace(
            "\n",
            " ",
            regex=False
        )

        .str.replace(
            "\r",
            " ",
            regex=False
        )

        .str.strip()

        .str.replace(
            r"\s+",
            " ",
            regex=True
        )

    )


    print("✓ Nama kolom dibersihkan")




    # =====================================================
    # 2. VALIDASI KOLOM WAJIB
    # =====================================================


    required_columns = [

        "Posting Date",

        "Material",

        "Material Description",

        "Qty in Un. of Entry"

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



    print("✓ Validasi kolom selesai")





    # =====================================================
    # 3. NORMALISASI MATERIAL
    #
    # Supaya:
    #
    # 101001
    # 101001.0
    #
    # dianggap sama
    #
    # =====================================================


    df["Material"] = (

        df["Material"]

        .astype(str)

        .str.strip()

        .str.replace(

            ".0",

            "",

            regex=False

        )

    )



    print("✓ Material berhasil dinormalisasi")





    # =====================================================
    # 4. KONVERSI QTY
    #
    # Jangan ubah tanda negatif/positif.
    #
    # Karena:
    #
    # GI:
    # -1000
    #
    # Cancel:
    # +1000
    #
    # ditangani movement_cleansing.py
    #
    # =====================================================


    df["Qty in Un. of Entry"] = pd.to_numeric(

        df["Qty in Un. of Entry"],

        errors="coerce"

    )



    before = len(df)



    df = df.dropna(

        subset=[

            "Qty in Un. of Entry"

        ]

    )



    after = len(df)



    print(

        f"✓ Invalid Qty dihapus: {before-after} baris"

    )






    # =====================================================
    # 5. KONVERSI POSTING DATE
    # =====================================================


    df["Posting Date"] = pd.to_datetime(

        df["Posting Date"],

        errors="coerce"

    )



    before = len(df)



    df = df.dropna(

        subset=[

            "Posting Date"

        ]

    )



    after = len(df)



    print(

        f"✓ Invalid Posting Date dihapus: {before-after} baris"

    )






    # =====================================================
    # 6. NORMALISASI DESCRIPTION
    # =====================================================


    df["Material Description"] = (

        df["Material Description"]

        .fillna("")

        .astype(str)

        .str.strip()

    )






    # =====================================================
    # 7. SORT DATA
    # =====================================================


    df = (

        df

        .sort_values(

            [

                "Material",

                "Posting Date"

            ]

        )

        .reset_index(drop=True)

    )



    print(

        "✓ Data diurutkan berdasarkan Material dan tanggal"

    )





    # =====================================================
    # OUTPUT
    # =====================================================


    print("=" * 60)

    print(

        "Jumlah data akhir preprocessing:",

        len(df)

    )


    print(

        "Jumlah material unik:",

        df["Material"].nunique()

    )


    print("=" * 60)



    return df