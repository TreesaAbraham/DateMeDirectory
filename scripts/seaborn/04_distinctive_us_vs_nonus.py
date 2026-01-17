#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_04_distinctive_us_vs_nonus.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"


US_COLOR = "#2F855A"      # green
NONUS_COLOR = "#7B2CBF"   # purple


def _prep(df: pd.DataFrame, top: int) -> pd.DataFrame:
    required = [
        "rank", "US_word", "US_count", "US_z",
        "NON_US_word", "NON_US_count", "NON_US_z",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    # Ensure rank numeric and sort
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df.dropna(subset=["rank"]).sort_values("rank").head(top).copy()

    # Coerce metrics
    for c in ["US_count", "US_z", "NON_US_count", "NON_US_z"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def render(in_csv: Path, out_dir: Path, top: int, metric: str, dpi: int) -> None:
    df = pd.read_csv(in_csv)
    df = _prep(df, top=top)

    # Style: seaborn theme + serif + big text
    sns.set_theme(style="whitegrid", context="poster")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 22
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 13
    plt.rcParams["ytick.labelsize"] = 13

    if metric == "z":
        us_val_col = "US_z"
        nonus_val_col = "NON_US_z"
        xlabel = "Distinctiveness (z-score)"
        title = f"Most distinctive words: US vs Non-US (Top {len(df)})"
        fmt = "{:.2f}"
    else:
        us_val_col = "US_count"
        nonus_val_col = "NON_US_count"
        xlabel = "Count"
        title = f"Most distinctive words: US vs Non-US (counts, Top {len(df)})"
        fmt = "{:.0f}"

    # Build plotting frame: one row per rank, with separate word + value for each side
    plot_df = pd.DataFrame({
        "rank": df["rank"].astype(int),
        "US_word": df["US_word"].astype(str),
        "US_val": df[us_val_col],
        "NON_US_word": df["NON_US_word"].astype(str),
        "NON_US_val": df[nonus_val_col],
    })

    # We want a shared y-axis. Use rank as the row order (top rank at top).
    plot_df = plot_df.sort_values("rank", ascending=False).reset_index(drop=True)

    # Left side should go negative so it diverges from 0.
    # If you're plotting z-scores, Non-US z is already negative (good).
    # If you're plotting counts, we negate it for the diverging effect.
    if metric == "count":
        plot_df["NON_US_plot"] = -plot_df["NON_US_val"]
    else:
        plot_df["NON_US_plot"] = plot_df["NON_US_val"]

    # US should be positive; if z is positive it already is.
    plot_df["US_plot"] = plot_df["US_val"]

    # Figure
    fig, ax = plt.subplots(figsize=(12, 8))

    y = range(len(plot_df))

    # Bars
    ax.barh(y, plot_df["NON_US_plot"], color=NONUS_COLOR, alpha=0.85, label="Non-US")
    ax.barh(y, plot_df["US_plot"], color=US_COLOR, alpha=0.85, label="US")


    # Center line
    ax.axvline(0, color="black", linewidth=1)
    ax.legend(loc="lower right", frameon=True, title="Region")


    # Y labels: show BOTH words (left | right) so it reads like the table
    ylabels = [
        f"{nonus}   |   {us}"
        for nonus, us in zip(plot_df["NON_US_word"], plot_df["US_word"])
    ]
    ax.set_yticks(list(y))
    ax.set_yticklabels(ylabels)

    ax.set_title(title)
    ax.set_xlabel(xlabel)

    # Annotate values at bar ends
    for i in y:
        left_val = plot_df.loc[i, "NON_US_plot"]
        right_val = plot_df.loc[i, "US_plot"]

        # Left annotation
        ax.text(
            left_val - (0.02 * (abs(left_val) + 1)),
            i,
            fmt.format(plot_df.loc[i, "NON_US_val"]),
            va="center",
            ha="right",
            fontsize=11,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )
        # Right annotation
        ax.text(
            right_val + (0.02 * (abs(right_val) + 1)),
            i,
            fmt.format(plot_df.loc[i, "US_val"]),
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )

    # Tighten x-limits for nicer framing
    xmax = max(plot_df["US_plot"].max(skipna=True), 0)
    xmin = min(plot_df["NON_US_plot"].min(skipna=True), 0)
    pad = 0.15 * max(abs(xmin), abs(xmax), 1)
    ax.set_xlim(xmin - pad, xmax + pad)

    fig.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"word_graph_04_distinctive_us_vs_nonus_{metric}_seaborn"
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
    stem = f"word_graph_04_distinctive_us_vs_nonus_{metric}_seaborn"
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
