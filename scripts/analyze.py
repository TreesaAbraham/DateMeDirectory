# scripts/analyze.py
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def load_profiles(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"[error] file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("[error] expected a JSON list of profiles")

    # enforce dict-ish
    profiles: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            profiles.append(item)
        else:
            print(f"[warn] skipping non-dict entry at index {i}")
    return profiles


def normalize_gender(x: Any) -> str:
    s = str(x or "").strip().lower()
    # handle common tokens from directory scrape (M/F/NB)
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


def last_location_token(loc: str) -> str:
    """
    For crude 'pattern' counts:
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
    print(f"  missing: {age.isna().sum()}")
    if len(age_valid) > 0:
        print(f"  count:   {len(age_valid)}")
        print(f"  min:     {int(age_valid.min())}")
        print(f"  max:     {int(age_valid.max())}")
        print(f"  mean:    {age_valid.mean():.2f}")
        print(f"  median:  {age_valid.median():.2f}")
        # simple bins for quick sanity
        bins = [17, 25, 30, 35, 40, 120]
        labels = ["18-25", "26-30", "31-35", "36-40", "41+"]
        binned = pd.cut(age_valid, bins=bins, labels=labels, include_lowest=True)
        print("  by age group:")
        print(binned.value_counts().reindex(labels, fill_value=0).to_string())
    else:
        print("  no valid ages found")

    # ---------- Gender ----------
    print("\n[gender]")
    gender = df.get("gender").apply(normalize_gender) if "gender" in df.columns else pd.Series([], dtype=str)
    if len(gender) > 0:
        print(gender.value_counts(dropna=False).to_string())
    else:
        print("  (no gender field found)")

    # ---------- Location ----------
    print("\n[location]")
    loc = df.get("location").fillna("").astype(str) if "location" in df.columns else pd.Series([], dtype=str)
    if len(loc) > 0:
        loc_clean = loc.str.strip()
        top = loc_clean[loc_clean != ""].value_counts().head(args.top_locations)
        print(f"  top {args.top_locations} (raw strings):")
        print(top.to_string())

        # crude token patterns
        token = loc_clean.apply(last_location_token)
        token_top = token[token != ""].value_counts().head(args.top_locations)
        print(f"\n  top {args.top_locations} (last token heuristic):")
        print(token_top.to_string())
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
