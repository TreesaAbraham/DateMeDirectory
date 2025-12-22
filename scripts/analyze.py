# scripts/analyze.py
# Step 6: Advanced Graphs for DateMeDirectory
#
# Generates:
# 1) Mosaic charts: gender vs word presence (adventure/serious/emotional)
# 2) "What People Want": top words + categorized bars from "Looking For"
# 3) Tone classification: humorous vs serious, vulnerable vs guarded + demographic distributions
#
# Output: publication-ready PNG + SVG + CSV tables

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt


# -----------------------------
# Utilities
# -----------------------------

TOKEN_RE = re.compile(r"[a-zA-Z']+")

# Small, pragmatic stopword list (kept local to avoid extra deps)
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "to", "of", "in", "on", "for", "with",
    "as", "at", "by", "from", "about", "into", "over", "after", "before", "between", "through",
    "i", "im", "i'm", "me", "my", "mine", "we", "us", "our", "ours", "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers", "they", "them", "their", "theirs",
    "is", "are", "was", "were", "be", "been", "being", "am", "do", "does", "did", "doing",
    "have", "has", "had", "having", "will", "would", "can", "could", "should", "may", "might", "must",
    "not", "no", "yes", "yeah", "yep",
    "this", "that", "these", "those", "it", "its", "it's",
    "just", "really", "very", "more", "most", "less", "like", "love", "loving",
    "also", "too", "much", "many", "some", "any", "all",
}

def safe_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "untitled"

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})

def tokenize(text: str) -> List[str]:
    if not text:
        return []
    toks = [t.lower() for t in TOKEN_RE.findall(text)]
    return toks

def contains_any(tokens_set: set, keywords: Iterable[str]) -> bool:
    return any(k in tokens_set for k in keywords)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def age_group(age: Optional[int]) -> str:
    if age is None:
        return "Unknown"
    if age < 25:
        return "Gen Z (<25)"
    if age < 41:
        return "Millennial (25–40)"
    if age < 57:
        return "Gen X (41–56)"
    return "Boomer+ (57+)"


# -----------------------------
# Data extraction
# -----------------------------

@dataclass
class ProfileRecord:
    id: str
    gender: str
    age: Optional[int]
    location: str
    tokens_all: List[str]
    tokens_looking: List[str]

def normalize_gender(g: Any) -> str:
    if g is None:
        return "Unknown"
    s = str(g).strip().lower()
    if not s:
        return "Unknown"
    # loose normalization for common variants
    if s in {"m", "male", "man", "men"}:
        return "Men"
    if s in {"f", "female", "woman", "women"}:
        return "Women"
    if "non" in s and "binary" in s:
        return "Non-binary"
    return s.title()

def extract_text_fields(profile: Dict[str, Any]) -> Tuple[str, str]:
    """
    Returns (all_text, looking_for_text).

    Tries to be robust to whatever shape your profileDetails ended up as.
    Common patterns:
    - profile["profileDetails"]["sections"] is a dict of sectionName->text
    - profile["profileDetails"]["lookingFor"] or ["looking_for"] etc.
    - profile["profileDetails"] may be a dict of arbitrary strings
    """
    all_chunks: List[str] = []
    looking_chunks: List[str] = []

    # 1) If you stored longform in profileDetails
    details = profile.get("profileDetails")
    if isinstance(details, dict):
        # sections dict
        sections = details.get("sections")
        if isinstance(sections, dict):
            for k, v in sections.items():
                if isinstance(v, str) and v.strip():
                    all_chunks.append(v)
                    if "looking" in str(k).lower():
                        looking_chunks.append(v)

        # direct keys
        for k in ["lookingFor", "looking_for", "looking", "seeking", "whatImLookingFor", "what_i_m_looking_for"]:
            v = details.get(k)
            if isinstance(v, str) and v.strip():
                looking_chunks.append(v)
                all_chunks.append(v)

        # if details has other text fields, include them
        for k, v in details.items():
            if isinstance(v, str) and v.strip():
                all_chunks.append(v)

    # 2) Also include any top-level longform (if present)
    for k in ["bio", "about", "aboutMe", "about_me", "promptAnswers", "prompts", "text"]:
        v = profile.get(k)
        if isinstance(v, str) and v.strip():
            all_chunks.append(v)

    all_text = "\n".join(all_chunks).strip()
    looking_text = "\n".join(looking_chunks).strip()

    return all_text, looking_text

def load_profiles(path: Path) -> List[ProfileRecord]:
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}, got {type(data)}")

    records: List[ProfileRecord] = []
    for p in data:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or p.get("_id") or "")
        g = normalize_gender(p.get("gender"))
        loc = str(p.get("location") or "").strip()
        a_raw = p.get("age")
        age_val: Optional[int] = None
        try:
            if a_raw is not None and str(a_raw).strip() != "":
                age_val = int(a_raw)
        except Exception:
            age_val = None

        all_text, looking_text = extract_text_fields(p)
        toks_all = tokenize(all_text)
        toks_looking = tokenize(looking_text)

        records.append(ProfileRecord(
            id=pid,
            gender=g,
            age=age_val,
            location=loc,
            tokens_all=toks_all,
            tokens_looking=toks_looking,
        ))

    return records


# -----------------------------
# Plotting helpers
# -----------------------------

def save_fig(out_dir: Path, filename_base: str, dpi: int = 300) -> None:
    ensure_dir(out_dir)
    png = out_dir / f"{filename_base}.png"
    svg = out_dir / f"{filename_base}.svg"
    plt.savefig(png, dpi=dpi, bbox_inches="tight")
    plt.savefig(svg, bbox_inches="tight")
    plt.close()

def mosaic_2x2(
    counts: Dict[str, Dict[str, int]],
    title: str,
    out_dir: Path,
    filename_base: str,
    x_label_left: str = "Women",
    x_label_right: str = "Men",
    y_label_top: str = "Contains",
    y_label_bottom: str = "Does not contain",
) -> None:
    """
    Custom mosaic chart (no external libs):
    - Width of each gender column proportional to its total
    - Height split within each gender by contains vs not
    """
    genders = [x_label_left, x_label_right]
    for g in genders:
        counts.setdefault(g, {"contains": 0, "not": 0})

    totals = {g: counts[g]["contains"] + counts[g]["not"] for g in genders}
    grand_total = sum(totals.values()) or 1

    widths = {g: totals[g] / grand_total for g in genders}

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.set_title(title)

    x0 = 0.0
    for g in genders:
        w = widths[g]
        g_total = totals[g] or 1
        h_contains = counts[g]["contains"] / g_total
        h_not = counts[g]["not"] / g_total

        # bottom = not
        ax.add_patch(plt.Rectangle((x0, 0.0), w, h_not, fill=False))
        # top = contains
        ax.add_patch(plt.Rectangle((x0, h_not), w, h_contains, fill=False))

        # labels inside rectangles
        ax.text(x0 + w/2, h_not/2,
                f"{y_label_bottom}\n{counts[g]['not']}",
                ha="center", va="center", fontsize=10)
        ax.text(x0 + w/2, h_not + h_contains/2,
                f"{y_label_top}\n{counts[g]['contains']}",
                ha="center", va="center", fontsize=10)

        # gender label under column
        ax.text(x0 + w/2, -0.06, f"{g}\n(n={totals[g]})",
                ha="center", va="top", fontsize=10)

        x0 += w

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)

    save_fig(out_dir, filename_base)

def bar_chart(
    labels: List[str],
    values: List[float],
    title: str,
    out_dir: Path,
    filename_base: str,
    xlabel: str = "",
    ylabel: str = "",
    rotate: int = 25,
) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if rotate:
        plt.xticks(rotation=rotate, ha="right")
    save_fig(out_dir, filename_base)

def grouped_bar_chart(
    labels: List[str],
    series: Dict[str, List[float]],
    title: str,
    out_dir: Path,
    filename_base: str,
    xlabel: str = "",
    ylabel: str = "",
    rotate: int = 25,
) -> None:
    """
    series: name -> list of values aligned with labels
    """
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    n = len(labels)
    k = len(series)
    if n == 0 or k == 0:
        return
    width = 0.8 / k
    x = list(range(n))
    for i, (name, vals) in enumerate(series.items()):
        ax.bar([xi + i*width for xi in x], vals, width=width, label=name)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticks([xi + (k-1)*width/2 for xi in x])
    ax.set_xticklabels(labels, rotation=rotate, ha="right")
    ax.legend()
    save_fig(out_dir, filename_base)

def stacked_bar_distribution(
    groups: List[str],
    categories: List[str],
    matrix: Dict[str, Dict[str, int]],
    title: str,
    out_dir: Path,
    filename_base: str,
    xlabel: str = "",
    ylabel: str = "Count",
    rotate: int = 0,
) -> None:
    """
    matrix[group][category] = count
    """
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    bottoms = [0] * len(groups)

    for cat in categories:
        vals = [matrix.get(g, {}).get(cat, 0) for g in groups]
        ax.bar(groups, vals, bottom=bottoms, label=cat)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if rotate:
        plt.xticks(rotation=rotate, ha="right")
    ax.legend()
    save_fig(out_dir, filename_base)


# -----------------------------
# Step 6: Analyses
# -----------------------------

MOSAIC_WORDS = ["adventure", "serious", "emotional"]

# "What people want" categories: tune freely
LOOKING_FOR_CATEGORIES: Dict[str, List[str]] = {
    "Long-term / Commitment": ["relationship", "commitment", "longterm", "long-term", "serious", "partner", "marriage", "wife", "husband"],
    "Dating / Getting to know": ["dating", "dates", "see", "meet", "connection"],
    "Casual": ["casual", "hookup", "hook-up", "fun", "fwb", "situationship"],
    "Friendship": ["friends", "friendship", "buddy", "hangout"],
    "Adventure / Travel": ["adventure", "travel", "trip", "explore", "hiking", "roadtrip", "road-trip"],
    "Emotional connection": ["emotional", "vulnerable", "open", "honest", "communication", "feelings"],
    "Values / Faith": ["faith", "church", "god", "religion", "values"],
}

HUMOR_MARKERS = [
    "lol", "lmao", "haha", "joke", "joking", "funny", "humor", "humour", "sarcasm", "meme", "memes", "pun", "witty",
]
SERIOUS_MARKERS = [
    "serious", "intentional", "commitment", "longterm", "long-term", "relationship", "marriage", "partner", "stable",
]

VULNERABLE_MARKERS = [
    "vulnerable", "open", "honest", "feelings", "emotional", "therapy", "anxious", "sensitive", "heart", "genuine",
]
GUARDED_MARKERS = [
    "private", "lowkey", "low-key", "chill", "no drama", "nodrama", "guarded", "nonchalant", "not emotional",
]

def classify_tone(tokens: List[str]) -> Dict[str, str]:
    """
    Returns:
      humor: Humorous | Serious | Neutral
      vulnerability: Vulnerable | Guarded | Neutral
    """
    tset = set(tokens)

    humor_score = sum(1 for w in HUMOR_MARKERS if w in tset)
    serious_score = sum(1 for w in SERIOUS_MARKERS if w in tset)

    vuln_score = sum(1 for w in VULNERABLE_MARKERS if w in tset)
    guard_score = 0
    # include multiword markers by scanning raw join
    joined = " ".join(tokens)
    for w in GUARDED_MARKERS:
        if " " in w:
            if w in joined:
                guard_score += 1
        else:
            if w in tset:
                guard_score += 1

    if humor_score >= 2 and humor_score >= serious_score + 1:
        humor = "Humorous"
    elif serious_score >= 2 and serious_score >= humor_score + 1:
        humor = "Serious"
    else:
        humor = "Neutral"

    if vuln_score >= 2 and vuln_score >= guard_score + 1:
        vulnerability = "Vulnerable"
    elif guard_score >= 2 and guard_score >= vuln_score + 1:
        vulnerability = "Guarded"
    else:
        vulnerability = "Neutral"

    return {"humor": humor, "vulnerability": vulnerability}

def top_words(tokens_lists: List[List[str]], n: int = 25) -> List[Tuple[str, int]]:
    c = Counter()
    for toks in tokens_lists:
        for t in toks:
            if t in STOPWORDS:
                continue
            if len(t) <= 2:
                continue
            c[t] += 1
    return c.most_common(n)

def make_step6_charts(records: List[ProfileRecord], out_root: Path) -> None:
    charts_dir = out_root / "charts"
    tables_dir = out_root / "tables"
    ensure_dir(charts_dir)
    ensure_dir(tables_dir)

    # Filter down to the main two genders for these visuals (keeps mosaics clean)
    # You still keep other genders in tone distributions below.
    gender_main = {"Women", "Men"}

    # -------------------------
    # 1) Mosaic charts: gender vs word presence
    # -------------------------
    mosaic_rows: List[Dict[str, Any]] = []
    for word in MOSAIC_WORDS:
        counts = {"Women": {"contains": 0, "not": 0}, "Men": {"contains": 0, "not": 0}}
        for r in records:
            if r.gender not in gender_main:
                continue
            tset = set(r.tokens_all)
            if word in tset:
                counts[r.gender]["contains"] += 1
            else:
                counts[r.gender]["not"] += 1

        mosaic_2x2(
            counts=counts,
            title=f'Gendered Language: "{word}" presence',
            out_dir=charts_dir,
            filename_base=f"mosaic_gender_word_{safe_slug(word)}",
            x_label_left="Women",
            x_label_right="Men",
            y_label_top=f'Contains "{word}"',
            y_label_bottom=f'Does not contain "{word}"',
        )

        for g in ["Women", "Men"]:
            mosaic_rows.append({
                "word": word,
                "gender": g,
                "contains": counts[g]["contains"],
                "not_contains": counts[g]["not"],
                "total": counts[g]["contains"] + counts[g]["not"],
            })

    write_csv(
        tables_dir / "mosaic_gender_word_counts.csv",
        mosaic_rows,
        ["word", "gender", "contains", "not_contains", "total"],
    )

    # -------------------------
    # 2) What People Want: Looking For analysis
    # -------------------------
    looking_tokens = [r.tokens_looking for r in records if r.tokens_looking]
    top = top_words(looking_tokens, n=25)
    if top:
        labels = [w for w, _ in top]
        values = [float(n) for _, n in top]
        bar_chart(
            labels, values,
            title='Top words in "Looking For" sections (excluding stopwords)',
            out_dir=charts_dir,
            filename_base="lookingfor_top_words",
            xlabel="Word",
            ylabel="Count",
            rotate=30,
        )

        write_csv(
            tables_dir / "lookingfor_top_words.csv",
            [{"word": w, "count": n} for w, n in top],
            ["word", "count"],
        )

    # Categorized counts overall + by gender
    cat_rows: List[Dict[str, Any]] = []
    counts_overall = Counter()
    counts_by_gender = defaultdict(Counter)

    for r in records:
        if not r.tokens_looking:
            continue
        tset = set(r.tokens_looking)
        for cat, keys in LOOKING_FOR_CATEGORIES.items():
            if contains_any(tset, keys):
                counts_overall[cat] += 1
                counts_by_gender[r.gender][cat] += 1

    cats = list(LOOKING_FOR_CATEGORIES.keys())
    bar_chart(
        cats,
        [float(counts_overall[c]) for c in cats],
        title='What People Want: category counts from "Looking For" sections',
        out_dir=charts_dir,
        filename_base="lookingfor_category_counts",
        xlabel="Category",
        ylabel="Profiles mentioning category",
        rotate=25,
    )

    # By gender (keep readable: plot Women/Men/Non-binary/Unknown if present)
    genders_present = sorted({r.gender for r in records})
    series = {}
    for g in genders_present:
        series[g] = [float(counts_by_gender[g][c]) for c in cats]

    grouped_bar_chart(
        labels=cats,
        series=series,
        title='What People Want by Gender (from "Looking For")',
        out_dir=charts_dir,
        filename_base="lookingfor_category_by_gender",
        xlabel="Category",
        ylabel="Profiles mentioning category",
        rotate=25,
    )

    for c in cats:
        cat_rows.append({"category": c, "count_overall": counts_overall[c]})
    write_csv(
        tables_dir / "lookingfor_category_counts.csv",
        cat_rows,
        ["category", "count_overall"],
    )

    # -------------------------
    # 3) Tone classification + distributions
    # -------------------------
    tone_rows: List[Dict[str, Any]] = []
    humor_dist_by_gender = defaultdict(Counter)
    vuln_dist_by_gender = defaultdict(Counter)

    humor_dist_by_age = defaultdict(Counter)
    vuln_dist_by_age = defaultdict(Counter)

    humor_categories = ["Humorous", "Neutral", "Serious"]
    vuln_categories = ["Vulnerable", "Neutral", "Guarded"]

    for r in records:
        tone = classify_tone(r.tokens_all)
        ag = age_group(r.age)

        humor_dist_by_gender[r.gender][tone["humor"]] += 1
        vuln_dist_by_gender[r.gender][tone["vulnerability"]] += 1

        humor_dist_by_age[ag][tone["humor"]] += 1
        vuln_dist_by_age[ag][tone["vulnerability"]] += 1

        tone_rows.append({
            "id": r.id,
            "gender": r.gender,
            "age": r.age if r.age is not None else "",
            "age_group": ag,
            "humor": tone["humor"],
            "vulnerability": tone["vulnerability"],
        })

    write_csv(
        tables_dir / "tone_classification_per_profile.csv",
        tone_rows,
        ["id", "gender", "age", "age_group", "humor", "vulnerability"],
    )

    # Stacked bars by gender
    genders = sorted(humor_dist_by_gender.keys())
    stacked_bar_distribution(
        groups=genders,
        categories=humor_categories,
        matrix=humor_dist_by_gender,
        title="Tone: Humorous vs Serious distribution by Gender",
        out_dir=charts_dir,
        filename_base="tone_humor_by_gender",
        xlabel="Gender",
    )

    stacked_bar_distribution(
        groups=genders,
        categories=vuln_categories,
        matrix=vuln_dist_by_gender,
        title="Tone: Vulnerable vs Guarded distribution by Gender",
        out_dir=charts_dir,
        filename_base="tone_vulnerability_by_gender",
        xlabel="Gender",
    )

    # Stacked bars by age group (fixed order)
    age_groups = ["Gen Z (<25)", "Millennial (25–40)", "Gen X (41–56)", "Boomer+ (57+)", "Unknown"]
    age_groups_present = [g for g in age_groups if g in humor_dist_by_age]

    stacked_bar_distribution(
        groups=age_groups_present,
        categories=humor_categories,
        matrix=humor_dist_by_age,
        title="Tone: Humorous vs Serious distribution by Age Group",
        out_dir=charts_dir,
        filename_base="tone_humor_by_agegroup",
        xlabel="Age Group",
        rotate=15,
    )

    stacked_bar_distribution(
        groups=age_groups_present,
        categories=vuln_categories,
        matrix=vuln_dist_by_age,
        title="Tone: Vulnerable vs Guarded distribution by Age Group",
        out_dir=charts_dir,
        filename_base="tone_vulnerability_by_agegroup",
        xlabel="Age Group",
        rotate=15,
    )

    # Also dump summary tables (counts) for reproducibility
    summary_rows = []
    for g in genders:
        row = {"group": g}
        for c in humor_categories:
            row[f"humor_{c.lower()}"] = humor_dist_by_gender[g].get(c, 0)
        for c in vuln_categories:
            row[f"vuln_{c.lower()}"] = vuln_dist_by_gender[g].get(c, 0)
        summary_rows.append(row)

    write_csv(
        tables_dir / "tone_summary_by_gender.csv",
        summary_rows,
        ["group",
         "humor_humorous", "humor_neutral", "humor_serious",
         "vuln_vulnerable", "vuln_neutral", "vuln_guarded"],
    )

    print(f"\nSaved charts to: {charts_dir}")
    print(f"Saved tables to: {tables_dir}")
    print("Done. Your profiles have been turned into rectangles and moral judgments.\n")


# -----------------------------
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="DateMeDirectory analysis: Step 6 advanced graphs")
    ap.add_argument("--input", type=str, default="data/profiles_master.json", help="Path to profiles JSON")
    ap.add_argument("--out", type=str, default="", help="Output directory (default: data/analysis/YYYYMMDD)")
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    in_path = Path(args.input)

    if args.out.strip():
        out_root = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y%m%d")
        out_root = Path("data") / "analysis" / stamp

    ensure_dir(out_root)

    records = load_profiles(in_path)
    print(f"Loaded {len(records)} profiles from {in_path}")

    # quick sanity
    genders = Counter(r.gender for r in records)
    print("Gender counts:", dict(genders))
    ages_known = sum(1 for r in records if r.age is not None)
    print(f"Ages present: {ages_known}/{len(records)}")

    make_step6_charts(records, out_root)

if __name__ == "__main__":
    main()
