"""
Model evaluation utilities: regression metrics (RMSE, MAE, R2) and diagnostic reporting.
"""
from typing import Dict, Any, Union
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def compute_regression_metrics(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list]
) -> Dict[str, float]:
    """
    Computes standard regression evaluation metrics for emissions prediction:
    - MAE: Mean Absolute Error (g CO2 / km)
    - RMSE: Root Mean Squared Error (g CO2 / km)
    - R2: Coefficient of Determination
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    mse = float(mean_squared_error(y_t, y_p))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_t, y_p))
    r2 = float(r2_score(y_t, y_p))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mse": round(mse, 4),
        "r2_score": round(r2, 4),
    }


def evaluate_model_pipeline(
    pipeline,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    split_name: str = "validation"
) -> Dict[str, Any]:
    """
    Predicts using a fitted pipeline and returns evaluation metrics with metadata.
    """
    predictions = pipeline.predict(X_val)
    metrics = compute_regression_metrics(y_val, predictions)
    return {
        "split": split_name,
        "sample_count": len(y_val),
        "metrics": metrics,
    }
