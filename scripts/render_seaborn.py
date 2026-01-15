#!/usr/bin/env python3
"""
Render Seaborn-styled charts from existing CSVs in data/charts/graphscsv.

This script does NOT recompute metrics. It only reads the canonical CSV outputs
your analysis scripts already produce, then renders "seaborn versions" as PNGs.

Usage examples:
  python3 scripts/render_seaborn.py --graph all
  python3 scripts/render_seaborn.py --graph 07 --theme whitegrid --context paper
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ---------- helpers ----------

def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    return pd.read_csv(path)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _save(fig: plt.Figure, outpath: Path, dpi: int = 200) -> None:
    _ensure_dir(outpath.parent)
    fig.savefig(outpath, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _apply_style(theme: str, context: str, font_scale: float) -> None:
    sns.set_theme(style=theme, context=context, font_scale=font_scale)


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of these columns exist: {candidates}. Found: {list(df.columns)}")


# ---------- graph renderers ----------
# Each renderer reads your existing canonical CSVs and outputs a seaborn-styled PNG.

def render_01_mosaic_serious_relationship(in_dir: Path, out_dir: Path, dpi: int) -> None:
    """
    Your mosaic is basically a contingency table. Seaborn doesn't do a true mosaic plot natively,
    so we render a heatmap with annotations (still counts + same message).
    """
    csv_path = in_dir / "word_graph_01_mosaic_serious_relationship.csv"
    df = _read_csv(csv_path)

    # Try to infer structure: expect something like: row_category, col_category, count
    row_col = _pick_col(df, ["row", "rows", "gender", "sex", "group_row"])
    col_col = _pick_col(df, ["col", "cols", "generation", "ageGroup", "group_col"])
    val_col = _pick_col(df, ["count", "n", "value", "num"])

    pivot = df.pivot_table(index=row_col, columns=col_col, values=val_col, aggfunc="sum", fill_value=0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.heatmap(pivot, annot=True, fmt="g", cbar=False, ax=ax)
    ax.set_title("Serious Relationship Language (Counts)")
    ax.set_xlabel(col_col)
    ax.set_ylabel(row_col)

    outpath = out_dir / "word_graph_01_mosaic_serious_relationship_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_02_exclam_by_generation(in_dir: Path, out_dir: Path, dpi: int) -> None:
    """
    Boxplot of exclamation points per 100k words by generation.
    Uses per-profile CSV, optionally overlays outliers if you have the outliers CSV.
    """
    per_profile = in_dir / "word_graph_02_exclam_per100k_by_generation_per_profile.csv"
    outliers = in_dir / "word_graph_02_exclam_per100k_by_generation_outliers_dots_outliers.csv"

    df = _read_csv(per_profile)
    gen_col = _pick_col(df, ["generation", "ageGroup", "cohort"])
    val_col = _pick_col(df, ["exclam_per_100k", "exclam_per100k", "value", "metric"])

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=df, x=gen_col, y=val_col, ax=ax, showfliers=True)
    ax.set_title("Exclamation Points per 100k Words by Generation")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Exclamation Points per 100k Words")

    # Optional overlay for outliers (nice for storytelling)
    if outliers.exists():
        odf = _read_csv(outliers)
        ogen = _pick_col(odf, [gen_col, "generation", "ageGroup", "cohort"])
        oval = _pick_col(odf, [val_col, "exclam_per_100k", "exclam_per100k", "value", "metric"])
        sns.stripplot(data=odf, x=ogen, y=oval, ax=ax, jitter=True, size=4)

    outpath = out_dir / "word_graph_02_exclam_per100k_by_generation_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_03_complexity_by_interest(in_dir: Path, out_dir: Path, dpi: int) -> None:
    """
    Your screenshot shows boxplot-like visuals by gender, for a specific interestedIn group.
    You have multiple outputs already; this renderer focuses on the per-profile CSV so it can facet.
    """
    per_profile = in_dir / "word_graph_03_complexity_by_interest_gender_per_profile.csv"
    df = _read_csv(per_profile)

    interest_col = _pick_col(df, ["interestedIn", "interest", "looking_for", "target_gender"])
    gender_col = _pick_col(df, ["gender", "profile_gender"])
    val_col = _pick_col(df, ["pct_complex_words", "complex_pct", "percent_complex", "value", "metric"])

    # Facet: one panel per interestedIn (Women/Men/NB etc), same idea as your current outputs
    g = sns.catplot(
        data=df,
        x=gender_col,
        y=val_col,
        col=interest_col,
        kind="box",
        col_wrap=3,
        height=4,
        aspect=1.0,
        showfliers=True,
    )
    g.set_titles("{col_name}")
    g.set_axis_labels("Profile Gender", "Percent of Words That Are Complex")
    g.fig.suptitle("Word Complexity by Gender (Faceted by Interested In)", y=1.03)

    outpath = out_dir / "word_graph_03_complexity_by_interest_gender_seaborn.png"
    _ensure_dir(outpath.parent)
    g.fig.savefig(outpath, dpi=dpi, bbox_inches="tight")
    plt.close(g.fig)


def render_04_table_distinctive_us_nonus(in_dir: Path, out_dir: Path, dpi: int) -> None:
    """
    Distinctive words is a table. Seaborn isn't a table library.
    We render a clean figure with a matplotlib table, under seaborn theme.
    """
    csv_path = in_dir / "word_graph_04_distinctive_us_vs_nonus.csv"
    df = _read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    ax.set_title("Most Distinctive Words: US vs Non-US")

    # show first N rows (you can tweak)
    show = df.head(25)
    table = ax.table(
        cellText=show.values,
        colLabels=list(show.columns),
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    outpath = out_dir / "word_graph_04_distinctive_us_vs_nonus_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_05_table_distinctive_bayarea_uk(in_dir: Path, out_dir: Path, dpi: int) -> None:
    csv_path = in_dir / "word_graph_05_distinctive_bayarea_vs_centraleurope_uk.csv"
    df = _read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    ax.set_title("Most Distinctive Words: SF Bay Area vs UK/Central Europe")

    show = df.head(25)
    table = ax.table(
        cellText=show.values,
        colLabels=list(show.columns),
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)

    outpath = out_dir / "word_graph_05_distinctive_bayarea_vs_centraleurope_uk_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_06_em_dash(in_dir: Path, out_dir: Path, dpi: int) -> None:
    """
    Bar chart: bucket counts.
    """
    csv_path = in_dir / "word_graph_06_em_dash_bucket_counts.csv"
    df = _read_csv(csv_path)

    bucket_col = _pick_col(df, ["bucket", "range", "bin"])
    count_col = _pick_col(df, ["count", "n", "value"])

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=df, x=bucket_col, y=count_col, ax=ax)
    ax.set_title("Em-dash Usage Buckets (Counts)")
    ax.set_xlabel("Em-dash bucket")
    ax.set_ylabel("Profiles")

    outpath = out_dir / "word_graph_06_em_dash_bucket_counts_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_07_exclam_by_gender(in_dir: Path, out_dir: Path, dpi: int) -> None:
    per_profile = in_dir / "word_graph_07_exclam_per100k_by_gender_per_profile.csv"
    df = _read_csv(per_profile)

    gender_col = _pick_col(df, ["gender", "profile_gender"])
    val_col = _pick_col(df, ["exclam_per_100k", "exclam_per100k", "value", "metric"])

    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.boxplot(data=df, x=gender_col, y=val_col, ax=ax, showfliers=True)
    ax.set_title("Exclamation Points per 100k Words by Gender")
    ax.set_xlabel("Gender")
    ax.set_ylabel("Exclamation Points per 100k Words")

    outpath = out_dir / "word_graph_07_exclam_per100k_by_gender_seaborn.png"
    _save(fig, outpath, dpi=dpi)


def render_08_sentence_complexity(in_dir: Path, out_dir: Path, dpi: int) -> None:
    per_profile = in_dir / "word_graph_08_sentence_complexity_by_interest_gender_per_profile.csv"
    df = _read_csv(per_profile)

    interest_col = _pick_col(df, ["interestedIn", "interest", "looking_for", "target_gender"])
    gender_col = _pick_col(df, ["gender", "profile_gender"])
    val_col = _pick_col(df, ["sentence_complexity", "complexity", "value", "metric"])

    g = sns.catplot(
        data=df,
        x=gender_col,
        y=val_col,
        col=interest_col,
        kind="box",
        col_wrap=3,
        height=4,
        aspect=1.0,
        showfliers=True,
    )
    g.set_titles("{col_name}")
    g.set_axis_labels("Profile Gender", "Sentence Complexity")
    g.fig.suptitle("Sentence Complexity by Gender (Faceted by Interested In)", y=1.03)

    outpath = out_dir / "word_graph_08_sentence_complexity_by_interest_gender_seaborn.png"
    _ensure_dir(outpath.parent)
    g.fig.savefig(outpath, dpi=dpi, bbox_inches="tight")
    plt.close(g.fig)


def render_09_prevalence_bay_uk(in_dir: Path, out_dir: Path, dpi: int) -> None:
    csv_path = in_dir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.csv"
    df = _read_csv(csv_path)

    group_col = _pick_col(df, ["group", "region", "bucket", "label"])
    val_col = _pick_col(df, ["value", "percent", "pct", "rate", "prevalence"])

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=df, x=group_col, y=val_col, ax=ax)
    ax.set_title("Prevalence of Bay/UK Wordsets by Region")
    ax.set_xlabel("Group")
    ax.set_ylabel("Prevalence")

    outpath = out_dir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us_seaborn.png"
    _save(fig, outpath, dpi=dpi)


RENDERERS = {
    "01": render_01_mosaic_serious_relationship,
    "02": render_02_exclam_by_generation,
    "03": render_03_complexity_by_interest,
    "04": render_04_table_distinctive_us_nonus,
    "05": render_05_table_distinctive_bayarea_uk,
    "06": render_06_em_dash,
    "07": render_07_exclam_by_gender,
    "08": render_08_sentence_complexity,
    "09": render_09_prevalence_bay_uk,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default="all", help="Graph number 01-09 or 'all'")
    parser.add_argument("--input-dir", default="data/charts/graphscsv", help="Where CSVs live")
    parser.add_argument("--output-dir", default="data/charts/graphs_seaborn/png", help="Where seaborn PNGs go")
    parser.add_argument("--theme", default="whitegrid", choices=["whitegrid", "darkgrid", "white", "ticks"])
    parser.add_argument("--context", default="paper", choices=["paper", "notebook", "talk", "poster"])
    parser.add_argument("--font-scale", type=float, default=1.0)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)

    _apply_style(theme=args.theme, context=args.context, font_scale=args.font_scale)

    if args.graph == "all":
        for key in sorted(RENDERERS.keys()):
            RENDERERS[key](in_dir, out_dir, args.dpi)
    else:
        g = args.graph.zfill(2)
        if g not in RENDERERS:
            raise SystemExit(f"Unknown graph '{args.graph}'. Choose one of: {sorted(RENDERERS.keys())} or 'all'")
        RENDERERS[g](in_dir, out_dir, args.dpi)


if __name__ == "__main__":
    main()
