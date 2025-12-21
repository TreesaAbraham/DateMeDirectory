# scripts/analyze.py
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


# -------------------------
# Load
# -------------------------
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


# -------------------------
# Normalizers (Step 2)
# -------------------------
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

    # unique, preserve order
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


# -------------------------
# Text metric helpers (Step 3)
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


def get_full_text(profile: dict[str, Any]) -> str:
    details = profile.get("profileDetails") or {}
    if isinstance(details, dict):
        return str(details.get("fullText") or "")
    return ""


# -------------------------
# Main
# -------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze demographics + text metrics for Date Me Directory")
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
    ap.add_argument(
        "--out-metrics-csv",
        type=Path,
        default=None,
        help="Optional output CSV path for per-profile stylistic metrics",
    )
    args = ap.parse_args()

    profiles = load_profiles(args.input)
    df = pd.DataFrame(profiles)

    print(f"\n[dataset] profiles: {len(df)}")
    if len(df) == 0:
        return

    # ---------- Step 2: demographics ----------
    # Age
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

    # Gender
    print("\n[gender]")
    if "gender" in df.columns:
        df["gender_norm"] = df["gender"].apply(normalize_gender)
        print(df["gender_norm"].value_counts(dropna=False).to_string())
    else:
        df["gender_norm"] = "unknown"
        print("  (no gender field found)")

    # Interested In
    print("\n[interested in]")
    interest_series = None
    if "genderInterestedIn" in df.columns:
        interest_series = df["genderInterestedIn"]
    elif "interestedIn" in df.columns:
        interest_series = df["interestedIn"]

    if interest_series is None:
        df["interested_norm"] = [[] for _ in range(len(df))]
        print("  (no interestedIn / genderInterestedIn field found)")
    else:
        df["interested_norm"] = interest_series.apply(normalize_interest_tokens)
        interested = df["interested_norm"]

        interested_male = int(interested.apply(lambda xs: "male" in xs).sum())
        interested_female = int(interested.apply(lambda xs: "female" in xs).sum())
        interested_both_mf = int(interested.apply(lambda xs: ("male" in xs and "female" in xs)).sum())
        missing_interest = int(interested.apply(lambda xs: len(xs) == 0).sum())

        print(f"  missing/unknown: {missing_interest}")
        print(f"  interested in male: {interested_male}")
        print(f"  interested in female: {interested_female}")
        print(f"  interested in both male+female: {interested_both_mf}")

        combo_counts = interested.apply(lambda xs: ", ".join(xs) if xs else "unknown").value_counts()
        print("\n  top interest combinations:")
        print(combo_counts.head(10).to_string())

    # Location
    print("\n[location]")
    if "location" in df.columns:
        loc = df["location"].fillna("").astype(str).str.strip()

        top = loc[loc != ""].value_counts().head(args.top_locations)
        print(f"  top {args.top_locations} (raw strings):")
        if len(top) > 0:
            print(top.to_string())
        else:
            print("  (no non-empty locations)")

        token = loc.apply(last_location_token)
        token_top = token[token != ""].value_counts().head(args.top_locations)
        print(f"\n  top {args.top_locations} (last token heuristic):")
        if len(token_top) > 0:
            print(token_top.to_string())
        else:
            print("  (no tokens)")
    else:
        print("  (no location field found)")

    # Location flexibility
    print("\n[location flexibility]")
    if "locationFlexibility" in df.columns:
        df["locationFlexibility_norm"] = df["locationFlexibility"].apply(normalize_loc_flex)
        print(df["locationFlexibility_norm"].value_counts(dropna=False).to_string())
    else:
        df["locationFlexibility_norm"] = "unknown"
        print("  (no locationFlexibility field found)")

    # ---------- Step 3: text analysis ----------
    df["fullText"] = df.apply(lambda row: get_full_text(row.to_dict()), axis=1)

    metrics = df["fullText"].apply(compute_text_metrics).apply(pd.Series)

    out_df = pd.concat(
        [
            df[["id", "age", "gender_norm", "location", "locationFlexibility_norm", "profileUrl"]],
            metrics,
        ],
        axis=1,
    )

    has_text = out_df["word_count"] > 0

    print("\n[text coverage]")
    print(f"  profiles with any text: {int(has_text.sum())} / {len(out_df)}")

    if int(has_text.sum()) > 0:
        print("\n[summary stats] (profiles with text)")
        cols = [
            "word_count",
            "avg_sentence_len_words",
            "exclam_per_100_words",
            "emoji_per_100_words",
            "questions_per_100_words",
        ]
        for c in cols:
            s = pd.to_numeric(out_df.loc[has_text, c], errors="coerce").dropna()
            print(
                f"  {c}: mean={s.mean():.3f} | median={s.median():.3f} | "
                f"min={s.min():.3f} | max={s.max():.3f}"
            )

    # Optional CSV export = “Stylistic metrics for each profile”
    if args.out_metrics_csv:
        out_path = args.out_metrics_csv
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_path, index=False)
        print(f"\n[output] wrote per-profile stylistic metrics CSV: {out_path}")

    print("\n[done]\n")


if __name__ == "__main__":
    main()
