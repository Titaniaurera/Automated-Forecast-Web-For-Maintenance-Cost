# # # =====================================================
# # # GI FORECASTING PIPELINE
# # # =====================================================


# # from services.preprocessing import preprocessing

# # from services.movement_cleansing import (
# #     clean_gi_movement
# # )

# # from services.readiness import readiness

# # from services.winsorizing import winsorizing

# # from services.aggregation import aggregation

# # from services.feature_engineering import feature_engineering

# # from services.forecasting import forecasting





# # # =====================================================
# # # RUN PIPELINE GI
# # # =====================================================


# # def run_pipeline(df):


# #     print("\n")
# #     print("=" * 60)
# #     print("START GI FORECASTING PIPELINE")
# #     print("=" * 60)






# #     # =================================================
# #     # 1. PREPROCESSING
# #     #
# #     # Membersihkan:
# #     #
# #     # - column
# #     # - tanggal
# #     # - numeric qty
# #     #
# #     # =================================================


# #     df = preprocessing(df)



# #     print(

# #         "[1] GI Preprocessing:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 2. MOVEMENT CLEANSING
# #     #
# #     # Valid GI:
# #     #
# #     # 261
# #     # 281
# #     # 961
# #     #
# #     # Cancel:
# #     #
# #     # 262
# #     # 282
# #     # 962
# #     #
# #     # =================================================


# #     df = clean_gi_movement(df)



# #     print(

# #         "[2] GI Movement Cleansing:",

# #         len(df)

# #     )








# #     # =================================================
# #     # CEK DATA
# #     # =================================================


# #     if len(df) == 0:


# #         raise ValueError(

# #             "Tidak ada data GI valid setelah movement cleansing."

# #         )









# #     # =================================================
# #     # 3. READINESS CHECK
# #     #
# #     # Cek kesiapan forecasting
# #     #
# #     # =================================================


# #     df = readiness(df)



# #     print(

# #         "[3] GI Readiness:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 4. WINSORIZING
# #     #
# #     # Mengurangi efek outlier Qty GI
# #     #
# #     # =================================================


# #     df = winsorizing(df)



# #     print(

# #         "[4] GI Winsorizing:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 5. AGGREGATION
# #     #
# #     # Level:
# #     #
# #     # Material
# #     # Bulan
# #     #
# #     # Target:
# #     #
# #     # Qty GI
# #     #
# #     # =================================================


# #     df = aggregation(df)



# #     print(

# #         "[5] GI Aggregation:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 6. FEATURE ENGINEERING
# #     #
# #     # Membuat:
# #     #
# #     # Lag
# #     # Rolling Mean
# #     # Rolling STD
# #     # EMA
# #     #
# #     # =================================================


# #     df = feature_engineering(df)



# #     print(

# #         "[6] GI Feature Engineering:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 7. FORECASTING GI
# #     #
# #     # IMPORTANT:
# #     #
# #     # Gunakan forecasting generic
# #     # dengan type GI
# #     #
# #     # Output:
# #     #
# #     # GI_Actual
# #     # Forecast_GI
# #     # Trend_GI
# #     # Best_Model_GI
# #     #
# #     # =================================================


# #     results_df = forecasting(

# #         df,

# #         transaction_type="GI"

# #     )



# #     print(

# #         "[7] GI Forecasting:",

# #         type(results_df),

# #         len(results_df)

# #     )









# #     # =================================================
# #     # VALIDASI OUTPUT GI
# #     # =================================================


# #     required_columns = [


# #         "Material",

# #         "Material Description",

# #         "Bulan",

# #         "GI_Actual",

# #         "Forecast_GI",

# #         "Trend_GI",

# #         "Best_Model_GI"


# #     ]





# #     missing_columns = [

# #         col

# #         for col in required_columns

# #         if col not in results_df.columns

# #     ]






# #     if len(missing_columns) > 0:


# #         raise ValueError(

# #             "Output GI Forecast tidak lengkap. Missing: "

# #             +

# #             str(missing_columns)

# #         )









# #     print("\n")
# #     print("=" * 60)
# #     print("GI FORECASTING PIPELINE SELESAI")
# #     print("=" * 60)





# #     return results_df




# # =====================================================
# # GI FORECASTING PIPELINE
# # =====================================================


# from services.preprocessing import preprocessing

# from services.movement_cleansing import (
#     clean_gi_movement
# )

# from services.readiness import readiness

# from services.winsorizing import winsorizing

# from services.aggregation import aggregation

# from services.feature_engineering import feature_engineering

# from services.forecasting import forecasting





# # =====================================================
# # DEBUG FUNCTION
# # =====================================================


# def debug_material(stage, df):


#     print("\n")

#     print("=" * 60)

#     print(stage)

#     print("=" * 60)



#     print(
#         "Jumlah Row:",
#         len(df)
#     )



#     if "Material" in df.columns:


#         print(
#             "Jumlah Material Unik:",
#             df["Material"].nunique()
#         )


#         print(
#             "Contoh Material:"
#         )


#         print(
#             list(
#                 df["Material"]
#                 .astype(str)
#                 .unique()
#             )[:20]
#         )


#     print("=" * 60)







# # =====================================================
# # RUN PIPELINE GI
# # =====================================================


# def run_pipeline(df):


#     print("\n")

#     print("=" * 60)

#     print("START GI FORECASTING PIPELINE")

#     print("=" * 60)







#     # =================================================
#     # 1. PREPROCESSING
#     # =================================================


#     df = preprocessing(df)



#     debug_material(
#         "GI AFTER PREPROCESSING",
#         df
#     )








#     # =================================================
#     # 2. MOVEMENT CLEANSING
#     # =================================================


#     df = clean_gi_movement(df)



#     debug_material(
#         "GI AFTER MOVEMENT CLEANSING",
#         df
#     )







#     if len(df) == 0:


#         raise ValueError(

#             "Tidak ada data GI valid setelah movement cleansing."

#         )









#     # =================================================
#     # 3. READINESS CHECK
#     # =================================================


#     df = readiness(df)



#     debug_material(
#         "GI AFTER READINESS",
#         df
#     )







#     # =================================================
#     # 4. WINSORIZING
#     # =================================================


#     df = winsorizing(df)



#     debug_material(
#         "GI AFTER WINSORIZING",
#         df
#     )








#     # =================================================
#     # 5. AGGREGATION
#     # =================================================


#     df = aggregation(df)



#     debug_material(
#         "GI AFTER AGGREGATION",
#         df
#     )








#     # =================================================
#     # 6. FEATURE ENGINEERING
#     # =================================================


#     df = feature_engineering(df)



#     debug_material(
#         "GI AFTER FEATURE ENGINEERING",
#         df
#     )








#     # =================================================
#     # 7. FORECASTING GI
#     # =================================================


#     results_df = forecasting(

#         df,

#         transaction_type="GI"

#     )



#     debug_material(
#         "GI FINAL FORECAST RESULT",
#         results_df
#     )









#     # =================================================
#     # VALIDASI OUTPUT GI
#     # =================================================


#     required_columns = [


#         "Material",

#         "Material Description",

#         "Bulan",

#         "GI_Actual",

#         "Forecast_GI",

#         "Trend_GI",

#         "Best_Model_GI"


#     ]





#     missing_columns = [


#         col

#         for col in required_columns

#         if col not in results_df.columns


#     ]







#     if len(missing_columns) > 0:


#         raise ValueError(

#             "Output GI Forecast tidak lengkap. Missing: "

#             +

#             str(missing_columns)

#         )








#     print("\n")

#     print("=" * 60)

#     print("GI FORECASTING PIPELINE SELESAI")

#     print("=" * 60)





#     return results_df





# =====================================================
# GI FORECASTING PIPELINE
# =====================================================


from services.preprocessing import preprocessing

from services.movement_cleansing import (
    clean_gi_movement
)

from services.winsorizing import winsorizing

from services.aggregation import aggregation

from services.feature_engineering import feature_engineering

from services.forecasting import forecasting





# =====================================================
# DEBUG FUNCTION
# =====================================================


def debug_material(stage, df):


    print("\n")

    print("=" * 60)

    print(stage)

    print("=" * 60)



    print(
        "Jumlah Row:",
        len(df)
    )


    if "Material" in df.columns:


        print(
            "Jumlah Material Unik:",
            df["Material"].nunique()
        )


        print(
            "Contoh Material:"
        )


        print(
            list(
                df["Material"]
                .astype(str)
                .unique()
            )[:20]
        )


    print("=" * 60)








# =====================================================
# RUN PIPELINE GI
# =====================================================


def run_pipeline(df):


    print("\n")

    print("=" * 60)

    print("START GI FORECASTING PIPELINE")

    print("=" * 60)





    # =================================================
    # 1. PREPROCESSING
    #
    # Membersihkan:
    # - column
    # - tanggal
    # - qty
    #
    # =================================================


    df = preprocessing(df)



    debug_material(
        "GI AFTER PREPROCESSING",
        df
    )







    # =================================================
    # 2. MOVEMENT CLEANSING
    #
    # Menghapus:
    # - full cancel
    # - reversal pasangan
    #
    # Output:
    # GI valid
    #
    # =================================================


    df = clean_gi_movement(df)



    debug_material(
        "GI AFTER MOVEMENT CLEANSING",
        df
    )






    if len(df) == 0:


        raise ValueError(

            "Tidak ada data GI valid setelah movement cleansing."

        )








    # =================================================
    # 3. WINSORIZING
    #
    # Mengurangi efek outlier
    #
    # =================================================


    df = winsorizing(df)



    debug_material(
        "GI AFTER WINSORIZING",
        df
    )







    # =================================================
    # 4. AGGREGATION
    #
    # Level:
    # Material
    # Bulan
    #
    # Target:
    # Qty GI
    #
    # =================================================


    df = aggregation(df)



    debug_material(
        "GI AFTER AGGREGATION",
        df
    )








    # =================================================
    # 5. FEATURE ENGINEERING
    #
    # Membuat:
    # Lag
    # Rolling Mean
    # Rolling STD
    # EMA
    #
    # =================================================


    df = feature_engineering(df)



    debug_material(
        "GI AFTER FEATURE ENGINEERING",
        df
    )








    # =================================================
    # 6. FORECASTING GI
    #
    # Output:
    # GI_Actual
    # Forecast_GI
    # Trend_GI
    # Best_Model_GI
    #
    # =================================================


    results_df = forecasting(

        df,

        transaction_type="GI"

    )



    debug_material(
        "GI FINAL FORECAST RESULT",
        results_df
    )







    # =================================================
    # VALIDASI OUTPUT GI
    # =================================================


    required_columns = [


        "Material",

        "Material Description",

        "Bulan",

        "GI_Actual",

        "Forecast_GI",

        "Trend_GI",

        "Best_Model_GI"


    ]





    missing_columns = [


        col

        for col in required_columns

        if col not in results_df.columns


    ]







    if len(missing_columns) > 0:


        raise ValueError(

            "Output GI Forecast tidak lengkap. Missing: "

            +

            str(missing_columns)

        )









    print("\n")

    print("=" * 60)

    print("GI FORECASTING PIPELINE SELESAI")

    print("=" * 60)



    print(

        "Total Material Forecast:",

        results_df["Material"].nunique()

    )



    print("=" * 60)






    return results_df