import pandas as pd



# =====================================================
# MOVEMENT TYPE MAPPING
# =====================================================


MAIN_MOVEMENTS = {

    "261": "262",

    "281": "282",

    "961": "962"

}



CANCEL_MOVEMENTS = {

    "262": "261",

    "282": "281",

    "962": "961"

}




# =====================================================
# REQUIRED COLUMN
# =====================================================


REQUIRED_COLUMNS = [

    "Material",

    "Posting Date",

    "Movement Type",

    "Qty in Un. of Entry"

]





# =====================================================
# CLEAN MOVEMENT TYPE
# =====================================================


def normalize_movement(value):


    if pd.isna(value):

        return ""


    value = str(value).strip()



    if value.endswith(".0"):

        value = value[:-2]


    return value






# =====================================================
# CLEAN MATERIAL
# =====================================================


def normalize_material(value):


    if pd.isna(value):

        return ""


    value = str(value).strip()



    if value.endswith(".0"):

        value = value[:-2]


    return value





# =====================================================
# VALIDATION
# =====================================================


def validate_columns(df):


    missing = [

        col

        for col in REQUIRED_COLUMNS

        if col not in df.columns

    ]


    if missing:


        raise ValueError(

            f"Kolom GI tidak ditemukan: {missing}"

        )







# =====================================================
# CHECK FULL CANCEL
#
# Contoh:
#
# 261 -1000
# 262 +1000
#
# total = 0
#
# maka buang
#
# =====================================================


def is_full_cancel(main_qty, cancel_qty):


    total = main_qty + cancel_qty


    return abs(total) < 0.0001







# =====================================================
# MOVEMENT CLEANSING
# =====================================================


def clean_gi_movement(df):


    print("\n===================================")

    print("START MOVEMENT CLEANSING GI")

    print("===================================")




    df = df.copy()



    # ================================================
    # VALIDASI
    # ================================================


    validate_columns(df)



    # ================================================
    # NORMALISASI
    # ================================================


    df["Movement Type"] = (

        df["Movement Type"]

        .apply(
            normalize_movement
        )

    )


    df["Material"] = (

        df["Material"]

        .apply(
            normalize_material
        )

    )



    df["Qty in Un. of Entry"] = (

        pd.to_numeric(

            df["Qty in Un. of Entry"],

            errors="coerce"

        )

        .fillna(0)

    )





    # ================================================
    # PISAHKAN MOVEMENT
    # ================================================


    main_df = df[

        df["Movement Type"]

        .isin(

            MAIN_MOVEMENTS.keys()

        )

    ].copy()



    cancel_df = df[

        df["Movement Type"]

        .isin(

            CANCEL_MOVEMENTS.keys()

        )

    ].copy()





    print(

        "TOTAL DATA AWAL:",

        len(df)

    )


    print(

        "MAIN MOVEMENT:",

        len(main_df)

    )


    print(

        "CANCEL MOVEMENT:",

        len(cancel_df)

    )







    # ================================================
    # IDENTIFIKASI FULL CANCEL
    #
    # Tidak menggunakan netting
    #
    # hanya mencari pasangan
    #
    # material sama
    #
    # tanggal sama
    #
    # movement pasangan
    #
    # ================================================


    cancelled_index = []



    for index, row in main_df.iterrows():


        movement = row["Movement Type"]


        cancel_type = MAIN_MOVEMENTS[movement]



        candidate = cancel_df[

            (cancel_df["Material"] == row["Material"])

            &

            (cancel_df["Movement Type"] == cancel_type)

        ]



        if len(candidate) == 0:


            continue





        remaining_qty = abs(

            row["Qty in Un. of Entry"]

        )



        for cancel_index, cancel_row in candidate.iterrows():


            cancel_qty = abs(

                cancel_row["Qty in Un. of Entry"]

            )



            if abs(

                remaining_qty

                -

                cancel_qty

            ) < 0.0001:



                cancelled_index.append(

                    index

                )


                cancelled_index.append(

                    cancel_index

                )


                break






    # ================================================
    # HAPUS FULL CANCEL
    # ================================================


    cleaned_df = df.drop(

        index=cancelled_index

    ).copy()





    # ================================================
    # HANYA AMBIL MAIN MOVEMENT VALID
    #
    # Cancel tanpa pasangan dibuang
    #
    # ================================================


    cleaned_df = cleaned_df[

        cleaned_df["Movement Type"]

        .isin(

            MAIN_MOVEMENTS.keys()

        )

    ].copy()





    # ================================================
    # OUTPUT
    # ================================================


    cleaned_df = (

        cleaned_df

        .reset_index(

            drop=True

        )

    )





    print("\n===================================")

    print(

        "DATA SETELAH CLEANSING:",

        len(cleaned_df)

    )


    print(

        "MOVEMENT TYPE AKHIR:",

        cleaned_df[

            "Movement Type"

        ]

        .unique()

        .tolist()

    )


    print("===================================\n")





    return cleaned_df






# =====================================================
# SUMMARY CLEANSING
# =====================================================


def cleansing_summary(df):


    return {


        "total_data":

            len(df),



        "movement_type":

            df["Movement Type"]

            .value_counts()

            .to_dict()


    }