#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# -----------------------------
# Repo paths (robust root find)
# -----------------------------
def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "data" / "profiles_master.json").exists():
            return parent
    raise FileNotFoundError("Could not find repo root containing data/profiles_master.json")


REPO_ROOT = find_repo_root(Path(__file__).parent)

MASTER_JSON = REPO_ROOT / "data" / "profiles_master.json"

OUT_DIR_PNG = REPO_ROOT / "data" / "charts" / "matplotlib"
OUT_PNG = OUT_DIR_PNG / "word_graph_10_mosaic_kids_mentions_by_style.png"
OUT_SVG = OUT_DIR_PNG / "word_graph_10_mosaic_kids_mentions_by_style.svg"

OUT_CSV = REPO_ROOT / "data" / "charts" / "graphscsv" / "word_graph_10_kids_mentions_by_style_mosaic_counts.csv"


# -----------------------------
# Kids-bucket + negation logic
# -----------------------------
KIDS_TERMS = {
    "kid", "kids", "child", "children", "baby", "babies",
    "stepkid", "stepkids", "stepchild", "stepchildren",
    "coparent", "co-parent", "custody"
}


NEGATION_TOKENS = {
    "no", "not", "never", "none", "without",
    "dont", "don't", "doesnt", "doesn't", "didnt", "didn't",
    "cannot", "can't", "wont", "won't"
}

NEGATION_PHRASES = [
    r"\b(childfree|child-free)\b",
    r"\bno\s+kids\b",
    r"\b(don'?t|do\s+not|doesn'?t|didn'?t)\s+want\s+(any\s+)?kids\b",
    r"\bnot\s+want\s+(any\s+)?kids\b",
    r"\bnot\s+looking\s+for\s+kids\b",
    r"\bnot\s+interested\s+in\s+kids\b",
    r"\b(don'?t|do\s+not)\s+want\s+children\b",
    r"\bnot\s+want\s+children\b",
    r"\b(don'?t|do\s+not|not|never)\s+(start|have|want)\s+(a\s+)?family\b",
]
NEGATION_PHRASES_RE = [re.compile(pat, re.IGNORECASE) for pat in NEGATION_PHRASES]

TOKEN_RE = re.compile(r"[a-zA-Z']+")


def normalize_style(raw: str | None) -> str | None:
    s = (raw or "").strip().lower()
    if s in {"mono", "monogamous", "monogamy"}:
        return "mono"
    if s in {"poly", "polyamorous", "polyamory"}:
        return "poly"
    if s in {"any"}:
        return "any"
    return None


def get_full_text(profile: dict) -> str:
    details = profile.get("profileDetails") or {}
    return (details.get("fullText") or "").strip()


def mentions_kids_without_negation(text: str) -> bool:
    """
    True if kids topic is mentioned AND not negated.
    False if no kids mention OR only negated mention (e.g., "don't want kids").
    """
    if not text:
        return False

    lower = text.lower()

    # Hard negation phrases override everything
    for rx in NEGATION_PHRASES_RE:
        if rx.search(lower):
            return False

    tokens = [t.lower().strip("'") for t in TOKEN_RE.findall(lower)]
    if not tokens:
        return False

    kids_idxs = [i for i, tok in enumerate(tokens) if tok in KIDS_TERMS]
    if not kids_idxs:
        # also catch "start a family" in non-negated form
        if re.search(r"\b(start|have|want)\s+(a\s+)?family\b", lower):
            return True
        return False

    window = 4
    for idx in kids_idxs:
        start = max(0, idx - window)
        context = tokens[start:idx]
        if any(tok in NEGATION_TOKENS for tok in context):
            continue
        return True

    return False


# -----------------------------
# CSV output
# -----------------------------
def write_counts_csv(counts: dict[tuple[str, str], int], out_csv: Path) -> None:
    styles = ["mono", "poly", "any"]
    buckets = ["No kids mention", "Kids mention"]

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["datingStyle", "kids_bucket", "count", "style_total", "pct_within_style"],
        )
        w.writeheader()

        for s in styles:
            style_total = sum(counts.get((s, b), 0) for b in buckets)
            for b in buckets:
                c = counts.get((s, b), 0)
                pct = (c / style_total * 100) if style_total else 0.0
                w.writerow(
                    {
                        "datingStyle": s,
                        "kids_bucket": b,
                        "count": c,
                        "style_total": style_total,
                        "pct_within_style": round(pct, 3),
                    }
                )


# -----------------------------
# Mosaic plotting (matplotlib)
# -----------------------------
def draw_mosaic(counts: dict[tuple[str, str], int], out_png: Path, out_svg: Path) -> None:
    styles = ["mono", "poly", "any"]
    buckets = ["No kids mention", "Kids mention"]

    style_totals = {s: sum(counts.get((s, b), 0) for b in buckets) for s in styles}
    grand_total = sum(style_totals.values())
    if grand_total == 0:
        raise RuntimeError("No data to plot. Do you have datingStyle populated in profiles_master.json?")

    # Two panels: mosaic + legend table
    fig, (ax, ax_legend) = plt.subplots(
        ncols=2,
        figsize=(13, 6),
        gridspec_kw={"width_ratios": [3.2, 1.3]},
    )

    # ---- Mosaic panel ----
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    x = 0.0
    for s in styles:
        s_total = style_totals[s]
        if s_total == 0:
            continue

        width = s_total / grand_total
        no_cnt = counts.get((s, "No kids mention"), 0)
        yes_cnt = counts.get((s, "Kids mention"), 0)

        no_h = no_cnt / s_total if s_total else 0
        yes_h = yes_cnt / s_total if s_total else 0

        ax.add_patch(Rectangle((x, 0), width, no_h, fill=False))
        ax.add_patch(Rectangle((x, no_h), width, yes_h, fill=False))

        ax.text(x + width / 2, 1.02, f"{s} (n={s_total})", ha="center", va="bottom", fontsize=11)

        if no_h > 0:
            ax.text(
                x + width / 2,
                no_h / 2,
                f"No\n{no_cnt} ({(no_cnt/s_total)*100:.1f}%)",
                ha="center",
                va="center",
                fontsize=10,
            )
        if yes_h > 0:
            ax.text(
                x + width / 2,
                no_h + yes_h / 2,
                f"Yes\n{yes_cnt} ({(yes_cnt/s_total)*100:.1f}%)",
                ha="center",
                va="center",
                fontsize=10,
            )

        x += width

    ax.set_title(
        "Kids mentions by dating style (mosaic)\nNegations excluded (e.g., “don’t want kids” counted as No)",
        pad=20,
    )

    # ---- Legend/table panel ----
    ax_legend.axis("off")

    # Sort terms so the list is stable and readable
    terms_sorted = sorted({t.lower() for t in KIDS_TERMS})

    # Wrap into lines for compact display
    term_lines = pretty_wrap_terms(terms_sorted, per_line=3)

    legend_text = (
        "Kids bucket terms scanned:\n\n"
        + "\n".join(term_lines)
        + "\n\nNegation handling:\n"
        + "• childfree / child-free\n"
        + "• “no kids”\n"
        + "• “don’t want kids/children”\n"
        + "• “not looking for kids”\n"
        + "…and similar phrasing\n"
        + "\nRule: if a kids-term is\nnegated, it counts as NO."
    )

    # Draw a nice box with text
    ax_legend.text(
        0.02,
        0.98,
        legend_text,
        ha="left",
        va="top",
        fontsize=9.5,
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.6", fill=False),
    )

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    fig.savefig(out_svg)
    plt.close(fig)


def pretty_wrap_terms(terms: list[str], per_line: int = 4) -> list[str]:
    """Format terms into multiple lines for a side-panel legend."""
    lines = []
    for i in range(0, len(terms), per_line):
        chunk = terms[i : i + per_line]
        lines.append(", ".join(chunk))
    return lines


def main() -> None:
    data = json.loads(MASTER_JSON.read_text(encoding="utf-8"))

    counts: dict[tuple[str, str], int] = defaultdict(int)

    used = 0
    skipped_no_style = 0

    for p in data:
        style = normalize_style(p.get("datingStyle"))
        if style is None:
            skipped_no_style += 1
            continue

        text = get_full_text(p)
        yes = mentions_kids_without_negation(text)
        bucket = "Kids mention" if yes else "No kids mention"

        counts[(style, bucket)] += 1
        used += 1

    print(f"Profiles used (have datingStyle): {used}")
    print(f"Profiles skipped (missing/unknown style): {skipped_no_style}")

    for s in ["mono", "poly", "any"]:
        yes = counts.get((s, "Kids mention"), 0)
        no = counts.get((s, "No kids mention"), 0)
        total = yes + no
        pct = (yes / total * 100) if total else 0.0
        print(f"{s:4s}: kids mention {yes:3d}/{total:3d} ({pct:5.1f}%)")

    write_counts_csv(counts, OUT_CSV)
    print(f"Wrote CSV: {OUT_CSV}")

    draw_mosaic(counts, OUT_PNG, OUT_SVG)
    print(f"Wrote PNG: {OUT_PNG}")
    print(f"Wrote SVG: {OUT_SVG}")


if __name__ == "__main__":
    main()
