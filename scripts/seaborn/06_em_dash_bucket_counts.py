#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_06_em_dash_per_profile.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"

BUCKET_ORDER = ["0", "1", "2", "3", "4", "5+"]


def render(in_csv: Path, out_dir: Path, dpi: int) -> None:
    df = pd.read_csv(in_csv)

    required = ["id", "word_count", "em_dash_count", "bucket"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    # Normalize bucket as strings (since we have '5+')
    df["bucket"] = df["bucket"].astype(str).str.strip()

    # Keep only known buckets (avoids surprises)
    df = df[df["bucket"].isin(BUCKET_ORDER)].copy()

    counts = (
        df["bucket"]
        .value_counts()
        .reindex(BUCKET_ORDER, fill_value=0)
        .reset_index()
    )
    counts.columns = ["bucket", "count"]
    total = int(counts["count"].sum())

    # Style: big + serif
    sns.set_theme(style="whitegrid", context="poster")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 22
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 14
    plt.rcParams["ytick.labelsize"] = 14

    fig, ax = plt.subplots(figsize=(10, 6))

    # Color palette: not-blue, not-hideous
    palette = sns.color_palette("mako", n_colors=len(BUCKET_ORDER))

    sns.barplot(
        data=counts,
        x="bucket",
        y="count",
        order=BUCKET_ORDER,
        palette=palette,
        ax=ax,
    )

    ax.set_title("Em dash usage in profiles (bucket counts)")
    ax.set_xlabel("Em dashes per profile (bucket)")
    ax.set_ylabel("Number of profiles")

    # Labels: count + percent
    for i, row in counts.iterrows():
        c = int(row["count"])
        pct = (c / total * 100.0) if total else 0.0
        ax.text(
            i,
            c + max(1, total * 0.005),
            f"{c} ({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / "word_graph_06_em_dash_bucket_counts_seaborn.png"
    out_svg = out_dir / "word_graph_06_em_dash_bucket_counts_seaborn.svg"

    fig.tight_layout()
    fig.savefig(out_png, dpi=dpi)
    fig.savefig(out_svg)
    plt.close(fig)

    print(f"Wrote: {out_png}")
    print(f"Wrote: {out_svg}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", type=Path, default=DEFAULT_IN_CSV)
    ap.add_argument("--out_dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    render(args.in_csv, args.out_dir, args.dpi)


if __name__ == "__main__":
    main()
