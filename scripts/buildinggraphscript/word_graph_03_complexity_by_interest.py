#!/usr/bin/env python3
# scripts/buildinggraphscript/word_graph_03_complexity_by_interest.py
"""
Graph 3 (updated): Word complexity by (source gender) within each target gender.

We create THREE graphs:

1) Looking for Men:
   Bars for Women vs Men vs NB (all profiles whose interestedIn includes Men)
2) Looking for Women:
   Bars for Women vs Men vs NB (interestedIn includes Women)
3) Looking for Non-binary:
   Bars for Women vs Men vs NB (interestedIn includes NB)

Important rule:
- If someone is looking for multiple genders, they are included in MULTIPLE graphs.
  Example: a Man interested in Men+Women contributes to BOTH "Looking for Men" and "Looking for Women".

Complexity definition:
- A word is "complex" if len(word) >= --min_len
- Per profile: complex_pct = (complex_words / total_words) * 100

Style:
- For each bar/group, draw a vertical IQR bar (Q1->Q3) with a median line and median label.

Text source:
- profileDetails.fullText (fallbacks included)

Outputs:
- data/charts/word_graph_03_complexity_looking_for_men.png
- data/charts/word_graph_03_complexity_looking_for_men.svg
- data/charts/word_graph_03_complexity_looking_for_women.png
- data/charts/word_graph_03_complexity_looking_for_women.svg
- data/charts/word_graph_03_complexity_looking_for_nb.png
- data/charts/word_graph_03_complexity_looking_for_nb.svg
- data/charts/word_graph_03_complexity_by_interest_gender_per_profile.csv
- data/charts/word_graph_03_complexity_by_interest_gender_summary.csv
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

SOURCE_ORDER = ["F", "M", "NB"]  # Women vs Men vs NB (as requested)


# -------------------- Helpers: text + fields --------------------

def get_fulltext(p: dict) -> str:
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def tokenize_words(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def complexity_percent(words: List[str], min_len: int) -> float:
    """Percent of words whose length >= min_len."""
    if not words:
        return 0.0
    complex_ct = sum(1 for w in words if len(w) >= min_len)
    return (complex_ct / len(words)) * 100.0


def get_interested_in_raw(p: dict):
    val = p.get("interestedIn", None)
    if val is None:
        val = p.get("genderInterestedIn", None)  # legacy
    return val


def get_interested_in_tokens(p: dict) -> List[str]:
    """
    Returns uppercase tokens from interestedIn.
    Handles:
      - list like ["M","F","NB"]
      - string like "M,F" or "MF"
    """
    val = get_interested_in_raw(p)

    if isinstance(val, list):
        return [str(x).strip().upper() for x in val if str(x).strip()]

    if isinstance(val, str):
        s = val.strip().upper()
        if "," in s:
            return [t.strip().upper() for t in s.split(",") if t.strip()]
        if " " in s:
            return [t.strip().upper() for t in s.split() if t.strip()]
        # treat as sequence of letters (e.g., "MF")
        return [ch for ch in s if ch.isalpha()]

    return []


def normalize_gender_token(tok: str) -> Optional[str]:
    """Normalize a token into {"M","F","NB"} or None."""
    if not isinstance(tok, str):
        return None
    t = tok.strip().lower()
    if not t:
        return None

    if t in {"m", "male", "man", "men", "guy", "guys", "boy"}:
        return "M"
    if t in {"f", "female", "woman", "women", "girl", "lady", "ladies"}:
        return "F"
    if t in {"nb", "nonbinary", "non-binary", "enby", "genderqueer", "gender-fluid", "genderfluid"}:
        return "NB"

    return None


def get_profile_gender(p: dict) -> Optional[str]:
    """Normalize p['gender'] into {"M","F","NB"}."""
    val = p.get("gender", None)
    if isinstance(val, str):
        return normalize_gender_token(val)
    return None


def get_target_genders(p: dict) -> List[str]:
    """
    From interestedIn, return normalized target genders in {"M","F","NB"}.
    Deduped, stable-ish ordering.
    """
    toks = get_interested_in_tokens(p)
    out: List[str] = []
    seen = set()
    for tok in toks:
        norm = normalize_gender_token(tok)
        if norm and norm not in seen:
            out.append(norm)
            seen.add(norm)
    return out


def pretty_gender(g: str) -> str:
    return {"M": "Men", "F": "Women", "NB": "NB"}.get(g, g)


# -------------------- Stats + plotting --------------------

def percentile(sorted_vals: List[float], p: float) -> float:
    """Linear-interpolated percentile. p in [0,1]."""
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


def compute_iqr_stats(vals: List[float]) -> Tuple[float, float, float]:
    s = sorted(vals)
    return (percentile(s, 0.25), percentile(s, 0.50), percentile(s, 0.75))


def plot_target_graph(
    *,
    out_png: Path,
    out_svg: Path,
    title: str,
    labels: List[str],
    stats: List[Tuple[float, float, float]],
    ylim: Optional[Tuple[float, float]] = None,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.set_title(title, pad=12)
    ax.set_ylabel("Percent complex words")
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)

    bar_width = 0.55
    for i, (q1, med, q3) in enumerate(stats, start=1):
        rect = Rectangle(
            (i - bar_width / 2, q1),
            bar_width,
            max(q3 - q1, 0.0001),
            alpha=0.6,
        )
        ax.add_patch(rect)

        ax.plot([i - bar_width / 2, i + bar_width / 2], [med, med], linewidth=2)
        ax.text(i, med + 0.05, f"{med:.0f}%", ha="center", va="bottom", fontsize=10)

    if ylim is None:
        all_q = [q for triple in stats for q in triple]
        ymin = max(0.0, min(all_q) - 1.0)
        ymax = max(all_q) + 1.0
        ax.set_ylim(ymin, ymax)
    else:
        ax.set_ylim(ylim[0], ylim[1])

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)


# -------------------- Main --------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--min_words", type=int, default=50, help="Skip profiles with fewer than this many words")
    ap.add_argument("--min_len", type=int, default=8, help="Word length threshold for 'complex'")
    ap.add_argument(
        "--shared_ylim",
        action="store_true",
        help="Use the same y-axis range for all three target graphs (recommended for comparison).",
    )
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_profile_csv = outdir / "word_graph_03_complexity_by_interest_gender_per_profile.csv"
    summary_csv = outdir / "word_graph_03_complexity_by_interest_gender_summary.csv"

    out_m_png = outdir / "word_graph_03_complexity_looking_for_men.png"
    out_m_svg = outdir / "word_graph_03_complexity_looking_for_men.svg"
    out_f_png = outdir / "word_graph_03_complexity_looking_for_women.png"
    out_f_svg = outdir / "word_graph_03_complexity_looking_for_women.svg"
    out_nb_png = outdir / "word_graph_03_complexity_looking_for_nb.png"
    out_nb_svg = outdir / "word_graph_03_complexity_looking_for_nb.svg"

    # by_target[target][source] = list of complexity pcts
    by_target: Dict[str, Dict[str, List[float]]] = {
        "M": {s: [] for s in SOURCE_ORDER},
        "F": {s: [] for s in SOURCE_ORDER},
        "NB": {s: [] for s in SOURCE_ORDER},
    }

    skipped_no_text = 0
    skipped_short = 0
    skipped_no_profile_gender = 0
    skipped_no_targets = 0
    kept_profiles = 0
    kept_assignments = 0  # includes duplicates across multi-target

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "id",
            "source_gender",
            "target_gender",
            "word_count",
            "complex_pct",
            "interestedIn_raw",
        ])

        for p in profiles:
            text = get_fulltext(p)
            if not text.strip():
                skipped_no_text += 1
                continue

            words = tokenize_words(text)
            if len(words) < args.min_words:
                skipped_short += 1
                continue

            src = get_profile_gender(p)
            if src is None:
                skipped_no_profile_gender += 1
                continue

            targets = get_target_genders(p)
            if not targets:
                skipped_no_targets += 1
                continue

            pct = complexity_percent(words, min_len=args.min_len)
            raw_interest = get_interested_in_raw(p)

            kept_profiles += 1

            # Include in multiple targets if needed
            for tgt in targets:
                if tgt not in by_target:
                    # ignore unexpected tokens outside M/F/NB
                    continue
                if src not in by_target[tgt]:
                    # ignore unexpected source values
                    continue

                by_target[tgt][src].append(pct)
                w.writerow([p.get("id", ""), src, tgt, len(words), round(pct, 3), raw_interest])
                kept_assignments += 1

    # Summary CSV (one file, includes target + source)
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["target", "source", "n", "min", "q1", "median", "q3", "max"])
        for tgt in ["M", "F", "NB"]:
            for src in SOURCE_ORDER:
                vals = sorted(by_target[tgt][src])
                if not vals:
                    w.writerow([tgt, src, 0, "", "", "", "", ""])
                    continue
                q1, med, q3 = compute_iqr_stats(vals)
                w.writerow([
                    tgt,
                    src,
                    len(vals),
                    round(vals[0], 3),
                    round(q1, 3),
                    round(med, 3),
                    round(q3, 3),
                    round(vals[-1], 3),
                ])

    # Optional shared y-limits across all 3 graphs
    shared_ylim: Optional[Tuple[float, float]] = None
    if args.shared_ylim:
        all_quartiles: List[float] = []
        for tgt in ["M", "F", "NB"]:
            for src in SOURCE_ORDER:
                vals = by_target[tgt][src]
                if not vals:
                    continue
                q1, med, q3 = compute_iqr_stats(vals)
                all_quartiles.extend([q1, med, q3])

        if all_quartiles:
            ymin = max(0.0, min(all_quartiles) - 1.0)
            ymax = max(all_quartiles) + 1.0
            shared_ylim = (ymin, ymax)

    # Build and plot each target graph
    def build_stats_for_target(tgt: str) -> Tuple[List[str], List[Tuple[float, float, float]]]:
        labels: List[str] = []
        stats: List[Tuple[float, float, float]] = []
        for src in SOURCE_ORDER:
            vals = by_target[tgt][src]
            if not vals:
                continue
            labels.append(pretty_gender(src))
            stats.append(compute_iqr_stats(vals))
        return labels, stats

    # Graph 1: looking for men
    labels_m, stats_m = build_stats_for_target("M")
    if not stats_m:
        print("[warn] No data for target Men (M). Skipping men graph.")
    else:
        plot_target_graph(
            out_png=out_m_png,
            out_svg=out_m_svg,
            title="Percent of Words That Are Complex (Looking for Men)",
            labels=labels_m,
            stats=stats_m,
            ylim=shared_ylim,
        )

    # Graph 2: looking for women
    labels_f, stats_f = build_stats_for_target("F")
    if not stats_f:
        print("[warn] No data for target Women (F). Skipping women graph.")
    else:
        plot_target_graph(
            out_png=out_f_png,
            out_svg=out_f_svg,
            title="Percent of Words That Are Complex (Looking for Women)",
            labels=labels_f,
            stats=stats_f,
            ylim=shared_ylim,
        )

    # Graph 3: looking for non-binary
    labels_nb, stats_nb = build_stats_for_target("NB")
    if not stats_nb:
        print("[warn] No data for target NB. Skipping NB graph.")
    else:
        plot_target_graph(
            out_png=out_nb_png,
            out_svg=out_nb_svg,
            title="Percent of Words That Are Complex (Looking for Non-binary)",
            labels=labels_nb,
            stats=stats_nb,
            ylim=shared_ylim,
        )

    print(f"[done] kept profiles (unique): {kept_profiles}")
    print(f"[done] kept assignments (includes multi-target duplicates): {kept_assignments}")
    print(
        f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short} | "
        f"no/unknown gender: {skipped_no_profile_gender} | no targets: {skipped_no_targets}"
    )
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")
    if stats_m:
        print(f"[out] {out_m_png}\n[out] {out_m_svg}")
    if stats_f:
        print(f"[out] {out_f_png}\n[out] {out_f_svg}")
    if stats_nb:
        print(f"[out] {out_nb_png}\n[out] {out_nb_svg}")


if __name__ == "__main__":
    main()
