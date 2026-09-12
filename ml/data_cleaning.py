"""
data_cleaning.py
================
Handles loading, cleaning, and preparing the Dengue dataset.

Key decisions:
  - Drop rows where 'Final Output' is missing (14 rows) — cannot impute labels.
  - KNN imputation for WBC Count (24), Platelet Count (17), PDW (19).
  - Encode Sex: Male=0, Female=1, Child=2.
  - NO scaling here — scaling happens AFTER train/test split in preprocess.py.
  - Duplicate check: 0 duplicates found in this dataset.

NOTE on dataset characteristics:
  WBC Count has a -0.917 correlation with the target — it is a near-perfect
  clinical proxy for dengue diagnosis (Dengue: 2000–4000, Non-Dengue: 3600–10900).
  This is NOT data leakage (target not used as feature), but it means any model
  trained with WBC Count will achieve artificially high accuracy. The feature
  sets in preprocess.py control which features are included.
"""

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer

DATA_PATH = "data/Dengue_diseases_dataset.csv"


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[DATA] Loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    return df


def report_summary(df: pd.DataFrame, label: str = ""):
    print(f"\n{'='*55}")
    print(f"  Dataset Summary -- {label}")
    print(f"{'='*55}")
    print(f"  Shape      : {df.shape}")
    print(f"  Duplicates : {df.duplicated().sum()}")
    print("\n  Missing values:")
    miss = df.isnull().sum()
    for col, cnt in miss[miss > 0].items():
        print(f"    {col:<22}: {cnt} ({cnt/len(df)*100:.1f}%)")
    if miss.sum() == 0:
        print("    None")
    if "Final Output" in df.columns:
        vc = df["Final Output"].value_counts(dropna=False)
        print(f"\n  Class distribution (Final Output):")
        for k, v in vc.items():
            print(f"    {k}: {v} ({v/len(df)*100:.1f}%)")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline. Returns a clean DataFrame ready for feature
    extraction and train/test splitting.

    Steps
    -----
    1. Remove duplicate rows (none expected, but good practice).
    2. Normalize 'Sex' strings (strip whitespace, title-case).
    3. Drop rows with missing 'Final Output' -- label imputation is invalid.
    4. KNN-impute missing numeric values (WBC Count, Platelet Count, PDW).
       KNN imputer uses feature-feature relationships only, so it is NOT
       a source of target leakage.
    5. Encode 'Sex' to integer: Male=0, Female=1, Child=2.
    """

    # Step 1 -- Duplicates
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f"\n[CLEAN] Step 1 -- Removed {removed} duplicate rows. Rows: {len(df)}")

    # Step 2 -- Normalize Sex
    df["Sex"] = df["Sex"].str.strip().str.title()
    print(f"[CLEAN] Step 2 -- Sex values: {df['Sex'].value_counts().to_dict()}")

    # Step 3 -- Drop missing targets
    missing_target = df["Final Output"].isna().sum()
    df = df.dropna(subset=["Final Output"])
    df["Final Output"] = df["Final Output"].astype(int)
    print(f"[CLEAN] Step 3 -- Dropped {missing_target} rows with missing target. Rows: {len(df)}")

    # Step 4 -- KNN imputation for numeric cols
    impute_cols = ["WBC Count", "Platelet Count", "PDW"]
    missing_counts = df[impute_cols].isna().sum().to_dict()
    print(f"[CLEAN] Step 4 -- KNN imputing: {missing_counts}")
    knn_imp = KNNImputer(n_neighbors=5)
    df[impute_cols] = knn_imp.fit_transform(df[impute_cols])

    # Step 5 -- Encode Sex
    sex_map = {"Male": 0, "Female": 1, "Child": 2}
    df["Sex"] = df["Sex"].map(sex_map).fillna(0).astype(int)
    print(f"[CLEAN] Step 5 -- Sex encoded: {sex_map}")

    print(f"[CLEAN] Complete -- Final shape: {df.shape}")
    return df


def get_clean_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Load, report, clean, and return the dataset."""
    df = load_data(path)
    report_summary(df, label="BEFORE CLEANING")
    df = clean_data(df)
    report_summary(df, label="AFTER CLEANING")
    return df


if __name__ == "__main__":
    df = get_clean_data()
    df.to_csv("data/cleaned_data.csv", index=False)
    print("\n[SAVED] data/cleaned_data.csv")
