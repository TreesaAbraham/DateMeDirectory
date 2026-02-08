#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN_JSON = REPO_ROOT / "data" / "profiles_master.json"

DEFAULT_OUT_PNG = (
    REPO_ROOT
    / "data"
    / "charts"
    / "seaborn"
    / "png"
    / "word_graph_11_gym_mentions_by_career_field.png"
)
DEFAULT_OUT_SVG = (
    REPO_ROOT
    / "data"
    / "charts"
    / "seaborn"
    / "svg"
    / "word_graph_11_gym_mentions_by_career_field.svg"
)

FIELDS_ORDER = ["STUDENT", "ARTS_HUMANITIES", "ENGINEERING", "MEDICINE", "OTHER"]
FIELD_LABEL = {
    "STUDENT": "Students",
    "ARTS_HUMANITIES": "Arts & Humanities",
    "ENGINEERING": "Engineering",
    "MEDICINE": "Medicine/Health",
    "OTHER": "Other",
}

# --- Career bucket regexes (heuristics) ---
STUDENT_PATTERNS = [
    r"\bstudent\b", r"\bundergrad(uate)?\b", r"\bgrad(uate)?\s+student\b",
    r"\bphd\b", r"\bmaster'?s\b", r"\bmajor(ing)?\b",
    r"\buniversity\b", r"\bcollege\b", r"\bclass of\b", r"\bcampus\b",
]
ENGINEERING_PATTERNS = [
    r"\bengineer(ing)?\b", r"\bsoftware\b", r"\bdeveloper\b", r"\bprogrammer\b", r"\bcoding\b",
    r"\bcomputer science\b", r"\bcs\b", r"\bdata engineer\b",
    r"\bmechanical\b", r"\belectrical\b", r"\bcivil\b", r"\baerospace\b",
    r"\bchemical\b", r"\bindustrial\b", r"\bsystems\b", r"\brobot(ic|ics)\b",
]
MEDICINE_PATTERNS = [
    r"\bmedical\b", r"\bmed\s*student\b", r"\bmedical\s+student\b",
    r"\bdoctor\b", r"\bphysician\b", r"\bmd\b", r"\bdo\b",
    r"\bnurse\b", r"\brn\b", r"\bpa\b", r"\bparamedic\b", r"\bemt\b",
    r"\bpharmac(y|ist)\b", r"\bdent(al|ist)\b", r"\bveterin(ary|arian)\b",
    r"\btherap(y|ist)\b", r"\bphysical therapy\b", r"\boccupational therapy\b",
    r"\bclinical\b", r"\bhospital\b", r"\bpublic health\b",
]
ARTS_HUMANITIES_PATTERNS = [
    r"\bart(ist|s)?\b", r"\bwriter\b", r"\bauthor\b", r"\bpoet\b", r"\bmusician\b", r"\bsinger\b",
    r"\bactor\b", r"\btheat(re|er)\b", r"\bdancer\b", r"\bphotograph(er|y)\b", r"\bpainter\b",
    r"\bgraphic\s+design(er)?\b", r"\bdesigner\b", r"\billustrat(or|ion)\b",
    r"\bhistory\b", r"\benglish\b", r"\bphilosophy\b", r"\blinguistics\b",
    r"\bjournalis(m|t)\b", r"\bcommunications\b", r"\bliterature\b", r"\bhumanities\b",
]

# --- Gym/exercise regexes ---
GYM_PATTERNS = [
    r"\bgym\b",
    r"\bwork\s*out\b", r"\bworkout(s)?\b",
    r"\bexercise\b",
    r"\blift(ing)?\b", r"\bweight\s*lift(ing)?\b", r"\bweightlifting\b", r"\bweights\b",
    r"\bcardio\b", r"\bhiit\b", r"\bcrossfit\b",
    r"\brun(ning)?\b", r"\bjog(ging)?\b",
    r"\bcycle(ing)?\b", r"\bspin\b",
    r"\bswim(ming)?\b",
    r"\byoga\b", r"\bpilates\b",
    r"\bhike(ing)?\b",
    r"\bclimb(ing)?\b", r"\bboulder(ing)?\b",
    r"\bfitness\b",
]

def _compile_any(patterns: List[str]) -> re.Pattern:
    return re.compile("(" + "|".join(patterns) + ")", flags=re.IGNORECASE)

RE_STUDENT = _compile_any(STUDENT_PATTERNS)
RE_ENGINEERING = _compile_any(ENGINEERING_PATTERNS)
RE_MEDICINE = _compile_any(MEDICINE_PATTERNS)
RE_ARTS = _compile_any(ARTS_HUMANITIES_PATTERNS)
RE_GYM = _compile_any(GYM_PATTERNS)


def get_fulltext(p: dict) -> str:
    pd_ = p.get("profileDetails") or {}
    if isinstance(pd_, dict):
        for k in ("fullText", "full_text", "fulltext", "text", "body"):
            v = pd_.get(k)
            if isinstance(v, str) and v.strip():
                return v
    v = p.get("fullText")
    return v if isinstance(v, str) else ""


def extract_career_text(profile: Dict[str, Any]) -> str:
    chunks: List[str] = []

    for k in [
        "occupation", "job", "jobTitle", "title", "company", "industry",
        "education", "school", "major", "field", "career",
    ]:
        v = profile.get(k)
        if isinstance(v, str) and v.strip():
            chunks.append(v)

    details = profile.get("profileDetails")
    if isinstance(details, dict):
        sections = details.get("sections")
        if isinstance(sections, dict):
            for sk, sv in sections.items():
                if not (isinstance(sv, str) and sv.strip()):
                    continue
                sk_l = str(sk).lower()
                if any(t in sk_l for t in ["work", "job", "career", "education", "school", "major", "industry", "profession"]):
                    chunks.append(sv)

        for k, v in details.items():
            if not (isinstance(v, str) and v.strip()):
                continue
            k_l = str(k).lower()
            if any(t in k_l for t in ["work", "job", "career", "education", "school", "major", "industry", "profession"]):
                chunks.append(v)

    if not chunks:
        chunks.append(get_fulltext(profile))

    return "\n".join(chunks)


def classify_field(career_text: str) -> str:
    t = career_text or ""

    # medical student => MEDICINE
    if re.search(r"\bmed\s*student\b|\bmedical\s+student\b", t, flags=re.IGNORECASE):
        return "MEDICINE"

    if RE_STUDENT.search(t):
        return "STUDENT"
    if RE_ENGINEERING.search(t):
        return "ENGINEERING"
    if RE_MEDICINE.search(t):
        return "MEDICINE"
    if RE_ARTS.search(t):
        return "ARTS_HUMANITIES"
    return "OTHER"


def gym_mentioned(full_text: str) -> int:
    if not full_text:
        return 0
    return 1 if RE_GYM.search(full_text) else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_IN_JSON)
    ap.add_argument("--out_png", type=Path, default=DEFAULT_OUT_PNG)
    ap.add_argument("--out_svg", type=Path, default=DEFAULT_OUT_SVG)
    args = ap.parse_args()

    profiles = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("profiles_master.json must be a list")

    totals = {k: 0 for k in FIELDS_ORDER}
    hits = {k: 0 for k in FIELDS_ORDER}
    total_all = 0
    hit_all = 0

    for p in profiles:
        field = classify_field(extract_career_text(p))
        hit = gym_mentioned(get_fulltext(p))

        totals[field] += 1
        hits[field] += hit
        total_all += 1
        hit_all += hit

    rows = []
    for k in FIELDS_ORDER:
        t = totals[k]
        h = hits[k]
        pct = (h / t * 100.0) if t else 0.0
        rows.append(
            {
                "career_field": k,
                "career_field_label": FIELD_LABEL[k],
                "total_profiles": t,
                "gym_profiles": h,
                "gym_pct": pct,
            }
        )

    df = pd.DataFrame(rows)
    df["career_field_label"] = pd.Categorical(
        df["career_field_label"],
        categories=[FIELD_LABEL[k] for k in FIELDS_ORDER],
        ordered=True,
    )

    overall_pct = (hit_all / total_all * 100.0) if total_all else 0.0

    # ---- Plot styling ----
    sns.set_theme(style="whitegrid")
    # You said "have fun": this palette is loud but readable.
    palette = sns.color_palette("Spectral", n_colors=len(df))

    plt.close("all")
    fig, ax = plt.subplots(figsize=(11.2, 6.2))

    sns.barplot(
        data=df,
        y="career_field_label",
        x="gym_pct",
        palette=palette,
        ax=ax,
        edgecolor="black",
        linewidth=0.6,
    )

    ax.set_xlabel("Percent of profiles mentioning gym/exercise")
    ax.set_ylabel("")
    ax.set_title("Gym/exercise mentions by career field", loc="left", fontsize=18, weight="bold")

    ax.text(
        1.0,
        1.02,
        f"Overall: {overall_pct:.1f}% ({hit_all}/{total_all})",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
    )

    # annotate bars with % and counts
    for i, r in df.reset_index(drop=True).iterrows():
        txt = f"{r['gym_pct']:.1f}% ({int(r['gym_profiles'])}/{int(r['total_profiles'])})"
        ax.text(float(r["gym_pct"]) + 0.6, i, txt, va="center", fontsize=10)

    x_max = max(5, float(df["gym_pct"].max()) * 1.18 if len(df) else 5)
    ax.set_xlim(0, x_max)

    sns.despine(left=True, bottom=False)
    fig.tight_layout()

    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    args.out_svg.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(args.out_png, dpi=220, bbox_inches="tight")
    fig.savefig(args.out_svg, bbox_inches="tight")

    print(f"[out] {args.out_png}")
    print(f"[out] {args.out_svg}")


if __name__ == "__main__":
    main()
