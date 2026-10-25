import os
import json
import traceback



# =====================================================
# FILE STORAGE CURRENT STOCK
# =====================================================


DATA_FOLDER = "data"


FILE_PATH = os.path.join(

    DATA_FOLDER,

    "latest_stock.json"

)



# =====================================================
# CREATE DATA FOLDER
# =====================================================


os.makedirs(

    DATA_FOLDER,

    exist_ok=True

)





# =====================================================
# SAVE LATEST STOCK
# =====================================================


def save_latest_stock(data):


    try:


        print(

            "\n========== SAVE CURRENT STOCK =========="

        )



        with open(

            FILE_PATH,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                data,

                f,

                indent=4,

                ensure_ascii=False

            )




        total_data = 0



        if isinstance(data, dict):


            total_data = len(

                data.get(

                    "data",

                    []

                )

            )


        elif isinstance(data, list):


            total_data = len(data)





        print(

            "CURRENT STOCK DISIMPAN:",

            FILE_PATH

        )


        print(

            "JUMLAH MATERIAL:",

            total_data

        )


        print(

            "========================================\n"

        )




    except Exception as e:


        print(

            "ERROR SAVE CURRENT STOCK"

        )


        print(

            str(e)

        )


        traceback.print_exc()







# =====================================================
# LOAD LATEST STOCK
# =====================================================


def load_latest_stock():


    try:


        if not os.path.exists(

            FILE_PATH

        ):


            print(

                "FILE CURRENT STOCK BELUM ADA"

            )


            return None





        with open(

            FILE_PATH,

            "r",

            encoding="utf-8"

        ) as f:


            data = json.load(f)






        print(

            "\n========== LOAD CURRENT STOCK =========="

        )



        if isinstance(data, dict):


            print(

                "JUMLAH MATERIAL:",

                len(

                    data.get(

                        "data",

                        []

                    )

                )

            )



        elif isinstance(data, list):


            print(

                "JUMLAH MATERIAL:",

                len(data)

            )




        print(

            "========================================\n"

        )



        return data





    except Exception as e:


        print(

            "ERROR LOAD CURRENT STOCK"

        )


        print(

            str(e)

        )


        traceback.print_exc()



        return None