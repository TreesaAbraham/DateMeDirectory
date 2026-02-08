#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "data").exists():
            return parent
    return start.resolve().parents[2]


REPO_ROOT = find_repo_root(Path(__file__).parent)

DEFAULT_IN_CSV = (
    REPO_ROOT
    / "data"
    / "charts"
    / "graphscsv"
    / "word_graph_10_kids_mentions_by_style_mosaic_counts.csv"
)

DEFAULT_OUT_PNG = (
    REPO_ROOT
    / "data"
    / "charts"
    / "seaborn"
    / "png"
    / "word_graph_10_mosaic_kids_by_style.png"
)

DEFAULT_OUT_SVG = (
    REPO_ROOT
    / "data"
    / "charts"
    / "seaborn"
    / "svg"
    / "word_graph_10_mosaic_kids_by_style.svg"
)

STYLE_ORDER = ["mono", "poly", "any"]
BUCKET_ORDER = ["No kids mention", "Kids mention"]

# Keep this list aligned with your “kids-topic” detection terms.
# (childfree/child-free is NOT here because it’s a negation signal)
KIDS_TOPIC_TERMS = sorted([
    "baby", "babies", "child", "children", "kid", "kids",
    "parent", "parents", "mom", "dad", "mother", "father",
    "stepkid", "stepkids", "stepchild", "stepchildren",
    "coparent", "co-parent", "custody",
])

NEGATION_EXAMPLES = [
    "childfree / child-free",
    "“no kids”",
    "“don’t want kids/children”",
    "“not looking for kids”",
]


def pretty_wrap_terms(terms: list[str], per_line: int = 3) -> list[str]:
    lines = []
    for i in range(0, len(terms), per_line):
        lines.append(", ".join(terms[i:i + per_line]))
    return lines


def load_counts(in_csv: Path) -> dict[tuple[str, str], dict]:
    df = pd.read_csv(in_csv)

    needed = {"datingStyle", "kids_bucket", "count", "style_total", "pct_within_style"}
    missing = needed - set(df.columns)
    if missing:
        raise RuntimeError(f"CSV missing columns: {sorted(missing)}")

    df["datingStyle"] = df["datingStyle"].astype(str).str.strip().str.lower()
    df["kids_bucket"] = df["kids_bucket"].astype(str).str.strip()

    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    df["style_total"] = pd.to_numeric(df["style_total"], errors="coerce").fillna(0).astype(int)
    df["pct_within_style"] = pd.to_numeric(df["pct_within_style"], errors="coerce").fillna(0.0)

    out: dict[tuple[str, str], dict] = {}
    for _, r in df.iterrows():
        out[(r["datingStyle"], r["kids_bucket"])] = {
            "count": int(r["count"]),
            "style_total": int(r["style_total"]),
            "pct_within_style": float(r["pct_within_style"]),
        }
    return out


def draw_mosaic_from_counts(
    counts: dict[tuple[str, str], dict],
    out_png: Path,
    out_svg: Path,
    include_side_legend: bool = True,
) -> None:
    # Seaborn theme, but we draw the mosaic with matplotlib rectangles
    sns.set_theme(style="whitegrid")

    # Your requested palette
    STYLE_COLORS = {
        "mono": "#D2042D",  # cherry red
        "poly": "#F4B400",  # marigold yellow
        "any":  "#FFCBA4",  # peach
    }

    def lighten(hex_color: str, factor: float) -> tuple[float, float, float]:
        """
        factor: 0 = original color, 1 = white
        returns RGB tuple for matplotlib
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r + (1 - r) * factor, g + (1 - g) * factor, b + (1 - b) * factor)

    # totals per style
    style_totals = {
        s: sum(counts.get((s, b), {}).get("count", 0) for b in BUCKET_ORDER)
        for s in STYLE_ORDER
    }
    grand_total = sum(style_totals.values())
    if grand_total == 0:
        raise RuntimeError("Grand total is 0. CSV might be empty or mismatched.")

    # Layout: mosaic + optional side legend
    if include_side_legend:
        fig, (ax, ax_leg) = plt.subplots(
            ncols=2,
            figsize=(14, 7),
            gridspec_kw={"width_ratios": [3.4, 1.2]},
        )
        ax_leg.axis("off")
    else:
        fig, ax = plt.subplots(figsize=(11, 7))
        ax_leg = None

    # Fix the “everything shoved into the top” issue:
    # - use suptitle
    # - adjust top margin
    fig.subplots_adjust(top=0.86, wspace=0.25)

    fig.suptitle(
        "Kids mentions by dating style (mosaic)\nNegations excluded (e.g., “don’t want kids” counted as No)",
        y=0.96,
        fontsize=13,
    )

    # Mosaic panel
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    x = 0.0
    for s in STYLE_ORDER:
        s_total = style_totals.get(s, 0)
        if s_total <= 0:
            continue

        width = s_total / grand_total

        no_cnt = counts.get((s, "No kids mention"), {}).get("count", 0)
        yes_cnt = counts.get((s, "Kids mention"), {}).get("count", 0)

        no_h = no_cnt / s_total if s_total else 0
        yes_h = yes_cnt / s_total if s_total else 0

        base = STYLE_COLORS.get(s, "#999999")

        # Two shades per style: lighter = No, darker = Yes
        face_no = lighten(base, 0.65)
        face_yes = lighten(base, 0.25)

        # Filled rectangles
        ax.add_patch(Rectangle((x, 0), width, no_h, facecolor=face_no, edgecolor="black", linewidth=1.0))
        ax.add_patch(Rectangle((x, no_h), width, yes_h, facecolor=face_yes, edgecolor="black", linewidth=1.0))

        # Column label just above mosaic (not in the title area)
        ax.text(
            x + width / 2,
            1.005,
            f"{s} (n={s_total})",
            ha="center",
            va="bottom",
            fontsize=11,
        )

        # Cell labels
        if no_h > 0:
            ax.text(
                x + width / 2,
                no_h / 2,
                f"No\n{no_cnt} ({(no_cnt/s_total)*100:.1f}%)",
                ha="center",
                va="center",
                fontsize=10,
            )
        if yes_h > 0:
            ax.text(
                x + width / 2,
                no_h + yes_h / 2,
                f"Yes\n{yes_cnt} ({(yes_cnt/s_total)*100:.1f}%)",
                ha="center",
                va="center",
                fontsize=10,
            )

        x += width

    # Side legend
    if include_side_legend and ax_leg is not None:
        term_lines = pretty_wrap_terms(KIDS_TOPIC_TERMS, per_line=3)
        neg_lines = "\n".join([f"• {x}" for x in NEGATION_EXAMPLES])

        legend_text = (
            "Style colors:\n"
            "• mono = cherry red\n"
            "• poly = marigold\n"
            "• any  = peach\n\n"
            "Kids-topic terms scanned:\n\n"
            + "\n".join(term_lines)
            + "\n\nNegation phrases excluded:\n"
            + neg_lines
            + "\n\nRule:\nKids-topic words only count\nas YES if not negated."
        )

        ax_leg.text(
        0.02,
        0.98,
        legend_text,
        ha="left",
        va="top",
        fontsize=10,
        # Match the rest of the plot text (seaborn/matplotlib default)
        bbox=dict(boxstyle="round,pad=0.6", fill=False),
    )


    # Save outputs
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(out_png, dpi=200)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mosaic-style kids-by-style plot (Seaborn theme + Matplotlib rectangles) from CSV."
    )
    parser.add_argument("--in", dest="in_csv", default=str(DEFAULT_IN_CSV), help="Input CSV path")
    parser.add_argument("--out-png", dest="out_png", default=str(DEFAULT_OUT_PNG), help="Output PNG path")
    parser.add_argument("--out-svg", dest="out_svg", default=str(DEFAULT_OUT_SVG), help="Output SVG path")
    parser.add_argument("--no-legend", action="store_true", help="Disable the side legend panel")
    args = parser.parse_args()

    in_csv = Path(args.in_csv)
    out_png = Path(args.out_png)
    out_svg = Path(args.out_svg)

    counts = load_counts(in_csv)
    draw_mosaic_from_counts(counts, out_png, out_svg, include_side_legend=(not args.no_legend))

    print(f"Wrote PNG: {out_png}")
    print(f"Wrote SVG: {out_svg}")


if __name__ == "__main__":
    main()
