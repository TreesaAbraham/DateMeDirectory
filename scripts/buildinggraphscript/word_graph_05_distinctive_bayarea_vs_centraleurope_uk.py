#!/usr/bin/env python3
"""
Most Distinctive Words: SF Bay Area vs UK + Central Europe (table figure)

- Reads: data/profiles_master.json
- Uses: p["location"] for Bay Area vs UK/Central Europe classification (heuristic)
- Text: profileDetails.fullText (fallbacks included)
- Distinctiveness: log-odds ratio with Dirichlet prior (z-scored)

Outputs:
- data/charts/word_graph_05_distinctive_bayarea_vs_centraleurope_uk.png
- data/charts/word_graph_05_distinctive_bayarea_vs_centraleurope_uk.svg
- data/charts/word_graph_05_distinctive_bayarea_vs_centraleurope_uk.csv
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

# Keep this similar to your US vs non-US script (small on purpose)
STOPWORDS = {
    "a","an","and","are","as","at","be","but","by","for","from","has","have","he","her","hers",
    "him","his","i","if","in","is","it","its","me","my","not","of","on","or","our","ours","she",
    "so","that","the","their","theirs","them","then","there","these","they","this","to","too",
    "us","was","we","were","what","when","where","which","who","why","with","you","your","yours",
    "im","i'm","ive","i've","dont","don't","cant","can't","just","really","like"
}


# --- Location heuristics ---

# Bay Area signals (string contains any of these -> BAY_AREA)
BAY_AREA_HINTS = {
    "san francisco", "bay area", "silicon valley",
    "oakland", "berkeley", "san jose", "sanjose",
    "palo alto", "menlo park", "mountain view", "sunnyvale", "cupertino",
    "fremont", "daly city", "redwood city", "san mateo", "santa clara",
    "milpitas", "pleasanton", "livermore", "walnut creek", "concord",
    "marin", "sausalito",
    "alameda county", "contra costa", "san mateo county", "santa clara county", "marin county",
}

# Regex to catch “SF” without matching random words
BAY_AREA_REGEX = [
    re.compile(r"\b(sf|s\.f\.)\b", re.IGNORECASE),
    re.compile(r"\bbay\s+area\b", re.IGNORECASE),
    re.compile(r"\bsilicon\s+valley\b", re.IGNORECASE),
]

# UK + Central Europe signals (string contains any of these -> EUROPE_UK)
EUROPE_UK_HINTS = {
    # UK / London
    "uk", "u.k.", "united kingdom", "great britain", "britain",
    "england", "scotland", "wales", "northern ireland",
    "london", "london uk",
    "manchester", "birmingham", "edinburgh", "glasgow", "bristol", "leeds", "liverpool",

    # Central Europe (and nearby commonly used)
    "germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt", "cologne", "köln",
    "austria", "vienna", "wien", "salzburg",
    "switzerland", "zurich", "zürich", "geneva", "basel",
    "poland", "warsaw", "krakow", "kraków", "wroclaw", "wrocław",
    "czech", "czech republic", "prague", "praha",
    "slovakia", "bratislava",
    "hungary", "budapest",
    "slovenia", "ljubljana",
    "croatia", "zagreb",

    # Optional “central-ish” extensions (leave in or remove based on your definition)
    "netherlands", "amsterdam", "rotterdam",
    "belgium", "brussels", "antwerp",
}

EUROPE_UK_REGEX = [
    re.compile(r"\b(uk|u\.k\.)\b", re.IGNORECASE),
    re.compile(r"\bunited\s+kingdom\b", re.IGNORECASE),
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
    out = []
    for w in words:
        if len(w) < min_len:
            continue
        if w in STOPWORDS:
            continue
        out.append(w)
    return out


def is_bay_area(loc: str) -> bool:
    low = loc.lower()
    if any(h in low for h in BAY_AREA_HINTS):
        return True
    return any(rx.search(loc) for rx in BAY_AREA_REGEX)


def is_europe_uk(loc: str) -> bool:
    low = loc.lower()
    if any(h in low for h in EUROPE_UK_HINTS):
        return True
    return any(rx.search(loc) for rx in EUROPE_UK_REGEX)


def classify_bayarea_vs_europe_uk(location: Optional[str]) -> Optional[str]:
    """
    STRICT classifier:
    Returns "BAY_AREA", "EUROPE_UK", or None (exclude).

    We ONLY want Bay Area vs UK/Central Europe. Everything else is ignored.
    """
    if not isinstance(location, str):
        return None
    s = location.strip()
    if not s:
        return None

    # If something weird matches both (rare), prefer Bay Area.
    if is_bay_area(s):
        return "BAY_AREA"
    if is_europe_uk(s):
        return "EUROPE_UK"
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

    fig, ax = plt.subplots(figsize=(8.5, 10))
    ax.axis("off")
    ax.set_title(title, fontsize=14, pad=12)

    tbl = ax.table(
        cellText=cell_text,
        colLabels=[col_a, col_b],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1, 1.35)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--top_n", type=int, default=20, help="Words per column")
    ap.add_argument("--min_word_len", type=int, default=3, help="Min token length")
    ap.add_argument("--min_total_count", type=int, default=5, help="Drop words with total count < this")
    ap.add_argument("--alpha", type=float, default=0.01, help="Prior strength multiplier")
    ap.add_argument("--location_field", default="location", help="Field containing location string")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    counts_bay = Counter()
    counts_eu = Counter()

    n_bay_docs = 0
    n_eu_docs = 0
    skipped_not_in_regions = 0
    skipped_no_text = 0

    for p in profiles:
        loc = p.get(args.location_field)
        group = classify_bayarea_vs_europe_uk(loc)
        if group is None:
            skipped_not_in_regions += 1
            continue

        text = get_fulltext(p)
        if not text.strip():
            skipped_no_text += 1
            continue

        tokens = tokenize(text, min_len=args.min_word_len)

        if group == "BAY_AREA":
            counts_bay.update(tokens)
            n_bay_docs += 1
        elif group == "EUROPE_UK":
            counts_eu.update(tokens)
            n_eu_docs += 1

    if n_bay_docs == 0 or n_eu_docs == 0:
        raise SystemExit(
            f"Not enough classified profiles. BAY_AREA={n_bay_docs}, EUROPE_UK={n_eu_docs}. "
            f"(Adjust BAY_AREA_HINTS / EUROPE_UK_HINTS to match your location strings.)"
        )

    prior = counts_bay + counts_eu
    z = log_odds_zscores(counts_bay, counts_eu, prior=prior, alpha=args.alpha)

    def total_count(w: str) -> int:
        return counts_bay.get(w, 0) + counts_eu.get(w, 0)

    items = [(w, score) for w, score in z.items() if total_count(w) >= args.min_total_count]
    if not items:
        raise SystemExit("No words left after filtering. Lower --min_total_count.")

    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    top_bay = [w for w, _ in items_sorted[: args.top_n]]

    items_sorted_eu = sorted(items, key=lambda x: x[1])  # ascending => distinctive for EUROPE_UK
    top_eu = [w for w, _ in items_sorted_eu[: args.top_n]]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_png = outdir / "word_graph_05_distinctive_bayarea_vs_centraleurope_uk.png"
    out_svg = outdir / "word_graph_05_distinctive_bayarea_vs_centraleurope_uk.svg"
    out_csv = outdir / "word_graph_05_distinctive_bayarea_vs_centraleurope_uk.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "BAY_AREA_word", "BAY_AREA_z", "EUROPE_UK_word", "EUROPE_UK_z"])
        for i in range(args.top_n):
            wb = top_bay[i] if i < len(top_bay) else ""
            we = top_eu[i] if i < len(top_eu) else ""
            w.writerow([
                i + 1,
                wb,
                round(z.get(wb, 0.0), 4) if wb else "",
                we,
                round(z.get(we, 0.0), 4) if we else "",
            ])

    title = "Most Distinctive Words: SF Bay Area vs UK + Central Europe (Date Me Docs)"
    render_table(
        out_png=out_png,
        out_svg=out_svg,
        title=title,
        col_a="SF BAY AREA",
        col_b="UK + CENTRAL EUROPE",
        words_a=top_bay,
        words_b=top_eu,
    )

    print(f"[done] BAY_AREA_docs={n_bay_docs} | EUROPE_UK_docs={n_eu_docs}")
    print(f"[skipped] not in these regions: {skipped_not_in_regions} | no text: {skipped_no_text}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {out_csv}")


if __name__ == "__main__":
    main()
