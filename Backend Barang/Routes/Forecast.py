
from fastapi import APIRouter


from services.gi_storage import (
    load_latest_gi_forecast
)


from services.gr_storage import (
    load_latest_gr_forecast
)


from services.stock_storage import (
    load_latest_stock
)



router = APIRouter()





# =====================================================
# HOME FORECAST
# =====================================================


@router.get("/forecast")
def home_forecast():


    return {

        "status":
            "success",

        "message":
            "Forecast API Running 🚀"

    }









# =====================================================
# GET LATEST FORECAST DATA
#
# Mengambil data terakhir yang pernah diupload
#
# GI -> jika ada tampil
# GR -> jika ada tampil
# STOCK -> jika ada tampil
#
# Tidak perlu upload ulang ketika buka dashboard
# =====================================================


@router.get("/api/forecast/latest")
def get_latest_forecast():


    gi_data = load_latest_gi_forecast()


    gr_data = load_latest_gr_forecast()


    stock_data = load_latest_stock()





    return {


        "exists": True,


        "gi": gi_data,


        "gr": gr_data,


        "stock": stock_data



    }









# =====================================================
# STATUS DATA UPLOAD
# =====================================================


@router.get("/api/forecast/status")
def get_forecast_status():


    gi_data = load_latest_gi_forecast()


    gr_data = load_latest_gr_forecast()


    stock_data = load_latest_stock()





    return {


        "gi_uploaded":

            gi_data is not None,



        "gr_uploaded":

            gr_data is not None,



        "stock_uploaded":

            stock_data is not None



    }
