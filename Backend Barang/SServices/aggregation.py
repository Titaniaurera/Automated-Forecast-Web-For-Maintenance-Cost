import pandas as pd



def aggregation(df):


    print("=" * 60)
    print("STEP 4 : MONTHLY AGGREGATION")
    print("=" * 60)



    # =====================================================
    # VALIDASI
    # =====================================================


    required_columns = [

        "Posting Date",

        "Material",

        "Material Description",

        "Qty_Winsor",

        "Stock Akhir"

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
    # BULAN
    # =====================================================


    df["Bulan"] = (

        df["Posting Date"]

        .dt

        .to_period("M")

        .astype(str)

    )




    # =====================================================
    # SORT DATA
    # =====================================================

    df = (

        df

        .sort_values(

            [

                "Material",

                "Bulan",

                "Posting Date"

            ]

        )

    )




    # =====================================================
    # KONVERSI GI MENJADI DEMAND
    #
    # Pada titik ini:
    #
    # 261 valid
    # 281 valid
    # 961 valid
    #
    # sudah melewati movement_cleansing.
    #
    # Cancel:
    # 262
    # 282
    # 962
    #
    # sudah tidak ada.
    #
    # Jadi abs() aman digunakan.
    #
    # =====================================================


    df["Qty_Model"] = (

        df["Qty_Winsor"]

        .abs()

    )




    # =====================================================
    # AGREGASI BULANAN
    # =====================================================


    monthly_df = (

        df

        .groupby(

            [

                "Material",

                "Material Description",

                "Bulan"

            ],

            as_index=False

        )

        .agg(

            Qty=(

                "Qty_Model",

                "sum"

            ),


            Stock_Akhir=(

                "Stock Akhir",

                "last"

            )

        )

    )




    # =====================================================
    # DEBUG
    # =====================================================


    print(

        "Jumlah Material:",

        monthly_df["Material"].nunique()

    )


    print(

        "Jumlah Data Bulanan:",

        len(monthly_df)

    )


    print(

        monthly_df.head()

    )


    print("=" * 60)



    return monthly_df
    
