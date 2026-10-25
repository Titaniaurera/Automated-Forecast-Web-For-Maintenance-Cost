# # # =====================================================
# # # GR FORECASTING PIPELINE
# # # =====================================================


# # from services.preprocessing import preprocessing

# # from services.readiness import readiness

# # from services.winsorizing import winsorizing

# # from services.gr_aggregation import gr_aggregation

# # from services.feature_engineering import feature_engineering

# # from services.forecasting import forecasting





# # # =====================================================
# # # RUN PIPELINE GR
# # # =====================================================


# # def run_gr_pipeline(df):


# #     print("\n")
# #     print("=" * 60)
# #     print("START GR FORECASTING PIPELINE")
# #     print("=" * 60)





# #     # =================================================
# #     # 1. PREPROCESSING
# #     #
# #     # Membersihkan:
# #     #
# #     # - nama kolom
# #     # - tanggal
# #     # - numeric qty
# #     #
# #     # =================================================


# #     df = preprocessing(df)



# #     print(

# #         "[1] GR Preprocessing:",

# #         type(df),

# #         len(df)

# #     )







# #     # =================================================
# #     # 2. READINESS CHECK
# #     #
# #     # Mengecek kesiapan data
# #     #
# #     # =================================================


# #     df = readiness(df)



# #     print(

# #         "[2] GR Readiness:",

# #         type(df),

# #         len(df)

# #     )








# #     # =================================================
# #     # 3. WINSORIZING
# #     #
# #     # Mengurangi pengaruh outlier
# #     #
# #     # transaksi GR ekstrem
# #     #
# #     # =================================================


# #     df = winsorizing(df)



# #     print(

# #         "[3] GR Winsorizing:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 4. GR AGGREGATION
# #     #
# #     # Aggregasi:
# #     #
# #     # Material
# #     # Bulan
# #     # Qty GR
# #     #
# #     # =================================================


# #     df = gr_aggregation(df)



# #     print(

# #         "[4] GR Aggregation:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 5. FEATURE ENGINEERING
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

# #         "[5] GR Feature Engineering:",

# #         type(df),

# #         len(df)

# #     )









# #     # =================================================
# #     # 6. FORECASTING GR
# #     #
# #     # IMPORTANT:
# #     #
# #     # Menggunakan forecasting generic
# #     #
# #     # dengan parameter GR
# #     #
# #     # sehingga output:
# #     #
# #     # GR_Actual
# #     # Forecast_GR
# #     # Trend_GR
# #     # Best_Model_GR
# #     #
# #     # =================================================


# #     result = forecasting(

# #         df,

# #         transaction_type="GR"

# #     )



# #     print(

# #         "[6] GR Forecasting:",

# #         type(result),

# #         len(result)

# #     )









# #     # =================================================
# #     # VALIDASI OUTPUT
# #     # =================================================


# #     required_output = [


# #         "Material",

# #         "Material Description",

# #         "Bulan",

# #         "GR_Actual",

# #         "Forecast_GR",

# #         "Trend_GR",

# #         "Best_Model_GR"


# #     ]





# #     missing_columns = [

# #         col

# #         for col in required_output

# #         if col not in result.columns

# #     ]






# #     if len(missing_columns) > 0:


# #         raise ValueError(

# #             "Output GR Forecast tidak lengkap. Missing: "

# #             +

# #             str(missing_columns)

# #         )











# #     print("\n")
# #     print("=" * 60)
# #     print("GR FORECASTING PIPELINE SELESAI")
# #     print("=" * 60)





# #     return result



# # =====================================================
# # GR FORECASTING PIPELINE
# # =====================================================


# from services.preprocessing import preprocessing

# from services.readiness import readiness

# from services.winsorizing import winsorizing

# from services.gr_aggregation import gr_aggregation

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
# # RUN PIPELINE GR
# # =====================================================


# def run_gr_pipeline(df):


#     print("\n")

#     print("=" * 60)

#     print("START GR FORECASTING PIPELINE")

#     print("=" * 60)







#     # =================================================
#     # 1. PREPROCESSING
#     # =================================================


#     df = preprocessing(df)



#     debug_material(
#         "GR AFTER PREPROCESSING",
#         df
#     )








#     # =================================================
#     # 2. READINESS CHECK
#     # =================================================


#     df = readiness(df)



#     debug_material(
#         "GR AFTER READINESS",
#         df
#     )









#     # =================================================
#     # 3. WINSORIZING
#     # =================================================


#     df = winsorizing(df)



#     debug_material(
#         "GR AFTER WINSORIZING",
#         df
#     )









#     # =================================================
#     # 4. GR AGGREGATION
#     # =================================================


#     df = gr_aggregation(df)



#     debug_material(
#         "GR AFTER GR AGGREGATION",
#         df
#     )









#     # =================================================
#     # 5. FEATURE ENGINEERING
#     # =================================================


#     df = feature_engineering(df)



#     debug_material(
#         "GR AFTER FEATURE ENGINEERING",
#         df
#     )









#     # =================================================
#     # 6. FORECASTING GR
#     # =================================================


#     result = forecasting(

#         df,

#         transaction_type="GR"

#     )



#     debug_material(
#         "GR FINAL FORECAST RESULT",
#         result
#     )









#     # =================================================
#     # VALIDASI OUTPUT
#     # =================================================


#     required_output = [


#         "Material",

#         "Material Description",

#         "Bulan",

#         "GR_Actual",

#         "Forecast_GR",

#         "Trend_GR",

#         "Best_Model_GR"


#     ]





#     missing_columns = [


#         col

#         for col in required_output

#         if col not in result.columns


#     ]







#     if len(missing_columns) > 0:


#         raise ValueError(

#             "Output GR Forecast tidak lengkap. Missing: "

#             +

#             str(missing_columns)

#         )









#     print("\n")

#     print("=" * 60)

#     print("GR FORECASTING PIPELINE SELESAI")

#     print("=" * 60)





#     return result



# =====================================================
# GR FORECASTING PIPELINE
# =====================================================


from services.preprocessing import preprocessing

from services.winsorizing import winsorizing

from services.gr_aggregation import gr_aggregation

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
# RUN PIPELINE GR
# =====================================================


def run_gr_pipeline(df):


    print("\n")

    print("=" * 60)

    print("START GR FORECASTING PIPELINE")

    print("=" * 60)







    # =================================================
    # 1. PREPROCESSING
    #
    # Membersihkan:
    # - nama kolom
    # - tanggal
    # - numeric qty
    #
    # =================================================


    df = preprocessing(df)



    debug_material(
        "GR AFTER PREPROCESSING",
        df
    )









    # =================================================
    # 2. WINSORIZING
    #
    # Mengurangi pengaruh outlier
    #
    # =================================================


    df = winsorizing(df)



    debug_material(
        "GR AFTER WINSORIZING",
        df
    )









    # =================================================
    # 3. GR AGGREGATION
    #
    # Aggregasi:
    #
    # Material
    # Bulan
    #
    # Target:
    # Qty GR
    #
    # =================================================


    df = gr_aggregation(df)



    debug_material(
        "GR AFTER GR AGGREGATION",
        df
    )









    # =================================================
    # 4. FEATURE ENGINEERING
    #
    # Membuat:
    #
    # Lag
    # Rolling Mean
    # Rolling STD
    # EMA
    #
    # =================================================


    df = feature_engineering(df)



    debug_material(
        "GR AFTER FEATURE ENGINEERING",
        df
    )









    # =================================================
    # 5. FORECASTING GR
    #
    # Output:
    #
    # GR_Actual
    # Forecast_GR
    # Trend_GR
    # Best_Model_GR
    #
    # =================================================


    result = forecasting(

        df,

        transaction_type="GR"

    )



    debug_material(
        "GR FINAL FORECAST RESULT",
        result
    )









    # =================================================
    # VALIDASI OUTPUT
    # =================================================


    required_output = [


        "Material",

        "Material Description",

        "Bulan",

        "GR_Actual",

        "Forecast_GR",

        "Trend_GR",

        "Best_Model_GR"


    ]





    missing_columns = [


        col

        for col in required_output

        if col not in result.columns


    ]








    if len(missing_columns) > 0:


        raise ValueError(

            "Output GR Forecast tidak lengkap. Missing: "

            +

            str(missing_columns)

        )









    print("\n")

    print("=" * 60)

    print("GR FORECASTING PIPELINE SELESAI")

    print("=" * 60)



    print(

        "Total Material Forecast:",

        result["Material"].nunique()

    )



    print("=" * 60)






    return result