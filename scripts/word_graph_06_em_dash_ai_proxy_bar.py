#!/usr/bin/env python3
"""
Graph 6: "AI proxy" via em-dash usage (—) in profile text.

- Reads: data/profiles_master.json (list of profiles)
- Text: profileDetails.fullText (fallbacks included)
- Counts em dashes: the Unicode em dash character '—'
- Builds a bar chart of how many profiles fall into each em-dash count bucket

Buckets:
- 0, 1, 2, 3, 4, 5+

Outputs:
- data/charts/word_graph_06_em_dash_bar.png
- data/charts/word_graph_06_em_dash_bar.svg
- data/charts/word_graph_06_em_dash_per_profile.csv
- data/charts/word_graph_06_em_dash_bucket_counts.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt


EM_DASH = "—"


def get_fulltext(p: dict) -> str:
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def count_em_dashes(text: str) -> int:
    return text.count(EM_DASH)


def bucketize(n: int, cap: int = 5) -> str:
    """
    0..cap-1 are literal buckets, cap+ is grouped as 'cap+'
    """
    if n >= cap:
        return f"{cap}+"
    return str(n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--cap", type=int, default=5, help="Top bucket cap (default 5 => '5+')")
    ap.add_argument("--min_words", type=int, default=0, help="Optional: skip profiles with fewer than this many words")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_profile_csv = outdir / "word_graph_06_em_dash_per_profile.csv"
    bucket_csv = outdir / "word_graph_06_em_dash_bucket_counts.csv"
    out_png = outdir / "word_graph_06_em_dash_bar.png"
    out_svg = outdir / "word_graph_06_em_dash_bar.svg"

    # Simple word count (split-based) only if you use --min_words
    def word_count(text: str) -> int:
        return len(text.split())

    bucket_counts = Counter()
    total = 0
    skipped_no_text = 0
    skipped_short = 0

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "word_count", "em_dash_count", "bucket"])

        for p in profiles:
            text = get_fulltext(p)
            if not text.strip():
                skipped_no_text += 1
                continue

            wc = word_count(text)
            if wc < args.min_words:
                skipped_short += 1
                continue

            n = count_em_dashes(text)
            b = bucketize(n, cap=args.cap)

            bucket_counts[b] += 1
            total += 1

            w.writerow([p.get("id", ""), wc, n, b])

    # Ensure consistent bucket order: 0..cap-1 then cap+
    labels = [str(i) for i in range(args.cap)] + [f"{args.cap}+"]
    values = [bucket_counts.get(lbl, 0) for lbl in labels]

    with bucket_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "count", "percent"])
        for lbl, val in zip(labels, values):
            pct = (val / total * 100) if total else 0.0
            w.writerow([lbl, val, round(pct, 2)])

    # Plot
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(labels, values)
    ax.set_title('Em-dash "AI proxy" (—) usage in Date Me profiles', pad=12)
    ax.set_xlabel("Em dashes per profile (bucketed)")
    ax.set_ylabel("Number of profiles")

    # Add counts on top of bars (readability)
    for i, v in enumerate(values):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=10)

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] analyzed profiles: {total}")
    print(f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {bucket_csv}")


if __name__ == "__main__":
    main()
