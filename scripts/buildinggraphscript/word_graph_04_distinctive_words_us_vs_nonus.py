#!/usr/bin/env python3
"""
Most Distinctive Words: US vs Non-US (table figure)

- Reads: data/profiles_master.json
- Uses: p["location"] for US vs Non-US classification (heuristic)
- Text: profileDetails.fullText (fallbacks included)
- Distinctiveness: log-odds ratio with Dirichlet prior (z-scored)

Outputs:
- data/charts/word_graph_04_distinctive_us_vs_nonus.png
- data/charts/word_graph_04_distinctive_us_vs_nonus.svg
- data/charts/word_graph_04_distinctive_us_vs_nonus.csv

Change:
- Distinctive candidate words must be >= 6 letters (default).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt


# Tokenizer: letters + apostrophes
WORD_RE = re.compile(r"\b[a-zA-Z']+\b")

# A practical stopword list (small on purpose, tweak if needed)
STOPWORDS = {
    "a","an","and","are","as","at","be","but","by","for","from","has","have","he","her","hers",
    "him","his","i","if","in","is","it","its","me","my","not","of","on","or","our","ours","she",
    "so","that","the","their","theirs","them","then","there","these","they","this","to","too",
    "us","was","we","were","what","when","where","which","who","why","with","you","your","yours",
    "im","i'm","ive","i've","dont","don't","cant","can't","just","really","like","because","people","making","arounds","things", "create", "content", "generally", "around", 
}

US_STATE_ABBRS = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME",
    "MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA",
    "RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
}

US_STATE_NAMES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware","florida",
    "georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky","louisiana","maine",
    "maryland","massachusetts","michigan","minnesota","mississippi","missouri","montana","nebraska",
    "nevada","new hampshire","new jersey","new mexico","new york","north carolina","north dakota",
    "ohio","oklahoma","oregon","pennsylvania","rhode island","south carolina","south dakota","tennessee",
    "texas","utah","vermont","virginia","washington","west virginia","wisconsin","wyoming","district of columbia"
}

# Common explicit non-US signals (not exhaustive; add more if your data needs it)
NONUS_HINTS = {
    "canada","uk","u.k.","united kingdom","england","scotland","wales","ireland","australia","new zealand",
    "india","pakistan","bangladesh","singapore","malaysia","philippines","indonesia","japan","korea","china",
    "taiwan","hong kong","mexico","brazil","argentina","chile","peru","colombia","venezuela",
    "france","germany","italy","spain","portugal","netherlands","belgium","sweden","norway","denmark","finland",
    "switzerland","austria","poland","czech","slovakia","hungary","romania","bulgaria","greece","turkey",
    "russia","ukraine","israel","saudi","uae","dubai","qatar","egypt","south africa","nigeria","kenya"
}


def get_fulltext(p: dict) -> str:
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def tokenize(text: str, min_len: int) -> List[str]:
    words = [w.lower() for w in WORD_RE.findall(text)]
    out: List[str] = []
    for w in words:
        if len(w) < min_len:
            continue
        if w in STOPWORDS:
            continue
        out.append(w)
    return out


def classify_us_vs_nonus(location: Optional[str]) -> Optional[str]:
    """
    Heuristic classifier:
    Returns "US", "NON_US", or None (unknown/ambiguous).

    US if:
    - explicit US indicators (USA, United States, U.S., etc.)
    - contains US ZIP code pattern
    - ends with or contains a US state abbreviation (e.g., "Columbia, SC")
    - contains a US state full name

    Non-US if:
    - contains explicit non-US country hints (Canada, UK, etc.)

    Otherwise: None
    """
    if not isinstance(location, str):
        return None
    s = location.strip()
    if not s:
        return None

    low = s.lower()

    # Explicit US indicators
    if re.search(r"\b(usa|u\.s\.a\.|u\.s\.|us|united states|america)\b", low):
        return "US"

    # ZIP code (5-digit or 5+4)
    if re.search(r"\b\d{5}(-\d{4})?\b", s):
        return "US"

    # State abbreviation like ", SC" or " SC"
    m = re.search(r"(?:,|\s)\s*([A-Z]{2})\b", s)
    if m:
        ab = m.group(1).upper()
        if ab in US_STATE_ABBRS:
            return "US"

    # Full state name
    for st in US_STATE_NAMES:
        if st in low:
            return "US"

    # Non-US hints
    for hint in NONUS_HINTS:
        if hint in low:
            return "NON_US"

    return None


def log_odds_zscores(
    counts_a: Counter,
    counts_b: Counter,
    prior: Counter,
    alpha: float,
) -> Dict[str, float]:
    """
    z-scored log-odds ratio with informative Dirichlet prior.
    Positive => distinctive for A; Negative => distinctive for B.
    """
    n_a = sum(counts_a.values())
    n_b = sum(counts_b.values())
    n_0 = sum(prior.values())

    z: Dict[str, float] = {}
    vocab = set(counts_a.keys()) | set(counts_b.keys()) | set(prior.keys())

    for w in vocab:
        a_w = counts_a.get(w, 0)
        b_w = counts_b.get(w, 0)
        p_w = prior.get(w, 0)

        a = a_w + alpha * p_w
        b = b_w + alpha * p_w
        a_d = (n_a - a_w) + alpha * (n_0 - p_w)
        b_d = (n_b - b_w) + alpha * (n_0 - p_w)

        if a <= 0 or b <= 0 or a_d <= 0 or b_d <= 0:
            continue

        logodds = math.log(a / a_d) - math.log(b / b_d)
        var = (1 / a) + (1 / b)
        z[w] = logodds / math.sqrt(var)

    return z


def render_table(
    out_png: Path,
    out_svg: Path,
    title: str,
    col_a: str,
    col_b: str,
    words_a: List[str],
    words_b: List[str],
) -> None:
    rows = max(len(words_a), len(words_b))

    cell_text = []
    for i in range(rows):
        cell_text.append([
            words_a[i] if i < len(words_a) else "",
            words_b[i] if i < len(words_b) else "",
        ])

    # Bigger canvas = bigger cells (most important change)
    # Width/height are inches. Increase height for more row spacing.
    fig_w = 10.5
    fig_h = max(12, rows * 0.75)  # scales with number of rows
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.axis("off")
    ax.set_title(title, fontsize=16, pad=18)

    tbl = ax.table(
        cellText=cell_text,
        colLabels=[col_a, col_b],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )

    # Font settings
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)  # try 11–13 if you want

    # Increase row height (second number) and slightly widen columns (first number)
    # This is the “make boxes bigger” knob.
    tbl.scale(1.15, 2.0)

    # Optional: add a little padding inside each cell so text isn't glued to borders
    for (_, _), cell in tbl.get_celld().items():
        cell.PAD = 0.15

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=250, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--top_n", type=int, default=20, help="Words per column")

    # CHANGE: default now 6 (but still overridable from CLI)
    ap.add_argument("--min_word_len", type=int, default=6, help="Min token length (default: 6)")

    ap.add_argument("--min_total_count", type=int, default=5, help="Drop words with total count < this")
    ap.add_argument("--alpha", type=float, default=0.01, help="Prior strength multiplier")
    ap.add_argument("--location_field", default="location", help="Field containing location string")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    counts_us = Counter()
    counts_non = Counter()

    n_us_docs = 0
    n_non_docs = 0
    skipped_unknown_loc = 0
    skipped_no_text = 0

    for p in profiles:
        loc = p.get(args.location_field)
        group = classify_us_vs_nonus(loc)
        if group is None:
            skipped_unknown_loc += 1
            continue

        text = get_fulltext(p)
        if not text.strip():
            skipped_no_text += 1
            continue

        tokens = tokenize(text, min_len=args.min_word_len)

        if group == "US":
            counts_us.update(tokens)
            n_us_docs += 1
        elif group == "NON_US":
            counts_non.update(tokens)
            n_non_docs += 1

    if n_us_docs == 0 or n_non_docs == 0:
        raise SystemExit(
            f"Not enough classified profiles. US={n_us_docs}, NON_US={n_non_docs}. "
            f"(Most likely locations are too messy; broaden NONUS_HINTS or adjust classifier.)"
        )

    prior = counts_us + counts_non
    z = log_odds_zscores(counts_us, counts_non, prior=prior, alpha=args.alpha)

    def total_count(w: str) -> int:
        return counts_us.get(w, 0) + counts_non.get(w, 0)

    # ALSO enforce min length here (extra safety)
    items = [
        (w, score)
        for w, score in z.items()
        if total_count(w) >= args.min_total_count and len(w) >= args.min_word_len
    ]
    if not items:
        raise SystemExit("No words left after filtering. Lower --min_total_count or --min_word_len.")

    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    top_us_words = [w for w, _ in items_sorted[: args.top_n]]

    items_sorted_non = sorted(items, key=lambda x: x[1])  # ascending => distinctive for NON_US
    top_non_words = [w for w, _ in items_sorted_non[: args.top_n]]

    # Display strings that include raw occurrence counts in that group
    # (These are token counts across the whole corpus for that group.)
    top_us = [f"{w} ({counts_us.get(w, 0)})" for w in top_us_words]
    top_non = [f"{w} ({counts_non.get(w, 0)})" for w in top_non_words]


    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_png = outdir / "word_graph_04_distinctive_us_vs_nonus.png"
    out_svg = outdir / "word_graph_04_distinctive_us_vs_nonus.svg"
    out_csv = outdir / "word_graph_04_distinctive_us_vs_nonus.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["rank", "US_word", "US_count", "US_z", "NON_US_word", "NON_US_count", "NON_US_z"])
        for i in range(args.top_n):
            wu = top_us_words[i] if i < len(top_us_words) else ""
            wn = top_non_words[i] if i < len(top_non_words) else ""

            wr.writerow([
            i + 1,
            wu,
            counts_us.get(wu, 0) if wu else "",
            round(z.get(wu, 0.0), 4) if wu else "",
            wn,
            counts_non.get(wn, 0) if wn else "",
            round(z.get(wn, 0.0), 4) if wn else "",
        ])


    title = "Most Distinctive Words (>=6 letters): United States vs Non-US (Date Me Docs)"
    render_table(
        out_png=out_png,
        out_svg=out_svg,
        title=title,
        col_a="UNITED STATES",
        col_b="NON-US",
        words_a=top_us,
        words_b=top_non,
    )

    print(f"[done] US_docs={n_us_docs} | NON_US_docs={n_non_docs} | min_word_len={args.min_word_len}")
    print(f"[skipped] unknown/ambiguous location: {skipped_unknown_loc} | no text: {skipped_no_text}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {out_csv}")


if __name__ == "__main__":
    main()
