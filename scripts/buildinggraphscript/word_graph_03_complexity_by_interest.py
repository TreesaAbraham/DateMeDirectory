#!/usr/bin/env python3
# scripts/buildinggraphscript/word_graph_03_complexity_by_interest.py
"""
Graph 3 (updated): "Percent of words that are complex" by (profile gender -> who they're looking for).

We compute per-profile complexity as:
  percent of words with length >= --min_len

Then we bucket each profile into one or more groups based on:
  source gender (the profile owner) AND each target gender in interestedIn.

Examples (each is a separate group):
- Men → Women
- Women → Women
- Women → Men
- NB → NB
- Men → NB
- Women → NB
(and any other combos that appear, like NB → Women, etc.)

IMPORTANT: If someone is looking for multiple genders, we include them in multiple groups.
Example: Man interested in Men + Women contributes to both:
  Men → Men  and  Men → Women

Text source: profileDetails.fullText (fallbacks included)

Outputs:
- data/charts/word_graph_03_complexity_by_interest_gender.png
- data/charts/word_graph_03_complexity_by_interest_gender.svg
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


# ---------- Extractors ----------

def get_fulltext(p: dict) -> str:
    pd = p.get("profileDetails") or {}
    if isinstance(pd, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def get_interested_in_raw(p: dict):
    val = p.get("interestedIn", None)
    if val is None:
        val = p.get("genderInterestedIn", None)  # legacy
    return val


def get_interested_in_tokens(p: dict) -> List[str]:
    """
    Tries common shapes:
    - p["interestedIn"] as list like ["M","F","NB"]
    - p["interestedIn"] as string like "M,F" or "MF"
    - p["genderInterestedIn"] (legacy)
    Returns uppercase tokens.
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
    """
    Normalize various gender token formats into {"M","F","NB"}.
    Returns None if unknown/unsupported.
    """
    if not isinstance(tok, str):
        return None
    t = tok.strip().lower()
    if not t:
        return None

    # Common male tokens
    if t in {"m", "male", "man", "men", "boy", "guys", "guy"}:
        return "M"

    # Common female tokens
    if t in {"f", "female", "woman", "women", "girl", "ladies", "lady"}:
        return "F"

    # Common nonbinary tokens
    if t in {"nb", "nonbinary", "non-binary", "enby", "genderqueer", "gender-fluid", "genderfluid"}:
        return "NB"

    return None


def get_profile_gender(p: dict) -> Optional[str]:
    """
    Normalize p["gender"] into {"M","F","NB"}.
    """
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


# ---------- Complexity ----------

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


def pretty_gender(g: str) -> str:
    return {"M": "Men", "F": "Women", "NB": "NB"}.get(g, g)


def group_label(src: str, tgt: str) -> str:
    return f"{pretty_gender(src)} → {pretty_gender(tgt)}"


def default_order() -> List[str]:
    """
    A sensible, consistent plotting order. We only plot groups that actually have data.
    """
    srcs = ["M", "F", "NB"]
    tgts = ["M", "F", "NB"]
    return [group_label(s, t) for s in srcs for t in tgts]


# ---------- Main ----------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path, help="Path to profiles_master.json (list)")
    ap.add_argument("--outdir", default="data/charts", help="Output directory")
    ap.add_argument("--min_words", type=int, default=50, help="Skip profiles with fewer than this many words")
    ap.add_argument("--min_len", type=int, default=8, help="Word length threshold for 'complex'")
    ap.add_argument(
        "--order",
        default="",
        help=(
            "Optional comma-separated plotting order of group labels, e.g. "
            "'Men → Women,Women → Women,Women → Men'. If empty, uses default grid order."
        ),
    )
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("Input JSON must be a list of profiles.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    per_profile_csv = outdir / "word_graph_03_complexity_by_interest_gender_per_profile.csv"
    summary_csv = outdir / "word_graph_03_complexity_by_interest_gender_summary.csv"
    out_png = outdir / "word_graph_03_complexity_by_interest_gender.png"
    out_svg = outdir / "word_graph_03_complexity_by_interest_gender.svg"

    # Order (optional override)
    if args.order.strip():
        order = [x.strip() for x in args.order.split(",") if x.strip()]
    else:
        order = default_order()

    by_group: Dict[str, List[float]] = {g: [] for g in order}

    skipped_no_text = 0
    skipped_short = 0
    skipped_no_profile_gender = 0
    skipped_no_targets = 0
    kept_profiles = 0
    kept_group_assignments = 0  # counts duplicates across multiple target groups

    with per_profile_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "id",
            "source_gender",
            "target_gender",
            "group",
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

            # Count profile as kept once
            kept_profiles += 1

            # Add to multiple groups if multiple targets
            for tgt in targets:
                g = group_label(src, tgt)
                if g not in by_group:
                    # if user gave custom order that doesn't include this, we still keep it,
                    # and append it to the end so it's plotted.
                    by_group[g] = []
                    order.append(g)

                by_group[g].append(pct)
                w.writerow([p.get("id", ""), src, tgt, g, len(words), round(pct, 3), raw_interest])
                kept_group_assignments += 1

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

    # Build plot stats (only groups with data)
    labels: List[str] = []
    stats: List[Tuple[float, float, float]] = []  # (q1, median, q3)
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
        raise SystemExit("No data to plot (check gender + interestedIn + min_words).")

    # Plot: vertical IQR bars + median line + median label
    # More groups now, so make it wider.
    fig_w = max(10, 0.75 * len(labels))
    fig, ax = plt.subplots(figsize=(fig_w, 6.0))

    ax.set_title("Percent of Words That Are Complex (by gender → who they're looking for)", pad=12)
    ax.set_ylabel("Percent complex words")
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=30, ha="right")

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
        ax.text(i, med + 0.05, f"{med:.0f}%", ha="center", va="bottom", fontsize=9)

    all_q = [q for triple in stats for q in triple]
    ymin = max(0.0, min(all_q) - 1.0)
    ymax = max(all_q) + 1.0
    ax.set_ylim(ymin, ymax)

    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_svg, bbox_inches="tight")
    plt.close(fig)

    print(f"[done] kept profiles (unique): {kept_profiles}")
    print(f"[done] kept group-assignments (includes duplicates across targets): {kept_group_assignments}")
    print(
        f"[skipped] no text: {skipped_no_text} | <min_words: {skipped_short} | "
        f"no/unknown gender: {skipped_no_profile_gender} | no interestedIn targets: {skipped_no_targets}"
    )
    print(f"[out] {out_png}")
    print(f"[out] {out_svg}")
    print(f"[out] {per_profile_csv}")
    print(f"[out] {summary_csv}")


if __name__ == "__main__":
    main()
