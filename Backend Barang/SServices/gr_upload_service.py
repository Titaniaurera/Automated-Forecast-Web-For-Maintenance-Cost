import os
 
import traceback
 
import pandas as pd
 
 
from fastapi import HTTPException
 
 
 
from services.gr_pipeline import (
 
    run_gr_pipeline
 
)
 
 
 
from services.gr_storage import (
 
    save_latest_gr_forecast
 
)
 
 
 
# [BARU] simpan tabel acuan satuan Material -> Unit of Entry
from services.unit_service import (
 
    save_material_unit_map
 
)
 
 
 
 
 
 
 
 
 
# =====================================================
# FOLDER GR
# =====================================================
 
 
UPLOAD_FOLDER = "uploads/GR"
 
 
 
os.makedirs(
 
    UPLOAD_FOLDER,
 
    exist_ok=True
 
)
 
 
 
 
 
 
 
 
 
# =====================================================
# REQUIRED COLUMN GR
# =====================================================
 
 
REQUIRED_GR_COLUMNS = [
 
 
    "Posting Date",
 
 
    "Material",
 
 
    "Material Description",
 
 
    "Qty in Un. of Entry",
 
 
    "Movement Type"
 
 
]
 
 
 
 
 
 
 
 
 
# =====================================================
# [BARU] UNIT COLUMN GR
#
# Sengaja TIDAK dimasukkan ke REQUIRED_GR_COLUMNS
# supaya file GR lama tanpa kolom ini tetap bisa
# diupload. Kalau kolom tidak ada, satuan dikosongkan.
#
# =====================================================
 
 
UNIT_COLUMN = "Unit of Entry"
 
 
 
 
 
 
 
 
 
# =====================================================
# FILTER COLUMN
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
 
 
 
 
 
    return str(value).strip()
 
    # =====================================================
# BUILD FILTER DATA
# =====================================================
 
 
def build_filter_data(df):
 
 
    filter_df = pd.DataFrame()
 
 
 
 
 
    for column in FILTER_COLUMNS:
 
 
        if column in df.columns:
 
 
            filter_df[column] = (
 
 
                df[column]
 
 
                .apply(
 
                    normalize_value
 
                )
 
 
            )
 
 
        else:
 
 
            filter_df[column] = ""
 
 
 
 
 
 
 
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
# [BARU] BUILD MATERIAL UNIT MAP
#
# Material -> Unit of Entry (acuan: GR)
#
# Kalau satu material punya lebih dari satu satuan
# di data, ambil yang paling baru (Posting Date terakhir)
#
# =====================================================
 
 
def build_material_unit_map(df):
 
 
    if UNIT_COLUMN not in df.columns:
 
 
        return {}
 
 
 
 
 
 
 
    unit_df = df[
 
 
        [
 
 
            "Material",
 
 
            "Posting Date",
 
 
            UNIT_COLUMN
 
 
        ]
 
 
    ].copy()
 
 
 
 
 
 
 
    unit_df = unit_df[
 
 
        unit_df[UNIT_COLUMN] != ""
 
 
    ]
 
 
 
 
 
 
 
    unit_df = unit_df.sort_values(
 
 
        "Posting Date"
 
 
    )
 
 
 
 
 
 
 
    unit_df = unit_df.drop_duplicates(
 
 
        "Material",
 
 
        keep="last"
 
 
    )
 
 
 
 
 
 
 
    return dict(
 
 
        zip(
 
 
            unit_df["Material"],
 
 
            unit_df[UNIT_COLUMN]
 
 
        )
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
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
 
 
        values = (
 
 
            preview
 
 
            .iloc[index]
 
 
            .astype(str)
 
 
            .str.strip()
 
 
            .tolist()
 
 
        )
 
 
 
 
 
 
 
 
        if all(
 
 
 
            col in values
 
 
 
            for col in REQUIRED_GR_COLUMNS
 
 
 
        ):
 
 
 
            return index
 
 
 
 
 
 
 
 
 
 
    return None
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
# =====================================================
# FORMAT FORECAST GR
#
# FIX:
#
# Jangan overwrite Forecast_GR
# jika pipeline sudah menghasilkan
#
# =====================================================
 
 
def format_gr_result(result):
 
 
    formatted = []
 
 
 
 
 
    for item in result:
 
 
 
        new_item = dict(item)
 
 
 
 
 
        print("\nSEBELUM FORMAT GR")
 
        print(new_item)
 
 
 
 
 
 
 
 
 
        rename_map = {
 
 
 
            "Forecast":
 
                "Forecast_GR",
 
 
 
 
            "Trend":
 
                "Trend_GR",
 
 
 
 
            "Best_Model":
 
                "Best_Model_GR",
 
 
 
 
            "MAE":
 
                "MAE_GR",
 
 
 
 
            "RMSE":
 
                "RMSE_GR",
 
 
 
 
            "MAPE":
 
                "MAPE_GR"
 
 
 
 
        }
 
 
 
 
 
 
 
 
 
        for old_key, new_key in rename_map.items():
 
 
 
            if old_key in new_item:
 
 
 
                new_item[new_key] = new_item.pop(old_key)
 
 
 
 
 
 
 
 
 
 
 
 
        if "Forecast_GR" not in new_item:
 
 
            new_item["Forecast_GR"] = 0
 
 
 
 
 
 
 
        if "Trend_GR" not in new_item:
 
 
            new_item["Trend_GR"] = []
 
 
 
 
 
 
 
 
        if "Best_Model_GR" not in new_item:
 
 
            new_item["Best_Model_GR"] = ""
 
 
 
 
 
 
 
 
        if "MAE_GR" not in new_item:
 
 
            new_item["MAE_GR"] = 0
 
 
 
 
 
 
 
 
        if "RMSE_GR" not in new_item:
 
 
            new_item["RMSE_GR"] = 0
 
 
 
 
 
 
 
 
        if "MAPE_GR" not in new_item:
 
 
            new_item["MAPE_GR"] = 0
 
 
 
 
 
 
 
 
 
 
        print("\nSESUDAH FORMAT GR")
 
        print(new_item)
 
 
 
 
 
 
        formatted.append(
 
 
            new_item
 
 
        )
 
 
 
 
 
 
 
    return formatted
 
    # =====================================================
# UPLOAD GR EXCEL
# =====================================================
 
 
async def upload_gr_excel(file):
 
 
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
 
 
            "\nFILE GR:",
 
 
            filepath
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # READ EXCEL
        # =============================================
 
 
        excel_file = pd.ExcelFile(
 
 
            filepath
 
 
        )
 
 
 
 
 
 
 
        df = None
 
 
 
        selected_sheet = None
 
 
 
        selected_header = None
 
 
 
 
 
 
 
 
 
 
 
 
        for sheet_name in excel_file.sheet_names:
 
 
 
 
            print(
 
 
                "CHECK SHEET GR:",
 
 
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
 
 
 
 
 
 
 
 
 
            missing = [
 
 
                col
 
 
                for col in REQUIRED_GR_COLUMNS
 
 
                if col not in temp_df.columns
 
 
            ]
 
 
 
 
 
 
 
 
 
            if len(missing) == 0:
 
 
 
                df = temp_df
 
 
 
                selected_sheet = sheet_name
 
 
 
                selected_header = header_row
 
 
 
                break
 
 
 
 
 
 
 
 
 
 
        excel_file.close()
 
 
 
 
 
 
 
 
 
 
        if df is None:
 
 
            raise ValueError(
 
 
                "Format Excel GR tidak valid"
 
 
            )
 
 
 
 
 
 
 
 
 
        print(
 
 
            "SHEET GR TERPILIH:",
 
 
            selected_sheet
 
 
        )
 
 
 
 
 
 
 
        print(
 
 
            "HEADER GR:",
 
 
            selected_header
 
 
        )
 
 
 
 
 
 
 
        print(
 
 
            "JUMLAH DATA GR:",
 
 
            len(df)
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # DATA CLEANING
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
 
 
 
 
 
 
 
 
 
        # [BARU] Unit of Entry: dibersihkan, tidak dibuang
        if UNIT_COLUMN in df.columns:
 
 
            df[UNIT_COLUMN] = (
 
 
                df[UNIT_COLUMN]
 
 
                .apply(
 
 
                    normalize_value
 
 
                )
 
 
            )
 
 
 
 
 
 
 
 
 
        df = df.dropna(
 
 
            subset=[
 
 
                "Posting Date",
 
 
                "Material"
 
 
            ]
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # HISTORY COUNT GR
        # =============================================
 
 
        history_count = (
 
 
            df
 
 
            .groupby(
 
 
                "Material"
 
 
            )
 
 
            .size()
 
 
            .to_dict()
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # [BARU] UNIT PER MATERIAL (ACUAN: GR)
        #
        # Disimpan ke data/material_unit.json
        # supaya GI, stock, dan projection
        # bisa memakai satuan yang sama
        #
        # =============================================
 
 
        material_unit_map = build_material_unit_map(
 
 
            df
 
 
        )
 
 
 
 
 
 
 
        save_material_unit_map(
 
 
            material_unit_map
 
 
        )
 
 
 
 
 
 
 
        print(
 
 
            "JUMLAH MATERIAL DENGAN SATUAN:",
 
 
            len(material_unit_map)
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # FILTER DATA
        # =============================================
 
 
        filter_data = build_filter_data(
 
 
            df
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # GR PIPELINE
        # =============================================
 
 
        print(
 
 
            "\nSTART GR PIPELINE"
 
 
        )
 
 
 
 
 
 
 
        result = run_gr_pipeline(
 
 
            df
 
 
        )
 
 
 
 
 
 
 
        print(
 
 
            "FINISH GR PIPELINE"
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # DEBUG HASIL PIPELINE
        #
        # CEK DISINI:
        #
        # Forecast_GR HILANG ATAU TIDAK
        #
        # =============================================
 
 
        print("\n")
 
        print("=" * 60)
 
        print("DEBUG OUTPUT GR PIPELINE")
 
        print("=" * 60)
 
 
 
        if isinstance(result, pd.DataFrame):
 
 
            print(result.head())
 
 
            print(
 
                "COLUMN:",
 
                result.columns.tolist()
 
            )
 
 
 
        elif isinstance(result, list):
 
 
            print(
 
                result[0]
 
                if len(result) > 0
 
                else "RESULT KOSONG"
 
            )
 
 
 
        print("=" * 60)
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # VALIDASI OUTPUT PIPELINE
        # =============================================
 
 
        if isinstance(
 
 
            result,
 
 
            pd.DataFrame
 
 
        ):
 
 
 
            result = (
 
 
 
                result
 
 
 
                .fillna("")
 
 
 
                .to_dict(
 
 
 
                    orient="records"
 
 
 
                )
 
 
 
            )
 
 
 
 
 
 
 
 
 
        if not isinstance(
 
 
            result,
 
 
            list
 
 
        ):
 
 
 
            raise ValueError(
 
 
 
                "Output GR pipeline harus list"
 
 
 
            )
 
                    # =============================================
        # FORMAT OUTPUT GR
        # =============================================
 
 
        result = format_gr_result(
 
 
            result
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # TAMBAH ATTRIBUTE GR
        #
        # Untuk projection:
        #
        # has_GR
        # History_Count
        # Unit (satuan dari GR, kosong jika tidak ada)
        #
        # =============================================
 
 
        for item in result:
 
 
 
            material = item.get(
 
 
                "Material",
 
 
                ""
 
 
            )
 
 
 
 
 
 
 
 
            item["History_Count"] = (
 
 
                history_count.get(
 
 
                    material,
 
 
                    0
 
 
                )
 
 
            )
 
 
 
 
 
 
 
 
 
            item["has_GR"] = True
 
 
 
 
 
 
 
 
 
            # [BARU] satuan dari GR, kosong jika tidak ada
            item["Unit"] = (
 
 
                material_unit_map.get(
 
 
                    material,
 
 
                    ""
 
 
                )
 
 
            )
 
 
 
 
 
 
 
 
 
 
 
 
 
        print(
 
 
            "JUMLAH HASIL FORECAST GR:",
 
 
            len(result)
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
        print(
 
 
            "CONTOH HASIL GR:",
 
 
 
            result[0]
 
            if len(result) > 0
 
            else None
 
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # SAVE STORAGE
        # =============================================
 
 
        save_latest_gr_forecast(
 
 
 
 
            {
 
 
                "data":
 
 
                    result,
 
 
 
 
 
 
                "filter_data":
 
 
                    filter_data
 
 
 
 
 
            }
 
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
        # =============================================
        # RETURN RESPONSE
        # =============================================
 
 
        return {
 
 
 
 
            "message":
 
 
 
                "GR berhasil diproses",
 
 
 
 
 
 
 
 
 
 
            "data":
 
 
 
                result,
 
 
 
 
 
 
 
 
 
 
 
            "filter_data":
 
 
 
                filter_data
 
 
 
 
 
 
        }
 
 
 
 
 
 
 
 
 
 
 
 
    except Exception as e:
 
 
 
 
        print(
 
 
            "\nUPLOAD GR ERROR"
 
 
        )
 
 
 
 
 
 
 
 
        print(
 
 
            str(e)
 
 
        )
 
 
 
 
 
 
 
 
        traceback.print_exc()
 
 
 
 
 
 
 
 
 
 
 
        raise HTTPException(
 
 
 
 
 
 
            status_code=500,
 
 
 
 
 
 
            detail=str(e)
 
 
 
 
 
 
        )

