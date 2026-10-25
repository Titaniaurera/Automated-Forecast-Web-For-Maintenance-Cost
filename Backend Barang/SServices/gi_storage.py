import os
import json
import traceback





# =====================================================
# FILE STORAGE GI FORECAST
# =====================================================


DATA_FOLDER = "data"



FILE_PATH = os.path.join(

    DATA_FOLDER,

    "latest_gi_forecast.json"

)







# =====================================================
# CREATE FOLDER
# =====================================================


os.makedirs(

    DATA_FOLDER,

    exist_ok=True

)









# =====================================================
# NORMALIZE PAYLOAD
#
# Semua GI disimpan:
#
# {
#    "data":[]
# }
#
# =====================================================


def normalize_gi_payload(data):


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

            "Format GI forecast tidak valid"

        )












# =====================================================
# SAVE LATEST GI FORECAST
# =====================================================


def save_latest_gi_forecast(data):


    try:


        print("\n")


        print("=" * 60)

        print("SAVE GI FORECAST")

        print("=" * 60)






        # =================================================
        # NORMALIZE FORMAT
        # =================================================


        payload = normalize_gi_payload(

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

            "FILE:",

            FILE_PATH

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

            "SAVE GI FORECAST ERROR"

        )



        print(

            str(e)

        )



        traceback.print_exc()



        raise e












# =====================================================
# LOAD LATEST GI FORECAST
# =====================================================


def load_latest_gi_forecast():


    try:





        if not os.path.exists(

            FILE_PATH

        ):



            print(

                "GI FORECAST BELUM ADA"

            )



            return None










        with open(

            FILE_PATH,

            "r",

            encoding="utf-8"

        ) as f:



            data = json.load(f)











        print("\n")

        print("=" * 60)

        print("LOAD GI FORECAST")

        print("=" * 60)








        # =================================================
        # NORMALIZE OUTPUT
        # =================================================


        data = normalize_gi_payload(

            data

        )











        print(

            "JUMLAH DATA:",

            len(

                data.get(

                    "data",

                    []

                )

            )

        )







        print("=" * 60)

        print("\n")







        return data












    except Exception as e:



        print(

            "LOAD GI FORECAST ERROR"

        )



        print(

            str(e)

        )



        traceback.print_exc()





        return None