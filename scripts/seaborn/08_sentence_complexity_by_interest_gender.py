#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]

# This is the CSV produced by your Graph 08 builder script (the gender-split one).
IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_08_sentence_complexity_by_interest_gender_per_profile.csv"
OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"

SOURCE_ORDER = ["F", "M", "NB"]
TARGET_ORDER = ["M", "F", "NB"]

# Colors per TARGET (what they’re looking for)
TARGET_COLOR = {
    "F": "#DB2777",   # fuchsia (looking for women)
    "NB": "#7B2CBF",  # purple  (looking for NB)
    "M": "#2563EB",   # blue    (looking for men)
}

PRETTY_TARGET = {"M": "Men", "F": "Women", "NB": "Non-binary"}


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of these columns exist: {candidates}. Found: {list(df.columns)}")


def render_one(df: pd.DataFrame, target: str, threshold_words: int) -> None:
    dft = df[df["target_gender"] == target].copy()
    if dft.empty:
        print(f"Skipping target={target}: no rows")
        return

    color = TARGET_COLOR.get(target, "#6B7280")

    fig, ax = plt.subplots(figsize=(9.5, 6.5))

    sns.boxplot(
        data=dft,
        x="source_gender",
        y="long_sentence_pct",
        order=SOURCE_ORDER,
        showfliers=False,   # exclude outliers
        ax=ax,
        color=color,
    )

    # Median labels
    medians = (
        dft.groupby("source_gender")["long_sentence_pct"]
        .median()
        .reindex(SOURCE_ORDER)
    )

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
            fontsize=14,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )

    pretty = PRETTY_TARGET.get(target, target)
    ax.set_title(f"Sentence Complexity by Profile Gender (Looking for {pretty})\n% sentences > {threshold_words} words")
    ax.set_xlabel("Profile gender (source)")
    ax.set_ylabel("Long sentences (%)")

    ax.set_ylim(0, 100)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"word_graph_08_sentence_complexity_looking_for_{target}_seaborn.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Wrote: {out_path}")


def main() -> None:
    # Theme + typography (match your Graph 03 vibe)
    sns.set_theme(style="whitegrid", context="poster")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 20
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 14
    plt.rcParams["ytick.labelsize"] = 14

    if not IN_CSV.exists():
        raise SystemExit(f"CSV not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)

    # Some older files used different names; we normalize to long_sentence_pct.
    pct_col = _pick_col(df, ["long_sentence_pct", "percent_complex_sentences", "sentence_complex_pct"])
    if pct_col != "long_sentence_pct":
        df = df.rename(columns={pct_col: "long_sentence_pct"})

    required = ["source_gender", "target_gender", "long_sentence_pct"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    df["long_sentence_pct"] = pd.to_numeric(df["long_sentence_pct"], errors="coerce")
    df = df.dropna(subset=["source_gender", "target_gender", "long_sentence_pct"])

    df["source_gender"] = df["source_gender"].astype(str)
    df["target_gender"] = df["target_gender"].astype(str)

    # Keep only the categories we intend to plot
    df = df[df["source_gender"].isin(SOURCE_ORDER)]
    df = df[df["target_gender"].isin(TARGET_ORDER)]

    # This threshold is only for labeling the title.
    # It MUST match whatever you used when generating the CSV.
    threshold_words = 20

    for target in TARGET_ORDER:
        render_one(df, target, threshold_words)


if __name__ == "__main__":
    main()
