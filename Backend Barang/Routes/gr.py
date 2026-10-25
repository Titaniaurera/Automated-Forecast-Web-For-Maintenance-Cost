from fastapi import APIRouter, UploadFile, File


from services.gr_upload_service import (
    upload_gr_excel
)


from services.gr_storage import (
    save_latest_gr_forecast,
    load_latest_gr_forecast
)



router = APIRouter()







# =====================================================
# HOME GR
# =====================================================


@router.get("/gr")
def home_gr():

    return {

        "message":
            "GR Forecast API Running 🚀"

    }









# =====================================================
# UPLOAD GOODS RECEIPT
# =====================================================


@router.post("/api/upload-gr")
async def upload_gr(
    file: UploadFile = File(...)
):


    result = await upload_gr_excel(
        file
    )




    # ===============================================
    # SIMPAN HASIL GR
    # ===============================================


    save_latest_gr_forecast(
        result
    )




    return {


        "message":

            "Data GR berhasil diproses",



        "data":

            result


    }









# =====================================================
# GET LATEST GR
# =====================================================


@router.get("/api/gr/latest")
def get_latest_gr():


    data = load_latest_gr_forecast()



    if data is None:


        return {


            "exists":

                False,


            "data":

                None


        }





    return {


        "exists":

            True,


        "data":

            data


    }
