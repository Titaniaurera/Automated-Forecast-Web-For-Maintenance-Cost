import numpy as np
import pandas as pd


from sklearn.model_selection import TimeSeriesSplit


from sklearn.linear_model import LinearRegression


from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    AdaBoostRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor
)


from xgboost import XGBRegressor


from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error
)


from sklearn.base import clone





# =====================================================
# MODEL DICTIONARY
# =====================================================


MODELS = {


    "Linear Regression":

        LinearRegression(),



    "Random Forest":

        RandomForestRegressor(

            random_state=42,

            n_estimators=200

        ),



    "Extra Trees":

        ExtraTreesRegressor(

            random_state=42,

            n_estimators=200

        ),



    "AdaBoost":

        AdaBoostRegressor(

            random_state=42,

            n_estimators=100

        ),



    "Gradient Boosting":

        GradientBoostingRegressor(

            random_state=42,

            n_estimators=200

        ),



    "Hist Gradient Boosting":

        HistGradientBoostingRegressor(

            random_state=42

        ),



    "XGBoost":

        XGBRegressor(

            random_state=42,

            n_estimators=200,

            learning_rate=0.05,

            max_depth=6,

            verbosity=0

        )

}





# =====================================================
# CONSTANT
# =====================================================


TARGET_COLUMN = "Qty"



FEATURE_COLUMNS = [

    "Lag_1",

    "Lag_2",

    "Lag_3",

    "Rolling_Mean_3",

    "Rolling_STD_3",

    "EMA_3",

    "Month",

    "Quarter",

    "Year"

]



MIN_HISTORY_MONTHS = 7



N_SPLITS = 5



EMA_SPAN = 3



ROLLING_WINDOW = 3





# =====================================================
# EVALUATION
# =====================================================


def evaluate_model(

    y_true,

    y_pred

):


    mae = mean_absolute_error(

        y_true,

        y_pred

    )



    rmse = np.sqrt(

        mean_squared_error(

            y_true,

            y_pred

        )

    )



    try:


        mape = (

            mean_absolute_percentage_error(

                y_true,

                y_pred

            )

            *

            100

        )


    except Exception:


        mape = np.nan





    return {


        "MAE":

            mae,



        "RMSE":

            rmse,



        "MAPE":

            mape


    }







# =====================================================
# TRAIN MODEL
# =====================================================


def train_model(

    model,

    X_train,

    y_train,

    X_test

):


    model.fit(

        X_train,

        y_train

    )


    prediction = model.predict(

        X_test

    )


    return prediction







# =====================================================
# TIME SERIES CROSS VALIDATION
# =====================================================


def cross_validate_model(

    model_template,

    X,

    y,

    n_splits=N_SPLITS

):


    n_samples = len(X)



    effective_splits = min(

        n_splits,

        n_samples - 1

    )



    if effective_splits < 2:


        return None






    tscv = TimeSeriesSplit(

        n_splits=effective_splits

    )



    fold_mae = []

    fold_rmse = []

    fold_mape = []







    for train_index, test_index in tscv.split(X):


        X_train = X.iloc[train_index]


        X_test = X.iloc[test_index]



        y_train = y.iloc[train_index]


        y_test = y.iloc[test_index]





        model = clone(

            model_template

        )





        prediction = train_model(

            model,

            X_train,

            y_train,

            X_test

        )





        metrics = evaluate_model(

            y_test.values,

            prediction

        )





        fold_mae.append(

            metrics["MAE"]

        )



        fold_rmse.append(

            metrics["RMSE"]

        )



        fold_mape.append(

            metrics["MAPE"]

        )







    return {


        "MAE":

            float(

                np.nanmean(

                    fold_mae

                )

            ),




        "RMSE":

            float(

                np.nanmean(

                    fold_rmse

                )

            ),




        "MAPE":

            float(

                np.nanmean(

                    fold_mape

                )

            )


    }

    # =====================================================
# BUILD NEXT PERIOD FEATURES
# =====================================================


def build_next_period_features(

    material_df

):


    qty_history = (

        material_df[TARGET_COLUMN]

        .reset_index(drop=True)

        .astype(float)

        .fillna(0)

    )





    # ===============================
    # LAG FEATURES
    # ===============================


    lag_1 = (

        qty_history.iloc[-1]

        if len(qty_history) >= 1

        else 0

    )



    lag_2 = (

        qty_history.iloc[-2]

        if len(qty_history) >= 2

        else lag_1

    )



    lag_3 = (

        qty_history.iloc[-3]

        if len(qty_history) >= 3

        else lag_2

    )








    # ===============================
    # ROLLING FEATURES
    # ===============================


    last_window = (

        qty_history

        .tail(

            ROLLING_WINDOW

        )

    )



    rolling_mean_3 = (

        last_window.mean()

    )



    rolling_std_3 = (

        last_window.std()

        if len(last_window) > 1

        else 0

    )









    # ===============================
    # EMA
    # ===============================


    ema = (

        qty_history

        .ewm(

            span=EMA_SPAN,

            adjust=False

        )

        .mean()

    )



    ema_3 = ema.iloc[-1]









    # ===============================
    # NEXT MONTH
    # ===============================


    last_date = pd.to_datetime(

        material_df["Bulan"]

        .iloc[-1]

    )



    next_bulan = (

        last_date

        +

        pd.DateOffset(

            months=1

        )

    )



    month = next_bulan.month



    quarter = (

        (month - 1)

        //

        3

    ) + 1



    year = next_bulan.year









    next_features = pd.DataFrame([{



        "Lag_1":

            lag_1,



        "Lag_2":

            lag_2,



        "Lag_3":

            lag_3,



        "Rolling_Mean_3":

            rolling_mean_3,



        "Rolling_STD_3":

            rolling_std_3,



        "EMA_3":

            ema_3,



        "Month":

            month,



        "Quarter":

            quarter,



        "Year":

            year



    }])









    next_features = (

        next_features

        .fillna(0)

    )









    return (

        next_features[FEATURE_COLUMNS],

        next_bulan

    )








# =====================================================
# FORECAST SINGLE MATERIAL
# GENERIC GI / GR
# =====================================================


def forecast_single_material(

    material,

    material_df,

    transaction_type="GI"

):


    print("\n" + "-" * 50)



    print(

        "PROCESS MATERIAL:",

        material,

        "| TYPE:",

        transaction_type

    )



    print("-" * 50)








    # ======================================
    # CEK HISTORY
    # ======================================


    if len(material_df) < MIN_HISTORY_MONTHS:



        print(

            "Skip:",

            material,

            "history kurang"

        )



        return None

            # ======================================
    # PREPARE TRAIN DATA
    # ======================================


    X = (

        material_df[FEATURE_COLUMNS]

        .astype(float)

        .fillna(0)

    )




    y = (

        material_df[TARGET_COLUMN]

        .astype(float)

        .fillna(0)

    )









    best_model = None

    best_model_name = None


    best_score = np.inf



    best_metric = {


        "MAE": None,


        "RMSE": None,


        "MAPE": None


    }









    # ======================================
    # MODEL SELECTION
    # ======================================


    for model_name, model_template in MODELS.items():


        try:


            cv_result = cross_validate_model(

                model_template,

                X,

                y

            )





            if cv_result is None:


                continue








            print(

                model_name,

                "MAE:",

                round(

                    cv_result["MAE"],

                    3

                )

            )









            if cv_result["MAE"] < best_score:



                best_score = cv_result["MAE"]


                best_model = model_template


                best_model_name = model_name


                best_metric = cv_result










        except Exception as e:


            print(

                "Model gagal:",

                model_name,

                e

            )


            continue











    if best_model is None:


        print(

            "Tidak ada model cocok"

        )


        return None











    print(

        "BEST MODEL:",

        best_model_name

    )









    # ======================================
    # FINAL TRAIN
    # ======================================


    final_model = clone(

        best_model

    )



    final_model.fit(

        X,

        y

    )












    # ======================================
    # FORECAST NEXT MONTH
    # ======================================


    next_features, next_month = build_next_period_features(

        material_df

    )




    forecast_value = final_model.predict(

        next_features

    )[0]



    forecast_value = float(

        forecast_value

    )












    # ======================================
    # HANDLE INVALID FORECAST
    # ======================================


    fallback = False





    if forecast_value < 0:


        forecast_value = float(

            material_df[TARGET_COLUMN]

            .tail(3)

            .mean()

        )


        fallback = True







    if np.isnan(forecast_value):


        forecast_value = 0


        fallback = True







    forecast_value = max(

        forecast_value,

        0

    )












    # ======================================
    # ACTUAL LAST MONTH
    # ======================================


    actual_value = float(

        material_df[TARGET_COLUMN]

        .iloc[-1]

    )











    # ======================================
    # TREND HISTORY + LABEL
    # ======================================


    history_df = (

        material_df

        .tail(6)

        .copy()

    )





    # ===============================
    # HISTORY QUANTITY
    # ===============================


    trend = (

        history_df[TARGET_COLUMN]

        .astype(float)

        .tolist()

    )





    # ===============================
    # HISTORY DATE LABEL
    # ===============================


    trend_bulan = (

        pd.to_datetime(

            history_df["Bulan"]

        )

        .dt.strftime(

            "%Y-%m"

        )

        .tolist()

    )





    # ===============================
    # FORECAST DATE LABEL
    # ===============================


    forecast_bulan = (

        next_month.strftime(

            "%Y-%m"

        )

    )









    # ======================================
    # DESCRIPTION
    # ======================================


    description = str(

        material_df["Material Description"]

        .iloc[-1]

    )











    # ======================================
    # OUTPUT PREFIX
    # ======================================


    prefix = transaction_type.upper()










    result = {


        "Material":

            material,



        "Material Description":

            description,



        "Bulan":

            next_month.strftime(

                "%Y-%m"

            ),



        "Trend_Bulan":

            trend_bulan,



        "Forecast_Bulan":

            forecast_bulan,



        "Low_Confidence":

            fallback,



        "MAE":

            round(

                float(best_metric["MAE"]),

                4

            ),



        "RMSE":

            round(

                float(best_metric["RMSE"]),

                4

            ),



        "MAPE":

            round(

                float(best_metric["MAPE"]),

                4

            )

    }













    # ======================================
    # DINAMIC OUTPUT GI / GR
    # ======================================


    if prefix == "GI":


        result.update({



            "GI_Actual":

                round(

                    actual_value,

                    2

                ),



            "Forecast_GI":

                round(

                    forecast_value,

                    2

                ),



            "Trend_GI":

                trend,



            "Trend_Bulan":

                trend_bulan,



            "Forecast_Bulan":

                forecast_bulan,



            "Best_Model_GI":

                best_model_name



        })









    elif prefix == "GR":


        result.update({



            "GR_Actual":

                round(

                    actual_value,

                    2

                ),



            "Forecast_GR":

                round(

                    forecast_value,

                    2

                ),



            "Trend_GR":

                trend,



            "Trend_Bulan":

                trend_bulan,



            "Forecast_Bulan":

                forecast_bulan,



            "Best_Model_GR":

                best_model_name



        })









    return result

    # =====================================================
# FORECASTING ORCHESTRATOR
#
# Generic GI / GR
#
# Input:
# dataframe hasil feature engineering
#
# transaction_type:
# GI
# GR
#
# Output:
# dataframe forecast
# =====================================================


def forecasting(

    df,

    transaction_type="GI"

):


    results = []



    print("\n")

    print("=" * 60)



    print(

        "START FORECASTING",

        transaction_type

    )



    print("=" * 60)









    # ======================================
    # LOOP MATERIAL
    # ======================================


    for material, material_df in df.groupby(

        "Material"

    ):





        material_df = (

            material_df

            .sort_values(

                "Bulan"

            )

            .reset_index(

                drop=True

            )

        )









        result = forecast_single_material(

            material,

            material_df,

            transaction_type

        )









        if result is not None:


            results.append(

                result

            )












    result_df = pd.DataFrame(

        results

    )









    print(

        "TOTAL FORECAST RESULT:",

        len(result_df)

    )









    print("=" * 60)



    print(

        "FORECASTING SELESAI",

        transaction_type

    )



    print("=" * 60)









    return result_df



