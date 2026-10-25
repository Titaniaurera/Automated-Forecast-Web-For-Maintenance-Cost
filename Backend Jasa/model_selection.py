import pandas as pd
import numpy as np

from sklearn.base import clone

from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    Lasso,
    ElasticNet
)

from sklearn.tree import DecisionTreeRegressor

from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    AdaBoostRegressor,
    BaggingRegressor,
    HistGradientBoostingRegressor
)

from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR


# ============================================================
# KONFIGURASI
# ============================================================

RANDOM_STATE = 42

# Batas toleransi gap train-validation
# Digunakan sebagai indikator tambahan,
# bukan sebagai satu-satunya dasar pemilihan.
MAX_MAPE_GAP = 10.0


# ============================================================
# 1. DAFTAR MODEL
# ============================================================

def get_candidate_models():
    """
    Daftar seluruh model yang akan dibandingkan.

    Decision Tree menggunakan konfigurasi
    yang sudah digunakan pada eksperimen Rutin.
    """

    models = {

        # ----------------------------------------------------
        # LINEAR MODELS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # TREE
        # ----------------------------------------------------

        "Decision Tree":
            DecisionTreeRegressor(
                max_depth=5,
                min_samples_leaf=2,
                random_state=RANDOM_STATE
            ),

        # ----------------------------------------------------
        # ENSEMBLE
        # ----------------------------------------------------

        "Random Forest":
            RandomForestRegressor(
                n_estimators=500,
                max_depth=10,
                min_samples_leaf=2,
                min_samples_split=4,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ),

        "Extra Trees":
            ExtraTreesRegressor(
                n_estimators=500,
                max_depth=10,
                min_samples_leaf=2,
                min_samples_split=4,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ),

        "Gradient Boosting":
            GradientBoostingRegressor(
                n_estimators=300,
                learning_rate=0.03,
                max_depth=3,
                random_state=RANDOM_STATE
            ),

        "AdaBoost":
            AdaBoostRegressor(
                n_estimators=300,
                learning_rate=0.03,
                random_state=RANDOM_STATE
            ),

        "Bagging":
            BaggingRegressor(
                n_estimators=300,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ),

        "HistGradientBoosting":
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.03,
                max_leaf_nodes=15,
                random_state=RANDOM_STATE
            ),

        # ----------------------------------------------------
        # OTHER
        # ----------------------------------------------------

        "KNN":
            KNeighborsRegressor(
                n_neighbors=5
            ),

        "SVR":
            SVR(
                kernel="rbf",
                C=10,
                gamma="scale",
                epsilon=0.1
            )
    }

    return models


# ============================================================
# 2. VALIDASI HASIL EVALUASI
# ============================================================

def validate_evaluation_results(
    evaluation_results: pd.DataFrame
):
    """
    Memastikan hasil evaluasi memiliki
    kolom yang dibutuhkan.
    """

    if evaluation_results is None:
        raise ValueError(
            "evaluation_results tidak boleh None."
        )

    if evaluation_results.empty:
        raise ValueError(
            "evaluation_results kosong."
        )

    required_columns = [
        "Model",
        "Train MAPE",
        "Validation MAPE",
        "Validation RMSE",
        "Validation R2"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in evaluation_results.columns
    ]

    if missing_columns:

        raise ValueError(
            "Kolom hasil evaluasi tidak lengkap: "
            + ", ".join(missing_columns)
        )


# ============================================================
# 3. HITUNG MAPE GAP
# ============================================================

def calculate_mape_gap(
    evaluation_results: pd.DataFrame
):
    """
    Menghitung selisih MAPE training dan validation.

    Gap besar dapat menjadi indikasi overfitting.
    """

    results = evaluation_results.copy()

    results["MAPE Gap"] = (
        results["Validation MAPE"]
        - results["Train MAPE"]
    )

    return results


# ============================================================
# 4. HITUNG RMSE GAP
# ============================================================

def calculate_rmse_gap(
    evaluation_results: pd.DataFrame
):
    """
    Menghitung selisih RMSE training dan validation.
    """

    results = evaluation_results.copy()

    if (
        "Train RMSE" in results.columns
        and
        "Validation RMSE" in results.columns
    ):

        results["RMSE Gap"] = (
            results["Validation RMSE"]
            - results["Train RMSE"]
        )

    else:

        results["RMSE Gap"] = np.nan

    return results


# ============================================================
# 5. STATUS OVERFITTING
# ============================================================

def determine_overfitting_status(
    mape_gap
):
    """
    Memberikan indikator sederhana:

    NORMAL
        Gap relatif kecil.

    WARNING
        Gap mulai besar.

    OVERFIT RISK
        Gap sangat besar.

    Catatan:
    status ini hanya indikator,
    bukan bukti statistik overfitting.
    """

    if pd.isna(mape_gap):

        return "UNKNOWN"

    if mape_gap <= MAX_MAPE_GAP:

        return "NORMAL"

    if mape_gap <= (
        MAX_MAPE_GAP * 2
    ):

        return "WARNING"

    return "OVERFIT RISK"


# ============================================================
# 6. TAMBAHKAN STATUS MODEL
# ============================================================

def add_model_status(
    evaluation_results: pd.DataFrame
):
    """
    Menambahkan:
    - MAPE Gap
    - RMSE Gap
    - Status
    """

    results = evaluation_results.copy()

    results = calculate_mape_gap(
        results
    )

    results = calculate_rmse_gap(
        results
    )

    results["Status"] = (
        results["MAPE Gap"]
        .apply(
            determine_overfitting_status
        )
    )

    return results


# ============================================================
# 7. RANKING MODEL
# ============================================================

def rank_models(
    evaluation_results: pd.DataFrame
):
    """
    Ranking model.

    Prioritas:

    1. Validation MAPE terkecil
    2. Validation RMSE terkecil
    3. Validation R2 terbesar
    """

    validate_evaluation_results(
        evaluation_results
    )

    results = add_model_status(
        evaluation_results
    )

    results = (
        results
        .sort_values(
            [
                "Validation MAPE",
                "Validation RMSE",
                "Validation R2"
            ],
            ascending=[
                True,
                True,
                False
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # Nomor ranking
    results["Rank"] = (
        np.arange(
            len(results)
        )
        + 1
    )

    # Susun Rank di depan
    columns = [
        "Rank"
    ] + [
        column
        for column in results.columns
        if column != "Rank"
    ]

    results = results[
        columns
    ]

    return results


# ============================================================
# 8. PILIH MODEL TERBAIK
# ============================================================

def select_best_model(
    evaluation_results: pd.DataFrame,
    allow_overfit_risk=False
):
    """
    Memilih model terbaik.

    Default:
        model dengan OVERFIT RISK tetap tidak dipilih
        jika tersedia alternatif yang valid.

    Prioritas:
        Validation MAPE
        Validation RMSE
        Validation R2
    """

    ranked = rank_models(
        evaluation_results
    )

    # --------------------------------------------------------
    # Kandidat normal / warning
    # --------------------------------------------------------

    if not allow_overfit_risk:

        valid_candidates = ranked[
            ranked["Status"]
            != "OVERFIT RISK"
        ].copy()

        # Jika semua model overfit,
        # tetap gunakan ranking asli.
        if not valid_candidates.empty:

            ranked_for_selection = (
                valid_candidates
            )

        else:

            ranked_for_selection = ranked

    else:

        ranked_for_selection = ranked

    # --------------------------------------------------------
    # Pilih baris pertama
    # --------------------------------------------------------

    best_row = (
        ranked_for_selection
        .iloc[0]
    )

    best_model_name = (
        best_row["Model"]
    )

    # --------------------------------------------------------
    # Ambil model
    # --------------------------------------------------------

    models = get_candidate_models()

    if best_model_name not in models:

        raise ValueError(
            f"Model '{best_model_name}' "
            "tidak tersedia."
        )

    best_model = clone(
        models[
            best_model_name
        ]
    )

    return (
        best_model_name,
        best_model,
        best_row,
        ranked
    )


# ============================================================
# 9. RINGKASAN MODEL TERBAIK
# ============================================================

def summarize_best_model(
    best_row
):
    """
    Membuat dictionary ringkasan
    model terbaik.
    """

    return {

        "model":
            best_row["Model"],

        "rank":
            int(best_row["Rank"]),

        "train_mape":
            float(
                best_row["Train MAPE"]
            ),

        "validation_mape":
            float(
                best_row["Validation MAPE"]
            ),

        "mape_gap":
            float(
                best_row["MAPE Gap"]
            ),

        "validation_rmse":
            float(
                best_row["Validation RMSE"]
            ),

        "validation_r2":
            float(
                best_row["Validation R2"]
            ),

        "status":
            best_row["Status"]
    }


# ============================================================
# 10. CETAK RANKING
# ============================================================

def print_model_ranking(
    ranked_results: pd.DataFrame
):
    """
    Menampilkan ranking model di terminal.
    """

    print(
        "\n"
        + "=" * 90
    )

    print(
        "RANKING MODEL FORECASTING"
    )

    print(
        "=" * 90
    )

    display_columns = [
        "Rank",
        "Model",
        "Train MAPE",
        "Validation MAPE",
        "MAPE Gap",
        "Validation RMSE",
        "Validation R2",
        "Status"
    ]

    available_columns = [
        column
        for column in display_columns
        if column in ranked_results.columns
    ]

    print(
        ranked_results[
            available_columns
        ].to_string(
            index=False
        )
    )

    print(
        "=" * 90
    )


# ============================================================
# 11. ANALISIS GENERALIZATION
# ============================================================

def analyze_generalization(
    ranked_results: pd.DataFrame
):
    """
    Menganalisis hubungan performa training
    dan validation.

    Output berupa DataFrame.
    """

    results = ranked_results.copy()

    analysis = []

    for _, row in results.iterrows():

        train_mape = row[
            "Train MAPE"
        ]

        validation_mape = row[
            "Validation MAPE"
        ]

        gap = row[
            "MAPE Gap"
        ]

        if (
            validation_mape
            < train_mape
        ):

            interpretation = (
                "Validation lebih baik "
                "daripada training"
            )

        elif gap <= MAX_MAPE_GAP:

            interpretation = (
                "Generalization cukup baik"
            )

        elif gap <= (
            MAX_MAPE_GAP * 2
        ):

            interpretation = (
                "Perlu perhatian terhadap "
                "potensi overfitting"
            )

        else:

            interpretation = (
                "Potensi overfitting tinggi"
            )

        analysis.append(
            {
                "Model":
                    row["Model"],

                "Train MAPE":
                    train_mape,

                "Validation MAPE":
                    validation_mape,

                "MAPE Gap":
                    gap,

                "Status":
                    row["Status"],

                "Interpretasi":
                    interpretation
            }
        )

    return pd.DataFrame(
        analysis
    )


# ============================================================
# 12. PIPELINE MODEL SELECTION
# ============================================================

def run_model_selection(
    evaluation_results: pd.DataFrame,
    allow_overfit_risk=False
):
    """
    Pipeline lengkap pemilihan model.

    Input:
        hasil Time Series CV
        dari forecasting.py

    Output:
        model terbaik
        ranking
        analisis generalization
    """

    print(
        "\n"
        + "=" * 90
    )

    print(
        "MODEL SELECTION"
    )

    print(
        "=" * 90
    )

    # --------------------------------------------------------
    # 1. Ranking
    # --------------------------------------------------------

    ranked_results = rank_models(
        evaluation_results
    )

    # --------------------------------------------------------
    # 2. Print ranking
    # --------------------------------------------------------

    print_model_ranking(
        ranked_results
    )

    # --------------------------------------------------------
    # 3. Pilih model
    # --------------------------------------------------------

    (
        best_model_name,
        best_model,
        best_row,
        ranked_results
    ) = select_best_model(
        evaluation_results,
        allow_overfit_risk=allow_overfit_risk
    )

    # --------------------------------------------------------
    # 4. Generalization
    # --------------------------------------------------------

    generalization = (
        analyze_generalization(
            ranked_results
        )
    )

    # --------------------------------------------------------
    # 5. Summary
    # --------------------------------------------------------

    summary = summarize_best_model(
        best_row
    )

    print(
        "\n"
        + "=" * 90
    )

    print(
        "MODEL TERPILIH"
    )

    print(
        "=" * 90
    )

    print(
        f"Model              : "
        f"{best_model_name}"
    )

    print(
        f"Train MAPE         : "
        f"{summary['train_mape']:.2f}%"
    )

    print(
        f"Validation MAPE    : "
        f"{summary['validation_mape']:.2f}%"
    )

    print(
        f"MAPE Gap           : "
        f"{summary['mape_gap']:.2f}%"
    )

    print(
        f"Validation RMSE    : "
        f"{summary['validation_rmse']:.2f}"
    )

    print(
        f"Validation R2      : "
        f"{summary['validation_r2']:.4f}"
    )

    print(
        f"Status             : "
        f"{summary['status']}"
    )

    print(
        "=" * 90
    )

    return {

        "best_model_name":
            best_model_name,

        "best_model":
            best_model,

        "best_row":
            best_row,

        "summary":
            summary,

        "ranking":
            ranked_results,

        "generalization":
            generalization
    }


# ============================================================
# 13. CEK APAKAH MODEL LAYAK
# ============================================================

def is_model_acceptable(
    best_row,
    max_validation_mape=None
):
    """
    Mengecek apakah model terbaik memenuhi
    batas performa yang ditentukan.

    max_validation_mape bersifat opsional.
    """

    if best_row is None:

        return False

    status = best_row[
        "Status"
    ]

    if status == "OVERFIT RISK":

        return False

    if max_validation_mape is not None:

        validation_mape = (
            best_row[
                "Validation MAPE"
            ]
        )

        if validation_mape > (
            max_validation_mape
        ):

            return False

    return True


# ============================================================
# 14. AMBIL PARAMETER MODEL
# ============================================================

def get_model_parameters(
    model
):
    """
    Mengambil parameter model
    untuk ditampilkan di dashboard/log.
    """

    if model is None:

        return {}

    try:

        return model.get_params()

    except Exception:

        return {}


# ============================================================
# 15. HASIL SELECTION DALAM FORMAT JSON-SAFE
# ============================================================

def selection_to_dict(
    selection_result
):
    """
    Mengubah hasil model selection menjadi
    dictionary sederhana yang aman dikirim
    melalui FastAPI.
    """

    if selection_result is None:

        return {}

    best_row = (
        selection_result
        .get("best_row")
    )

    if best_row is None:

        return {}

    return {

        "model":
            str(
                selection_result[
                    "best_model_name"
                ]
            ),

        "rank":
            int(
                best_row["Rank"]
            ),

        "train_mape":
            float(
                best_row[
                    "Train MAPE"
                ]
            ),

        "validation_mape":
            float(
                best_row[
                    "Validation MAPE"
                ]
            ),

        "mape_gap":
            float(
                best_row[
                    "MAPE Gap"
                ]
            ),

        "validation_rmse":
            float(
                best_row[
                    "Validation RMSE"
                ]
            ),

        "validation_r2":
            float(
                best_row[
                    "Validation R2"
                ]
            ),

        "status":
            str(
                best_row[
                    "Status"
                ]
            )
    }