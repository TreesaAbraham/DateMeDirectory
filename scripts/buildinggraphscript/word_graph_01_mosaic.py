#!/usr/bin/env python3
# scripts/buildinggraphscript/word_graph_01_mosaic.py
"""
Graph 1: Mosaic plot (2x2)
Rows: Male vs Female
Cols: Uses "serious relationship" language bucket vs Does not

Upgrades:
- Adds a right-side table defining what "serious language" means (bucket terms + rules)
- Avoids label overlap by using a two-panel layout (mosaic + table)
- Handles negation so phrases like "not looking for a serious relationship" don't count as "serious"
  (counts ONLY non-negated bucket hits within sentence context)
- Places column labels in a reserved header band above the mosaic (no overlap)
- Wraps rule text so it stays readable

Text source: profileDetails.fullText (with fallbacks)
Input: data/profiles_master.json (list of profile dicts)

Outputs:
- data/charts/word_graph_01_mosaic_serious_relationship.png
- data/charts/word_graph_01_mosaic_serious_relationship.svg
- data/charts/word_graph_01_mosaic_serious_relationship.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import textwrap
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# -------- Sentence splitting + negation handling --------

SENT_SPLIT_RE = re.compile(r"[.!?]+\s+|\n+")
WORD_TOKEN_RE = re.compile(r"\b[\w']+\b", flags=re.UNICODE)

NEGATION_WORD_RE = re.compile(
    r"\b("
    r"no|not|never|without|hardly|rarely|none|neither|nor|"
    r"don't|dont|doesn't|doesnt|didn't|didnt|won't|wont|"
    r"can't|cant|cannot|isn't|isnt|aren't|arent|ain't|aint"
    r")\b",
    flags=re.IGNORECASE,
)


def split_sentences(text: str) -> List[str]:
    parts = SENT_SPLIT_RE.split(text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def count_non_negated_hits(text: str, bucket_re: re.Pattern, neg_window_words: int) -> int:
    """
    Count bucket matches that are NOT negated.

    For each bucket match, look in the same sentence.
    If a negation word occurs within `neg_window_words` tokens BEFORE the match,
    treat it as negated and ignore it.

    Examples ignored:
      - "not looking for a serious relationship"
      - "don't want marriage"
      - "no kids"
    """
    hits = 0
    for sent in split_sentences(text):
        if not sent:
            continue

        # Tokenize sentence with positions
        tokens = []
        for m in WORD_TOKEN_RE.finditer(sent):
            tokens.append((m.group(0).lower(), m.start(), m.end()))

        if not tokens:
            continue

        # Negation token indices
        neg_idxs = set()
        for i, (tok, _, _) in enumerate(tokens):
            if NEGATION_WORD_RE.fullmatch(tok):
                neg_idxs.add(i)

        # If no negations, count all matches quickly
        if not neg_idxs:
            hits += len(bucket_re.findall(sent))
            continue

        # Otherwise, inspect each match
        for match in bucket_re.finditer(sent):
            m_start = match.start()

            # Find the first token whose span includes or follows the match start
            match_tok_i = None
            for i, (_, t_start, t_end) in enumerate(tokens):
                if t_start <= m_start < t_end:
                    match_tok_i = i
                    break
                if t_start > m_start:
                    match_tok_i = i
                    break

            if match_tok_i is None:
                continue

            lo = max(0, match_tok_i - neg_window_words)
            negated = any(i in neg_idxs for i in range(lo, match_tok_i))

            if not negated:
                hits += 1

    return hits


# -------- Data extraction --------

def get_fulltext(p: dict) -> str:
    """
    Robustly pull full text from common shapes:
    - p["profileDetails"]["fullText"] (expected)
    - p["profileDetails"]["full_text"]
    - p["profileDetails"]["fulltext"]
    - p["profileDetails"]["text"] / ["body"] (fallbacks)
    - p["fullText"] (last resort)
    """
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def canonical_gender(raw) -> str:
    """
    Normalize your gender field into canonical labels.
    Handles common inputs like 'M', 'F', 'male', 'female'.
    """
    if not isinstance(raw, str):
        return "Other"
    s = raw.strip().upper()
    if s in {"M", "MALE", "MAN"}:
        return "Male"
    if s in {"F", "FEMALE", "WOMAN"}:
        return "Female"
    return "Other"


# -------- Bucket regex --------

def compile_bucket_regex(bucket_terms: List[str]) -> re.Pattern:
    """
    Build a regex that matches any term with word boundaries.
    Supports multi-word phrases too (spaces become \\s+).
    """
    cleaned = []
    for t in bucket_terms:
        t = t.strip().lower()
        if not t:
            continue
        escaped = re.escape(t).replace(r"\ ", r"\s+")
        cleaned.append(escaped)

    if not cleaned:
        raise SystemExit("Bucket is empty. Add terms with --bucket.")

    pat = r"\b(" + "|".join(cleaned) + r")\b"
    return re.compile(pat, flags=re.IGNORECASE)


# -------- Contingency table --------

def build_contingency(
    profiles: List[dict],
    bucket_re: re.Pattern,
    allowed_rows: List[str],
    min_hits: int,
    neg_window_words: int,
) -> Tuple[List[str], List[str], Dict[Tuple[str, str], int], int]:
    """
    Columns are always: ["Uses bucket", "Does not use bucket"]
    Returns: rows, cols, counts[(row,col)], total
    """
    rows = allowed_rows
    cols = ["Uses bucket", "Does not use bucket"]
    counts: Dict[Tuple[str, str], int] = {(r, c): 0 for r in rows for c in cols}
    total = 0

    for p in profiles:
        row = canonical_gender(p.get("gender", ""))
        if row not in rows:
            continue

        text = get_fulltext(p)
        if not text.strip():
            continue

        # Negation-aware hit counting
        hits = count_non_negated_hits(text, bucket_re, neg_window_words=neg_window_words)

        has = hits >= min_hits
        col = cols[0] if has else cols[1]
        counts[(row, col)] += 1
        total += 1

    return rows, cols, counts, total


# -------- Output helpers --------

def save_csv(out_csv: Path, rows: List[str], cols: List[str], counts: Dict[Tuple[str, str], int]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["row", "col", "count"])
        for r in rows:
            for c in cols:
                w.writerow([r, c, counts[(r, c)]])


def _chunk_terms(terms: List[str], per_row: int = 2) -> List[List[str]]:
    terms = [t.strip() for t in terms if t.strip()]
    rows = []
    for i in range(0, len(terms), per_row):
        rows.append(terms[i : i + per_row])
    return rows


def _draw_definition_table(ax_tbl, bucket_terms: List[str], min_hits: int, neg_window_words: int) -> None:
    ax_tbl.axis("off")

    ax_tbl.text(
        0.0,
        1.0,
        "Definition",
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        transform=ax_tbl.transAxes,
    )

    rule1 = f'Counts as "Uses bucket" if ≥ {min_hits} non-negated match(es).'
    rule2 = (
        f"Negation rule: ignore matches if a negation appears within "
        f"{neg_window_words} words before the term."
    )

    wrapped = textwrap.fill(rule1, width=48) + "\n" + textwrap.fill(rule2, width=48)

    ax_tbl.text(
        0.0,
        0.93,
        wrapped,
        ha="left",
        va="top",
        fontsize=9.5,
        transform=ax_tbl.transAxes,
        linespacing=1.25,
    )

    term_rows = _chunk_terms(bucket_terms, per_row=2)
    cell_text = []
    for row in term_rows:
        if len(row) == 1:
            cell_text.append([row[0], ""])
        else:
            cell_text.append([row[0], row[1]])

    tbl = ax_tbl.table(
        cellText=cell_text,
        colLabels=["Serious terms", ""],
        colLoc="left",
        cellLoc="left",
        loc="upper left",
        bbox=[0.0, 0.00, 1.0, 0.72],  # lowered + shortened to avoid collisions with rule text
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.5)
    for (_, _), cell in tbl.get_celld().items():
        cell.PAD = 0.12


def draw_mosaic(
    out_png: Path,
    out_svg: Path,
    title: str,
    rows: List[str],
    cols: List[str],
    counts: Dict[Tuple[str, str], int],
    total: int,
    bucket_terms: List[str],
    min_hits: int,
    neg_window_words: int,
) -> None:
    """
    Mosaic with right-side definition table and anti-overlap layout tweaks.
    """
    if total == 0:
        raise SystemExit("No usable rows found. Check gender codes and fullText path.")

    col_totals = {c: sum(counts[(r, c)] for r in rows) for c in cols}

    fig, (ax, ax_tbl) = plt.subplots(
        1,
        2,
        figsize=(11.2, 5.4),
        gridspec_kw={"width_ratios": [2.2, 1.25]},
    )
    fig.suptitle(title, fontsize=14, y=0.97)
    fig.subplots_adjust(top=0.88, wspace=0.25)

    # Mosaic axis: reserve a header band above the mosaic so column labels never overlap
    ax.set_xlim(-0.14, 1.0)
    ax.set_ylim(0, 1.10)  # header band is (1.00..1.10)
    ax.axis("off")

    x0 = 0.0
    for c in cols:
        ct = col_totals[c]
        w = ct / total if total else 0.0

        y0 = 0.0
        for r in reversed(rows):
            cell = counts[(r, c)]
            h = (cell / ct) if ct else 0.0

            hatch = "///" if c == "Does not use bucket" else None
            rect = Rectangle(
                (x0, y0),
                w,
                h,
                fill=True,
                alpha=0.55,
                edgecolor="white",
                linewidth=2,
                hatch=hatch,
            )
            ax.add_patch(rect)

            if cell > 0 and w > 0 and h > 0:
                ax.text(
                    x0 + w / 2,
                    y0 + h / 2,
                    str(cell),
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                )

            y0 += h

        # Column label in header band with a light background for readability
        ax.text(
            x0 + w / 2,
            1.045,
            c,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2.5),
        )
        x0 += w

    # Row labels (within mosaic area 0..1)
    row_totals = {r: sum(counts[(r, c)] for c in cols) for r in rows}
    running = 0.0
    for r in reversed(rows):
        rh = row_totals[r] / total
        ax.text(-0.02, running + rh / 2, r, ha="right", va="center", fontsize=11, fontweight="bold")
        running += rh

    # Frame only around the mosaic region (0..1), not the header band
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, linewidth=1.5))

    # Definition table
    _draw_definition_table(ax_tbl, bucket_terms=bucket_terms, min_hits=min_hits, neg_window_words=neg_window_words)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--concept", default="serious relationship", help="Used in title/output naming")
    ap.add_argument(
        "--bucket",
        default="love,loving,relationship,relationships,stability,stable,dating,partner,partners,marriage,married,family,commitment,committed,serious,long term,long-term,kids,children, compatible, long-term, longterm",
        help="Comma-separated bucket terms/phrases",
    )
    ap.add_argument(
        "--rows",
        default="Male,Female",
        help="Comma-separated gender rows to include (canonical): Male,Female",
    )
    ap.add_argument(
        "--min_hits",
        type=int,
        default=1,
        help="Minimum number of NON-NEGATED bucket matches required to count as 'Uses bucket' (default: 1)",
    )
    ap.add_argument(
        "--neg_window_words",
        type=int,
        default=8,
        help="Ignore a bucket match if a negation word occurs within this many words BEFORE it (default: 8)",
    )
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    bucket_terms = [t.strip() for t in args.bucket.split(",") if t.strip()]
    bucket_re = compile_bucket_regex(bucket_terms)

    rows = [r.strip() for r in args.rows.split(",") if r.strip()]
    rows, cols, counts, total = build_contingency(
        profiles,
        bucket_re,
        allowed_rows=rows,
        min_hits=args.min_hits,
        neg_window_words=args.neg_window_words,
    )

    outdir = Path(args.outdir)
    safe = "serious_relationship"
    out_png = outdir / f"word_graph_01_mosaic_{safe}.png"
    out_svg = outdir / f"word_graph_01_mosaic_{safe}.svg"
    out_csv = outdir / f"word_graph_01_mosaic_{safe}.csv"

    save_csv(out_csv, rows, cols, counts)
    draw_mosaic(
        out_png=out_png,
        out_svg=out_svg,
        title=f"Use of {args.concept} language in profiles (negation-aware)",
        rows=rows,
        cols=cols,
        counts=counts,
        total=total,
        bucket_terms=bucket_terms,
        min_hits=args.min_hits,
        neg_window_words=args.neg_window_words,
    )

    print(f"[done] n={total}")
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {out_csv}")
    print(f"[rule] min_hits={args.min_hits} | neg_window_words={args.neg_window_words}")


if __name__ == "__main__":
    main()
