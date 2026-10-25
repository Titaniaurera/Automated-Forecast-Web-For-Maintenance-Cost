import pandas as pd
import numpy as np



# =====================================================
# FORECAST READINESS
# =====================================================

def readiness(df):


    print("=" * 60)
    print("STEP 2 : FORECAST READINESS")
    print("=" * 60)



    # =====================================================
    # PERIODE ANALISIS
    # =====================================================


    total_months = (

        (df["Posting Date"].max().year 
        - 
        df["Posting Date"].min().year)

        * 12

        +

        (df["Posting Date"].max().month 
        - 
        df["Posting Date"].min().month)

        + 1

    )



    print(
        "Total periode analisis:",
        total_months,
        "bulan"
    )





    # =====================================================
    # STATISTIK PER MATERIAL
    # =====================================================


    summary = (

        df.groupby(

            [
                "Material",
                "Material Description"
            ]

        )

        .agg(

            Total_Transaksi=(

                "Qty in Un. of Entry",

                "count"

            ),


            Total_Qty=(

                "Qty in Un. of Entry",

                "sum"

            ),


            Hari_Pertama=(

                "Posting Date",

                "min"

            ),


            Hari_Terakhir=(

                "Posting Date",

                "max"

            ),


            Bulan_Aktif=(

                "Posting Date",

                lambda x:

                x.dt.to_period("M").nunique()

            )

        )

        .reset_index()

    )







    # =====================================================
    # RENTANG HARI AKTIF
    # =====================================================


    summary["Rentang_Hari"] = (

        summary["Hari_Terakhir"]

        -

        summary["Hari_Pertama"]

    ).dt.days + 1







    # =====================================================
    # ACTIVITY RATIO
    # =====================================================


    summary["Activity_Ratio"] = (

        summary["Bulan_Aktif"]

        /

        total_months

    )







    # =====================================================
    # FORECAST READINESS SCORE
    # =====================================================


    summary["Forecast_Readiness"] = (

        summary["Activity_Ratio"]

        *

        100

    )







    # =====================================================
    # KATEGORI MATERIAL
    # =====================================================


    conditions = [

        summary["Forecast_Readiness"] >= 30,

        summary["Forecast_Readiness"] >= 10

    ]



    choices = [

        "High",

        "Medium"

    ]



    summary["Kategori"] = np.select(

        conditions,

        choices,

        default="Low"

    )








    # =====================================================
    # DEBUG DISTRIBUSI KATEGORI
    # =====================================================


    print("\n")

    print("=" * 60)

    print("DISTRIBUSI KATEGORI MATERIAL")

    print("=" * 60)



    kategori_summary = (

        summary["Kategori"]

        .value_counts()

        .reset_index()

    )


    kategori_summary.columns = [

        "Kategori",

        "Jumlah_Material"

    ]



    print(

        kategori_summary

    )



    print("\nDETAIL JUMLAH:")



    print(

        "High   :",

        len(

            summary[

                summary["Kategori"]

                ==

                "High"

            ]

        ),

        "material"

    )



    print(

        "Medium :",

        len(

            summary[

                summary["Kategori"]

                ==

                "Medium"

            ]

        ),

        "material"

    )



    print(

        "Low    :",

        len(

            summary[

                summary["Kategori"]

                ==

                "Low"

            ]

        ),

        "material"

    )



    print("=" * 60)







    # =====================================================
    # AMBIL MATERIAL HIGH + MEDIUM
    # =====================================================


    material_layak = (

        summary[

            summary["Kategori"].isin(

                [

                    "High",

                    "Medium"

                ]

            )

        ]

        ["Material"]

    )







    # =====================================================
    # FILTER DATA
    # =====================================================


    df_ready = df[

        df["Material"]

        .isin(

            material_layak

        )

    ].copy()







    # =====================================================
    # FINAL DEBUG
    # =====================================================


    print("\n")

    print("=" * 60)

    print("HASIL FORECAST READINESS")

    print("=" * 60)



    print(

        "Total Material Awal :",

        summary.shape[0]

    )



    print(

        "Material Layak      :",

        len(material_layak)

    )



    print(

        "Data Setelah Filter :",

        len(df_ready)

    )



    print("=" * 60)







    return df_ready