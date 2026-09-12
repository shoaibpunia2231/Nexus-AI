"""
train_model.py
==============
Trains multiple ML models, evaluates them, selects the best, saves model.pkl.

Usage
-----
  python train_model.py             # uses default Experiment C (Clinical Safe)
  EXPERIMENT=A python train_model.py  # all 8 features (shows ~100% issue)
  EXPERIMENT=B python train_model.py  # without WBC Count
  EXPERIMENT=C python train_model.py  # clinical safe features (RECOMMENDED)

Models trained
--------------
  - Logistic Regression  (L2 regularization, C=0.1, class_weight=balanced)
  - Random Forest        (max_depth=4, min_samples_leaf=10, balanced weights)
  - Gradient Boosting    (max_depth=3, lr=0.05, subsample=0.8)

Anti-overfitting measures
--------------------------
  - All models have regularization / depth limits
  - 5-fold Stratified Cross-Validation on train set only
  - Training accuracy vs test accuracy compared and logged
  - Log-loss computed for both train and test sets
  - Feature selection: configurable via EXPERIMENT env var

Metrics reported
----------------
  Accuracy, Precision, Recall, F1, ROC-AUC,
  Train Acc, Test Acc, Train Loss, Test Loss,
  CV mean accuracy, CV std, Confusion Matrix
"""

import os, json, warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, log_loss
)

from data_cleaning import get_clean_data
from preprocess import preprocess_and_split, FEATURE_COLS, EXPERIMENT

warnings.filterwarnings("ignore")
os.makedirs("models",  exist_ok=True)
os.makedirs("outputs", exist_ok=True)


# ── Model definitions (regularized & limited complexity) ─────────────────────
def get_models() -> dict:
    return {
        "Logistic Regression": LogisticRegression(
            C=0.1,                    # L2 regularization strength
            penalty="l2",
            solver="lbfgs",
            max_iter=2000,
            random_state=42,
            class_weight="balanced"  # handles class imbalance (2:1 ratio)
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=50,
            max_depth=4,              # limit depth to reduce overfitting
            min_samples_leaf=10,      # each leaf needs at least 10 samples
            random_state=42,
            class_weight="balanced",
            n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=80,
            max_depth=3,              # shallow trees
            learning_rate=0.05,       # slow learning rate
            min_samples_leaf=10,
            subsample=0.8,            # stochastic GB reduces overfitting
            random_state=42
        ),
    }


# ── Full evaluation function ──────────────────────────────────────────────────
def evaluate_model(model, X_train, X_test, y_train, y_test, skf) -> dict:
    """Compute all metrics including train/test gap and cross-validation."""
    y_pred       = model.predict(X_test)
    y_prob       = model.predict_proba(X_test)[:, 1]
    y_train_pred = model.predict(X_train)
    y_train_prob = model.predict_proba(X_train)[:, 1]

    train_acc  = accuracy_score(y_train, y_train_pred)
    test_acc   = accuracy_score(y_test,  y_pred)
    train_loss = log_loss(y_train, y_train_prob)
    test_loss  = log_loss(y_test,  y_prob)

    # CV on training set only (no data leakage)
    cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring="accuracy")

    cm = confusion_matrix(y_test, y_pred)

    return {
        "train_acc":   round(train_acc,  4),
        "test_acc":    round(test_acc,   4),
        "train_loss":  round(train_loss, 4),
        "test_loss":   round(test_loss,  4),
        "overfit_gap": round(train_acc - test_acc, 4),
        "precision":   round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":      round(recall_score(y_test,    y_pred),                  4),
        "f1":          round(f1_score(y_test,        y_pred),                  4),
        "roc_auc":     round(roc_auc_score(y_test,   y_prob),                  4),
        "cv_mean":     round(cv_scores.mean(), 4),
        "cv_std":      round(cv_scores.std(),  4),
        "confusion_matrix": cm.tolist(),
    }


# ── Feature importance plot ───────────────────────────────────────────────────
def plot_feature_importance(model, feature_names: list, model_name: str):
    if not hasattr(model, "feature_importances_"):
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)
    sorted_feats = [feature_names[i] for i in indices]
    sorted_vals  = [importances[i]   for i in indices]

    # Color top feature red as a warning if it dominates
    max_imp = max(sorted_vals)
    colors = ["#ef4444" if v == max_imp and v > 0.4 else "#3b82f6"
              for v in sorted_vals]

    plt.figure(figsize=(9, 5))
    plt.barh(sorted_feats, sorted_vals, color=colors, edgecolor="white")
    plt.xlabel("Importance Score")
    plt.title(f"Feature Importance -- {model_name} (Experiment {EXPERIMENT})", fontsize=12)
    plt.tight_layout()
    plt.savefig("outputs/feature_importance.png", dpi=130)
    plt.close()
    print("[TRAIN] Feature importance chart saved to outputs/feature_importance.png")

    fi_dict = {feature_names[i]: round(float(importances[i]), 4)
               for i in range(len(feature_names))}
    with open("models/feature_importance.json", "w") as f:
        json.dump(fi_dict, f, indent=2)


# ── Main training pipeline ───────────────────────────────────────────────────
def train():
    print("\n" + "=" * 65)
    print(f"  DENGUE RISK PREDICTION -- MODEL TRAINING  (Experiment {EXPERIMENT})")
    print("=" * 65)

    df = get_clean_data()
    X_train, X_test, y_train, y_test, scaler = preprocess_and_split(df)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    models = get_models()
    results = {}

    print(f"\n[TRAIN] Training {len(models)} models with regularization...\n")
    for name, model in models.items():
        print(f"  Training: {name}")
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_train, X_test, y_train, y_test, skf)
        results[name] = {"model": model, "metrics": metrics}

        gap_warn = " <-- OVERFITTING" if metrics["overfit_gap"] > 0.05 else ""
        print(f"    Train Acc: {metrics['train_acc']*100:.1f}%  "
              f"Test Acc: {metrics['test_acc']*100:.1f}%  "
              f"Gap: {metrics['overfit_gap']*100:.1f}%{gap_warn}")
        print(f"    Train Loss: {metrics['train_loss']:.4f}  "
              f"Test Loss: {metrics['test_loss']:.4f}")
        print(f"    F1: {metrics['f1']:.4f}  "
              f"ROC-AUC: {metrics['roc_auc']:.4f}  "
              f"CV: {metrics['cv_mean']*100:.1f}% +/- {metrics['cv_std']*100:.1f}%\n")

    # Select best model by F1 (more robust than accuracy for imbalanced data)
    best_name = max(results, key=lambda k: results[k]["metrics"]["f1"])
    best_model   = results[best_name]["model"]
    best_metrics = results[best_name]["metrics"]

    print(f"[BEST] Best model by F1: {best_name}")
    print(f"       F1={best_metrics['f1']}  "
          f"ROC-AUC={best_metrics['roc_auc']}  "
          f"Test Acc={best_metrics['test_acc']}")

    # Save model
    joblib.dump(best_model, "models/model.pkl")
    print("[SAVED] models/model.pkl")

    # Save training report
    report = {
        "experiment":   EXPERIMENT,
        "feature_cols": FEATURE_COLS,
        "best_model":   best_name,
        "best_metrics": best_metrics,
        "all_models":   {k: v["metrics"] for k, v in results.items()},
        "dataset": {
            "total":          len(df),
            "train":          len(X_train),
            "test":           len(X_test),
            "features":       len(FEATURE_COLS),
            "dengue_positive": int((y_test == 1).sum() + (y_train == 1).sum()),
            "dengue_negative": int((y_test == 0).sum() + (y_train == 0).sum()),
        },
        "cv": {
            "folds":    5,
            "mean_f1":  best_metrics["cv_mean"],
            "std_f1":   best_metrics["cv_std"],
        },
        "overfitting_note": (
            "OVERFITTING DETECTED" if best_metrics["overfit_gap"] > 0.05
            else "No significant overfitting (train-test gap < 5%)"
        ),
    }
    with open("models/training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("[SAVED] models/training_report.json")

    # Feature importance chart
    plot_feature_importance(best_model, FEATURE_COLS, best_name)

    # Summary table
    print("\n" + "-" * 90)
    print(f"{'Model':<22} {'Train%':>8} {'Test%':>7} {'Gap':>6} {'Precision':>10} "
          f"{'Recall':>8} {'F1':>8} {'ROC-AUC':>9} {'CV%':>8}")
    print("-" * 90)
    for name, data in results.items():
        m = data["metrics"]
        marker = " <- BEST" if name == best_name else ""
        flag   = " OVERFIT" if m["overfit_gap"] > 0.05 else ""
        print(f"  {name:<20} {m['train_acc']*100:>7.1f}% {m['test_acc']*100:>6.1f}% "
              f"{m['overfit_gap']*100:>5.1f}% {m['precision']:>10.4f} {m['recall']:>8.4f} "
              f"{m['f1']:>8.4f} {m['roc_auc']:>9.4f} {m['cv_mean']*100:>7.1f}%"
              f"{marker}{flag}")
    print("-" * 90)
    print(f"\n[NOTE] Experiment {EXPERIMENT}: {FEATURE_COLS}")
    print("[NOTE] Use EXPERIMENT=A to see original ~100% result for comparison.")


if __name__ == "__main__":
    train()
