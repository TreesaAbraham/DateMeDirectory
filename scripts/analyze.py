# scripts/analyze.py
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

# -------------------------
# Text metric helpers
# -------------------------
WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)

# heuristic emoji matcher (good enough for trends)
EMOJI_RE = re.compile(
    "["  # noqa: W605
    "\U0001F1E6-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]",
    re.UNICODE,
)

def word_count(text: str) -> int:
    return len(WORD_RE.findall((text or "").strip()))

def split_sentences(text: str) -> list[str]:
    """
    Simple heuristic: split on whitespace after . ! ?
    """
    t = (text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p for p in parts if word_count(p) > 0]

def emoji_count(text: str) -> int:
    return len(EMOJI_RE.findall(text or ""))

def per_100(count: int, words: int) -> float:
    return 0.0 if words <= 0 else (count / words) * 100.0

def compute_text_metrics(full_text: str) -> dict[str, Any]:
    t = full_text or ""
    wc = word_count(t)
    sentences = split_sentences(t)
    sc = len(sentences)

    avg_sent_len = (sum(word_count(s) for s in sentences) / sc) if sc > 0 else 0.0

    exclam = t.count("!")
    questions = t.count("?")
    emojis = emoji_count(t)

    return {
        "word_count": wc,
        "sentence_count": sc,
        "avg_sentence_len_words": float(avg_sent_len),
        "exclam_count": int(exclam),
        "exclam_per_100_words": float(per_100(exclam, wc)),
        "question_count": int(questions),
        "questions_per_100_words": float(per_100(questions, wc)),
        "emoji_count": int(emojis),
        "emoji_per_100_words": float(per_100(emojis, wc)),
    }



def load_profiles(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"[error] file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("[error] expected a JSON list of profiles")

    profiles: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            profiles.append(item)
        else:
            print(f"[warn] skipping non-dict entry at index {i}")
    return profiles


def normalize_gender(x: Any) -> str:
    s = str(x or "").strip().lower()
    mapping = {
        "m": "male",
        "male": "male",
        "man": "male",
        "f": "female",
        "female": "female",
        "woman": "female",
        "nb": "nonbinary",
        "non-binary": "nonbinary",
        "nonbinary": "nonbinary",
        "non binary": "nonbinary",
        "other": "other",
    }
    return mapping.get(s, s or "unknown")


def normalize_loc_flex(x: Any) -> str:
    s = str(x or "").strip().lower()
    mapping = {
        "none": "none",
        "not flexible": "none",
        "no": "none",
        "some": "some",
        "maybe": "some",
        "flexible": "high",
        "very flexible": "high",
        "high": "high",
    }
    return mapping.get(s, s or "unknown")


def normalize_interest_tokens(val: Any) -> list[str]:
    """
    Accepts either:
      - genderInterestedIn: ["male","female"]
      - interestedIn: ["M","F","NB"]
    Returns normalized list like: ["male","female"] (unique, preserved order).
    """
    if val is None:
        return []
    if isinstance(val, str):
        raw = [val]
    elif isinstance(val, list):
        raw = val
    else:
        return []

    out: list[str] = []
    for x in raw:
        s = str(x or "").strip().lower()
        mapping = {
            "m": "male",
            "male": "male",
            "man": "male",
            "f": "female",
            "female": "female",
            "woman": "female",
            "nb": "nonbinary",
            "non-binary": "nonbinary",
            "nonbinary": "nonbinary",
            "other": "other",
        }
        normed = mapping.get(s, "")
        if normed:
            out.append(normed)

    seen = set()
    uniq: list[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def last_location_token(loc: str) -> str:
    """
    Crude 'pattern' counts:
    - If location has commas, take last chunk (often state/country)
    - Otherwise return last word-ish token
    """
    if not loc:
        return ""
    loc = loc.strip()
    if "," in loc:
        return loc.split(",")[-1].strip()
    parts = re.split(r"\s+", loc)
    return parts[-1].strip() if parts else loc


def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze demographics in profiles_master.json")
    ap.add_argument(
        "--input",
        type=Path,
        default=Path("data/profiles_master.json"),
        help="Path to canonical profiles JSON (default: data/profiles_master.json)",
    )
    ap.add_argument(
        "--top-locations",
        type=int,
        default=15,
        help="How many top locations to display (default: 15)",
    )
    args = ap.parse_args()

    profiles = load_profiles(args.input)
    df = pd.DataFrame(profiles)

    print(f"\n[dataset] profiles: {len(df)}")
    if len(df) == 0:
        return

    # ---------- Age ----------
    age = pd.to_numeric(df.get("age"), errors="coerce")
    age_valid = age.dropna()

    print("\n[age]")
    print(f"  missing: {int(age.isna().sum())}")
    if len(age_valid) > 0:
        print(f"  count:   {len(age_valid)}")
        print(f"  min:     {int(age_valid.min())}")
        print(f"  max:     {int(age_valid.max())}")
        print(f"  mean:    {age_valid.mean():.2f}")
        print(f"  median:  {age_valid.median():.2f}")

        bins = [17, 25, 30, 35, 40, 120]
        labels = ["18-25", "26-30", "31-35", "36-40", "41+"]
        binned = pd.cut(age_valid, bins=bins, labels=labels, include_lowest=True)
        print("  by age group:")
        print(binned.value_counts().reindex(labels, fill_value=0).to_string())
    else:
        print("  no valid ages found")

    # ---------- Gender ----------
    print("\n[gender]")
    if "gender" in df.columns:
        gender = df["gender"].apply(normalize_gender)
        print(gender.value_counts(dropna=False).to_string())
    else:
        print("  (no gender field found)")

    # ---------- Interested In ----------
    print("\n[interested in]")

    interest_series = None
    if "genderInterestedIn" in df.columns:
        interest_series = df["genderInterestedIn"]
    elif "interestedIn" in df.columns:
        interest_series = df["interestedIn"]

    if interest_series is None:
        print("  (no interestedIn / genderInterestedIn field found)")
    else:
        interests = interest_series.apply(normalize_interest_tokens)

        interested_male = int(interests.apply(lambda xs: "male" in xs).sum())
        interested_female = int(interests.apply(lambda xs: "female" in xs).sum())
        interested_both_mf = int(interests.apply(lambda xs: ("male" in xs and "female" in xs)).sum())
        interested_nonbinary = int(interests.apply(lambda xs: "nonbinary" in xs).sum())
        interested_other = int(interests.apply(lambda xs: "other" in xs).sum())
        missing_interest = int(interests.apply(lambda xs: len(xs) == 0).sum())

        print(f"  missing/unknown: {missing_interest}")
        print(f"  interested in male: {interested_male}")
        print(f"  interested in female: {interested_female}")
        print(f"  interested in both male+female: {interested_both_mf}")
        if interested_nonbinary > 0:
            print(f"  interested in nonbinary: {interested_nonbinary}")
        if interested_other > 0:
            print(f"  interested in other: {interested_other}")

        combo_counts = interests.apply(lambda xs: ", ".join(xs) if xs else "unknown").value_counts()
        print("\n  top interest combinations:")
        print(combo_counts.head(10).to_string())

    # ---------- Location ----------
    print("\n[location]")
    if "location" in df.columns:
        loc = df["location"].fillna("").astype(str)
        loc_clean = loc.str.strip()

        top = loc_clean[loc_clean != ""].value_counts().head(args.top_locations)
        print(f"  top {args.top_locations} (raw strings):")
        if len(top) > 0:
            print(top.to_string())
        else:
            print("  (no non-empty locations)")

        token = loc_clean.apply(last_location_token)
        token_top = token[token != ""].value_counts().head(args.top_locations)
        print(f"\n  top {args.top_locations} (last token heuristic):")
        if len(token_top) > 0:
            print(token_top.to_string())
        else:
            print("  (no tokens)")
    else:
        print("  (no location field found)")

    # ---------- Location flexibility ----------
    print("\n[location flexibility]")
    if "locationFlexibility" in df.columns:
        flex = df["locationFlexibility"].apply(normalize_loc_flex)
        print(flex.value_counts(dropna=False).to_string())
    else:
        print("  (no locationFlexibility field found)")

    print("\n[done] demographics summary printed.\n")


if __name__ == "__main__":
    main()
