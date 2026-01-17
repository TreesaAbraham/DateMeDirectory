#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"

# Match your existing palette vibe
BAY_COLOR = "#2F855A"  # green
UK_COLOR = "#7B2CBF"   # purple

GROUP_ORDER = ["ALL_US", "BAY_AREA", "UK_LONDON"]
GROUP_LABELS = {
    "ALL_US": "All US",
    "BAY_AREA": "SF Bay Area",
    "UK_LONDON": "UK / London",
}


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "group",
        "docs",
        "total_tokens",
        "bay_wordset_rate_per_10k",
        "uk_wordset_rate_per_10k",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Found: {list(df.columns)}")

    df = df.copy()
    df["docs"] = pd.to_numeric(df["docs"], errors="coerce")
    df["total_tokens"] = pd.to_numeric(df["total_tokens"], errors="coerce")
    df["bay_wordset_rate_per_10k"] = pd.to_numeric(df["bay_wordset_rate_per_10k"], errors="coerce")
    df["uk_wordset_rate_per_10k"] = pd.to_numeric(df["uk_wordset_rate_per_10k"], errors="coerce")

    df = df.dropna(subset=["group", "bay_wordset_rate_per_10k", "uk_wordset_rate_per_10k"])
    df["group"] = df["group"].astype(str)

    # Keep only expected groups, and order them
    df = df[df["group"].isin(GROUP_ORDER)].copy()
    df["group"] = pd.Categorical(df["group"], categories=GROUP_ORDER, ordered=True)
    df = df.sort_values("group")

    return df


def render(in_csv: Path, out_dir: Path, dpi: int) -> None:
    df = pd.read_csv(in_csv)
    df = _prep(df)

    # Long -> tidy for seaborn hue bars
    plot_df = df.melt(
        id_vars=["group", "docs", "total_tokens"],
        value_vars=["bay_wordset_rate_per_10k", "uk_wordset_rate_per_10k"],
        var_name="wordset",
        value_name="rate_per_10k",
    )

    plot_df["wordset"] = plot_df["wordset"].map({
        "bay_wordset_rate_per_10k": "Bay wordset",
        "uk_wordset_rate_per_10k": "UK wordset",
    })

    # Avoid categorical fillna issues: build labels from plain strings
    plot_df["group_str"] = plot_df["group"].astype(str)
    plot_df["group_label"] = plot_df["group_str"].map(GROUP_LABELS)
    plot_df["group_label"] = plot_df["group_label"].fillna(plot_df["group_str"])

    # Ensure x order matches GROUP_ORDER via labels
    group_label_order = [GROUP_LABELS[g] for g in GROUP_ORDER]

    # Theme + serif + larger text (consistent with your other seaborn scripts)
    sns.set_theme(style="whitegrid", context="poster")
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 22
    plt.rcParams["axes.labelsize"] = 16
    plt.rcParams["xtick.labelsize"] = 13
    plt.rcParams["ytick.labelsize"] = 13

    palette = {"Bay wordset": BAY_COLOR, "UK wordset": UK_COLOR}

    title = "Prevalence of Bay vs UK wordsets (per 10k tokens)"

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.barplot(
        data=plot_df,
        x="group_label",
        y="rate_per_10k",
        hue="wordset",
        order=group_label_order,
        palette=palette,
        ax=ax,
        edgecolor="black",
    )

    # Title top-left
    ax.set_title(title, loc="left", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("Rate per 10k tokens")

    # Legend outside so it never covers bars
    ax.legend(
        title="Wordset",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
    )

    # Value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", padding=3, fontsize=11)

    # Context line under title: docs + tokens
    ctx = " | ".join(
        f"{GROUP_LABELS.get(r.group, r.group)}: {int(r.docs)} docs, {int(r.total_tokens)} tokens"
        for r in df.itertuples(index=False)
        if pd.notna(r.docs) and pd.notna(r.total_tokens)
    )
    ax.text(
        0.0,
        1.02,
        ctx,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        fontfamily="DejaVu Serif",
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us_seaborn.png"
    out_svg = out_dir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us_seaborn.svg"

    # tight_layout + bbox_inches="tight" so the outside legend gets included
    fig.tight_layout()
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
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
