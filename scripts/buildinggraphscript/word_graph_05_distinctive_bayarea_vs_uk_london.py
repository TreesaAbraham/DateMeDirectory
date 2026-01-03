#!/usr/bin/env python3
"""
Most Distinctive Words: SF Bay Area vs UK (incl. London) (table figure)

- Reads: data/profiles_master.json
- Uses: p["location"] for Bay Area vs UK/London classification (heuristic)
- Text: profileDetails.fullText (fallbacks included)
- Distinctiveness: log-odds ratio with Dirichlet prior (z-scored)

Outputs:
- data/charts/word_graph_05_distinctive_bayarea_vs_uk_london.png
- data/charts/word_graph_05_distinctive_bayarea_vs_uk_london.svg
- data/charts/word_graph_05_distinctive_bayarea_vs_uk_london.csv

Changes:
- UK group is ONLY UK/London (no Central Europe)
- Default min word length is 6 (still overridable)
- Graph shows counts inline: "word (21)"
- Table layout is scaled to be legible
- CSV includes counts
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


WORD_RE = re.compile(r"\b[a-zA-Z']+\b")

STOPWORDS = {
    "a","an","and","are","as","at","be","but","by","for","from","has","have","he","her","hers",
    "him","his","i","if","in","is","it","its","me","my","not","of","on","or","our","ours","she",
    "so","that","the","their","theirs","them","then","there","these","they","this","to","too",
    "us","was","we","were","what","when","where","which","who","why","with","you","your","yours",
    "im","i'm","ive","i've","dont","don't","cant","can't","just","really","like"
}

# --- Location heuristics ---

# Bay Area signals
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

# UK/London only
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


def classify_bayarea_vs_uk(location: Optional[str]) -> Optional[str]:
    """
    STRICT classifier: only Bay Area vs UK/London, everything else excluded.
    """
    if not isinstance(location, str):
        return None
    s = location.strip()
    if not s:
        return None

    if is_bay_area(s):
        return "BAY_AREA"
    if is_uk(s):
        return "UK"
    return None


def log_odds_zscores(
    counts_a: Counter,
    counts_b: Counter,
    prior: Counter,
    alpha: float,
) -> Dict[str, float]:
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

    fig_w = 11
    fig_h = max(12, rows * 0.6)
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

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    tbl.scale(1.15, 1.7)

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
    ap.add_argument("--min_word_len", type=int, default=6, help="Min token length (default: 6)")
    ap.add_argument("--min_total_count", type=int, default=5, help="Drop words with total count < this")
    ap.add_argument("--alpha", type=float, default=0.01, help="Prior strength multiplier")
    ap.add_argument("--location_field", default="location", help="Field containing location string")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    counts_bay = Counter()
    counts_uk = Counter()

    n_bay_docs = 0
    n_uk_docs = 0
    skipped_not_in_regions = 0
    skipped_no_text = 0

    for p in profiles:
        loc = p.get(args.location_field)
        group = classify_bayarea_vs_uk(loc)
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
        elif group == "UK":
            counts_uk.update(tokens)
            n_uk_docs += 1

    if n_bay_docs == 0 or n_uk_docs == 0:
        raise SystemExit(
            f"Not enough classified profiles. BAY_AREA={n_bay_docs}, UK={n_uk_docs}. "
            f"(Adjust BAY_AREA_HINTS / UK_HINTS to match your location strings.)"
        )

    prior = counts_bay + counts_uk
    z = log_odds_zscores(counts_bay, counts_uk, prior=prior, alpha=args.alpha)

    def total_count(w: str) -> int:
        return counts_bay.get(w, 0) + counts_uk.get(w, 0)

    items = [
        (w, score)
        for w, score in z.items()
        if total_count(w) >= args.min_total_count and len(w) >= args.min_word_len
    ]
    if not items:
        raise SystemExit("No words left after filtering. Lower --min_total_count or --min_word_len.")

    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    top_bay_words = [w for w, _ in items_sorted[: args.top_n]]

    items_sorted_uk = sorted(items, key=lambda x: x[1])  # ascending => distinctive for UK
    top_uk_words = [w for w, _ in items_sorted_uk[: args.top_n]]

    # Inline counts: "word (21)"
    top_bay = [f"{w} ({counts_bay.get(w, 0)})" for w in top_bay_words]
    top_uk = [f"{w} ({counts_uk.get(w, 0)})" for w in top_uk_words]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    out_png = outdir / "word_graph_05_distinctive_bayarea_vs_uk_london.png"
    out_svg = outdir / "word_graph_05_distinctive_bayarea_vs_uk_london.svg"
    out_csv = outdir / "word_graph_05_distinctive_bayarea_vs_uk_london.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["rank", "BAY_AREA_word", "BAY_AREA_count", "BAY_AREA_z", "UK_word", "UK_count", "UK_z"])
        for i in range(args.top_n):
            wb = top_bay_words[i] if i < len(top_bay_words) else ""
            wk = top_uk_words[i] if i < len(top_uk_words) else ""
            wr.writerow([
                i + 1,
                wb,
                counts_bay.get(wb, 0) if wb else "",
                round(z.get(wb, 0.0), 4) if wb else "",
                wk,
                counts_uk.get(wk, 0) if wk else "",
                round(z.get(wk, 0.0), 4) if wk else "",
            ])

    title = f"Most Distinctive Words (>= {args.min_word_len} letters): SF Bay Area vs UK/London (Date Me Docs)"
    render_table(
        out_png=out_png,
        out_svg=out_svg,
        title=title,
        col_a="SF BAY AREA",
        col_b="UK / LONDON",
        words_a=top_bay,
        words_b=top_uk,
    )

    print(f"[done] BAY_AREA_docs={n_bay_docs} | UK_docs={n_uk_docs} | min_word_len={args.min_word_len}")
    print(f"[skipped] not in these regions: {skipped_not_in_regions} | no text: {skipped_no_text}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {out_csv}")


if __name__ == "__main__":
    main()
