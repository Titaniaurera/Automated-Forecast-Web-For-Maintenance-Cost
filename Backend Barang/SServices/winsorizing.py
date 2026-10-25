import pandas as pd


def winsorizing(df):

    print("=" * 60)
    print("STEP 3 : WINSORIZING")
    print("=" * 60)

    qty_col = "Qty in Un. of Entry"

    # =====================================================
    # Validasi Kolom
    # =====================================================

    required_columns = [
        "Material",
        qty_col
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Kolom berikut tidak ditemukan: {missing_columns}"
        )

    # =====================================================
    # Copy Data
    # =====================================================

    df = df.copy()

    # Kolom hasil winsor
    df["Qty_Winsor"] = df[qty_col]

    # =====================================================
    # Loop Tiap Material
    # =====================================================

    total_material = df["Material"].nunique()

    print(f"Jumlah Material : {total_material}")

    summary = []

    for material in df["Material"].unique():

        material_mask = df["Material"] == material

        material_df = df.loc[
            material_mask,
            qty_col
        ]

        # ---------------------------------------------
        # Hitung Threshold
        # ---------------------------------------------

        lower_threshold = material_df.quantile(0.003)

        upper_threshold = material_df.quantile(0.95)

        # ---------------------------------------------
        # Winsorizing
        # ---------------------------------------------

        df.loc[
            material_mask,
            "Qty_Winsor"
        ] = material_df.clip(
            lower=lower_threshold,
            upper=upper_threshold
        )

        summary.append({

            "Material": material,

            "Lower_Threshold": lower_threshold,

            "Upper_Threshold": upper_threshold,

            "Jumlah_Data": len(material_df)

        })

    # =====================================================
    # Ringkasan
    # =====================================================

    summary_df = pd.DataFrame(summary)

    print("=" * 60)
    print("Winsorizing selesai")
    print(f"Material diproses : {len(summary_df)}")
    print("=" * 60)

    return df