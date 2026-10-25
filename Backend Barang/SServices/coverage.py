# =====================================================
# COVERAGE CALCULATION SERVICE
# =====================================================


import pandas as pd







# =====================================================
# SAFE NUMBER
# =====================================================


def safe_number(value):


    if value is None:

        return 0





    if pd.isna(value):

        return 0





    return float(value)









# =====================================================
# CHECK AVAILABILITY FLAG
#
# Standard flag dari projection.py:
#
# has_GI
# has_GR
# has_STOCK
#
# =====================================================


def check_ready(row):


    has_gi = row.get(

        "has_GI",

        False

    )



    has_gr = row.get(

        "has_GR",

        False

    )



    has_stock = row.get(

        "has_STOCK",

        False

    )





    return (

        has_gi

        and

        has_gr

        and

        has_stock

    )









# =====================================================
# COVERAGE AKTUAL
#
# Formula:
#
# Stock / Forecast_GI
#
#
# Aktif jika:
#
# GI tersedia
# GR tersedia
# STOCK tersedia
#
# =====================================================


def calculate_coverage(row):


    if not check_ready(row):

        return None







    stock = safe_number(

        row.get(

            "Stock",

            0

        )

    )







    forecast_gi = safe_number(

        row.get(

            "Forecast_GI",

            0

        )

    )







    if forecast_gi <= 0:

        return None







    coverage = (

        stock

        /

        forecast_gi

    )







    return round(

        coverage,

        2

    )









# =====================================================
# COVERAGE PROJECTION
#
# Formula:
#
# Projected Stock =
#
# Stock + Forecast_GR - Forecast_GI
#
#
# Coverage Projection =
#
# Projected Stock / Forecast_GI
#
#
# Aktif jika:
#
# GI tersedia
# GR tersedia
# STOCK tersedia
#
# =====================================================


def calculate_coverage_projection(row):


    if not check_ready(row):

        return {


            "Projected_Stock": None,


            "Coverage_Projection": None


        }









    stock = safe_number(

        row.get(

            "Stock",

            0

        )

    )









    forecast_gr = safe_number(

        row.get(

            "Forecast_GR",

            0

        )

    )









    forecast_gi = safe_number(

        row.get(

            "Forecast_GI",

            0

        )

    )









    if forecast_gi <= 0:


        return {


            "Projected_Stock": None,


            "Coverage_Projection": None


        }









    projected_stock = (

        stock

        +

        forecast_gr

        -

        forecast_gi

    )









    coverage_projection = (

        projected_stock

        /

        forecast_gi

    )









    return {


        "Projected_Stock":

            round(

                projected_stock,

                2

            ),





        "Coverage_Projection":

            round(

                coverage_projection,

                2

            )


    }









# =====================================================
# STATUS MATERIAL
#
# Berdasarkan Coverage Aktual
#
# =====================================================


def calculate_status(coverage):


    if coverage is None:

        return None





    if coverage >= 3:


        return "Aman"





    elif coverage >= 1:


        return "Kritis"





    else:


        return "Reorder"









# =====================================================
# APPLY COVERAGE TO DATAFRAME
# =====================================================


def coverage(df):


    print(

        "===== COVERAGE CALCULATION ====="

    )





    df = df.copy()







    # =====================================
    # COVERAGE AKTUAL
    # =====================================


    df["Coverage"] = (

        df.apply(

            calculate_coverage,

            axis=1

        )

    )









    # =====================================
    # COVERAGE PROJECTION
    # =====================================


    projection = (

        df.apply(

            calculate_coverage_projection,

            axis=1

        )

    )







    projection_df = pd.DataFrame(

        projection.tolist()

    )







    df = pd.concat(

        [

            df.reset_index(drop=True),


            projection_df.reset_index(drop=True)

        ],

        axis=1

    )









    # =====================================
    # STATUS
    #
    # Berdasarkan Coverage Aktual
    #
    # =====================================


    df["Status"] = (

        df["Coverage"]

        .apply(

            calculate_status

        )

    )









    return df