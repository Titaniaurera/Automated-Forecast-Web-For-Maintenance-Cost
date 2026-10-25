import os

import traceback

import pandas as pd


from fastapi import HTTPException



# [BARU] tabel acuan satuan Material -> Unit of Entry (dari GR)
from services.unit_service import (

    load_material_unit_map

)







# =====================================================
# FOLDER UPLOAD STOCK
# =====================================================


UPLOAD_FOLDER = "uploads/STOCK"



os.makedirs(

    UPLOAD_FOLDER,

    exist_ok=True

)









# =====================================================
# REQUIRED STOCK COLUMNS
# =====================================================


REQUIRED_STOCK_COLUMNS = [


    "Material",


    "Material Description",


    "Unrestricted"


]









# =====================================================
# OPTIONAL STOCK COLUMNS
#
# Dipakai untuk:
#
# - Filter frontend
# - Projection metadata
#
# =====================================================


OPTIONAL_STOCK_COLUMNS = [


    "Plant",


    "MRP Controller",


    "Material Type",


    "Material Group",


    "Storage Location",


    "Safety Stock",


    "Reorder Point",


    "Maximum Stock Level",


    "Quantity on PR",


    "Quantity on PO",


    "Base Unit of Measure",


    "ABC Indicator",


    "Equipment"

]









# =====================================================
# CLEAN COLUMN NAME
# =====================================================


def clean_columns(df):


    df.columns = (


        df.columns


        .astype(str)


        .str.replace(

            "\n",

            " ",

            regex=False

        )


        .str.replace(

            "\r",

            " ",

            regex=False

        )


        .str.strip()


        .str.replace(

            r"\s+",

            " ",

            regex=True

        )


    )


    return df











# =====================================================
# NORMALIZE VALUE
# =====================================================


def normalize_value(value):


    if pd.isna(value):


        return ""





    if isinstance(

        value,

        float

    ):



        if value.is_integer():


            return str(

                int(value)

            )





    return str(value).strip()












# =====================================================
# NORMALIZE MATERIAL
# =====================================================


def normalize_material(value):


    value = normalize_value(value)



    if value.endswith(".0"):


        value = value[:-2]



    return value

    # =====================================================
# FIND HEADER ROW
# =====================================================


def find_header_row(

    filepath,

    sheet_name

):


    preview = pd.read_excel(

        filepath,

        sheet_name=sheet_name,

        header=None,

        nrows=30

    )





    for index in range(

        len(preview)

    ):


        row_values = (

            preview

            .iloc[index]

            .astype(str)

            .str.strip()

            .tolist()

        )





        if all(

            col in row_values

            for col in REQUIRED_STOCK_COLUMNS

        ):


            return index





    return None











# =====================================================
# BUILD FILTER DATA
#
# Digunakan frontend:
#
# - MRP Controller
# - Material Type
# - Storage Location
#
# =====================================================


def build_stock_filter_data(df):


    filter_columns = [


        "Material",


        "MRP Controller",


        "Material Type",


        "Material Group",


        "Plant",


        "Storage Location"


    ]







    filter_df = pd.DataFrame()







    for column in filter_columns:



        if column in df.columns:



            filter_df[column] = (

                df[column]

                .apply(

                    normalize_value

                )

            )



        else:



            filter_df[column] = ""












    filter_df = filter_df[


        filter_df["Material"] != ""

    ]










    filter_df = (

        filter_df

        .drop_duplicates()

        .reset_index(

            drop=True

        )

    )










    return (

        filter_df

        .to_dict(

            orient="records"

        )

    )

    # =====================================================
# UPLOAD CURRENT STOCK
# =====================================================


async def upload_stock(file):


    try:


        print("\n")

        print("=" * 60)

        print("START STOCK UPLOAD")

        print("=" * 60)









        # =================================================
        # SAVE FILE
        # =================================================


        filepath = os.path.join(

            UPLOAD_FOLDER,

            file.filename

        )







        with open(

            filepath,

            "wb"

        ) as f:


            f.write(

                await file.read()

            )







        print(

            "FILE STOCK:",

            filepath

        )













        # =================================================
        # READ EXCEL
        # =================================================


        excel_file = pd.ExcelFile(

            filepath

        )





        print(

            "SHEET:",

            excel_file.sheet_names

        )









        df_stock = None


        selected_sheet = None


        selected_header = None











        # =================================================
        # SEARCH SHEET + HEADER
        # =================================================


        for sheet_name in excel_file.sheet_names:




            print(

                "CHECK SHEET:",

                sheet_name

            )








            header_row = find_header_row(

                filepath,

                sheet_name

            )








            if header_row is None:


                continue










            temp_df = pd.read_excel(

                filepath,

                sheet_name=sheet_name,

                header=header_row

            )









            temp_df = clean_columns(

                temp_df

            )









            missing_columns = [


                col



                for col in REQUIRED_STOCK_COLUMNS



                if col not in temp_df.columns


            ]









            if len(missing_columns)==0:



                df_stock = temp_df


                selected_sheet = sheet_name


                selected_header = header_row


                break










        excel_file.close()











        # =================================================
        # VALIDATION
        # =================================================


        if df_stock is None:



            raise ValueError(


                "Format Current Stock tidak sesuai. "

                "Pastikan terdapat Material, "

                "Material Description, "

                "dan Unrestricted."

            )









        print(

            "SHEET TERPILIH:",

            selected_sheet

        )



        print(

            "HEADER:",

            selected_header + 1

        )



        print(

            "TOTAL ROW:",

            len(df_stock)

        )

                # =================================================
        # NORMALIZE MATERIAL
        # =================================================


        df_stock["Material"] = (

            df_stock["Material"]

            .apply(

                normalize_material

            )

        )







        df_stock = df_stock[

            df_stock["Material"] != ""

        ].copy()












        # =================================================
        # NUMERIC PROCESSING
        # =================================================


        numeric_columns = [


            "Unrestricted",


            "Safety Stock",


            "Reorder Point",


            "Maximum Stock Level",


            "Quantity on PR",


            "Quantity on PO"


        ]









        for column in numeric_columns:



            if column not in df_stock.columns:


                df_stock[column] = 0







            df_stock[column] = pd.to_numeric(


                df_stock[column],


                errors="coerce"


            ).fillna(0)














        # =================================================
        # DESCRIPTION CLEANING
        # =================================================


        df_stock["Material Description"] = (


            df_stock["Material Description"]


            .fillna("")


            .astype(str)


            .str.strip()


        )














        # =================================================
        # FILTER DATA
        #
        # Disimpan untuk frontend
        #
        # =================================================


        filter_data = build_stock_filter_data(

            df_stock

        )









        print(

            "TOTAL FILTER DATA:",

            len(filter_data)

        )












        # =================================================
        # AGGREGATION MATERIAL
        #
        # Satu material bisa punya:
        #
        # - Plant berbeda
        # - Storage Location berbeda
        #
        # Stock dijumlahkan
        #
        # =================================================



        aggregation_rules = {



            "Material Description":

                "first",




            "Unrestricted":

                "sum",





            "Safety Stock":

                "sum",





            "Reorder Point":

                "sum",





            "Maximum Stock Level":

                "sum",





            "Quantity on PR":

                "sum",





            "Quantity on PO":

                "sum"

        }













        # =================================================
        # OPTIONAL TEXT COLUMN
        #
        # Metadata untuk dashboard
        #
        # =================================================


        optional_text_columns = [


            "Plant",


            "MRP Controller",


            "Material Type",


            "Material Group",


            "Storage Location",


            "Base Unit of Measure",


            "ABC Indicator",


            "Equipment"


        ]









        for column in optional_text_columns:



            if column in df_stock.columns:


                aggregation_rules[column] = "first"














        # =================================================
        # GROUP BY MATERIAL
        # =================================================


        df_stock_grouped = (

            df_stock

            .groupby(

                "Material",

                as_index=False

            )

            .agg(

                aggregation_rules

            )

        )









        print(

            "TOTAL MATERIAL SETELAH AGGREGASI:",

            df_stock_grouped["Material"].nunique()

        )

                # =================================================
        # RENAME OUTPUT
        #
        # Standard dashboard:
        #
        # Stock
        #
        # =================================================


        df_stock_grouped = (

            df_stock_grouped

            .rename(

                columns={


                    "Unrestricted":

                        "Stock",



                    "Safety Stock":

                        "Safety_Stock",



                    "Reorder Point":

                        "Reorder_Point",



                    "Maximum Stock Level":

                        "Maximum_Stock_Level",



                    "Quantity on PR":

                        "Quantity_on_PR",



                    "Quantity on PO":

                        "Quantity_on_PO"


                }

            )

        )













        # =================================================
        # ENSURE NUMERIC OUTPUT
        #
        # Untuk projection calculation
        #
        # =================================================


        output_numeric_columns = [


            "Stock",


            "Safety_Stock",


            "Reorder_Point",


            "Maximum_Stock_Level",


            "Quantity_on_PR",


            "Quantity_on_PO"


        ]









        for column in output_numeric_columns:



            if column not in df_stock_grouped.columns:


                df_stock_grouped[column] = 0







            df_stock_grouped[column] = pd.to_numeric(


                df_stock_grouped[column],


                errors="coerce"


            ).fillna(0)















        # =================================================
        # VALIDATION FINAL
        # =================================================


        if "Stock" not in df_stock_grouped.columns:


            raise ValueError(

                "Kolom Stock gagal dibuat"

            )













        print("\n")

        print("="*60)

        print("CURRENT STOCK SELESAI")

        print("="*60)





        print(

            "TOTAL MATERIAL:",

            df_stock_grouped["Material"].nunique()

        )





        print(

            "TOTAL STOCK:",

            df_stock_grouped["Stock"].sum()

        )





        print(

            "CONTOH DATA STOCK:"

        )





        print(

            df_stock_grouped.head()

        )

                # =================================================
        # FINAL CLEANING NULL VALUE
        #
        # Text tetap string
        # Numeric tetap angka
        #
        # =================================================


        text_columns = [


            "Material",


            "Material Description",


            "Plant",


            "MRP Controller",


            "Material Type",


            "Material Group",


            "Storage Location",


            "Base Unit of Measure",


            "ABC Indicator",


            "Equipment"


        ]







        for column in text_columns:



            if column in df_stock_grouped.columns:


                df_stock_grouped[column] = (

                    df_stock_grouped[column]

                    .fillna("")

                    .astype(str)

                    .str.strip()

                )











        numeric_columns = [


            "Stock",


            "Safety_Stock",


            "Reorder_Point",


            "Maximum_Stock_Level",


            "Quantity_on_PR",


            "Quantity_on_PO"


        ]









        for column in numeric_columns:



            if column in df_stock_grouped.columns:


                df_stock_grouped[column] = pd.to_numeric(


                    df_stock_grouped[column],


                    errors="coerce"


                ).fillna(0)












        # =================================================
        # [BARU] UNIT DARI GR
        #
        # Satuan resmi per material = Unit of Entry di GR
        # (tabel acuan data/material_unit.json).
        #
        # Material yang tidak ada di GR -> Unit kosong
        # (tidak memakai Base Unit of Measure sebagai cadangan)
        #
        # =================================================


        material_unit_map = load_material_unit_map()







        df_stock_grouped["Unit"] = (


            df_stock_grouped["Material"]


            .map(


                material_unit_map


            )


            .fillna("")


        )







        print(


            "MATERIAL STOCK DENGAN SATUAN:",


            int(


                (


                    df_stock_grouped["Unit"] != ""


                ).sum()


            )


        )












        # =================================================
        # DATAFRAME TO JSON
        # =================================================


        result = (

            df_stock_grouped

            .to_dict(

                orient="records"

            )

        )












        # =================================================
        # FINAL RESPONSE
        #
        # Dipakai oleh:
        #
        # routes/stock.py
        #
        # =================================================


        response = {


            "data":


                result,




            "filter_data":


                filter_data



        }









        print("\n")

        print("="*60)

        print("STOCK UPLOAD BERHASIL")

        print("="*60)





        print(

            "JUMLAH OUTPUT:",

            len(result)

        )





        print("="*60)









        return response













    except Exception as e:




        print("\n")

        print("="*60)

        print("STOCK UPLOAD ERROR")

        print("="*60)





        print(

            "ERROR TYPE:",

            type(e).__name__

        )





        print(

            "ERROR MESSAGE:",

            str(e)

        )





        traceback.print_exc()





        print("="*60)







        raise HTTPException(

            status_code=500,

            detail=str(e)

        )