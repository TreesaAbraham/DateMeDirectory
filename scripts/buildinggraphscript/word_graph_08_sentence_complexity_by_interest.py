#!/usr/bin/env python3
"""
Box plot: Sentence complexity by who they're looking for.

Complex sentence rule:
- complex if sentence has > complex_min_words words (default: >15)

Metric per profile:
- percent_complex_sentences = (complex_sentences / total_sentences) * 100

Groups from interestedIn:
- Looking for Men (M only)
- Looking for Women (F only)
- Looking for Both (contains M and F)

Text source: profileDetails.fullText (fallbacks included)

Outputs:
- data/charts/word_graph_sentence_complexity_by_interest.png
- data/charts/word_graph_sentence_complexity_by_interest.svg
- data/charts/word_graph_sentence_complexity_by_interest_per_profile.csv
- data/charts/word_graph_sentence_complexity_by_interest_summary.csv
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
SENT_SPLIT_RE = re.compile(r"[.!?]+")  # simple, not perfect, but good enough for profiles


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
    Common shapes:
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
        if "," in s:
            return [t.strip().upper() for t in s.split(",") if t.strip()]
        if " " in s:
            return [t.strip().upper() for t in s.split() if t.strip()]
        return [ch for ch in s if ch.isalpha()]
    return []


def classify_interest(tokens: List[str]) -> Optional[str]:
    """
    Only care about M and F for grouping.
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


def split_sentences(text: str) -> List[str]:
    # Normalize whitespace
    t = " ".join(text.strip().split())
    if not t:
        return []
    parts = [s.strip() for s in SENT_SPLIT_RE.split(t)]
    # filter out empty fragments
    return [s for s in parts if s]


def sentence_word_count(sentence: str) -> int:
    return len(WORD_RE.findall(sentence))


def sentence_complexity_metrics(text: str, complex_min_words: int) -> Tuple[int, int, float, float]:
    """
    Returns:
      total_sentences, complex_sentences, percent_complex, avg_sentence_len
    Complex = sentence word count > complex_min_words
    """
    sents = split_sentences(text)
    if not sents:
        return 0, 0, 0.0, 0.0

    lengths = [sentence_word_count(s) for s in sents]
    # Remove "sentences" with zero words (rare but can happen)
    lengths = [n for n in lengths if n > 0]
    if not lengths:
        return 0, 0, 0.0, 0.0

    total = len(lengths)
    complex_ct = sum(1 for n in lengths if n > complex_min_words)
    pct_complex = (complex_ct / total) * 100.0
    avg_len = sum(lengths) / total
    return total, complex_ct, pct_complex, avg_len


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
    ap.add_argument("--min_words", type=int, default=80, help="Skip profiles with fewer than this many words")
    ap.add_argument("--min_sentences", type=int, default=3, help="Skip profiles with fewer than this many sentences")
    ap.add_argument(
        "--complex_min_words",
        type=int,
        default=15,
        help="A sentence is 'complex' if it has MORE than this many words (default: >15)",
    )
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

    per_profile_csv = outdir / "word_graph_sentence_complexity_by_interest_per_profile.csv"
    summary_csv = outdir / "word_graph_sentence_complexity_by_interest_summary.csv"
    out_png = outdir / "word_graph_sentence_complexity_by_interest.png"
    out_svg = outdir / "word_graph_sentence_complexity_by_interest.svg"

    order = [x.strip() for x in args.order.split(",") if x.strip()]
    by_group: Dict[str, List[float]] = {g: [] for g in order}

    kept = 0
    skipped_no_text = 0
    skipped_short = 0
    skipped_no_interest = 0
    skipped_few_sentences = 0

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "id",
            "interest_group",
            "word_count",
            "sentence_count",
            "complex_sentence_count",
            "percent_complex_sentences",
            "avg_sentence_len",
        ])

        for p in profiles:
            text = get_fulltext(p)
            if not text.strip():
                skipped_no_text += 1
                continue

            words = WORD_RE.findall(text)
            if len(words) < args.min_words:
                skipped_short += 1
                continue

            tokens = get_interested_in(p)
            group = classify_interest(tokens)
            if group is None:
                skipped_no_interest += 1
                continue

            sent_ct, complex_ct, pct_complex, avg_len = sentence_complexity_metrics(
                text, complex_min_words=args.complex_min_words
            )
            if sent_ct < args.min_sentences:
                skipped_few_sentences += 1
                continue

            if group not in by_group:
                by_group[group] = []
                order.append(group)

            by_group[group].append(pct_complex)
            w.writerow([
                p.get("id", ""),
                group,
                len(words),
                sent_ct,
                complex_ct,
                round(pct_complex, 3),
                round(avg_len, 3),
            ])
            kept += 1

    # Summary stats
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

    # Plot
    labels = []
    plot_data = []
    for g in order:
        vals = by_group.get(g, [])
        if vals:
            labels.append(g)
            plot_data.append(vals)

    if not plot_data:
        raise SystemExit("No data to plot. Check interestedIn and min_words/min_sentences thresholds.")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.boxplot(plot_data, labels=labels, showfliers=False)
    ax.set_title("Percent of Sentences That Are Complex (sentence length > 15 words)", pad=12)
    ax.set_ylabel("Percent complex sentences")

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] kept profiles: {kept}")
    print(
        f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short} | "
        f"no interestedIn(M/F): {skipped_no_interest} | <min_sentences: {skipped_few_sentences}"
    )
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")


if __name__ == "__main__":
    main()
