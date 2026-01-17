#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_05_distinctive_bayarea_vs_uk_london.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"

BAY_COLOR = "#2F855A"   # green
UK_COLOR = "#7B2CBF"    # purple


def _prep(df: pd.DataFrame, top: int) -> pd.DataFrame:
    required = [
        "rank",
        "BAY_AREA_word", "BAY_AREA_count", "BAY_AREA_z",
        "UK_word", "UK_count", "UK_z",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df.dropna(subset=["rank"]).sort_values("rank").head(top).copy()

    for c in ["BAY_AREA_count", "BAY_AREA_z", "UK_count", "UK_z"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def render(in_csv: Path, out_dir: Path, top: int, metric: str, dpi: int) -> None:
    df = pd.read_csv(in_csv)
    df = _prep(df, top=top)

    # Theme + serif + bigger text (match your previous seaborn style)
    sns.set_theme(style="whitegrid", context="poster")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 22
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 13
    plt.rcParams["ytick.labelsize"] = 13

    if metric == "z":
        left_val_col = "UK_z"
        right_val_col = "BAY_AREA_z"
        xlabel = "Distinctiveness (z-score)"
        title = f"Most distinctive words: Bay Area vs UK/London (Top {len(df)})"
        fmt = "{:.2f}"
    else:
        left_val_col = "UK_count"
        right_val_col = "BAY_AREA_count"
        xlabel = "Count"
        title = f"Most distinctive words: Bay Area vs UK/London (counts, Top {len(df)})"
        fmt = "{:.0f}"

    plot_df = pd.DataFrame({
        "rank": df["rank"].astype(int),
        "BAY_word": df["BAY_AREA_word"].astype(str),
        "BAY_val": df[right_val_col],
        "UK_word": df["UK_word"].astype(str),
        "UK_val": df[left_val_col],
    })

    # Put rank 1 at top visually
    plot_df = plot_df.sort_values("rank", ascending=False).reset_index(drop=True)

    # Left side should be negative for diverging effect
    if metric == "count":
        plot_df["UK_plot"] = -plot_df["UK_val"]
    else:
        plot_df["UK_plot"] = plot_df["UK_val"]  # already negative z

    plot_df["BAY_plot"] = plot_df["BAY_val"]   # should be positive

    fig, ax = plt.subplots(figsize=(12, 8))
    y = range(len(plot_df))

    ax.barh(y, plot_df["UK_plot"], color=UK_COLOR, alpha=0.85, label="UK / London")
    ax.barh(y, plot_df["BAY_plot"], color=BAY_COLOR, alpha=0.85, label="SF Bay Area")


    ax.axvline(0, color="black", linewidth=1)
    ax.legend(loc="lower right", frameon=True, title="Region")


    # Show both words per row: UK | Bay
    ylabels = [
        f"{uk}   |   {bay}"
        for uk, bay in zip(plot_df["UK_word"], plot_df["BAY_word"])
    ]
    ax.set_yticks(list(y))
    ax.set_yticklabels(ylabels)

    ax.set_title(title)
    ax.set_xlabel(xlabel)

    # Annotate values at bar ends
    for i in y:
        left_val = plot_df.loc[i, "UK_plot"]
        right_val = plot_df.loc[i, "BAY_plot"]

        ax.text(
            left_val - (0.02 * (abs(left_val) + 1)),
            i,
            fmt.format(plot_df.loc[i, "UK_val"]),
            va="center",
            ha="right",
            fontsize=11,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )
        ax.text(
            right_val + (0.02 * (abs(right_val) + 1)),
            i,
            fmt.format(plot_df.loc[i, "BAY_val"]),
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )

    xmax = max(plot_df["BAY_plot"].max(skipna=True), 0)
    xmin = min(plot_df["UK_plot"].min(skipna=True), 0)
    pad = 0.15 * max(abs(xmin), abs(xmax), 1)
    ax.set_xlim(xmin - pad, xmax + pad)

    fig.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"word_graph_05_distinctive_bayarea_vs_uk_london_{metric}_seaborn"
    out_png = out_dir / f"{stem}.png"
    out_svg = out_dir / f"{stem}.svg"

    ax.axvline(0, color="black", linewidth=1)

    # Legend OUTSIDE so it never covers bars
    ax.legend(
        title="Region",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
    )

    fig.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"word_graph_05_distinctive_bayarea_vs_uk_london_{metric}_seaborn"
    out_png = out_dir / f"{stem}.png"
    out_svg = out_dir / f"{stem}.svg"

    # bbox_inches="tight" ensures the outside legend is included in the image
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote: {out_png}")
    print(f"Wrote: {out_svg}")



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", type=Path, default=DEFAULT_IN_CSV)
    ap.add_argument("--out_dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--metric", choices=["z", "count"], default="z")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    render(args.in_csv, args.out_dir, args.top, args.metric, args.dpi)


if __name__ == "__main__":
    main()
