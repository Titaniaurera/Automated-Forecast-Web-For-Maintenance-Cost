from fastapi import (

    APIRouter,

    UploadFile,

    File

)



from services.stock_service import (

    upload_stock

)



from services.stock_storage import (

    save_latest_stock,

    load_latest_stock

)






router = APIRouter()







# =====================================================
# HOME STOCK
# =====================================================


@router.get("/stock")

def home_stock():


    return {


        "message":

            "Current Stock API Running 🚀"


    }









# =====================================================
# UPLOAD CURRENT STOCK
# =====================================================


@router.post("/api/upload-stock")

async def upload_current_stock(


    file: UploadFile = File(...)


):


    print("\n")

    print("=" * 60)

    print("UPLOAD CURRENT STOCK")

    print("=" * 60)






    # =================================================
    # PROCESS STOCK FILE
    # =================================================


    result = await upload_stock(

        file

    )








    # =================================================
    # SAVE LATEST STOCK
    # =================================================
    #
    # Menyimpan:
    #
    # Material
    # Stock
    # Safety Stock
    # Reorder Point
    #
    # ke latest_stock.json
    #
    # =================================================


    save_latest_stock(

        result

    )








    print(

        "CURRENT STOCK BERHASIL DISIMPAN"

    )


    print("=" * 60)

    print("\n")








    return {


        "message":

            "Current Stock berhasil diproses",



        "data":

            result



    }









# =====================================================
# GET CURRENT STOCK TERAKHIR
# =====================================================


@router.get("/api/stock/latest")

def get_latest_stock():



    data = load_latest_stock()






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
