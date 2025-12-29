#!/usr/bin/env python3
"""
Graph 2: "Levels of excitement" via exclamation points used per 100,000 words.

- Reads: data/profiles_master.json (list of profiles)
- Text source: profileDetails.fullText (fallbacks included)
- Uses profile age to infer generation via birth year (ref year default: 2025)
- Computes exclamations per 100,000 words per profile
- Produces a boxplot by generation (like the reference figure)

Outputs:
- data/charts/word_graph_02_exclam_per100k_by_generation.png
- data/charts/word_graph_02_exclam_per100k_by_generation.svg
- data/charts/word_graph_02_exclam_per100k_by_generation_per_profile.csv
- data/charts/word_graph_02_exclam_per100k_by_generation_summary.csv
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
    """
    Pew-style boundaries (commonly used):
    - Gen Z: 1997–2012
    - Millennial: 1981–1996
    - Gen X: 1965–1980
    - Boomer: 1946–1964
    - Silent: 1928–1945
    Anything outside becomes "Other/Unknown"
    """
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
    """
    Returns: (exclam_count, word_count, rate_per_100k)
    """
    exc = text.count("!")
    wc = count_words(text)
    rate = (exc / wc) * 100000 if wc > 0 else 0.0
    return exc, wc, rate


def percentile(sorted_vals: List[float], p: float) -> float:
    """
    Simple linear interpolation percentile.
    p in [0, 1]
    """
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

    per_profile_csv = outdir / "word_graph_02_exclam_per100k_by_generation_per_profile.csv"
    summary_csv = outdir / "word_graph_02_exclam_per100k_by_generation_summary.csv"
    out_png = outdir / "word_graph_02_exclam_per100k_by_generation.png"
    out_svg = outdir / "word_graph_02_exclam_per100k_by_generation.svg"

    gen_order = [g.strip() for g in args.order.split(",") if g.strip()]
    by_gen: Dict[str, List[float]] = {g: [] for g in gen_order}

    rows_written = 0
    skipped_no_age = 0
    skipped_short = 0
    skipped_no_text = 0

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "age", "birth_year", "generation", "word_count", "exclam_count", "exclam_per_100k"])

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

            # Ensure in dict (in case order omitted it)
            if gen not in by_gen:
                by_gen[gen] = []
                gen_order.append(gen)

            by_gen[gen].append(rate)

            w.writerow([p.get("id", ""), age, birth_year, gen, wc, exc, round(rate, 3)])
            rows_written += 1

    # Build summary stats
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["generation", "n", "min", "q1", "median", "q3", "max"])
        for gen in gen_order:
            vals = sorted(by_gen.get(gen, []))
            if not vals:
                w.writerow([gen, 0, "", "", "", "", ""])
                continue
            w.writerow(
                [
                    gen,
                    len(vals),
                    round(vals[0], 3),
                    round(percentile(vals, 0.25), 3),
                    round(percentile(vals, 0.50), 3),
                    round(percentile(vals, 0.75), 3),
                    round(vals[-1], 3),
                ]
            )

    # Prepare data for plot (skip empty groups)
    plot_labels = []
    plot_data = []
    for gen in gen_order:
        vals = by_gen.get(gen, [])
        if vals:
            plot_labels.append(gen)
            plot_data.append(vals)

    if not plot_data:
        raise SystemExit("No data to plot. (Check age availability and min_words threshold.)")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.boxplot(plot_data, labels=plot_labels, showfliers=False)
    ax.set_title("Exclamation Points Used per 100,000 Words (by generation)", pad=12)
    ax.set_ylabel("Exclamation points per 100,000 words")

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] plotted profiles: {rows_written}")
    print(f"[skipped] no text: {skipped_no_text} | no age: {skipped_no_age} | <min_words: {skipped_short}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")


if __name__ == "__main__":
    main()
