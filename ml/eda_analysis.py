"""
eda_analysis.py
===============
Exploratory Data Analysis — generates charts and prints insights.
Includes feature dominance / root cause analysis.

Run: python eda_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
from data_cleaning import get_clean_data

os.makedirs("outputs", exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def plot_class_distribution(df: pd.DataFrame):
    counts = df["Final Output"].value_counts().sort_index()
    labels = {0: "No Dengue", 1: "Dengue"}
    colors = ["#22c55e", "#ef4444"]
    plt.figure(figsize=(6, 4))
    bars = plt.bar([labels[k] for k in counts.index], counts.values,
                   color=colors, edgecolor="white", width=0.5)
    for bar, val in zip(bars, counts.values):
        plt.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 5, str(val),
                 ha="center", va="bottom", fontweight="bold", fontsize=12)
    ratio = counts.iloc[1] / counts.iloc[0]
    plt.title(f"Class Distribution  (ratio {ratio:.2f}:1)", fontsize=13)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("outputs/class_distribution.png", dpi=130)
    plt.close()
    print("[EDA] Saved class_distribution.png")


def plot_feature_distributions(df: pd.DataFrame):
    num_cols = ["Age", "Haemoglobin", "WBC Count", "Platelet Count", "PDW"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    for i, col in enumerate(num_cols):
        axes[i].hist(df[df["Final Output"] == 0][col], bins=30,
                     alpha=0.65, label="No Dengue", color="#22c55e", edgecolor="white")
        axes[i].hist(df[df["Final Output"] == 1][col], bins=30,
                     alpha=0.65, label="Dengue",    color="#ef4444", edgecolor="white")
        axes[i].set_title(col, fontsize=11)
        axes[i].legend(fontsize=9)
    axes[5].axis("off")
    plt.suptitle("Feature Distributions by Class", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/feature_distributions.png", dpi=130)
    plt.close()
    print("[EDA] Saved feature_distributions.png")


def plot_correlation_matrix(df: pd.DataFrame):
    corr = df.select_dtypes(include=[np.number]).corr()
    plt.figure(figsize=(9, 7))
    mask = np.zeros_like(corr, dtype=bool)
    np.fill_diagonal(mask, True)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, linewidths=0.4, mask=mask)
    plt.title("Feature Correlation Matrix\n(WBC Count -0.91 with target = root cause of ~100% accuracy)",
              fontsize=11)
    plt.tight_layout()
    plt.savefig("outputs/correlation_matrix.png", dpi=130)
    plt.close()
    print("[EDA] Saved correlation_matrix.png")


def plot_boxplots(df: pd.DataFrame):
    features = ["Platelet Count", "WBC Count", "PDW", "Haemoglobin", "Age"]
    fig, axes = plt.subplots(1, len(features), figsize=(18, 5))
    for i, col in enumerate(features):
        data0 = df[df["Final Output"] == 0][col].dropna()
        data1 = df[df["Final Output"] == 1][col].dropna()
        axes[i].boxplot([data0, data1], labels=["No Dengue", "Dengue"],
                        patch_artist=True,
                        boxprops=dict(facecolor="#e0f2fe"),
                        medianprops=dict(color="#1d4ed8", linewidth=2))
        axes[i].set_title(col, fontsize=10)
        axes[i].set_xlabel("")
    fig.suptitle("Boxplots by Target Class", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig("outputs/boxplots.png", dpi=130)
    plt.close()
    print("[EDA] Saved boxplots.png")


def plot_feature_dominance(df: pd.DataFrame):
    """
    Highlight the WBC Count near-perfect separation issue.
    This is the root cause of ~100% model accuracy.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Feature Dominance Analysis -- Root Cause of ~100% Accuracy",
                 fontsize=12, fontweight="bold")

    # WBC Count separation
    ax = axes[0]
    ax.hist(df[df["Final Output"] == 0]["WBC Count"], bins=30,
            alpha=0.7, color="#3b82f6", label="No Dengue", edgecolor="white")
    ax.hist(df[df["Final Output"] == 1]["WBC Count"], bins=30,
            alpha=0.7, color="#ef4444", label="Dengue",    edgecolor="white")
    ax.axvline(4000, color="#fbbf24", linewidth=2, linestyle="--",
               label="Near-perfect threshold ~4000")
    ax.set_xlabel("WBC Count (cells/uL)")
    ax.set_ylabel("Frequency")
    ax.set_title("WBC Count: Correlation = -0.917\nRanges barely overlap => trivial separator")
    ax.legend(fontsize=9)

    # Correlation bar
    ax = axes[1]
    num_df = df.select_dtypes(include=[np.number])
    corr_vals = num_df.corr()["Final Output"].drop("Final Output").sort_values()
    colors = ["#ef4444" if abs(v) > 0.7 else "#f97316" if abs(v) > 0.3 else "#6b7280"
              for v in corr_vals]
    feats = [f.replace(" ", "\n") for f in corr_vals.index]
    ax.barh(feats, corr_vals.values, color=colors, edgecolor="white")
    ax.axvline(-0.7, color="#ef4444", linewidth=1.5, linestyle="--",
               alpha=0.7, label="Danger threshold (-0.7)")
    ax.set_xlabel("Pearson Correlation with Target")
    ax.set_title("Feature Correlation\n(Red: dominant | Orange: moderate)")
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig("outputs/feature_dominance.png", dpi=130)
    plt.close()
    print("[EDA] Saved feature_dominance.png")

    # Print correlation table
    print("\n[EDA] Feature correlations with target (Final Output):")
    for feat, val in corr_vals.items():
        flag = "  <-- HIGH DOMINANCE (root cause)" if abs(val) > 0.7 else ""
        print(f"  {feat:<22}: {val:>7.4f}{flag}")


def run_eda():
    df = get_clean_data()
    print("\n[EDA] Running exploratory data analysis...\n")
    plot_class_distribution(df)
    plot_feature_distributions(df)
    plot_correlation_matrix(df)
    plot_boxplots(df)
    plot_feature_dominance(df)
    print("\n[EDA] All charts saved to outputs/")


if __name__ == "__main__":
    run_eda()
