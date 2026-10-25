# ============================================================
# FORECASTING.PY - JASA FORECASTING
# ============================================================

import logging

import numpy as np
import pandas as pd

from sklearn.base import clone

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from sklearn.model_selection import TimeSeriesSplit

from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    Lasso,
    ElasticNet,
)

from sklearn.tree import DecisionTreeRegressor

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    AdaBoostRegressor,
    HistGradientBoostingRegressor,
)

from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR

logger = logging.getLogger(__name__)


# ============================================================
# KONFIGURASI
# ============================================================

TARGET_COLUMN = "total_amount"
DATE_COLUMN = "period"

RANDOM_STATE = 42
N_SPLITS = 5


# ============================================================
# 1. METRIK
# ============================================================

def calculate_mape(y_true, y_pred):

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0

    if mask.sum() == 0:
        return np.nan

    return float(
        np.mean(
            np.abs(
                (y_true[mask] - y_pred[mask])
                / y_true[mask]
            )
        ) * 100
    )


def calculate_smape(y_true, y_pred):

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    denominator = (
        np.abs(y_true) +
        np.abs(y_pred)
    )

    mask = denominator != 0

    if mask.sum() == 0:
        return np.nan

    return float(
        np.mean(
            2
            * np.abs(
                y_pred[mask] -
                y_true[mask]
            )
            / denominator[mask]
        )
        * 100
    )


def calculate_metrics(y_true, y_pred):

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
        r2 = r2_score(
            y_true,
            y_pred
        )
    except Exception:
        r2 = np.nan

    mape = calculate_mape(
        y_true,
        y_pred
    )

    smape = calculate_smape(
        y_true,
        y_pred
    )

    return {
        "MAE": float(mae),

        "RMSE": float(rmse),

        "R2":
            float(r2)
            if not np.isnan(r2)
            else np.nan,

        "MAPE":
            float(mape)
            if not np.isnan(mape)
            else np.nan,

        "SMAPE":
            float(smape)
            if not np.isnan(smape)
            else np.nan,
    }


# ============================================================
# 2. MODEL CANDIDATE
# ============================================================

def get_models():

    return {

        "Linear Regression":
            LinearRegression(),

        "Ridge":
            Ridge(
                alpha=1.0
            ),

        "Lasso":
            Lasso(
                alpha=0.001,
                max_iter=10000
            ),

        "ElasticNet":
            ElasticNet(
                alpha=0.001,
                l1_ratio=0.5,
                max_iter=10000
            ),

        "Decision Tree":
            DecisionTreeRegressor(
                max_depth=5,
                min_samples_leaf=2,
                random_state=RANDOM_STATE
            ),

        "Random Forest":
            RandomForestRegressor(
                n_estimators=300,
                max_depth=10,
                min_samples_leaf=2,
                min_samples_split=4,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ),

        "Extra Trees":
            ExtraTreesRegressor(
                n_estimators=300,
                max_depth=10,
                min_samples_leaf=2,
                min_samples_split=4,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.03,
                max_depth=3,
                random_state=RANDOM_STATE
            ),

        "AdaBoost":
            AdaBoostRegressor(
                n_estimators=200,
                learning_rate=0.03,
                random_state=RANDOM_STATE
            ),

        "HistGradientBoosting":
            HistGradientBoostingRegressor(
                max_iter=200,
                learning_rate=0.03,
                max_leaf_nodes=15,
                random_state=RANDOM_STATE
            ),

        "KNN":
            KNeighborsRegressor(
                n_neighbors=3
            ),

        "SVR":
            SVR(
                kernel="rbf",
                C=10,
                gamma="scale",
                epsilon=0.1
            ),
    }


# ============================================================
# 3. VALIDASI DATA
# ============================================================

def validate_forecast_data(df):

    if df is None:
        raise ValueError(
            "DataFrame tidak boleh None."
        )

    if df.empty:
        raise ValueError(
            "Data forecasting kosong."
        )

    required_columns = [
        TARGET_COLUMN,
        DATE_COLUMN,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Kolom forecasting tidak ditemukan:\n"
            + "\n".join(
                f"- {column}"
                for column in missing
            )
        )


# ============================================================
# 4. PREPARE DATASET
# ============================================================

def prepare_dataset(df):

    validate_forecast_data(df)

    df = df.copy()

    df[DATE_COLUMN] = pd.to_datetime(
        df[DATE_COLUMN],
        errors="coerce"
    )

    df[TARGET_COLUMN] = pd.to_numeric(
        df[TARGET_COLUMN],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            DATE_COLUMN,
            TARGET_COLUMN
        ]
    ).copy()

    df[TARGET_COLUMN] = (
        df[TARGET_COLUMN]
        .clip(lower=0)
    )

    df = (
        df
        .sort_values(DATE_COLUMN)
        .reset_index(drop=True)
    )

    return df


# ============================================================
# 5. BUILD MONTHLY DATASET
# ============================================================

def build_monthly_dataset(
    engineered_df
):
    """
    Mengubah event hasil feature engineering
    menjadi dataset bulanan.

    Event:
        Document Date + PO

    Menjadi:
        1 baris = 1 bulan
    """

    data = engineered_df.copy()

    if "Document Date" not in data.columns:

        raise ValueError(
            "Kolom 'Document Date' tidak ditemukan "
            "pada hasil feature engineering."
        )

    data["Document Date"] = pd.to_datetime(
        data["Document Date"],
        errors="coerce"
    )

    data["total_amount"] = pd.to_numeric(
        data["total_amount"],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "Document Date",
            "total_amount"
        ]
    ).copy()

    data["total_amount"] = (
        data["total_amount"]
        .clip(lower=0)
    )

    # --------------------------------------------------------
    # PERIOD
    # --------------------------------------------------------

    data["period"] = (
        data["Document Date"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # --------------------------------------------------------
    # AGREGASI BULANAN
    # --------------------------------------------------------

    monthly = (
        data
        .groupby("period")
        .agg(
            total_amount=(
                "total_amount",
                "sum"
            ),

            transaction_count=(
                "total_amount",
                "count"
            ),

            mean_amount=(
                "total_amount",
                "mean"
            ),

            median_amount=(
                "total_amount",
                "median"
            ),
        )
        .reset_index()
        .sort_values("period")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # FITUR WAKTU
    # --------------------------------------------------------

    monthly["month"] = (
        monthly["period"].dt.month
    )

    monthly["quarter"] = (
        monthly["period"].dt.quarter
    )

    monthly["month_index"] = (
        monthly["period"].dt.year * 12
        + monthly["period"].dt.month
    )

    # --------------------------------------------------------
    # LAG
    # --------------------------------------------------------

    monthly["lag_1"] = (
        monthly["total_amount"]
        .shift(1)
    )

    monthly["lag_2"] = (
        monthly["total_amount"]
        .shift(2)
    )

    monthly["lag_3"] = (
        monthly["total_amount"]
        .shift(3)
    )

    # --------------------------------------------------------
    # ROLLING MEAN
    # --------------------------------------------------------

    monthly["rolling_mean_3"] = (
        monthly["total_amount"]
        .shift(1)
        .rolling(
            3,
            min_periods=1
        )
        .mean()
    )

    monthly["rolling_std_3"] = (
        monthly["total_amount"]
        .shift(1)
        .rolling(
            3,
            min_periods=2
        )
        .std()
        .fillna(0)
    )

    monthly["rolling_mean_6"] = (
        monthly["total_amount"]
        .shift(1)
        .rolling(
            6,
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # PERUBAHAN
    # --------------------------------------------------------

    monthly["amount_change_1"] = (
        monthly["total_amount"]
        .shift(1)
        -
        monthly["total_amount"]
        .shift(2)
    )

    previous = (
        monthly["total_amount"]
        .shift(2)
    )

    monthly["amount_growth_1"] = np.where(
        previous != 0,
        (
            monthly["total_amount"].shift(1)
            - previous
        ) / previous,
        0
    )

    return monthly


# ============================================================
# 6. FORECAST FEATURES
# ============================================================

def get_forecast_features(df):

    preferred_features = [

        "month",
        "quarter",
        "month_index",

        "transaction_count",

        "mean_amount",
        "median_amount",

        "lag_1",
        "lag_2",
        "lag_3",

        "rolling_mean_3",
        "rolling_std_3",
        "rolling_mean_6",

        "amount_change_1",
        "amount_growth_1",
    ]

    available_features = [
        column
        for column in preferred_features
        if column in df.columns
    ]

    if not available_features:

        raise ValueError(
            "Tidak ditemukan feature forecasting."
        )

    return available_features


# ============================================================
# 7. PREPARE FEATURES
# ============================================================

def prepare_features(
    df,
    feature_columns
):

    X = df[
        feature_columns
    ].copy()

    for column in feature_columns:

        X[column] = pd.to_numeric(
            X[column],
            errors="coerce"
        )

    X = X.replace(
        [
            np.inf,
            -np.inf
        ],
        np.nan
    )

    X = (
        X
        .bfill()
        .ffill()
    )

    for column in X.columns:

        if X[column].isna().any():

            median = (
                X[column]
                .median()
            )

            if pd.isna(median):
                median = 0

            X[column] = (
                X[column]
                .fillna(median)
            )

    return X


# ============================================================
# 8. PREPARE TARGET
# ============================================================

def prepare_target(df):

    y = pd.to_numeric(
        df[TARGET_COLUMN],
        errors="coerce"
    )

    y = (
        y
        .replace(
            [
                np.inf,
                -np.inf
            ],
            np.nan
        )
        .fillna(0)
    )

    y = np.maximum(
        y,
        0
    )

    return y


# ============================================================
# 9. TIME SERIES SPLIT
# ============================================================

def get_time_series_splits(df):

    n_samples = len(df)

    max_splits = min(
        N_SPLITS,
        n_samples - 1
    )

    if max_splits < 2:

        raise ValueError(
            "Data bulanan terlalu sedikit "
            "untuk Time Series Cross Validation."
        )

    return TimeSeriesSplit(
        n_splits=max_splits
    )


# ============================================================
# 10. EVALUASI MODEL
# ============================================================

def evaluate_models(
    df,
    feature_columns
):

    df = prepare_dataset(df)

    tscv = get_time_series_splits(df)

    models = get_models()

    results = []
    fold_details = []

    for model_name, model_template in models.items():


        logger.info(
            f"Evaluasi model: {model_name}"
        )


        model_results = []

        for fold_number, (
            train_index,
            validation_index
        ) in enumerate(
            tscv.split(df),
            start=1
        ):

            train_df = (
                df
                .iloc[train_index]
                .copy()
            )

            validation_df = (
                df
                .iloc[validation_index]
                .copy()
            )

            try:

                X_train = prepare_features(
                    train_df,
                    feature_columns
                )

                X_validation = prepare_features(
                    validation_df,
                    feature_columns
                )

                y_train = prepare_target(
                    train_df
                )

                y_validation = prepare_target(
                    validation_df
                )

                model = clone(
                    model_template
                )

                model.fit(
                    X_train,
                    y_train
                )

                # ------------------------------------------------
                # TRAIN
                # ------------------------------------------------

                train_prediction = (
                    model.predict(
                        X_train
                    )
                )

                train_prediction = np.maximum(
                    train_prediction,
                    0
                )

                train_metrics = calculate_metrics(
                    y_train,
                    train_prediction
                )

                # ------------------------------------------------
                # VALIDATION
                # ------------------------------------------------

                validation_prediction = (
                    model.predict(
                        X_validation
                    )
                )

                validation_prediction = np.maximum(
                    validation_prediction,
                    0
                )

                validation_metrics = calculate_metrics(
                    y_validation,
                    validation_prediction
                )

                fold_result = {

                    "Model":
                        model_name,

                    "Fold":
                        fold_number,

                    "Train_MAE":
                        train_metrics["MAE"],

                    "Train_RMSE":
                        train_metrics["RMSE"],

                    "Train_MAPE":
                        train_metrics["MAPE"],

                    "Train_SMAPE":
                        train_metrics["SMAPE"],

                    "Train_R2":
                        train_metrics["R2"],

                    "Validation_MAE":
                        validation_metrics["MAE"],

                    "Validation_RMSE":
                        validation_metrics["RMSE"],

                    "Validation_MAPE":
                        validation_metrics["MAPE"],

                    "Validation_SMAPE":
                        validation_metrics["SMAPE"],

                    "Validation_R2":
                        validation_metrics["R2"],
                }

                model_results.append(
                    fold_result
                )

                fold_details.append(
                    fold_result
                )

                logger.debug(
                    f"Fold {fold_number} | "
                    f"Val MAPE: "
                    f"{validation_metrics['MAPE']:.2f}%"
                )

            except Exception as error:

                logger.warning(
                    f"Fold {fold_number} gagal: "
                    f"{error}"
                )

        if not model_results:
            continue

        model_df = pd.DataFrame(
            model_results
        )

        results.append({

            "Model":
                model_name,

            "Train MAPE":
                model_df[
                    "Train_MAPE"
                ].mean(),

            "Validation MAPE":
                model_df[
                    "Validation_MAPE"
                ].mean(),

            "Train RMSE":
                model_df[
                    "Train_RMSE"
                ].mean(),

            "Validation RMSE":
                model_df[
                    "Validation_RMSE"
                ].mean(),

            "Train MAE":
                model_df[
                    "Train_MAE"
                ].mean(),

            "Validation MAE":
                model_df[
                    "Validation_MAE"
                ].mean(),

            "Train R2":
                model_df[
                    "Train_R2"
                ].mean(),

            "Validation R2":
                model_df[
                    "Validation_R2"
                ].mean(),

            "Validation SMAPE":
                model_df[
                    "Validation_SMAPE"
                ].mean(),

            "Jumlah Fold":
                len(model_df),
        })

    if not results:

        raise ValueError(
            "Tidak ada model yang berhasil dievaluasi."
        )

    results_df = pd.DataFrame(
        results
    )

    results_df["MAPE Gap"] = (
        results_df["Validation MAPE"]
        -
        results_df["Train MAPE"]
    )

    results_df["RMSE Gap"] = (
        results_df["Validation RMSE"]
        -
        results_df["Train RMSE"]
    )

    results_df = (
        results_df
        .sort_values(
            [
                "Validation MAPE",
                "Validation RMSE",
                "Validation R2",
            ],
            ascending=[
                True,
                True,
                False,
            ]
        )
        .reset_index(drop=True)
    )

    return (
        results_df,
        pd.DataFrame(
            fold_details
        )
    )


# ============================================================
# 11. PILIH MODEL TERBAIK
# ============================================================

def select_best_model(
    evaluation_results
):

    if evaluation_results.empty:

        raise ValueError(
            "Hasil evaluasi model kosong."
        )

    best_row = (
        evaluation_results
        .sort_values(
            [
                "Validation MAPE",
                "Validation RMSE",
                "Validation R2",
            ],
            ascending=[
                True,
                True,
                False,
            ]
        )
        .iloc[0]
    )

    best_model_name = (
        best_row["Model"]
    )

    models = get_models()

    best_model = clone(
        models[
            best_model_name
        ]
    )

    return (
        best_model_name,
        best_model,
        best_row
    )


# ============================================================
# 12. TRAIN FINAL MODEL
# ============================================================

def train_final_model(
    df,
    feature_columns,
    model
):

    df = prepare_dataset(
        df
    )

    X = prepare_features(
        df,
        feature_columns
    )

    y = prepare_target(
        df
    )

    final_model = clone(
        model
    )

    final_model.fit(
        X,
        y
    )

    final_model._forecast_features = (
        feature_columns.copy()
    )

    return final_model


# ============================================================
# 13. CREATE FUTURE ROW
# ============================================================

def create_future_row(
    df,
    forecast_period
):

    df = prepare_dataset(
        df
    )

    forecast_period = pd.Timestamp(
        forecast_period
    )

    amounts = (
        df["total_amount"]
        .astype(float)
        .tolist()
    )

    future = {

        "period":
            forecast_period,

        "month":
            forecast_period.month,

        "quarter":
            forecast_period.quarter,

        "month_index":
            forecast_period.year * 12
            + forecast_period.month,
    }

    # --------------------------------------------------------
    # LAG
    # --------------------------------------------------------

    future["lag_1"] = (
        amounts[-1]
        if len(amounts) >= 1
        else 0
    )

    future["lag_2"] = (
        amounts[-2]
        if len(amounts) >= 2
        else future["lag_1"]
    )

    future["lag_3"] = (
        amounts[-3]
        if len(amounts) >= 3
        else future["lag_2"]
    )

    # --------------------------------------------------------
    # TRANSACTION COUNT
    # --------------------------------------------------------

    future["transaction_count"] = (
        df["transaction_count"]
        .tail(3)
        .mean()
        if "transaction_count" in df.columns
        else 0
    )

    # --------------------------------------------------------
    # MEAN
    # --------------------------------------------------------

    future["mean_amount"] = (
        df["mean_amount"]
        .tail(3)
        .mean()
        if "mean_amount" in df.columns
        else 0
    )

    # --------------------------------------------------------
    # MEDIAN
    # --------------------------------------------------------

    future["median_amount"] = (
        df["median_amount"]
        .tail(3)
        .median()
        if "median_amount" in df.columns
        else 0
    )

    # --------------------------------------------------------
    # ROLLING MEAN
    # --------------------------------------------------------

    future["rolling_mean_3"] = (
        df["total_amount"]
        .tail(3)
        .mean()
    )

    future["rolling_std_3"] = (
        df["total_amount"]
        .tail(3)
        .std()
    )

    if pd.isna(
        future["rolling_std_3"]
    ):
        future["rolling_std_3"] = 0

    future["rolling_mean_6"] = (
        df["total_amount"]
        .tail(6)
        .mean()
    )

    # --------------------------------------------------------
    # CHANGE
    # --------------------------------------------------------

    if len(amounts) >= 2:

        future["amount_change_1"] = (
            amounts[-1]
            -
            amounts[-2]
        )

        if amounts[-2] != 0:

            future["amount_growth_1"] = (
                (
                    amounts[-1]
                    -
                    amounts[-2]
                )
                /
                amounts[-2]
            )

        else:

            future["amount_growth_1"] = 0

    else:

        future["amount_change_1"] = 0
        future["amount_growth_1"] = 0

    return pd.DataFrame(
        [future]
    )


# ============================================================
# 14. FORECAST NEXT MONTH
# ============================================================

def forecast_next_month(
    model,
    df,
    feature_columns,
    forecast_period
):

    future_df = create_future_row(
        df,
        forecast_period
    )

    X_future = prepare_features(
        future_df,
        feature_columns
    )

    prediction = model.predict(
        X_future
    )

    prediction = np.asarray(
        prediction,
        dtype=float
    )

    prediction = np.maximum(
        prediction,
        0
    )

    return (
        float(prediction[0]),
        future_df
    )


# ============================================================
# 15. HISTORICAL SERIES
# ============================================================

def build_historical_series(
    df
):

    df = prepare_dataset(
        df
    )

    series = []

    for _, row in df.iterrows():

        period = row[
            DATE_COLUMN
        ]

        amount = row[
            TARGET_COLUMN
        ]

        series.append({

            "period":
                period.strftime(
                    "%Y-%m"
                ),

            "actual":
                float(amount),

            "forecast":
                None,
        })

    return series


# ============================================================
# 16. FORECAST SERIES
# ============================================================

def build_forecast_series(
    df,
    forecast_period,
    forecast_value
):

    series = build_historical_series(
        df
    )

    series.append({

        "period":
            pd.Timestamp(
                forecast_period
            ).strftime(
                "%Y-%m"
            ),

        "actual":
            None,

        "forecast":
            float(
                forecast_value
            ),
    })

    return series


# ============================================================
# 17. CONTRIBUTOR
# ============================================================

def build_contributors(
    raw_df,
    forecast_value
):

    if raw_df is None:
        return []

    if raw_df.empty:
        return []

    required_columns = [
        "Short Text",
        "Amount in doc. curr.",
        "Posting Date",
    ]

    if not all(
        column in raw_df.columns
        for column in required_columns
    ):
        return []

    data = raw_df.copy()

    data[
        "Amount in doc. curr."
    ] = pd.to_numeric(
        data[
            "Amount in doc. curr."
        ],
        errors="coerce"
    )

    data[
        "Posting Date"
    ] = pd.to_datetime(
        data[
            "Posting Date"
        ],
        errors="coerce"
    )

    data = data.dropna(
        subset=[
            "Posting Date"
        ]
    )

    if data.empty:
        return []

    latest_period = (
        data[
            "Posting Date"
        ]
        .dt.to_period("M")
        .max()
    )

    latest_data = data[
        data[
            "Posting Date"
        ]
        .dt.to_period("M")
        == latest_period
    ]

    contributors = (
        latest_data
        .groupby(
            "Short Text"
        )[
            "Amount in doc. curr."
        ]
        .sum()
        .abs()
        .sort_values(
            ascending=False
        )
        .head(10)
    )

    total = contributors.sum()

    result = []

    for service, amount in contributors.items():

        percentage = (
            (
                abs(amount)
                / total
            )
            * 100
            if total != 0
            else 0
        )

        result.append({

            "short_text":
                str(service),

            "amount":
                float(abs(amount)),

            "percentage":
                float(percentage),
        })

    return result


# ============================================================
# 18. FEATURE IMPORTANCE
# ============================================================

def get_feature_importance(
    model,
    feature_columns
):

    if not hasattr(
        model,
        "feature_importances_"
    ):
        return []

    importance = pd.DataFrame({

        "feature":
            feature_columns,

        "importance":
            model.feature_importances_,
    })

    importance = (
        importance
        .sort_values(
            "importance",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    return [

        {
            "feature":
                str(
                    row["feature"]
                ),

            "importance":
                float(
                    row["importance"]
                ),
        }

        for _, row
        in importance.iterrows()
    ]


# ============================================================
# 19. MAIN RUN FORECAST
# ============================================================

def run_forecast(
    df,
    classification=None
):
    """
    ENTRY POINT UNTUK app.py.

    Pipeline:

        MySQL
          ↓
        preprocessing
          ↓
        feature engineering
          ↓
        monthly aggregation
          ↓
        Time Series CV
          ↓
        model terbaik
          ↓
        final training
          ↓
        forecast bulan berikutnya
    """


    logger.info(
        "JASA FORECASTING"
    )


    # ========================================================
    # IMPORT FEATURE ENGINEERING
    # ========================================================

    try:

        from feature_engineering import (
            build_features
        )

    except ImportError as error:

        raise ImportError(
            "feature_engineering.py "
            "tidak dapat diimport: "
            f"{error}"
        )

    # ========================================================
    # RAW DATA
    # ========================================================

    if df is None:

        raise ValueError(
            "Data input kosong."
        )

    if df.empty:

        raise ValueError(
            "Data input kosong."
        )

    df = df.copy()

    # ========================================================
    # PASTIKAN DOCUMENT DATE ADA
    # ========================================================

    if (
        "Document Date" not in df.columns
        and
        "Posting Date" in df.columns
    ):

        df["Document Date"] = (
            df["Posting Date"]
        )

    # ========================================================
    # FILTER CLASSIFICATION
    # ========================================================

    if (
        classification is not None
        and
        "Klasifikasi" in df.columns
    ):

        df["Klasifikasi"] = (
            df["Klasifikasi"]
            .astype(str)
            .str.strip()
        )

        df = df[
            df["Klasifikasi"]
            .str.lower()
            ==
            str(classification)
            .strip()
            .lower()
        ].copy()

    if df.empty:

        raise ValueError(
            f"Tidak ada data untuk klasifikasi "
            f"{classification}."
        )

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    logger.info(
        "[1] Feature engineering..."
    )

    feature_result = build_features(
        df
    )

    # --------------------------------------------------------
    # PENTING:
    # build_features() mengembalikan:
    #
    #     data_features,
    #     feature_columns
    #
    # BUKAN hanya DataFrame.
    # --------------------------------------------------------

    if isinstance(
        feature_result,
        tuple
    ):

        engineered_df = (
            feature_result[0]
        )

        engineered_features = (
            feature_result[1]
        )

    else:

        # backward compatibility
        engineered_df = (
            feature_result
        )

        engineered_features = []

    if engineered_df is None:

        raise ValueError(
            "Feature engineering menghasilkan None."
        )

    if not isinstance(
        engineered_df,
        pd.DataFrame
    ):

        raise ValueError(
            "Hasil feature engineering "
            "bukan DataFrame."
        )

    if engineered_df.empty:

        raise ValueError(
            "Hasil feature engineering kosong."
        )

    logger.info(
        "Jumlah event: %s",
        len(engineered_df)
    )

    logger.info(
        "Jumlah feature engineering: %s",
        len(engineered_features)
    )

    # ========================================================
    # MONTHLY DATASET
    # ========================================================

    logger.info(
        "[2] Membentuk dataset bulanan..."
    )

    monthly = build_monthly_dataset(
        engineered_df
    )

    if monthly.empty:

        raise ValueError(
            "Dataset bulanan kosong."
        )

    logger.info(
        "Jumlah bulan historis: %s",
        len(monthly)
    )

    if len(monthly) < 4:

        raise ValueError(
            "Data historis bulanan terlalu sedikit "
            "untuk forecasting."
        )

    # ========================================================
    # FORECAST FEATURES
    # ========================================================

    feature_columns = (
        get_forecast_features(
            monthly
        )
    )

    logger.info(
        "Feature forecasting:"
    )

    for feature in feature_columns:

        logger.info(
            f"- {feature}"
        )

    # ========================================================
    # EVALUASI
    # ========================================================

    logger.info(
        "[3] Evaluasi model..."
    )

    (
        evaluation_results,
        fold_details
    ) = evaluate_models(
        monthly,
        feature_columns
    )

    # ========================================================
    # BEST MODEL
    # ========================================================

    (
        best_model_name,
        best_model,
        best_row
    ) = select_best_model(
        evaluation_results
    )


    logger.info(
        "MODEL TERBAIK"
    )


    logger.info(
        f"Model           : "
        f"{best_model_name}"
    )

    logger.info(
        f"Validation MAPE : "
        f"{best_row['Validation MAPE']:.2f}%"
    )

    logger.info(
        f"Validation RMSE : "
        f"{best_row['Validation RMSE']:.2f}"
    )

    logger.info(
        f"Validation R2   : "
        f"{best_row['Validation R2']:.4f}"
    )

    # ========================================================
    # FINAL TRAINING
    # ========================================================

    logger.info(
        "[4] Training final model..."
    )

    final_model = train_final_model(
        monthly,
        feature_columns,
        best_model
    )

    # ========================================================
    # FORECAST PERIOD
    # ========================================================

    last_period = (
        monthly[
            DATE_COLUMN
        ]
        .max()
    )

    forecast_period = (
        last_period
        +
        pd.DateOffset(
            months=1
        )
    )

    # ========================================================
    # FORECAST
    # ========================================================

    logger.info(
        "[5] Forecast bulan berikutnya..."
    )

    (
        forecast_value,
        future_df
    ) = forecast_next_month(
        final_model,
        monthly,
        feature_columns,
        forecast_period
    )

    logger.info(
        f"Forecast: Rp {forecast_value:,.0f}"
    )

    # ========================================================
    # HISTORICAL
    # ========================================================

    historical = (
        build_historical_series(
            monthly
        )
    )

    # ========================================================
    # SERIES
    # ========================================================

    series = (
        build_forecast_series(
            monthly,
            forecast_period,
            forecast_value
        )
    )

    # ========================================================
    # CONTRIBUTOR
    # ========================================================

    contributors = (
        build_contributors(
            df,
            forecast_value
        )
    )

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    feature_importance = (
        get_feature_importance(
            final_model,
            feature_columns
        )
    )

    # ========================================================
    # LABEL
    # ========================================================

    forecast_month_label = (
        forecast_period.strftime(
            "%B %Y"
        )
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "status":
            "success",

        "classification":
            classification,

        "forecast":
            float(
                forecast_value
            ),

        "forecast_month":
            forecast_period.strftime(
                "%Y-%m"
            ),

        "forecast_month_label":
            forecast_month_label,

        "model":
            best_model_name,

        "metrics": {

            "Train_MAPE":
                float(
                    best_row[
                        "Train MAPE"
                    ]
                ),

            "Validation_MAPE":
                float(
                    best_row[
                        "Validation MAPE"
                    ]
                ),

            "MAPE_Gap":
                float(
                    best_row[
                        "MAPE Gap"
                    ]
                ),

            "Validation_RMSE":
                float(
                    best_row[
                        "Validation RMSE"
                    ]
                ),

            "Validation_MAE":
                float(
                    best_row[
                        "Validation MAE"
                    ]
                ),

            "Validation_R2":
                float(
                    best_row[
                        "Validation R2"
                    ]
                ),

            "Validation_SMAPE":
                float(
                    best_row[
                        "Validation SMAPE"
                    ]
                ),
        },

        "historical":
            historical,

        "series":
            series,

        "contributors":
            contributors,

        "feature_importance":
            feature_importance,

        "ranking":
            evaluation_results.to_dict(
                orient="records"
            ),

        "fold_details":
            fold_details.to_dict(
                orient="records"
            ),

        "future_features":
            future_df.to_dict(
                orient="records"
            ),

        "data_info": {

            "historical_months":
                int(
                    len(monthly)
                ),

            "last_historical_month":
                last_period.strftime(
                    "%Y-%m"
                ),

            "forecast_month":
                forecast_period.strftime(
                    "%Y-%m"
                ),
        },
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def run_forecasting(
    df,
    feature_columns=None,
    future_df=None
):

    return run_forecast(
        df
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    logger.info("forecasting.py siap digunakan. Entry point: run_forecast(df)")