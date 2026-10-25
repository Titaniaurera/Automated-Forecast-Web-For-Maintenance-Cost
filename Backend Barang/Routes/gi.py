from fastapi import APIRouter, UploadFile, File


from services.gi_upload_service import (
    upload_gi_excel
)


from services.gi_storage import (
    save_latest_gi_forecast,
    load_latest_gi_forecast
)



router = APIRouter()





# =====================================================
# HOME GI
# =====================================================


@router.get("/gi")
def home_gi():

    return {

        "message":
            "GI Forecast API Running 🚀"

    }







# =====================================================
# UPLOAD GOODS ISSUE
# =====================================================


@router.post("/api/upload-gi")
async def upload_gi(
    file: UploadFile = File(...)
):


    result = await upload_gi_excel(
        file
    )



    # ===============================================
    # SIMPAN HASIL GI TERAKHIR
    # ===============================================


    save_latest_gi_forecast(
        result
    )



    return {

        "message":
            "Data GI berhasil diproses",


        "data":
            result

    }









# =====================================================
# GET LATEST GI
# =====================================================


@router.get("/api/gi/latest")
def get_latest_gi():


    result = load_latest_gi_forecast()



    if result is None:


        return {

            "exists":
                False,


            "data":
                None

        }





    # =================================================
    # NORMALISASI DATA STORAGE
    #
    # Jika storage menyimpan:
    #
    # {
    #   "message":"GI berhasil diproses",
    #   "data":[...]
    # }
    #
    # Ambil hanya array data.
    #
    # =================================================


    if isinstance(result, dict):


        if "data" in result:

            result = result["data"]



    return {


        "exists":
            True,


        "data":
            result

    }
