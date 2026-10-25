import os
import traceback

import pandas as pd

from fastapi import HTTPException

from services.pipeline import (
    run_pipeline as run_gi_pipeline
)

from services.gi_storage import (
    save_latest_gi_forecast
)


# =====================================================
# FOLDER GI
# =====================================================

UPLOAD_FOLDER = "uploads/GI"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =====================================================
# KOLOM WAJIB GI
# =====================================================

REQUIRED_COLUMNS = [
    "Posting Date",
    "Material",
    "Material Description",
    "Qty in Un. of Entry",
    "Movement Type"
]


# =====================================================
# KOLOM FILTER
# =====================================================

FILTER_COLUMNS = [
    "Material",
    "Material Type",
    "MRP Controller",
    "Storage Location",
    "Plant"
]


# =====================================================
# CLEAN COLUMN
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

    return str(
        value
    ).strip()


# =====================================================
# BUILD FILTER DATA
# =====================================================

def build_filter_data(df):

    filter_df = pd.DataFrame()

    print("\n")

    print("=" * 60)

    print(
        "BUILD FILTER DATA"
    )

    print("=" * 60)

    print(
        "COLUMN TERSEDIA:"
    )

    print(
        df.columns.tolist()
    )


    for col in FILTER_COLUMNS:


        # =============================================
        # CEK EXACT COLUMN
        # =============================================

        if col in df.columns:


            filter_df[col] = (
                df[col]
                .apply(
                    normalize_value
                )
            )


            print(
                "FILTER OK:",
                col
            )


        else:


            # =========================================
            # CEK KOLOM MIRIP
            #
            # Contoh:
            #
            # "MRP Controller "
            # "MRP Controller\n"
            #
            # menjadi:
            #
            # "MRP Controller"
            # =========================================

            matched_col = None


            for existing_col in df.columns:


                clean_existing = (
                    str(existing_col)
                    .replace(
                        "\n",
                        " "
                    )
                    .replace(
                        "\r",
                        " "
                    )
                    .strip()
                )


                clean_existing = " ".join(
                    clean_existing.split()
                )


                if clean_existing == col:

                    matched_col = existing_col

                    break


            if matched_col is not None:


                filter_df[col] = (
                    df[matched_col]
                    .apply(
                        normalize_value
                    )
                )


                print(
                    "FILTER MATCH:",
                    col,
                    "<=",
                    matched_col
                )


            else:


                # tetap dibuat supaya
                # struktur frontend tidak berubah

                filter_df[col] = ""


                print(
                    "FILTER TIDAK DITEMUKAN:",
                    col
                )


    # =============================================
    # HAPUS DUPLIKAT
    # =============================================

    filter_df = (
        filter_df
        .drop_duplicates()
        .reset_index(
            drop=True
        )
    )


    result = (
        filter_df
        .to_dict(
            orient="records"
        )
    )


    print(
        "JUMLAH FILTER DATA:",
        len(result)
    )


    print(
        "CONTOH FILTER:",
        result[:3]
    )


    print(
        "=" * 60
    )

    print("\n")


    return result


# =====================================================
# FIND HEADER ROW SHEET 1
# =====================================================

def find_header_row(
    filepath,
    sheet_name="Sheet1"
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


        values = (
            preview
            .iloc[index]
            .astype(str)
            .str.strip()
            .tolist()
        )


        if all(
            col in values
            for col in REQUIRED_COLUMNS
        ):

            return index


    return None


# =====================================================
# UPLOAD GI EXCEL
# =====================================================

async def upload_gi_excel(file):


    try:


        # =============================================
        # SAVE FILE
        # =============================================

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
            "GI FILE:",
            filepath
        )


        # =============================================
        # READ EXCEL
        # =============================================

        selected_sheet = "Sheet1"


        selected_header = find_header_row(
            filepath,
            selected_sheet
        )


        if selected_header is None:

            raise ValueError(
                "Header GI tidak ditemukan"
            )


        df = pd.read_excel(
            filepath,
            sheet_name=selected_sheet,
            header=selected_header
        )


        df = clean_columns(
            df
        )


        print(
            "KOLOM GI:",
            df.columns.tolist()
        )


        print(
            "TOTAL DATA:",
            len(df)
        )


        # =============================================
        # CLEAN DATA DASAR
        # =============================================

        df["Material"] = (
            df["Material"]
            .apply(
                normalize_value
            )
        )


        df["Movement Type"] = (
            df["Movement Type"]
            .apply(
                normalize_value
            )
        )


        df["Posting Date"] = pd.to_datetime(
            df["Posting Date"],
            errors="coerce"
        )


        df["Qty in Un. of Entry"] = pd.to_numeric(
            df["Qty in Un. of Entry"],
            errors="coerce"
        )


        df = df.dropna(
            subset=[
                "Posting Date",
                "Material"
            ]
        )


        # =============================================
        # HISTORY COUNT MATERIAL
        #
        # JUMLAH BULAN UNIK YANG MEMILIKI
        # TRANSAKSI GI PER MATERIAL
        #
        # BUKAN JUMLAH BARIS TRANSAKSI
        # =============================================

        history_count = (
            df
            .assign(
                _bulan=df[
                    "Posting Date"
                ].dt.to_period("M")
            )
            .groupby(
                "Material"
            )["_bulan"]
            .nunique()
            .to_dict()
        )


        # =============================================
        # FILTER DATA
        # =============================================

        filter_data = build_filter_data(
            df
        )


        # =============================================
        # GI PIPELINE
        # =============================================

        result = run_gi_pipeline(
            df
        )


        # =============================================
        # TAMBAH ATTRIBUTE MATERIAL
        # =============================================

        if isinstance(
            result,
            pd.DataFrame
        ):


            # =========================================
            # HISTORY COUNT
            # =========================================

            result["History_Count"] = (
                result["Material"]
                .map(
                    history_count
                )
                .fillna(0)
                .astype(int)
            )


            # =========================================
            # GI FLAG
            # =========================================

            result["has_GI"] = True


            # =========================================
            # GI ACTUAL
            # =========================================

            if "Trend_GI" in result.columns:


                result["GI_Actual"] = (
                    result["Trend_GI"]
                    .apply(

                        lambda trend:

                        trend[-2]

                        if isinstance(
                            trend,
                            list
                        )

                        and len(trend) >= 2

                        else None

                    )
                )


            else:


                result["GI_Actual"] = None


            # =========================================
            # DATAFRAME -> LIST OF DICTIONARY
            # =========================================

            result = (
                result
                .fillna("")
                .to_dict(
                    orient="records"
                )
            )


        elif isinstance(
            result,
            list
        ):


            # =========================================
            # HASIL SUDAH BERUPA LIST
            # =========================================

            for item in result:


                material = item.get(
                    "Material",
                    ""
                )


                # =====================================
                # HISTORY COUNT
                # =====================================

                item["History_Count"] = (
                    history_count.get(
                        material,
                        0
                    )
                )


                # =====================================
                # GI FLAG
                # =====================================

                item["has_GI"] = True


                # =====================================
                # GI ACTUAL
                # =====================================

                if "Trend_GI" in item:


                    trend = item[
                        "Trend_GI"
                    ]


                    item["GI_Actual"] = (

                        trend[-2]

                        if isinstance(
                            trend,
                            list
                        )

                        and len(trend) >= 2

                        else None

                    )


                else:


                    item["GI_Actual"] = None


        else:


            # =========================================
            # JIKA HASIL PIPELINE TIDAK VALID
            # =========================================

            result = []


        # =============================================
        # DEBUG HASIL FORECAST GI
        # =============================================

        print(
            "JUMLAH HASIL FORECAST GI:",
            len(result)
        )


        print(
            "CONTOH HASIL GI:",
            result[0]
            if len(result) > 0
            else None
        )


        # =============================================
        # DEBUG FILTER DATA
        # =============================================

        print("\n")


        print(
            "=" * 60
        )


        print(
            "FILTER DATA GI"
        )


        print(
            "=" * 60
        )


        print(
            "JUMLAH FILTER:",
            len(filter_data)
        )


        print(
            "CONTOH FILTER:",
            filter_data[:3]
        )


        print(
            "=" * 60
        )


        print("\n")


        # =============================================
        # SIMPAN JSON
        #
        # Output:
        #
        # {
        #     "data": [],
        #     "filter_data": []
        # }
        #
        # =============================================

        save_latest_gi_forecast(
            {
                "data": result,

                "filter_data": filter_data
            }
        )


        # =============================================
        # RETURN RESPONSE
        # =============================================

        return {

            "message":
                "GI berhasil diproses",

            "data":
                result,

            "filter_data":
                filter_data

        }


    except Exception as e:


        # =============================================
        # ERROR HANDLING
        # =============================================

        print(
            "GI UPLOAD ERROR"
        )


        traceback.print_exc()


        raise HTTPException(

            status_code=500,

            detail=str(e)

        )