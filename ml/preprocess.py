"""
preprocess.py
=============
Feature engineering, scaling pipeline, and train/test split.

FEATURE SETS (three experiments, selectable via EXPERIMENT env var):
  A  -- All 8 features (includes WBC Count -- gives ~100% acc due to dominance)
  B  -- Without WBC Count (partial fix, Platelet Count still dominant)
  C  -- Clinical Safe: Age, Sex, Haemoglobin, Platelet Count, PDW (DEFAULT)

  Set EXPERIMENT=A/B/C before running train_model.py, or leave default (C).

CRITICAL ANTI-LEAKAGE RULES ENFORCED HERE:
  1. train_test_split is called BEFORE StandardScaler.fit_transform.
  2. scaler.fit_transform is called ONLY on X_train.
  3. scaler.transform  is called ONLY on X_test (never fit on test set).
  4. Stratified split (stratify=y) preserves class ratio in both sets.
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from data_cleaning import get_clean_data

os.makedirs("models", exist_ok=True)

TARGET_COL = "Final Output"

# ── Feature sets ──────────────────────────────────────────────────────────────
FEATURE_SETS = {
    "A": ["Age", "Sex", "Haemoglobin", "WBC Count",
          "Differential Count", "RBC PANEL", "Platelet Count", "PDW"],
    "B": ["Age", "Sex", "Haemoglobin",
          "Differential Count", "RBC PANEL", "Platelet Count", "PDW"],
    "C": ["Age", "Sex", "Haemoglobin", "Platelet Count", "PDW"],
}

# Default experiment: C (Clinical Safe features — most honest evaluation)
EXPERIMENT = os.environ.get("EXPERIMENT", "C").upper()
if EXPERIMENT not in FEATURE_SETS:
    print(f"[WARN] Unknown EXPERIMENT={EXPERIMENT}, defaulting to C")
    EXPERIMENT = "C"

FEATURE_COLS = FEATURE_SETS[EXPERIMENT]
print(f"[PREPROCESS] Experiment {EXPERIMENT} -- Features ({len(FEATURE_COLS)}): {FEATURE_COLS}")

# Numeric columns to scale (all except the already-integer Sex)
_NUMERIC_COLS = [c for c in FEATURE_COLS if c != "Sex"]


def get_features_target(df: pd.DataFrame):
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()
    return X, y


def preprocess_and_split(df: pd.DataFrame,
                          test_size: float = 0.2,
                          random_state: int = 42):
    """
    Split data and scale features.

    Returns
    -------
    X_train, X_test, y_train, y_test, scaler
    """
    X, y = get_features_target(df)

    # ── Stratified 80/20 split BEFORE any scaling ────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y          # preserves class imbalance ratio
    )

    # ── Scale: fit on train ONLY, transform both ─────────────────────────────
    scaler = StandardScaler()
    X_train = X_train.copy()
    X_test  = X_test.copy()
    X_train[_NUMERIC_COLS] = scaler.fit_transform(X_train[_NUMERIC_COLS])
    X_test[_NUMERIC_COLS]  = scaler.transform(X_test[_NUMERIC_COLS])   # no fit!

    # Save scaler for inference
    joblib.dump(scaler, "models/scaler.pkl")

    print(f"[PREPROCESS] Train: {X_train.shape}  Test: {X_test.shape}")
    print(f"[PREPROCESS] Class balance (train): {dict(y_train.value_counts().sort_index())}")
    print(f"[PREPROCESS] Class balance (test) : {dict(y_test.value_counts().sort_index())}")
    print(f"[PREPROCESS] Scaler saved to models/scaler.pkl")

    return X_train, X_test, y_train, y_test, scaler


def preprocess_input(input_dict: dict, scaler=None) -> pd.DataFrame:
    """
    Preprocess a single prediction input dictionary for inference.
    Used by the backend API at prediction time.

    Parameters
    ----------
    input_dict : dict  -- keys: age, sex, haemoglobin, wbc_count,
                          differential_count, rbc_panel, platelet_count, pdw
    scaler     : fitted StandardScaler or None

    Returns
    -------
    pd.DataFrame with exactly the columns the model was trained on.
    """
    sex_map = {"male": 0, "female": 1, "child": 2}
    sex_val = sex_map.get(str(input_dict.get("sex", "male")).lower(), 0)

    # Build a row with ALL possible columns, then select FEATURE_COLS
    full_row = {
        "Age":                float(input_dict.get("age",                0)),
        "Sex":                sex_val,
        "Haemoglobin":        float(input_dict.get("haemoglobin",        0)),
        "WBC Count":          float(input_dict.get("wbc_count",          0)),
        "Differential Count": float(input_dict.get("differential_count", 1)),
        "RBC PANEL":          float(input_dict.get("rbc_panel",          1)),
        "Platelet Count":     float(input_dict.get("platelet_count",     0)),
        "PDW":                float(input_dict.get("pdw",                0)),
    }

    df_in = pd.DataFrame([full_row])[FEATURE_COLS]

    if scaler is not None:
        num_cols = [c for c in FEATURE_COLS if c != "Sex"]
        df_in[num_cols] = scaler.transform(df_in[num_cols])

    return df_in


if __name__ == "__main__":
    df = get_clean_data()
    X_train, X_test, y_train, y_test, scaler = preprocess_and_split(df)
    print("\n[DONE] Preprocessing complete.")
