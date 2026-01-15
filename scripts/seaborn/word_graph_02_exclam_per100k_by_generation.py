#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_02_exclam_per100k_by_generation_per_profile.csv"
OUT_PNG_WITH = REPO_ROOT / "data/charts/seaborn/png/word_graph_02_exclam_per100k_by_generation_seaborn.png"
OUT_PNG_NO = REPO_ROOT / "data/charts/seaborn/png/word_graph_02_exclam_per100k_by_generation_seaborn_no_outliers.png"

GEN_ORDER = ["Gen Z", "Millennial", "Gen X", "Boomer"]


def _basic_checks(df: pd.DataFrame) -> None:
    needed = ["generation", "exclam_per_100k"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Force numeric, drop junk
    df["exclam_per_100k"] = pd.to_numeric(df["exclam_per_100k"], errors="coerce")
    df = df.dropna(subset=["generation", "exclam_per_100k"])

    # Order generations consistently
    df["generation"] = df["generation"].astype(str)
    df["generation"] = pd.Categorical(df["generation"], categories=GEN_ORDER, ordered=True)
    df = df.dropna(subset=["generation"])  # removes anything not in GEN_ORDER
    return df


def _plot(df: pd.DataFrame, show_outliers: bool, out_path: Path) -> None:
    sns.set_theme(style="darkgrid", context="poster")
    sns.set_palette("pastel")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["font.size"] = 15
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.labelsize"] = 14




    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.boxplot(
        data=df,
        x="generation",
        y="exclam_per_100k",
        order=GEN_ORDER,
        showfliers=show_outliers,
        ax=ax,
    )

    title = "Exclamation Points per 100k Words by Generation (Seaborn)"
    if not show_outliers:
        title += " (No Outliers)"
    ax.set_title(title)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Exclamations per 100k words")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Wrote: {out_path}")


def main() -> None:
    df = pd.read_csv(IN_CSV)
    _basic_checks(df)
    df = _prep(df)

    _plot(df, show_outliers=True, out_path=OUT_PNG_WITH)
    _plot(df, show_outliers=False, out_path=OUT_PNG_NO)


if __name__ == "__main__":
    main()
