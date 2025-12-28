#!/usr/bin/env python3
"""
Graph 1: Mosaic plot (2x2)
Rows: Male vs Female
Cols: Uses "serious relationship" language bucket vs Does not

Text source: profileDetails.fullText (with fallbacks)
Input: data/profiles_master.json (list of profile dicts)

Outputs:
- data/charts/word_graph_01_mosaic_serious_relationship.png
- data/charts/word_graph_01_mosaic_serious_relationship.svg
- data/charts/word_graph_01_mosaic_serious_relationship.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def get_fulltext(p: dict) -> str:
    """
    Robustly pull full text from common shapes:
    - p["profileDetails"]["fullText"] (expected)
    - p["profileDetails"]["full_text"]
    - p["profileDetails"]["fulltext"]
    - p["profileDetails"]["text"] / ["body"] (fallbacks)
    - p["fullText"] (last resort)
    """
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def canonical_gender(raw) -> str:
    """
    Normalize your gender field into canonical labels.
    Handles common inputs like 'M', 'F', 'male', 'female'.
    """
    if not isinstance(raw, str):
        return "Other"
    s = raw.strip().upper()
    if s in {"M", "MALE", "MAN"}:
        return "Male"
    if s in {"F", "FEMALE", "WOMAN"}:
        return "Female"
    return "Other"


def compile_bucket_regex(bucket_terms: List[str]) -> re.Pattern:
    """
    Build a regex that matches any term with word boundaries.
    Supports multi-word phrases too (spaces become \\s+).
    """
    cleaned = []
    for t in bucket_terms:
        t = t.strip().lower()
        if not t:
            continue
        escaped = re.escape(t).replace(r"\ ", r"\s+")
        cleaned.append(escaped)

    if not cleaned:
        raise SystemExit("Bucket is empty. Add terms with --bucket.")

    pat = r"\b(" + "|".join(cleaned) + r")\b"
    return re.compile(pat, flags=re.IGNORECASE)


def build_contingency(
    profiles: List[dict],
    bucket_re: re.Pattern,
    allowed_rows: List[str],
    min_hits: int,
) -> Tuple[List[str], List[str], Dict[Tuple[str, str], int], int]:
    """
    Columns are always: ["Uses bucket", "Does not use bucket"]
    Returns: rows, cols, counts[(row,col)], total
    """
    rows = allowed_rows
    cols = ["Uses bucket", "Does not use bucket"]
    counts: Dict[Tuple[str, str], int] = {(r, c): 0 for r in rows for c in cols}
    total = 0

    for p in profiles:
        row = canonical_gender(p.get("gender", ""))
        if row not in rows:
            continue

        text = get_fulltext(p)
        if not text.strip():
            continue

        hits = len(bucket_re.findall(text))
        has = hits >= min_hits
        col = cols[0] if has else cols[1]
        counts[(row, col)] += 1
        total += 1

    return rows, cols, counts, total


def save_csv(out_csv: Path, rows: List[str], cols: List[str], counts: Dict[Tuple[str, str], int]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["row", "col", "count"])
        for r in rows:
            for c in cols:
                w.writerow([r, c, counts[(r, c)]])


def draw_mosaic(
    out_png: Path,
    out_svg: Path,
    title: str,
    rows: List[str],
    cols: List[str],
    counts: Dict[Tuple[str, str], int],
    total: int,
) -> None:
    """
    Simple mosaic:
    - Column widths proportional to column totals / total
    - Within each column, cell heights proportional to row share within that column

    Visual upgrades:
    - White borders so tiny columns don't disappear
    - Always label counts (2x2 won't clutter)
    - Hatch "Does not use bucket" cells to distinguish them
    """
    if total == 0:
        raise SystemExit("No usable rows found. Check gender codes and fullText path.")

    col_totals = {c: sum(counts[(r, c)] for r in rows) for c in cols}

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    x0 = 0.0
    for c in cols:
        ct = col_totals[c]
        w = ct / total if total else 0

        y0 = 0.0
        for r in reversed(rows):  # reversed so first row appears visually on top
            cell = counts[(r, c)]
            h = (cell / ct) if ct else 0

            hatch = "///" if c == "Does not use bucket" else None

            rect = Rectangle(
                (x0, y0),
                w,
                h,
                fill=True,
                alpha=0.55,
                edgecolor="white",
                linewidth=2,
                hatch=hatch,
            )
            ax.add_patch(rect)

            # Always label if cell > 0 (your 13 and 6 should show)
            if cell > 0:
                ax.text(
                    x0 + w / 2,
                    y0 + h / 2,
                    str(cell),
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                )

            y0 += h

        ax.text(x0 + w / 2, 1.02, c, ha="center", va="bottom", fontsize=11)
        x0 += w

    # Left-side row labels based on overall row totals (approximate)
    row_totals = {r: sum(counts[(r, c)] for c in cols) for r in rows}
    running = 0.0
    for r in reversed(rows):
        rh = row_totals[r] / total
        ax.text(-0.02, running + rh / 2, r, ha="right", va="center", fontsize=11)
        running += rh

    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, linewidth=1.5))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--concept", default="serious relationship", help="Used in title/output naming")
    ap.add_argument(
        "--bucket",
        default="love,loving,relationship,relationships,stability,stable,dating,partner,partners,marriage,married,family,commitment,committed,serious,long term,long-term",
        help="Comma-separated bucket terms/phrases",
    )
    ap.add_argument(
        "--rows",
        default="Male,Female",
        help="Comma-separated gender rows to include (canonical): Male,Female",
    )
    ap.add_argument(
        "--min_hits",
        type=int,
        default=1,
        help="Minimum number of bucket matches required to count as 'Uses bucket' (default: 1)",
    )
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    bucket_terms = [t.strip() for t in args.bucket.split(",")]
    bucket_re = compile_bucket_regex(bucket_terms)

    rows = [r.strip() for r in args.rows.split(",") if r.strip()]
    rows, cols, counts, total = build_contingency(
        profiles,
        bucket_re,
        allowed_rows=rows,
        min_hits=args.min_hits,
    )

    outdir = Path(args.outdir)
    safe = "serious_relationship"
    out_png = outdir / f"word_graph_01_mosaic_{safe}.png"
    out_svg = outdir / f"word_graph_01_mosaic_{safe}.svg"
    out_csv = outdir / f"word_graph_01_mosaic_{safe}.csv"

    save_csv(out_csv, rows, cols, counts)
    draw_mosaic(
        out_png=out_png,
        out_svg=out_svg,
        title=f"Use of {args.concept} language in profiles",
        rows=rows,
        cols=cols,
        counts=counts,
        total=total,
    )

    print(f"[done] n={total}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {out_csv}")


if __name__ == "__main__":
    main()
