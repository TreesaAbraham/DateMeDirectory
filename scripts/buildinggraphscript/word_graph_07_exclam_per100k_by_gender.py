#!/usr/bin/env python3
"""
Graph 7: "Levels of excitement" via exclamation points used per 100,000 words BY GENDER.

- Reads: data/profiles_master.json (list of profiles)
- Text source: profileDetails.fullText (fallbacks included)
- Computes exclamations per 100,000 words per profile
- Groups by gender (Male vs Female only)
- Produces a boxplot

Outputs:
- data/charts/word_graph_07_exclam_per100k_by_gender.png
- data/charts/word_graph_07_exclam_per100k_by_gender.svg
- data/charts/word_graph_07_exclam_per100k_by_gender_per_profile.csv
- data/charts/word_graph_07_exclam_per100k_by_gender_summary.csv
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


def normalize_gender(val: object) -> Optional[str]:
    """
    Map messy gender strings to Male/Female. Everything else => None.
    Adjust mappings if your dataset uses different labels.
    """
    if not isinstance(val, str):
        return None
    s = val.strip().lower()
    if not s:
        return None

    male_vals = {"male", "man", "m", "guy", "he/him", "he"}
    female_vals = {"female", "woman", "f", "girl", "she/her", "she"}

    if s in male_vals:
        return "Male"
    if s in female_vals:
        return "Female"

    # Common variations like "Male (cis)" or "female/woman"
    if "male" in s and "female" not in s:
        return "Male"
    if "female" in s and "male" not in s:
        return "Female"

    return None


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--min_words", type=int, default=30, help="Skip profiles with fewer than this many words")
    ap.add_argument("--gender_field", default="gender", help="Field name for gender")
    ap.add_argument("--order", default="Male,Female", help="Comma-separated order for plotting")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_profile_csv = outdir / "word_graph_07_exclam_per100k_by_gender_per_profile.csv"
    summary_csv = outdir / "word_graph_07_exclam_per100k_by_gender_summary.csv"
    out_png = outdir / "word_graph_07_exclam_per100k_by_gender.png"
    out_svg = outdir / "word_graph_07_exclam_per100k_by_gender.svg"

    order = [x.strip() for x in args.order.split(",") if x.strip()]
    by_gender: Dict[str, List[float]] = {g: [] for g in order}

    kept = 0
    skipped_no_text = 0
    skipped_short = 0
    skipped_gender = 0

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "gender", "word_count", "exclam_count", "exclam_per_100k"])

        for p in profiles:
            text = get_fulltext(p)
            if not text.strip():
                skipped_no_text += 1
                continue

            exc, wc, rate = exclam_per_100k(text)
            if wc < args.min_words:
                skipped_short += 1
                continue

            g = normalize_gender(p.get(args.gender_field))
            if g is None:
                skipped_gender += 1
                continue

            if g not in by_gender:
                by_gender[g] = []
                order.append(g)

            by_gender[g].append(rate)
            kept += 1

            w.writerow([p.get("id", ""), g, wc, exc, round(rate, 3)])

    # Summary CSV
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gender", "n", "min", "q1", "median", "q3", "max"])
        for g in order:
            vals = sorted(by_gender.get(g, []))
            if not vals:
                w.writerow([g, 0, "", "", "", "", ""])
                continue
            w.writerow([
                g,
                len(vals),
                round(vals[0], 3),
                round(percentile(vals, 0.25), 3),
                round(percentile(vals, 0.50), 3),
                round(percentile(vals, 0.75), 3),
                round(vals[-1], 3),
            ])

    # Plot
    plot_labels = []
    plot_data = []
    for g in order:
        vals = by_gender.get(g, [])
        if vals:
            plot_labels.append(g)
            plot_data.append(vals)

    if not plot_data:
        raise SystemExit("No data to plot. Check gender labels and min_words threshold.")

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.boxplot(plot_data, labels=plot_labels, showfliers=False)
    ax.set_title("Exclamation Points Used per 100,000 Words (by gender)", pad=12)
    ax.set_ylabel("Exclamation points per 100,000 words")

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] kept profiles: {kept}")
    print(f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short} | not Male/Female: {skipped_gender}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")


if __name__ == "__main__":
    main()
