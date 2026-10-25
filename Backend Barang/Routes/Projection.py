from fastapi import APIRouter


import pandas as pd

import math







from services.projection import (

    build_stock_projection

)







from services.gi_storage import (

    load_latest_gi_forecast as load_latest_forecast

)







from services.gr_storage import (

    load_latest_gr_forecast

)







from services.stock_storage import (

    load_latest_stock

)














router = APIRouter()















# ==========================================
# CLEAN JSON VALUE
#
# Menghapus:
#
# NaN
# Infinity
# -Infinity
#
# Termasuk:
#
# list
# dict
#
# ==========================================


def clean_nan_inf(obj):


    if isinstance(obj, dict):


        return {


            key:


            clean_nan_inf(value)


            for key, value in obj.items()


        }









    if isinstance(obj, list):


        return [


            clean_nan_inf(item)


            for item in obj


        ]









    if isinstance(obj, float):


        if math.isnan(obj) or math.isinf(obj):


            return None



        return obj







    return obj



















# ==========================================
# GET STOCK PROJECTION TERBARU
# ==========================================


@router.get("/api/projection/latest")

def get_latest_projection():









    # ======================================
    # LOAD GI
    #
    # GI WAJIB
    #
    # ======================================


    gi_data = load_latest_forecast()











    if gi_data is None:


        return {


            "exists": False,


            "message":


                "Forecast GI belum tersedia"


        }













    # ======================================
    # TAMBAHAN
    #
    # AMBIL FILTER DATA GI
    #
    # Jangan hilangkan ini
    #
    # Dipakai frontend dropdown:
    #
    # Material Type
    # MRP Controller
    # Storage Location
    # Plant
    #
    # ======================================


    gi_filter_data = []









    if isinstance(gi_data, dict):


        gi_filter_data = gi_data.get(


            "filter_data",


            []


        )















    # ======================================
    # LOAD GR
    #
    # GR OPTIONAL
    #
    # ======================================


    gr_data = load_latest_gr_forecast()











    if gr_data is None:


        gr_data = {


            "data": []


        }















    # ======================================
    # LOAD STOCK
    #
    # STOCK OPTIONAL
    #
    # ======================================


    stock_data = load_latest_stock()











    if stock_data is None:


        stock_data = {


            "data": []


        }













    # ======================================
    # AMBIL DATA ARRAY
    #
    # Storage format:
    #
    # {
    #    "data":[],
    #    "filter_data":[]
    # }
    #
    # ======================================


    if isinstance(gi_data, dict):


        gi_data = gi_data.get(


            "data",


            []

        )













    if isinstance(gr_data, dict):


        gr_data = gr_data.get(


            "data",


            []

        )













    if isinstance(stock_data, dict):


        stock_data = stock_data.get(


            "data",


            []

        )

            # ======================================
    # DATAFRAME
    # ======================================


    df_gi = pd.DataFrame(

        gi_data

    )





    df_gr = pd.DataFrame(

        gr_data

    )





    df_stock = pd.DataFrame(

        stock_data

    )













    print("\n")

    print("=" * 60)

    print("PROJECTION ROUTE")

    print("=" * 60)









    print(

        "GI ROW:",

        len(df_gi)

    )









    print(

        "GR ROW:",

        len(df_gr)

    )









    print(

        "STOCK ROW:",

        len(df_stock)

    )









    print("=" * 60)













    # ======================================
    # BUILD PROJECTION
    # ======================================


    result = build_stock_projection(





        df_gi,





        df_gr,





        df_stock





    )













    # ======================================
    # CONVERT DATAFRAME TO DICT
    # ======================================


    data = result.to_dict(

        orient="records"

    )













    # ======================================
    # CHECK FORECAST TREND FIELD
    #
    # Memastikan:
    #
    # Trend_Bulan
    # Forecast_Bulan
    #
    # tidak hilang sebelum response
    #
    # ======================================


    if len(data) > 0:



        print("\n")

        print("=" * 60)

        print("TREND DEBUG RESPONSE")

        print("=" * 60)





        print(

            "Trend_Bulan:",

            data[0].get(

                "Trend_Bulan",

                None

            )

        )





        print(

            "Forecast_Bulan:",

            data[0].get(

                "Forecast_Bulan",

                None

            )

        )





        print("=" * 60)









        required_trend_fields = [



            "Trend_Bulan",



            "Forecast_Bulan"



        ]









        for field in required_trend_fields:



            if field not in data[0]:


                print(

                    "WARNING FIELD HILANG:",

                    field

                )













    # ======================================
    # FINAL JSON CLEANING
    #
    # Bersihkan:
    #
    # NaN
    # Infinity
    # -Infinity
    #
    # termasuk:
    #
    # Trend_GI
    # Trend_GR
    # Trend_Bulan
    #
    # ======================================


    data = clean_nan_inf(data)

        # ======================================
    # DEBUG FILTER DATA
    #
    # memastikan filter ikut terkirim
    #
    # ======================================


    print("\n")

    print("=" * 60)

    print("FILTER DATA RESPONSE")

    print("=" * 60)









    print(

        "JUMLAH FILTER:",

        len(gi_filter_data)

    )









    if len(gi_filter_data) > 0:



        print(

            "CONTOH FILTER:",

            gi_filter_data[0]

        )









    print("=" * 60)













    # ======================================
    # RESPONSE
    #
    # Tambahan:
    #
    # filter_data
    #
    # agar frontend bisa
    # mengisi dropdown setelah refresh
    #
    # ======================================


    return {


        "exists": True,


        "data": data,


        "filter_data": gi_filter_data


    }

    

