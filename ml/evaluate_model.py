"""
evaluate_model.py
=================
Detailed post-training evaluation: confusion matrix, ROC curve,
training vs test comparison, and classification report.

Run: python evaluate_model.py
"""

import joblib, json, os, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_curve, auc, ConfusionMatrixDisplay,
    log_loss, accuracy_score
)
from sklearn.model_selection import learning_curve

from data_cleaning import get_clean_data
from preprocess import preprocess_and_split, FEATURE_COLS, EXPERIMENT

warnings.filterwarnings("ignore")
os.makedirs("outputs", exist_ok=True)


def plot_confusion_matrix(y_test, y_pred):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["No Dengue", "Dengue"],
                yticklabels=["No Dengue", "Dengue"],
                linewidths=0.5, annot_kws={"size": 14, "weight": "bold"})
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    plt.title(f"Confusion Matrix -- Experiment {EXPERIMENT}", fontsize=12)
    plt.tight_layout()
    plt.savefig("outputs/confusion_matrix.png", dpi=130)
    plt.close()
    tn, fp, fn, tp = cm.ravel()
    print(f"[EVAL] Confusion Matrix saved.  TP={tp}  TN={tn}  FP={fp}  FN={fn}")


def plot_roc_curve(model, X_test, y_test):
    y_prob = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, color="#3b82f6", lw=2,
             label=f"ROC Curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="#9ca3af", linestyle="--", lw=1)
    plt.fill_between(fpr, tpr, alpha=0.08, color="#3b82f6")
    plt.xlabel("False Positive Rate", fontsize=11)
    plt.ylabel("True Positive Rate", fontsize=11)
    plt.title(f"ROC Curve -- Experiment {EXPERIMENT}", fontsize=12)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig("outputs/roc_curve.png", dpi=130)
    plt.close()
    print(f"[EVAL] ROC curve saved. AUC = {roc_auc:.4f}")


def plot_train_vs_test(train_acc, test_acc, train_loss, test_loss):
    """Bar chart comparing train and test accuracy + loss."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle(f"Train vs Test -- Experiment {EXPERIMENT}", fontsize=12, fontweight="bold")

    ax = axes[0]
    ax.bar(["Train", "Test"], [train_acc * 100, test_acc * 100],
           color=["#3b82f6", "#10b981"], width=0.4, edgecolor="white")
    for i, v in enumerate([train_acc * 100, test_acc * 100]):
        ax.text(i, v + 0.3, f"{v:.2f}%", ha="center", fontsize=12, fontweight="bold")
    gap = (train_acc - test_acc) * 100
    ax.set_title(f"Accuracy  (Gap = {gap:.2f}%)", fontsize=11)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Accuracy (%)")
    color = "#dc2626" if gap > 5 else "#16a34a"
    ax.annotate(f"{'OVERFIT' if gap > 5 else 'OK'}: {gap:.2f}% gap",
                xy=(0.5, 0.05), xycoords="axes fraction", ha="center",
                fontsize=10, color=color, fontweight="bold")

    ax = axes[1]
    ax.bar(["Train", "Test"], [train_loss, test_loss],
           color=["#3b82f6", "#f97316"], width=0.4, edgecolor="white")
    for i, v in enumerate([train_loss, test_loss]):
        ax.text(i, v + 0.002, f"{v:.4f}", ha="center", fontsize=12, fontweight="bold")
    ax.set_title("Log Loss (lower = better)", fontsize=11)
    ax.set_ylabel("Log Loss")

    plt.tight_layout()
    plt.savefig("outputs/train_vs_test.png", dpi=130)
    plt.close()
    print("[EVAL] Train vs Test chart saved.")


def plot_learning_curves(model, X_train, y_train):
    """Learning curve to visualize underfitting / overfitting over dataset size."""
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train, y_train,
        cv=5,
        train_sizes=np.linspace(0.1, 1.0, 10),
        scoring="accuracy",
        n_jobs=-1
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_sizes, train_scores.mean(axis=1) * 100, "o-",
            color="#3b82f6", label="Training Accuracy")
    ax.plot(train_sizes, val_scores.mean(axis=1) * 100, "s--",
            color="#ef4444", label="CV Validation Accuracy")
    ax.fill_between(train_sizes,
                    (train_scores.mean(1) - train_scores.std(1)) * 100,
                    (train_scores.mean(1) + train_scores.std(1)) * 100,
                    alpha=0.12, color="#3b82f6")
    ax.fill_between(train_sizes,
                    (val_scores.mean(1) - val_scores.std(1)) * 100,
                    (val_scores.mean(1) + val_scores.std(1)) * 100,
                    alpha=0.12, color="#ef4444")
    ax.set_xlabel("Training Set Size")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"Learning Curves -- Experiment {EXPERIMENT}", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("outputs/learning_curves.png", dpi=130)
    plt.close()
    print("[EVAL] Learning curves saved.")


def evaluate():
    df = get_clean_data()
    X_train, X_test, y_train, y_test, _ = preprocess_and_split(df)

    model = joblib.load("models/model.pkl")
    y_pred       = model.predict(X_test)
    y_prob       = model.predict_proba(X_test)[:, 1]
    y_train_pred = model.predict(X_train)
    y_train_prob = model.predict_proba(X_train)[:, 1]

    train_acc  = accuracy_score(y_train, y_train_pred)
    test_acc   = accuracy_score(y_test,  y_pred)
    train_loss = log_loss(y_train, y_train_prob)
    test_loss  = log_loss(y_test,  y_prob)

    print(f"\n[EVAL] Model: {type(model).__name__}  --  Experiment {EXPERIMENT}")
    print(f"[EVAL] Features: {FEATURE_COLS}")
    print(f"\n[EVAL] Train Accuracy : {train_acc*100:.2f}%   Train Loss: {train_loss:.4f}")
    print(f"[EVAL] Test  Accuracy : {test_acc*100:.2f}%   Test  Loss: {test_loss:.4f}")
    print(f"[EVAL] Overfit Gap    : {(train_acc-test_acc)*100:.2f}%  "
          f"({'OVERFITTING' if train_acc-test_acc > 0.05 else 'OK'})")
    print(f"\n[EVAL] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Dengue", "Dengue"]))

    plot_confusion_matrix(y_test, y_pred)
    plot_roc_curve(model, X_test, y_test)
    plot_train_vs_test(train_acc, test_acc, train_loss, test_loss)
    plot_learning_curves(model, X_train, y_train)

    with open("models/training_report.json") as f:
        report = json.load(f)
    print(f"\n[EVAL] Best model from training report: {report['best_model']}")
    print(f"[EVAL] Metrics: {report['best_metrics']}")


if __name__ == "__main__":
    evaluate()
