#!/usr/bin/env python3
"""
Graph 3: "Percent of words that are complex" by interestedIn grouping.

Style: For each group, draw a vertical bar spanning Q1->Q3, with a median line + median label,
similar to the reference figure.

Groups derived from interestedIn:
- Looking for Men (M only)
- Looking for Women (F only)
- Looking for Both (contains M and F)

Text source: profileDetails.fullText (fallbacks included)

Outputs:
- data/charts/word_graph_03_complexity_by_interest.png
- data/charts/word_graph_03_complexity_by_interest.svg
- data/charts/word_graph_03_complexity_by_interest_per_profile.csv
- data/charts/word_graph_03_complexity_by_interest_summary.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


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


def get_interested_in(p: dict) -> List[str]:
    """
    Tries common shapes:
    - p["interestedIn"] as list like ["M","F"]
    - p["interestedIn"] as string like "M,F" or "MF"
    - p["genderInterestedIn"] (legacy)
    Returns uppercase tokens.
    """
    val = p.get("interestedIn", None)
    if val is None:
        val = p.get("genderInterestedIn", None)

    if isinstance(val, list):
        return [str(x).strip().upper() for x in val if str(x).strip()]
    if isinstance(val, str):
        s = val.strip().upper()
        # split on commas/spaces if present
        if "," in s:
            return [t.strip().upper() for t in s.split(",") if t.strip()]
        if " " in s:
            return [t.strip().upper() for t in s.split() if t.strip()]
        # treat as sequence of letters (e.g., "MF")
        return [ch for ch in s if ch.isalpha()]
    return []


def classify_interest(tokens: List[str]) -> Optional[str]:
    """
    Map interestedIn tokens to one of our chart groups.
    We only care about M and F for this graph.
    """
    tset = set(tokens)
    has_m = "M" in tset or "MALE" in tset or "MEN" in tset
    has_f = "F" in tset or "FEMALE" in tset or "WOMEN" in tset

    if has_m and has_f:
        return "Looking for Both"
    if has_m:
        return "Looking for Men"
    if has_f:
        return "Looking for Women"
    return None


def tokenize_words(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def complexity_percent(words: List[str], min_len: int) -> float:
    """
    Percent of words whose length >= min_len.
    """
    if not words:
        return 0.0
    complex_ct = sum(1 for w in words if len(w) >= min_len)
    return (complex_ct / len(words)) * 100.0


def percentile(sorted_vals: List[float], p: float) -> float:
    """
    Linear-interpolated percentile. p in [0,1]
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
    ap.add_argument("--min_words", type=int, default=50, help="Skip profiles with fewer than this many words")
    ap.add_argument("--min_len", type=int, default=7, help="Word length threshold for 'complex'")
    ap.add_argument(
        "--order",
        default="Looking for Men,Looking for Women,Looking for Both",
        help="Comma-separated plotting order",
    )
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_profile_csv = outdir / "word_graph_03_complexity_by_interest_per_profile.csv"
    summary_csv = outdir / "word_graph_03_complexity_by_interest_summary.csv"
    out_png = outdir / "word_graph_03_complexity_by_interest.png"
    out_svg = outdir / "word_graph_03_complexity_by_interest.svg"

    order = [x.strip() for x in args.order.split(",") if x.strip()]
    by_group: Dict[str, List[float]] = {g: [] for g in order}

    skipped_no_text = 0
    skipped_short = 0
    skipped_no_interest = 0
    kept = 0

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "interest_group", "word_count", "complex_pct"])

        for p in profiles:
            text = get_fulltext(p)
            if not text.strip():
                skipped_no_text += 1
                continue

            words = tokenize_words(text)
            if len(words) < args.min_words:
                skipped_short += 1
                continue

            tokens = get_interested_in(p)
            group = classify_interest(tokens)
            if group is None:
                skipped_no_interest += 1
                continue

            pct = complexity_percent(words, min_len=args.min_len)

            if group not in by_group:
                by_group[group] = []
                order.append(group)

            by_group[group].append(pct)
            w.writerow([p.get("id", ""), group, len(words), round(pct, 3)])
            kept += 1

    # Summary stats CSV
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "n", "min", "q1", "median", "q3", "max"])
        for g in order:
            vals = sorted(by_group.get(g, []))
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

    # Plot: vertical IQR bars + median line + median label
    labels = []
    stats = []  # (q1, median, q3)
    for g in order:
        vals = sorted(by_group.get(g, []))
        if not vals:
            continue
        q1 = percentile(vals, 0.25)
        med = percentile(vals, 0.50)
        q3 = percentile(vals, 0.75)
        labels.append(g)
        stats.append((q1, med, q3))

    if not stats:
        raise SystemExit("No data to plot (check interestedIn field + min_words).")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.set_title("Percent of Words That Are Complex (by who they're looking for)", pad=12)
    ax.set_ylabel("Percent complex words")
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)

    # draw bars
    bar_width = 0.55
    for i, (q1, med, q3) in enumerate(stats, start=1):
        # IQR bar
        rect = Rectangle(
            (i - bar_width / 2, q1),
            bar_width,
            max(q3 - q1, 0.0001),
            alpha=0.6,
        )
        ax.add_patch(rect)

        # median line
        ax.plot([i - bar_width / 2, i + bar_width / 2], [med, med], linewidth=2)

        # median label
        ax.text(i, med + 0.05, f"{med:.0f}%", ha="center", va="bottom", fontsize=10)

    # give a little padding
    all_q = [q for triple in stats for q in triple]
    ymin = max(0.0, min(all_q) - 1.0)
    ymax = max(all_q) + 1.0
    ax.set_ylim(ymin, ymax)

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] kept profiles: {kept}")
    print(f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short} | no interestedIn(M/F): {skipped_no_interest}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")


if __name__ == "__main__":
    main()
