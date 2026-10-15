"""
Scikit-learn pipeline builder for eco-friendly vehicle emissions regression models.
Encapsulates numerical scaling/imputation and categorical one-hot encoding
to prevent data leakage and ensure robust production inference.
"""
from typing import List, Optional
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

# Standard feature definitions matching validated Natural Resources Canada dataset
NUMERIC_FEATURES = [
    "Engine Size(L)",
    "Cylinders",
    "Fuel Consumption Comb (L/100 km)"
]

CATEGORICAL_FEATURES = [
    "Make",
    "Vehicle Class",
    "Transmission",
    "Fuel Type"
]


def build_emissions_preprocessor(
    numeric_features: Optional[List[str]] = None,
    categorical_features: Optional[List[str]] = None,
) -> ColumnTransformer:
    """
    Constructs the ColumnTransformer for vehicle emission predictors:
    - Numeric: median imputation + standard scaling
    - Categorical: most-frequent imputation + one-hot encoding with unknown handling
    """
    num_cols = numeric_features if numeric_features is not None else NUMERIC_FEATURES
    cat_cols = categorical_features if categorical_features is not None else CATEGORICAL_FEATURES

    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer([
        ("num", num_transformer, num_cols),
        ("cat", cat_transformer, cat_cols),
    ])


def build_emissions_pipeline(
    model=None,
    numeric_features: Optional[List[str]] = None,
    categorical_features: Optional[List[str]] = None,
) -> Pipeline:
    """
    Builds an end-to-end Scikit-learn Pipeline with preprocessing and estimator.
    """
    preprocessor = build_emissions_preprocessor(
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )
    steps = [("preprocessor", preprocessor)]
    if model is not None:
        steps.append(("regressor", model))
    return Pipeline(steps=steps)


# Backwards compatibility alias
def build_eco_pipeline(model=None) -> Pipeline:
    return build_emissions_pipeline(model=model)
