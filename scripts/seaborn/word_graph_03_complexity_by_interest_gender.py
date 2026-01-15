#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_03_complexity_by_interest_gender_per_profile.csv"
OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"

SOURCE_ORDER = ["F", "M", "NB"]
TARGET_ORDER = ["F", "M", "NB"]

# Pick ONE:
TARGET_COLOR = {
    "F": "#E11D74",   # fuchsia
    "NB": "#7B2CBF",  # purple
    "M": "#2563EB",   # blue
}



def render_one(df: pd.DataFrame, target: str) -> None:
    # Bigger overall text + serif
    sns.set_theme(style="darkgrid", context="poster")  # poster = larger text
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 20
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 14
    plt.rcParams["ytick.labelsize"] = 14

    dft = df[df["target_gender"] == target].copy()
    if dft.empty:
        print(f"Skipping target={target}: no rows")
        return

    fig, ax = plt.subplots(figsize=(9.5, 6.5))

    sns.boxplot(
        data=dft,
        x="source_gender",
        y="complex_pct",
        order=SOURCE_ORDER,
        showfliers=False,      # <- excludes outliers
        ax=ax,
        color=TARGET_COLOR.get(target, "#6B7280"),  # fallback gray

    )


    # Compute medians and label them on the median line
    medians = (
        dft.groupby("source_gender")["complex_pct"]
        .median()
        .reindex(SOURCE_ORDER)
    )

    # x positions for categories are 0..len-1 in the same order
    for i, sg in enumerate(SOURCE_ORDER):
        med = medians.get(sg)
        if pd.isna(med):
            continue
        ax.text(
            i,
            med,
            f"{med:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title(f"Word Complexity by Profile Gender (Interested in {target})")
    ax.set_xlabel("Profile gender (source)")
    ax.set_ylabel("Complex words (%)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"word_graph_03_complexity_by_interest_in_{target}_seaborn.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Wrote: {out_path}")


def main() -> None:
    df = pd.read_csv(IN_CSV)

    required = ["source_gender", "target_gender", "complex_pct"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    df["complex_pct"] = pd.to_numeric(df["complex_pct"], errors="coerce")
    df = df.dropna(subset=["source_gender", "target_gender", "complex_pct"])

    df["source_gender"] = df["source_gender"].astype(str)
    df["target_gender"] = df["target_gender"].astype(str)

    # Keep only the categories we intend to plot
    df = df[df["source_gender"].isin(SOURCE_ORDER)]
    df = df[df["target_gender"].isin(TARGET_ORDER)]

    for target in TARGET_ORDER:
        render_one(df, target)


if __name__ == "__main__":
    main()
