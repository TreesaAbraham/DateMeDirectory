#!/usr/bin/env python3
"""
Word Graph 09 — Word-set prevalence: Bay-vs-UK distinctive words compared to ALL US.

Inputs:
- data/profiles_master.json
- data/charts/word_graph_05_distinctive_bayarea_vs_uk_london.csv  (created by your word_graph_05 script)

Outputs:
- data/charts/word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.png
- data/charts/word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.svg
- data/charts/word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.csv

What it measures:
- For the BAY word set (top N words distinctive for Bay): rate per 10k tokens in
    - All US profiles
    - Bay Area profiles
    - UK/London profiles
- For the UK word set (top N words distinctive for UK): same rates
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

import matplotlib.pyplot as plt


WORD_RE = re.compile(r"\b[a-zA-Z']+\b")

STOPWORDS = {
    "a","an","and","are","as","at","be","but","by","for","from","has","have","he","her","hers",
    "him","his","i","if","in","is","it","its","me","my","not","of","on","or","our","ours","she",
    "so","that","the","their","theirs","them","then","there","these","they","this","to","too",
    "us","was","we","were","what","when","where","which","who","why","with","you","your","yours",
    "im","i'm","ive","i've","dont","don't","cant","can't","just","really","like"
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

BAY_AREA_HINTS = {
    "san francisco", "bay area", "silicon valley",
    "oakland", "berkeley", "san jose", "sanjose",
    "palo alto", "menlo park", "mountain view", "sunnyvale", "cupertino",
    "fremont", "daly city", "redwood city", "san mateo", "santa clara",
    "milpitas", "pleasanton", "livermore", "walnut creek", "concord",
    "marin", "sausalito",
    "alameda county", "contra costa", "san mateo county", "santa clara county", "marin county",
}

BAY_AREA_REGEX = [
    re.compile(r"\b(sf|s\.f\.)\b", re.IGNORECASE),
    re.compile(r"\bbay\s+area\b", re.IGNORECASE),
    re.compile(r"\bsilicon\s+valley\b", re.IGNORECASE),
]

UK_HINTS = {
    "uk", "u.k.", "united kingdom", "great britain", "britain",
    "england", "scotland", "wales", "northern ireland",
    "london", "london uk",
}

UK_REGEX = [
    re.compile(r"\b(uk|u\.k\.)\b", re.IGNORECASE),
    re.compile(r"\bunited\s+kingdom\b", re.IGNORECASE),
    re.compile(r"\bgreat\s+britain\b", re.IGNORECASE),
    re.compile(r"\bbritain\b", re.IGNORECASE),
    re.compile(r"\blondon\b", re.IGNORECASE),
]


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


def classify_us(location: Optional[str]) -> bool:
    if not isinstance(location, str):
        return False
    s = location.strip()
    if not s:
        return False
    low = s.lower()

    if re.search(r"\b(usa|u\.s\.a\.|u\.s\.|united states|america)\b", low):
        return True
    if re.search(r"\b\d{5}(-\d{4})?\b", s):
        return True

    m = re.search(r"(?:,|\s)\s*([A-Z]{2})\b", s)
    if m and m.group(1).upper() in US_STATE_ABBRS:
        return True

    for st in US_STATE_NAMES:
        if st in low:
            return True

    return False


def is_bay_area(loc: str) -> bool:
    low = loc.lower()
    if any(h in low for h in BAY_AREA_HINTS):
        return True
    return any(rx.search(loc) for rx in BAY_AREA_REGEX)


def is_uk(loc: str) -> bool:
    low = loc.lower()
    if any(h in low for h in UK_HINTS):
        return True
    return any(rx.search(loc) for rx in UK_REGEX)


def load_word_sets(csv_path: Path, top_n: int) -> Tuple[List[str], List[str]]:
    bay: List[str] = []
    uk: List[str] = []
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if len(bay) < top_n:
                w = (row.get("BAY_AREA_word") or "").strip().lower()
                if w:
                    bay.append(w)
            if len(uk) < top_n:
                w = (row.get("UK_word") or "").strip().lower()
                if w:
                    uk.append(w)
            if len(bay) >= top_n and len(uk) >= top_n:
                break
    return bay, uk


def rate_per_10k(word_hits: int, total_tokens: int) -> float:
    if total_tokens <= 0:
        return 0.0
    return (word_hits / total_tokens) * 10_000.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json")
    ap.add_argument(
        "--wordset_csv",
        type=Path,
        default=Path("data/charts/word_graph_05_distinctive_bayarea_vs_uk_london.csv"),
        help="CSV produced by word_graph_05 (Bay vs UK/London)",
    )
    ap.add_argument("--top_n", type=int, default=20, help="How many top distinctive words per set")
    ap.add_argument("--min_word_len", type=int, default=6, help="Min token length (default: 6)")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--location_field", default="location", help="Field containing location string")
    args = ap.parse_args()

    if not args.wordset_csv.exists():
        raise SystemExit(f"Missing wordset CSV: {args.wordset_csv} (run word_graph_05 first)")

    bay_words, uk_words = load_word_sets(args.wordset_csv, top_n=args.top_n)
    bay_set: Set[str] = set(bay_words)
    uk_set: Set[str] = set(uk_words)

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    group_tokens = {"ALL_US": 0, "BAY_AREA": 0, "UK_LONDON": 0}
    group_counts_bayset = {"ALL_US": 0, "BAY_AREA": 0, "UK_LONDON": 0}
    group_counts_ukset = {"ALL_US": 0, "BAY_AREA": 0, "UK_LONDON": 0}
    docs = {"ALL_US": 0, "BAY_AREA": 0, "UK_LONDON": 0}

    skipped_no_text = 0
    skipped_no_loc = 0

    for p in profiles:
        loc = p.get(args.location_field)
        if not isinstance(loc, str) or not loc.strip():
            skipped_no_loc += 1
            continue

        text = get_fulltext(p)
        if not text.strip():
            skipped_no_text += 1
            continue

        tokens = tokenize(text, min_len=args.min_word_len)
        if not tokens:
            continue

        tok_count = len(tokens)

        in_us = classify_us(loc)
        in_bay = is_bay_area(loc)
        in_uk = is_uk(loc)

        # ALL US bucket
        if in_us:
            group_tokens["ALL_US"] += tok_count
            docs["ALL_US"] += 1
            for t in tokens:
                if t in bay_set:
                    group_counts_bayset["ALL_US"] += 1
                if t in uk_set:
                    group_counts_ukset["ALL_US"] += 1

        # BAY bucket
        if in_bay:
            group_tokens["BAY_AREA"] += tok_count
            docs["BAY_AREA"] += 1
            for t in tokens:
                if t in bay_set:
                    group_counts_bayset["BAY_AREA"] += 1
                if t in uk_set:
                    group_counts_ukset["BAY_AREA"] += 1

        # UK bucket
        if in_uk:
            group_tokens["UK_LONDON"] += tok_count
            docs["UK_LONDON"] += 1
            for t in tokens:
                if t in bay_set:
                    group_counts_bayset["UK_LONDON"] += 1
                if t in uk_set:
                    group_counts_ukset["UK_LONDON"] += 1

    rows = []
    for g in ["ALL_US", "BAY_AREA", "UK_LONDON"]:
        bay_rate = rate_per_10k(group_counts_bayset[g], group_tokens[g])
        uk_rate = rate_per_10k(group_counts_ukset[g], group_tokens[g])
        rows.append((g, docs[g], group_tokens[g], bay_rate, uk_rate))

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_csv = outdir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.csv"
    out_png = outdir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.png"
    out_svg = outdir / "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.svg"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "docs", "total_tokens", "bay_wordset_rate_per_10k", "uk_wordset_rate_per_10k"])
        for g, d, toks, bay_rate, uk_rate in rows:
            w.writerow([g, d, toks, round(bay_rate, 4), round(uk_rate, 4)])

    groups = [r[0] for r in rows]
    bay_rates = [r[3] for r in rows]
    uk_rates = [r[4] for r in rows]

    x = list(range(len(groups)))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.bar([i - width/2 for i in x], bay_rates, width=width, label=f"Bay word set (top {args.top_n})")
    ax.bar([i + width/2 for i in x], uk_rates, width=width, label=f"UK word set (top {args.top_n})")

    ax.set_xticks(x)
    ax.set_xticklabels(["ALL US", "SF BAY", "UK/LONDON"])
    ax.set_ylabel("Occurrences per 10,000 tokens")
    ax.set_title("Word Graph 09: Bay/UK distinctive word sets vs ALL US")
    ax.legend()

    for i, v in enumerate(bay_rates):
        ax.text(i - width/2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    for i, v in enumerate(uk_rates):
        ax.text(i + width/2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

    fig.savefig(out_png, dpi=250, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print("[done] wrote:")
    print(f"  {out_png}")
    print(f"  {out_svg}")
    print(f"  {out_csv}")
    print(f"[info] docs: ALL_US={docs['ALL_US']} | BAY_AREA={docs['BAY_AREA']} | UK_LONDON={docs['UK_LONDON']}")
    print(f"[skipped] no location: {skipped_no_loc} | no text: {skipped_no_text}")


if __name__ == "__main__":
    main()
