"""
GR MONTHLY AGGREGATION
=======================

Berbeda dari GI, dataset Goods Receipt TIDAK butuh cleansing
movement-cancel (lihat spec §B: "Digunakan untuk melihat histori
barang masuk dan membuat forecast supply" -- tidak ada aturan
Case 1/2/3 untuk GR).

Jadi di sini kita tidak melakukan pairing/cancel-matching seperti
di services/movement_cleansing.py (yang khusus GI). Kita hanya
menjumlahkan qty per Material per Bulan.

Qty di data GR SAP biasanya sudah tercatat positif (barang masuk),
tapi untuk jaga-jaga (mis. ada baris pembalik/retur yang tercatat
negatif) kita pakai nilai absolut supaya tidak ada bulan dengan GR
negatif -- barang masuk tidak pernah negatif dalam pengertian
forecast supply.
"""

import pandas as pd


def gr_aggregation(df, qty_column="Qty in Un. of Entry"):

    print("=" * 60)
    print("STEP : GR MONTHLY AGGREGATION")
    print("=" * 60)

    # =====================================================
    # Validasi Kolom
    # =====================================================

    required_columns = [
        "Posting Date",
        "Material",
        "Material Description",
        qty_column,
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Kolom berikut tidak ditemukan (GR): {missing_columns}"
        )

    df = df.copy()

    # =====================================================
    # Bulan
    # =====================================================

    df["Bulan"] = (
        df["Posting Date"]
        .dt.to_period("M")
        .astype(str)
    )

    # =====================================================
    # Qty GR selalu diperlakukan sebagai barang masuk (positif)
    # =====================================================

    qty_source = (
        df["Qty_Winsor"] if "Qty_Winsor" in df.columns else df[qty_column]
    )

    df["Qty_Model"] = qty_source.abs()

    # =====================================================
    # Agregasi Bulanan
    # =====================================================

    agg_kwargs = {
        "Qty": ("Qty_Model", "sum"),
    }

    if "Stock Akhir" in df.columns:
        agg_kwargs["Stock_Akhir"] = ("Stock Akhir", "last")

    monthly_df = (
        df.groupby(
            [
                "Material",
                "Material Description",
                "Bulan"
            ],
            as_index=False
        )
        .agg(**agg_kwargs)
    )

    print(f"Jumlah Material : {monthly_df['Material'].nunique()}")
    print(f"Jumlah Data Bulanan : {len(monthly_df)}")
    print("=" * 60)

    return monthly_df
