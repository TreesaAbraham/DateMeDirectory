#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


REPO_ROOT = Path(__file__).resolve().parents[2]
IN_CSV = REPO_ROOT / "data/charts/graphscsv/word_graph_01_mosaic_serious_relationship.csv"
OUT_DIR = REPO_ROOT / "data/charts/seaborn/png"
OUT_PNG = OUT_DIR / "word_graph_01_mosaic_serious_relationship_seaborn.png"

# Force a consistent order (matches your screenshot)
ROW_ORDER = ["Male", "Female"]
COL_ORDER = ["Uses bucket", "Does not use bucket"]

# Styling
BASE_COLOR = "#6BAED6"         # muted blue fill
EDGE_COLOR = "white"
HATCH_COL = "Does not use bucket"
HATCH_STYLE = "///"

# “Definition” content shown on the right (display-only)
NEGATION_WINDOW = 8
DEFINITION_LINES = [
    'Counts as "Uses bucket" if ≥ 1 non-negated match(es).',
    f"Negation rule: ignore matches if a negation appears within {NEGATION_WINDOW} words before the term.",
]
ROW_COLORS = {
    "Male": "#1B5E20",    # dark green
    "Female": "#00897B",  # teal 
}

# The terms table you showed (left = primary, right = variants/synonyms)
SERIOUS_TERMS = [
    ("love", "loving"),
    ("relationship", "relationships"),
    ("stability", "stable"),
    ("dating", "partner"),
    ("partners", "marriage"),
    ("married", "family"),
    ("commitment", "committed"),
    ("serious", "long term"),
    ("long-term", "kids"),
    ("children", "compatible"),
    ("long-term", "longterm"),
]


def load_counts() -> pd.DataFrame:
    if not IN_CSV.exists():
        raise SystemExit(f"CSV not found: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    required = {"row", "col", "count"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns {sorted(missing)}. Found: {list(df.columns)}")

    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    return df


def make_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pv = df.pivot_table(index="row", columns="col", values="count", aggfunc="sum", fill_value=0)

    # Ensure all expected rows/cols exist
    for r in ROW_ORDER:
        if r not in pv.index:
            pv.loc[r] = 0
    for c in COL_ORDER:
        if c not in pv.columns:
            pv[c] = 0

    pv = pv.reindex(index=ROW_ORDER, columns=COL_ORDER)
    return pv


def draw_mosaic(ax, pv: pd.DataFrame) -> None:
    overall_total = pv.to_numpy().sum()
    if overall_total <= 0:
        raise SystemExit("No counts to plot (total is 0).")

    # Plot in [0,1] x [0,1] coordinates
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")



    # Column labels (top)
    # (we'll place them above the mosaic manually)
    # Row heights proportional to row totals
    y_top = 1.0
    for r in pv.index:
        row_total = pv.loc[r].sum()
        if row_total <= 0:
            continue

        row_h = row_total / overall_total
        y0 = y_top - row_h

        # Row label on the left
        ax.text(
            -0.03,
            y0 + row_h / 2,
            r,
            ha="right",
            va="center",
            fontsize=14,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )

        x_left = 0.0
        for c in pv.columns:
            v = int(pv.loc[r, c])
            w = (v / row_total) if row_total > 0 else 0.0

            if w <= 0:
                continue

            rect = Rectangle(
                (x_left, y0),
                w,
                row_h,
                facecolor=ROW_COLORS.get(r, BASE_COLOR),
                edgecolor=EDGE_COLOR,
                linewidth=2,
                alpha=0.85,
                hatch=(HATCH_STYLE if c == HATCH_COL else None),
            )
            ax.add_patch(rect)

            # Count label (center)
            # Slightly smaller if the cell is tiny
            area = w * row_h
            fs = 16 if area > 0.12 else 12 if area > 0.06 else 10
            ax.text(
                x_left + w / 2,
                y0 + row_h / 2,
                f"{v}",
                ha="center",
                va="center",
                fontsize=18,
                fontweight="bold",
                fontfamily="DejaVu Serif",
                color="black",
            )

            x_left += w

        y_top = y0

    # Column headers (centered above each column using overall totals)
    # Since widths vary per row in a mosaic, we place the labels above the *average* split
    # based on overall counts per column.
    col_totals = pv.sum(axis=0)
    total = col_totals.sum()
    x_left = 0.0
    for c in pv.columns:
        w = (col_totals[c] / total) if total else 0.0
        if w <= 0:
            continue
        ax.text(
            x_left + w / 2,
            1.02,
            c,
            ha="center",
            va="bottom",
            fontsize=13,
            fontweight="bold",
            fontfamily="DejaVu Serif",
        )
        x_left += w


def draw_definition_panel(ax) -> None:
    ax.axis("off")

    ax.text(
        0.0,
        1.0,
        "Definition",
        ha="left",
        va="top",
        fontsize=16,
        fontweight="bold",
        fontfamily="DejaVu Serif",
    )

    ax.text(
        0.0,
        0.90,
        "\n".join(DEFINITION_LINES),
        ha="left",
        va="top",
        fontsize=11,
        fontfamily="DejaVu Serif",
        wrap=True,
    )

    # Terms table
    cell_text = [[a, b] for (a, b) in SERIOUS_TERMS]
    table = ax.table(
        cellText=cell_text,
        colLabels=["Serious terms", ""],
        cellLoc="left",
        colLoc="left",
        loc="lower left",
        bbox=[0.0, 0.0, 1.0, 0.72],  # [x, y, width, height]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Make headers bold-ish
    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(1)
        if row == 0:
            cell.set_text_props(fontweight="bold", fontfamily="DejaVu Serif")
        else:
            cell.set_text_props(fontfamily="DejaVu Serif")


def main() -> None:
    # Typography to match your other plots
    plt.rcParams["font.family"] = "DejaVu Serif"
    plt.rcParams["axes.titlesize"] = 18

    df = load_counts()
    pv = make_pivot(df)

    fig = plt.figure(figsize=(11.5, 5.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.2, 1.3], wspace=0.08)

    ax_left = fig.add_subplot(gs[0, 0])
    ax_right = fig.add_subplot(gs[0, 1])

    fig.suptitle(
        "Use of serious relationship language in profiles (negation-aware)",
        y=0.98,
        fontsize=18,
        fontweight="bold",
        fontfamily="DejaVu Serif",
    )

    draw_mosaic(ax_left, pv)
    draw_definition_panel(ax_right)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote: {OUT_PNG}")


if __name__ == "__main__":
    main()
