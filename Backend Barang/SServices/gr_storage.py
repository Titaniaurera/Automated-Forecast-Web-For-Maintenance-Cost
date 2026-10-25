import os
import json
import traceback






# =====================================================
# FILE STORAGE GR FORECAST
# =====================================================


DATA_FOLDER = "data"



FILE_PATH = os.path.join(

    DATA_FOLDER,

    "latest_gr_forecast.json"

)








# =====================================================
# CREATE DATA FOLDER
# =====================================================


os.makedirs(

    DATA_FOLDER,

    exist_ok=True

)









# =====================================================
# NORMALIZE GR PAYLOAD
#
# Semua GR disimpan:
#
# {
#    "data":[]
# }
#
# GR boleh kosong
#
# =====================================================


def normalize_gr_payload(data):


    if isinstance(data, list):


        return {


            "data": data


        }





    elif isinstance(data, dict):


        if "data" not in data:


            data["data"] = []



        return data






    else:


        raise ValueError(

            "Format GR forecast tidak valid"

        )












# =====================================================
# SAVE LATEST GR FORECAST
# =====================================================


def save_latest_gr_forecast(data):


    try:


        print("\n")

        print("=" * 60)

        print("SAVE GR FORECAST")

        print("=" * 60)








        # =================================================
        # NORMALIZE FORMAT
        # =================================================


        payload = normalize_gr_payload(

            data

        )









        # =================================================
        # SAVE JSON
        # =================================================


        with open(

            FILE_PATH,

            "w",

            encoding="utf-8"

        ) as f:



            json.dump(

                payload,

                f,

                indent=4,

                ensure_ascii=False

            )









        print(

            "FILE RELATIVE:",

            FILE_PATH

        )



        print(

            "FILE ABSOLUTE:",

            os.path.abspath(FILE_PATH)

        )





        print(

            "JUMLAH DATA:",

            len(

                payload.get(

                    "data",

                    []

                )

            )

        )






        print("=" * 60)

        print("\n")








    except Exception as e:



        print(

            "SAVE GR FORECAST ERROR"

        )


        print(

            str(e)

        )


        traceback.print_exc()



        raise e












# =====================================================
# LOAD LATEST GR FORECAST
# =====================================================


def load_latest_gr_forecast():


    try:



        print("\n")

        print("=" * 60)

        print("LOAD GR FORECAST")

        print("=" * 60)






        print(

            "PATH YANG DIBACA:",

            os.path.abspath(FILE_PATH)

        )









        # =================================================
        # GR OPTIONAL
        #
        # Kalau belum ada:
        #
        # return None
        #
        # route akan ubah menjadi []
        #
        # =================================================


        if not os.path.exists(

            FILE_PATH

        ):



            print(

                "FILE GR FORECAST BELUM ADA"

            )



            return None












        with open(

            FILE_PATH,

            "r",

            encoding="utf-8"

        ) as f:



            data = json.load(f)











        # =================================================
        # NORMALIZE OUTPUT
        # =================================================


        data = normalize_gr_payload(

            data

        )









        jumlah_data = len(

            data.get(

                "data",

                []

            )

        )







        print(

            "JUMLAH DATA:",

            jumlah_data

        )







        if jumlah_data > 0:



            print(

                "CONTOH DATA GR:"

            )



            print(

                data["data"][0]

            )









        print("=" * 60)

        print("\n")









        return data











    except Exception as e:



        print(

            "LOAD GR FORECAST ERROR"

        )



        print(

            str(e)

        )



        traceback.print_exc()



        return None