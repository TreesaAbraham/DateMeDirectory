#!/usr/bin/env python3
"""
Graph 2B: Exclamation points used per 100,000 words (by generation) with Tukey outliers shown as dots.

- Same metric as Graph 2
- Boxplot uses whis=1.5 (Tukey fences)
- showfliers=True so outliers appear as dots
- Also writes a CSV listing which profiles are outliers per generation

Outputs:
- data/charts/word_graph_02_exclam_per100k_by_generation_outliers_dots.png
- data/charts/word_graph_02_exclam_per100k_by_generation_outliers_dots.svg
- data/charts/word_graph_02_exclam_per100k_by_generation_outliers_dots_outliers.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt


WORD_RE = re.compile(r"\b[\w']+\b", flags=re.UNICODE)


def get_fulltext(p: dict) -> str:
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def get_age(p: dict) -> Optional[int]:
    a = p.get("age")
    if isinstance(a, int):
        return a
    if isinstance(a, str) and a.strip().isdigit():
        return int(a.strip())
    return None


def generation_from_birth_year(by: int) -> str:
    if 1997 <= by <= 2012:
        return "Gen Z"
    if 1981 <= by <= 1996:
        return "Millennial"
    if 1965 <= by <= 1980:
        return "Gen X"
    if 1946 <= by <= 1964:
        return "Boomer"
    if 1928 <= by <= 1945:
        return "Silent"
    return "Other/Unknown"


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def exclam_per_100k(text: str) -> Tuple[int, int, float]:
    exc = text.count("!")
    wc = count_words(text)
    rate = (exc / wc) * 100000 if wc > 0 else 0.0
    return exc, wc, rate


def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = p * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def tukey_fences(vals: List[float]) -> Tuple[float, float, float]:
    """
    Returns (q1, q3, low/high fences) for Tukey 1.5*IQR rule.
    """
    s = sorted(vals)
    q1 = percentile(s, 0.25)
    q3 = percentile(s, 0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return q1, q3, low, high


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--ref_year", type=int, default=2025, help="Year used to convert age -> birth year")
    ap.add_argument("--min_words", type=int, default=30, help="Skip profiles with fewer than this many words")
    ap.add_argument(
        "--order",
        default="Gen Z,Millennial,Gen X,Boomer,Silent,Other/Unknown",
        help="Comma-separated generation order for plotting",
    )
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_png = outdir / "word_graph_02_exclam_per100k_by_generation_outliers_dots.png"
    out_svg = outdir / "word_graph_02_exclam_per100k_by_generation_outliers_dots.svg"
    outliers_csv = outdir / "word_graph_02_exclam_per100k_by_generation_outliers_dots_outliers.csv"

    gen_order = [g.strip() for g in args.order.split(",") if g.strip()]
    by_gen: Dict[str, List[float]] = {g: [] for g in gen_order}
    rows: List[dict] = []

    skipped_no_age = 0
    skipped_short = 0
    skipped_no_text = 0
    kept = 0

    for p in profiles:
        text = get_fulltext(p)
        if not text.strip():
            skipped_no_text += 1
            continue

        age = get_age(p)
        if age is None:
            skipped_no_age += 1
            continue

        exc, wc, rate = exclam_per_100k(text)
        if wc < args.min_words:
            skipped_short += 1
            continue

        birth_year = args.ref_year - age
        gen = generation_from_birth_year(birth_year)

        if gen not in by_gen:
            by_gen[gen] = []
            gen_order.append(gen)

        by_gen[gen].append(rate)
        rows.append(
            {
                "id": p.get("id", ""),
                "generation": gen,
                "age": age,
                "birth_year": birth_year,
                "word_count": wc,
                "exclam_count": exc,
                "exclam_per_100k": float(rate),
            }
        )
        kept += 1

    # Prepare plot data (skip empty)
    labels = []
    data = []
    for gen in gen_order:
        vals = by_gen.get(gen, [])
        if vals:
            labels.append(gen)
            data.append(vals)

    if not data:
        raise SystemExit("No data to plot. Check age availability and min_words threshold.")

    # Compute Tukey fences per generation and label outliers in a CSV
    fences: Dict[str, Tuple[float, float, float, float]] = {}
    for gen, vals in by_gen.items():
        if vals:
            q1, q3, low, high = tukey_fences(vals)
            fences[gen] = (q1, q3, low, high)

    outlier_rows = []
    for r in rows:
        gen = r["generation"]
        q1, q3, low, high = fences.get(gen, (0.0, 0.0, -float("inf"), float("inf")))
        val = r["exclam_per_100k"]
        if val < low or val > high:
            outlier_rows.append(
                [
                    r["id"],
                    gen,
                    r["age"],
                    r["birth_year"],
                    r["word_count"],
                    r["exclam_count"],
                    round(val, 3),
                    round(q1, 3),
                    round(q3, 3),
                    round(low, 3),
                    round(high, 3),
                ]
            )

    with outliers_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id",
                "generation",
                "age",
                "birth_year",
                "word_count",
                "exclam_count",
                "exclam_per_100k",
                "q1",
                "q3",
                "low_fence",
                "high_fence",
            ]
        )
        w.writerows(outlier_rows)

    # Plot with outliers shown as dots
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.boxplot(
        data,
        labels=labels,
        showfliers=True,   # this draws outliers
        whis=1.5,          # Tukey fences (1.5*IQR)
    )
    ax.set_title("Exclamation Points Used per 100,000 Words (by generation, outliers shown)", pad=12)
    ax.set_ylabel("Exclamation points per 100,000 words")

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] kept profiles: {kept}")
    print(f"[skipped] no text: {skipped_no_text} | no age: {skipped_no_age} | <min_words: {skipped_short}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {outliers_csv}")


if __name__ == "__main__":
    main()
