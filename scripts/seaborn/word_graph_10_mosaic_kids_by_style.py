#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "data").exists():
            return parent
    # fallback: two levels up from scripts/seaborn/
    return start.resolve().parents[2]


REPO_ROOT = find_repo_root(Path(__file__).parent)

DEFAULT_IN_CSV = REPO_ROOT / "data" / "charts" / "graphscsv" / "word_graph_10_kids_mentions_by_style_mosaic_counts.csv"
DEFAULT_OUT_PNG = REPO_ROOT / "data" / "charts" / "seaborn" / "png" / "word_graph_10_mosaic_kids_by_style.png"


STYLE_ORDER = ["mono", "poly", "any"]
BUCKET_ORDER = ["No kids mention", "Kids mention"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seaborn chart for kids mentions by dating style (from CSV).")
    parser.add_argument("--in", dest="in_csv", default=str(DEFAULT_IN_CSV), help="Input CSV path")
    parser.add_argument("--out", dest="out_png", default=str(DEFAULT_OUT_PNG), help="Output PNG path")
    args = parser.parse_args()

    in_csv = Path(args.in_csv)
    out_png = Path(args.out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_csv)

    # Basic validation
    required = {"datingStyle", "kids_bucket", "count", "style_total", "pct_within_style"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"CSV missing columns: {sorted(missing)}")

    # Ensure types
    df["pct_within_style"] = pd.to_numeric(df["pct_within_style"], errors="coerce")
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df["style_total"] = pd.to_numeric(df["style_total"], errors="coerce").fillna(0).astype(int)

    # Order categories for consistent plotting
    df["datingStyle"] = pd.Categorical(df["datingStyle"], categories=STYLE_ORDER, ordered=True)
    df["kids_bucket"] = pd.Categorical(df["kids_bucket"], categories=BUCKET_ORDER, ordered=True)

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(
        data=df,
        x="datingStyle",
        y="pct_within_style",
        hue="kids_bucket",
        ax=ax,
        errorbar=None,
    )

    ax.set_title("Kids mentions by dating style (Seaborn)")
    ax.set_xlabel("Dating style")
    ax.set_ylabel("Percent within style")

    # Make y-axis 0–100
    ax.set_ylim(0, 100)

    # Label bars with percent + count
    # Seaborn draws bars in hue order per x category; we can iterate patches.
    # We'll map each patch to its row using sorted df order (style, bucket).
    plot_df = (
        df.sort_values(["datingStyle", "kids_bucket"])
          .reset_index(drop=True)
    )

    patches = [p for p in ax.patches if p.get_height() is not None]
    if len(patches) == len(plot_df):
        for patch, row in zip(patches, plot_df.to_dict("records")):
            h = patch.get_height()
            label = f"{h:.1f}%\n(n={row['count']})"
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                h + 1.0,
                label,
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.legend(title="Kids bucket", loc="upper right")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)

    print(f"Wrote: {out_png}")


if __name__ == "__main__":
    main()
