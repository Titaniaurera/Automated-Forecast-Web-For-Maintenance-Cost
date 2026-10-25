

# =====================================================
# STOCK PROJECTION SERVICE
# =====================================================
#
# Menggabungkan:
#
# GI Forecast
# GR Forecast
# Current Stock
#
# Output:
#
# - GI Actual
# - GR Actual
# - Forecast GI
# - Forecast GR
# - Stock
# - Coverage
# - Status
# - Unit (satuan dari GR)
#
# Filter:
#
# - has_GI
# - has_GR
# - has_STOCK
# - History_Count
#
# =====================================================
 
 
import pandas as pd
 
 
 
from services.coverage import (
 
    calculate_coverage,
 
    calculate_coverage_projection,
 
    calculate_status
 
)
 
 
 
# [BARU] tabel acuan satuan Material -> Unit of Entry (dari GR)
from services.unit_service import (
 
    load_material_unit_map
 
)
 
 
 
 
 
 
 
 
 
# =====================================================
# BUILD STOCK PROJECTION
# =====================================================
 
 
def build_stock_projection(
 
 
    gi_forecast_df,
 
 
    gr_forecast_df,
 
 
    stock_df
 
 
):
 
 
 
    print("\n")
 
    print("="*60)
 
    print("START STOCK PROJECTION")
 
    print("="*60)
 
 
 
 
 
 
 
 
 
    # =====================================================
    # VALIDASI GI
    # =====================================================
 
 
    if (
 
        gi_forecast_df is None
 
        or
 
        len(gi_forecast_df) == 0
 
    ):
 
 
        raise ValueError(
 
            "GI forecast kosong"
 
        )
 
 
 
 
 
 
 
 
 
    required_gi = [
 
        "Material",
 
        "Forecast_GI"
 
    ]
 
 
 
 
 
 
 
 
 
    for col in required_gi:
 
 
        if col not in gi_forecast_df.columns:
 
 
            raise ValueError(
 
                f"Kolom GI tidak ditemukan: {col}"
 
            )
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # NORMALIZE MATERIAL
    # =====================================================
 
 
    def normalize_material(value):
 
 
        if pd.isna(value):
 
            return ""
 
 
 
        return (
 
            str(value)
 
            .strip()
 
            .replace(".0","")
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # PREPARE GI
    #
    # GI menjadi BASE MATERIAL
    #
    # =====================================================
 
 
    gi_columns = [
 
 
 
        "Material",
 
 
 
        "Material Description",
 
 
 
        "GI_Actual",
 
 
 
        "Forecast_GI",
 
 
 
        "Trend_GI",
 
 
 
        # TAMBAHAN DARI FORECASTING.PY
 
        "Trend_Bulan",
 
 
 
        "Forecast_Bulan",
 
 
 
        "Best_Model_GI",
 
 
 
        "Bulan",
 
 
 
        "History_Count",
 
 
 
        "has_GI"
 
 
 
    ]
 
 
 
 
 
 
 
 
 
    gi_columns = [
 
 
        col
 
 
        for col in gi_columns
 
 
        if col in gi_forecast_df.columns
 
 
    ]
 
 
 
 
 
 
 
 
 
    gi = gi_forecast_df[
 
        gi_columns
 
    ].copy()
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # NORMALIZE MATERIAL GI
    # =====================================================
 
 
    gi["Material"] = (
 
        gi["Material"]
 
        .apply(
 
            normalize_material
 
        )
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # FORECAST GI CLEAN
    # =====================================================
 
 
    gi["Forecast_GI"] = pd.to_numeric(
 
 
        gi["Forecast_GI"],
 
 
        errors="coerce"
 
 
    ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # GI ACTUAL
    # =====================================================
 
 
    if "GI_Actual" not in gi.columns:
 
 
        gi["GI_Actual"] = 0
 
 
 
 
 
 
 
 
 
 
 
 
    gi["GI_Actual"] = pd.to_numeric(
 
 
        gi["GI_Actual"],
 
 
        errors="coerce"
 
 
    ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # GI FLAG
    #
    # Default:
    #
    # GI selalu tersedia
    #
    # =====================================================
 
 
    if "has_GI" not in gi.columns:
 
 
        gi["has_GI"] = True
 
 
 
 
 
 
 
 
 
 
 
 
    gi["has_GI"] = (
 
        gi["has_GI"]
 
        .fillna(True)
 
        .astype(bool)
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
    print("\nDEBUG GI")
 
 
    print(
 
        gi.head(5)
 
    )
 
 
 
    print(
 
        "TOTAL GI MATERIAL:",
 
        gi["Material"].nunique()
 
    )
 
        # =====================================================
    # HISTORY COUNT
    #
    # Kalau upload GI sudah punya History_Count:
    # pakai langsung
    #
    # Kalau belum:
    # hitung dari Bulan
    #
    # =====================================================
 
 
    if "History_Count" not in gi.columns:
 
 
        if "Bulan" in gi.columns:
 
 
 
            history_count = (
 
 
                gi.groupby("Material")
 
 
                ["Bulan"]
 
 
                .nunique()
 
 
                .reset_index()
 
 
            )
 
 
 
            history_count.columns = [
 
 
                "Material",
 
 
                "History_Count"
 
 
            ]
 
 
 
 
 
 
 
 
            gi = gi.merge(
 
 
                history_count,
 
 
                on="Material",
 
 
                how="left"
 
 
            )
 
 
 
 
 
        else:
 
 
            gi["History_Count"] = 0
 
 
 
 
 
 
 
 
 
 
 
 
    gi["History_Count"] = pd.to_numeric(
 
 
        gi["History_Count"],
 
 
        errors="coerce"
 
 
    ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # PREPARE GR
    #
    # GR Forecast
    #
    # Jika belum upload GR:
    #
    # Forecast_GR = 0
    # has_GR = False
    #
    # =====================================================
 
 
 
    if (
 
 
        gr_forecast_df is not None
 
 
        and
 
 
        len(gr_forecast_df) > 0
 
 
    ):
 
 
 
        print(
 
            "GR TERSEDIA"
 
        )
 
 
 
 
 
 
 
 
 
        gr_columns = [
 
 
 
            "Material",
 
 
 
            "GR_Actual",
 
 
 
            "Forecast_GR",
 
 
 
            "Trend_GR",
 
 
 
            # TAMBAHAN DARI FORECASTING.PY
 
            "Trend_Bulan",
 
 
 
            "Forecast_Bulan",
 
 
 
            "Best_Model_GR",
 
 
 
            "has_GR"
 
 
 
        ]
 
 
 
 
 
 
 
 
 
        gr_columns = [
 
 
            col
 
 
            for col in gr_columns
 
 
            if col in gr_forecast_df.columns
 
 
        ]
 
 
 
 
 
 
 
 
 
        gr = gr_forecast_df[
 
            gr_columns
 
        ].copy()
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # NORMALIZE MATERIAL GR
        # =================================================
 
 
        gr["Material"] = (
 
 
            gr["Material"]
 
 
            .apply(
 
 
                normalize_material
 
 
            )
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # DEFAULT COLUMN GR
        # =================================================
 
 
        if "GR_Actual" not in gr.columns:
 
 
            gr["GR_Actual"] = 0
 
 
 
 
 
 
 
 
 
 
 
 
        if "Forecast_GR" not in gr.columns:
 
 
            gr["Forecast_GR"] = 0
 
 
 
 
 
 
 
 
 
 
 
 
        if "has_GR" not in gr.columns:
 
 
            gr["has_GR"] = True
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # NUMERIC CLEAN GR
        # =================================================
 
 
        gr["GR_Actual"] = pd.to_numeric(
 
 
            gr["GR_Actual"],
 
 
            errors="coerce"
 
 
        ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
 
        gr["Forecast_GR"] = pd.to_numeric(
 
 
            gr["Forecast_GR"],
 
 
            errors="coerce"
 
 
        ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # AGREGASI GR
        #
        # 1 material = 1 baris
        #
        # =================================================
 
 
        aggregation_gr = {
 
 
 
            "GR_Actual":
 
                "sum",
 
 
 
            "Forecast_GR":
 
                "sum"
 
 
 
        }
 
 
 
 
 
 
 
 
 
        if "Trend_GR" in gr.columns:
 
 
            aggregation_gr["Trend_GR"] = "first"
 
 
 
 
 
 
 
 
        # TAMBAHAN
        # supaya tanggal trend tidak hilang
 
 
        if "Trend_Bulan" in gr.columns:
 
 
            aggregation_gr["Trend_Bulan"] = "first"
 
 
 
 
 
 
 
 
        if "Forecast_Bulan" in gr.columns:
 
 
            aggregation_gr["Forecast_Bulan"] = "first"
 
 
 
 
 
 
 
 
        if "Best_Model_GR" in gr.columns:
 
 
            aggregation_gr["Best_Model_GR"] = "first"
 
 
 
 
 
 
 
 
        if "has_GR" in gr.columns:
 
 
            aggregation_gr["has_GR"] = "max"
 
 
 
 
 
 
 
 
 
 
 
 
 
        gr = (
 
            gr
 
            .groupby(
 
                "Material",
 
                as_index=False
 
            )
 
            .agg(
 
                aggregation_gr
 
            )
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
    else:
 
 
 
        print(
 
            "GR BELUM TERSEDIA"
 
        )
 
 
 
 
 
 
 
 
 
        gr = pd.DataFrame({
 
 
 
            "Material": [],
 
 
 
            "GR_Actual": [],
 
 
 
            "Forecast_GR": [],
 
 
 
            "has_GR": []
 
 
 
        })
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    print("\nDEBUG GR")
 
 
    print(
 
        gr.head(5)
 
    )
 
 
 
    print(
 
        "TOTAL GR MATERIAL:",
 
        gr["Material"].nunique()
 
    )
 
        # =====================================================
    # PREPARE STOCK
    #
    # Current Stock
    #
    # Jika belum upload:
    #
    # Stock = 0
    # has_STOCK = False
    #
    # =====================================================
 
 
    if (
 
        stock_df is not None
 
        and
 
        len(stock_df) > 0
 
    ):
 
 
        print(
 
            "STOCK TERSEDIA"
 
        )
 
 
 
 
 
        stock_columns = [
 
 
 
            "Material",
 
 
 
            "Stock",
 
 
 
            "Safety_Stock",
 
 
 
            "Reorder_Point",
 
 
 
            "Maximum_Stock_Level"
 
 
 
        ]
 
 
 
 
 
 
 
 
 
        stock_columns = [
 
 
 
            col
 
 
 
            for col in stock_columns
 
 
 
            if col in stock_df.columns
 
 
 
        ]
 
 
 
 
 
 
 
 
 
        stock = stock_df[
 
            stock_columns
 
        ].copy()
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # NORMALIZE MATERIAL STOCK
        # =================================================
 
 
        stock["Material"] = (
 
            stock["Material"]
 
            .apply(
 
                normalize_material
 
            )
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # NUMERIC CLEAN STOCK
        # =================================================
 
 
        for col in stock.columns:
 
 
            if col != "Material":
 
 
                stock[col] = pd.to_numeric(
 
 
                    stock[col],
 
 
                    errors="coerce"
 
 
                ).fillna(0)
 
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # STOCK FLAG
        # =================================================
 
 
        stock["has_STOCK"] = True
 
 
 
 
 
 
 
 
 
 
 
 
        # =================================================
        # AGREGASI STOCK
        #
        # Karena 1 material bisa banyak lokasi
        #
        # =================================================
 
 
        aggregation_stock = {}
 
 
 
 
 
        for col in stock.columns:
 
 
            if col == "Material":
 
 
                continue
 
 
 
 
 
            if col == "has_STOCK":
 
 
                aggregation_stock[col] = "max"
 
 
 
            else:
 
 
                aggregation_stock[col] = "sum"
 
 
 
 
 
 
 
 
 
 
 
 
 
        stock = (
 
 
 
            stock
 
 
 
            .groupby(
 
 
 
                "Material",
 
 
 
                as_index=False
 
 
 
            )
 
 
 
            .agg(
 
 
 
                aggregation_stock
 
 
 
            )
 
 
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
    else:
 
 
 
        print(
 
            "STOCK BELUM TERSEDIA"
 
        )
 
 
 
 
 
        stock = pd.DataFrame({
 
 
 
            "Material": [],
 
 
 
            "Stock": [],
 
 
 
            "has_STOCK": []
 
 
 
        })
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    print("\nDEBUG STOCK")
 
 
    print(
 
        stock.head(5)
 
    )
 
 
 
    print(
 
        "TOTAL STOCK MATERIAL:",
 
        stock["Material"].nunique()
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # MATERIAL SET
    #
    # Untuk menentukan availability
    #
    # =====================================================
 
 
    gi_material_set = set(
 
 
        gi["Material"]
 
 
    )
 
 
 
 
 
    gr_material_set = set(
 
 
        gr["Material"]
 
 
    )
 
 
 
 
 
    stock_material_set = set(
 
 
        stock["Material"]
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # MERGE GI + GR + STOCK
    #
    # GI menjadi BASE
    #
    # Semua material berasal dari GI
    #
    # =====================================================
 
 
    print(
 
        "\nSTART MERGE PROJECTION"
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # HINDARI DUPLIKASI LABEL TREND
    #
    # GI dijadikan sumber trend chart
    #
    # =====================================================
 
 
    if "Trend_Bulan" in gr.columns:
 
 
        gr = gr.drop(
 
            columns=[
 
                "Trend_Bulan"
 
            ],
 
            errors="ignore"
 
        )
 
 
 
 
 
    if "Forecast_Bulan" in gr.columns:
 
 
        gr = gr.drop(
 
            columns=[
 
                "Forecast_Bulan"
 
            ],
 
            errors="ignore"
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
    result = gi.merge(
 
 
        gr,
 
 
        on="Material",
 
 
        how="left"
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    result = result.merge(
 
 
        stock,
 
 
        on="Material",
 
 
        how="left"
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # DEFAULT VALUE GR
    #
    # Jika material tidak punya GR
    #
    # =====================================================
 
 
    if "GR_Actual" in result.columns:
 
 
        result["GR_Actual"] = (
 
            result["GR_Actual"]
 
            .fillna(0)
 
        )
 
 
 
 
 
    else:
 
 
        result["GR_Actual"] = 0
 
 
 
 
 
 
 
 
 
 
 
    if "Forecast_GR" in result.columns:
 
 
        result["Forecast_GR"] = (
 
            result["Forecast_GR"]
 
            .fillna(0)
 
        )
 
 
 
 
 
    else:
 
 
        result["Forecast_GR"] = 0
 
 
 
 
 
 
 
 
 
 
 
    if "has_GR" not in result.columns:
 
 
        result["has_GR"] = False
 
 
 
    else:
 
 
        result["has_GR"] = (
 
            result["has_GR"]
 
            .fillna(False)
 
            .astype(bool)
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
    if "has_STOCK" not in result.columns:
 
 
        result["has_STOCK"] = False
 
 
 
    else:
 
 
        result["has_STOCK"] = (
 
            result["has_STOCK"]
 
            .fillna(False)
 
            .astype(bool)
 
        )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # [BARU] UNIT DARI GR
    #
    # Satuan resmi per material = Unit of Entry di GR
    # (tabel acuan data/material_unit.json)
    #
    # Material yang tidak ada di GR -> Unit kosong
    #
    # Key tabel acuan dinormalisasi dengan fungsi yang sama
    # seperti Material di projection ini, supaya cocok
    #
    # =====================================================
 
 
    material_unit_map = {
 
 
        normalize_material(material): unit
 
 
        for material, unit in (
 
 
            load_material_unit_map().items()
 
 
        )
 
 
    }
 
 
 
 
 
 
 
 
 
    result["Unit"] = (
 
 
        result["Material"]
 
 
        .map(
 
 
            material_unit_map
 
 
        )
 
 
        .fillna("")
 
 
    )
 
 
 
 
 
 
 
 
 
    print(
 
 
        "MATERIAL PROJECTION DENGAN SATUAN:",
 
 
        int(
 
 
            (
 
 
                result["Unit"] != ""
 
 
            ).sum()
 
 
        )
 
 
    )
 
            # =====================================================
    # ACTUAL MOVEMENT
    #
    # Rumus:
    #
    # GR Actual - GI Actual
    #
    # =====================================================
 
 
    result["Net_Movement"] = (
 
 
        result["GR_Actual"]
 
 
        -
 
 
        result["GI_Actual"]
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # FORECAST MOVEMENT
    #
    # Rumus:
    #
    # Forecast GR - Forecast GI
    #
    # =====================================================
 
 
    result["Forecast_Net_Movement"] = (
 
 
        result["Forecast_GR"]
 
 
        -
 
 
        result["Forecast_GI"]
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # PROJECTED STOCK
    #
    # Rumus:
    #
    # Stock + Forecast GR - Forecast GI
    #
    # =====================================================
 
 
    result["Projected_Stock"] = None
 
 
 
 
 
 
 
 
 
 
 
    stock_ready = (
 
 
        result["has_STOCK"]
 
 
        ==
 
 
        True
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
    result.loc[
 
        stock_ready,
 
        "Projected_Stock"
 
    ] = (
 
 
 
        result.loc[
 
            stock_ready,
 
            "Stock"
 
        ]
 
 
 
        +
 
 
 
        result.loc[
 
            stock_ready,
 
            "Forecast_GR"
 
        ]
 
 
 
        -
 
 
 
        result.loc[
 
            stock_ready,
 
            "Forecast_GI"
 
        ]
 
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # GAP KEBUTUHAN
    #
    # =====================================================
 
 
    result["Gap_Kebutuhan"] = 0
 
 
 
 
 
 
 
 
 
 
 
    result.loc[
 
        stock_ready,
 
        "Gap_Kebutuhan"
 
    ] = (
 
 
        -result.loc[
 
            stock_ready,
 
            "Projected_Stock"
 
        ]
 
    ).clip(
 
        lower=0
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # COVERAGE
    #
    # Aktif jika:
    #
    # has_GI
    # has_GR
    # has_STOCK
    #
    # =====================================================
 
 
    result["Coverage"] = None
 
 
 
 
 
 
 
 
 
 
 
    coverage_ready = (
 
 
        result["has_GI"]
 
 
        &
 
 
        result["has_GR"]
 
 
        &
 
 
        result["has_STOCK"]
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    result.loc[
 
        coverage_ready,
 
        "Coverage"
 
    ] = result.loc[
 
        coverage_ready
 
    ].apply(
 
 
        calculate_coverage,
 
 
        axis=1
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # COVERAGE PROJECTION
    #
    # =====================================================
 
 
    result["Coverage_Projection"] = None
 
 
 
 
 
 
 
 
 
 
 
    projection_result = (
 
 
 
        result.loc[
 
            coverage_ready
 
        ]
 
 
 
        .apply(
 
 
 
            calculate_coverage_projection,
 
 
 
            axis=1
 
 
 
        )
 
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    if len(projection_result) > 0:
 
 
 
        projection_df = pd.DataFrame(
 
 
            projection_result.tolist()
 
 
        )
 
 
 
 
 
        projection_df.index = result.loc[
 
            coverage_ready
 
        ].index
 
 
 
 
 
 
 
        for col in projection_df.columns:
 
 
 
            result.loc[
 
                coverage_ready,
 
                col
 
            ] = projection_df[col]
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # STATUS
    #
    # =====================================================
 
 
    result["Status"] = None
 
 
 
 
 
 
 
 
 
 
 
    result.loc[
 
        coverage_ready,
 
        "Status"
 
    ] = result.loc[
 
        coverage_ready,
 
        "Coverage"
 
    ].apply(
 
 
 
        calculate_status
 
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # SORT MATERIAL
    # =====================================================
 
 
    result = result.sort_values(
 
        by="Material"
 
    ).reset_index(
 
        drop=True
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # FINAL BOOLEAN CLEANING
    #
    # =====================================================
 
 
    boolean_columns = [
 
 
 
        "has_GI",
 
 
 
        "has_GR",
 
 
 
        "has_STOCK"
 
 
 
    ]
 
 
 
 
 
 
 
 
 
 
 
 
 
    for col in boolean_columns:
 
 
 
        if col in result.columns:
 
 
 
            result[col] = (
 
 
 
                result[col]
 
 
 
                .fillna(False)
 
 
 
                .astype(bool)
 
 
 
            )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # FINAL NUMERIC CLEANING
    #
    # =====================================================
 
 
    numeric_final_columns = [
 
 
 
        "GI_Actual",
 
 
 
        "Forecast_GI",
 
 
 
        "GR_Actual",
 
 
 
        "Forecast_GR",
 
 
 
        "Stock",
 
 
 
        "Net_Movement",
 
 
 
        "Forecast_Net_Movement",
 
 
 
        "Projected_Stock",
 
 
 
        "Gap_Kebutuhan",
 
 
 
        "History_Count",
 
 
 
        "Coverage",
 
 
 
        "Coverage_Projection"
 
 
 
    ]
 
 
 
 
 
 
 
 
 
 
 
 
 
    for col in numeric_final_columns:
 
 
 
        if col in result.columns:
 
 
 
            result[col] = pd.to_numeric(
 
 
 
                result[col],
 
 
 
                errors="coerce"
 
 
 
            )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print("\n")
 
    print("="*60)
 
    print("FINAL PROJECTION RESULT")
 
    print("="*60)
 
 
 
 
 
 
 
 
 
 
 
 
 
    debug_columns = [
 
 
 
        "Material",
 
 
 
        "Unit",
 
 
 
        "Forecast_GI",
 
 
 
        "Forecast_GR",
 
 
 
        "Stock",
 
 
 
        "has_GI",
 
 
 
        "has_GR",
 
 
 
        "has_STOCK",
 
 
 
        "History_Count",
 
 
 
        "Coverage",
 
 
 
        "Status"
 
 
 
    ]
 
 
 
 
 
 
 
 
 
 
 
 
 
    debug_columns = [
 
 
 
        col
 
 
 
        for col in debug_columns
 
 
 
        if col in result.columns
 
 
 
    ]
 
 
 
 
 
 
 
 
 
 
 
 
 
    print(
 
 
 
        result[debug_columns]
 
 
 
        .head(20)
 
 
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print("\nSUMMARY FILTER")
 
 
 
 
 
 
 
 
 
 
 
 
 
    print(
 
        "TOTAL MATERIAL:",
 
        len(result)
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print(
 
        "GI + GR:",
 
        len(
 
            result[
 
                result["has_GR"]
 
            ]
 
        )
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print(
 
        "GI + GR + STOCK:",
 
        len(
 
            result[
 
 
 
                result["has_GR"]
 
 
 
                &
 
 
 
                result["has_STOCK"]
 
 
 
            ]
 
        )
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print(
 
        "HISTORY > 7:",
 
        len(
 
            result[
 
                result["History_Count"] > 7
 
            ]
 
        )
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    print("="*60)
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # FINAL JSON SAFETY CLEANING
    #
    # =====================================================
 
 
    result = result.replace(
 
        [
 
            float("inf"),
 
            float("-inf")
 
        ],
 
        None
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    result = result.where(
 
        pd.notnull(result),
 
        None
 
    )
 
 
 
 
 
 
 
 
 
 
 
 
 
    # =====================================================
    # RETURN FINAL DATAFRAME
    #
    # =====================================================
 
 
    return result
