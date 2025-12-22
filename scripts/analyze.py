# scripts/analyze.py
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer


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
# Charts (Step 4)
# -------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_age_patterns_chart(out_df: pd.DataFrame, charts_dir: Path) -> Path | None:
    """
    Graph A: Bar chart of average profile length (word_count) by age group.
    """
    if "age" not in out_df.columns or "word_count" not in out_df.columns:
        return None

    age = pd.to_numeric(out_df["age"], errors="coerce")
    valid = out_df.copy()
    valid["age_num"] = age
    valid = valid.dropna(subset=["age_num"])

    if len(valid) == 0:
        return None

    bins = [17, 25, 30, 35, 40, 120]
    labels = ["18-25", "26-30", "31-35", "36-40", "41+"]
    valid["age_group"] = pd.cut(valid["age_num"], bins=bins, labels=labels, include_lowest=True)

    means = valid.groupby("age_group", dropna=False)["word_count"].mean().reindex(labels)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.bar(means.index.astype(str), means.values)
    ax.set_title("Average Profile Length by Age Group")
    ax.set_xlabel("Age Group")
    ax.set_ylabel("Average Word Count")

    out_path = charts_dir / "graph_a_age_patterns.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_exclam_boxplot(out_df: pd.DataFrame, charts_dir: Path) -> Path | None:
    """
    Graph B: Box plot of exclamation points per 100 words by gender.
    """
    if "gender_norm" not in out_df.columns or "exclam_per_100_words" not in out_df.columns:
        return None

    df = out_df.copy()
    df = df[df["word_count"] > 0]
    if len(df) == 0:
        return None

    order = ["female", "male", "nonbinary", "other", "unknown"]
    genders = [g for g in order if g in set(df["gender_norm"].astype(str))] + [
        g for g in sorted(set(df["gender_norm"].astype(str))) if g not in order
    ]

    data = [df.loc[df["gender_norm"] == g, "exclam_per_100_words"].dropna().values for g in genders]

    genders2: list[str] = []
    data2: list[Any] = []
    for g, arr in zip(genders, data):
        if len(arr) > 0:
            genders2.append(g)
            data2.append(arr)

    if not data2:
        return None

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.boxplot(data2, labels=genders2, showfliers=True)
    ax.set_title("Exclamation Points per 100 Words by Gender")
    ax.set_xlabel("Gender")
    ax.set_ylabel("Exclamations per 100 Words")

    out_path = charts_dir / "graph_b_exclam_by_gender.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def save_location_flex_chart(out_df: pd.DataFrame, charts_dir: Path) -> Path | None:
    """
    Graph C: Bar chart of location flexibility.
    Map:
      high -> Open to relocate
      some -> Willing to travel
      none -> Location-specific
    """
    if "locationFlexibility_norm" not in out_df.columns:
        return None

    mapping = {
        "high": "Open to relocate",
        "some": "Willing to travel",
        "none": "Location-specific",
        "unknown": "Unknown",
    }

    df = out_df.copy()
    labels_order = ["Location-specific", "Willing to travel", "Open to relocate", "Unknown"]

    df["locflex_label"] = (
        df["locationFlexibility_norm"]
        .astype(str)
        .str.lower()
        .map(mapping)
        .fillna("Unknown")
    )
    counts = df["locflex_label"].value_counts().reindex(labels_order, fill_value=0)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.bar(counts.index.astype(str), counts.values)
    ax.set_title("Location Flexibility Distribution")
    ax.set_xlabel("Location Flexibility")
    ax.set_ylabel("Profile Count")
    ax.tick_params(axis="x", rotation=15)

    out_path = charts_dir / "graph_c_location_flex.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


# -------------------------
# TF-IDF helpers (Step 5)
# -------------------------
def age_cohort_from_age(age_val: Any) -> str:
    """
    Approx cohorts from *age* (not birth year).
    Using common 2025-ish boundaries:
      Gen Z: 18-28
      Millennials: 29-44
      Gen X: 45+
    """
    try:
        a = int(age_val)
    except Exception:
        return "unknown"
    if 18 <= a <= 28:
        return "gen_z"
    if 29 <= a <= 44:
        return "millennials"
    if a >= 45:
        return "gen_x"
    return "unknown"


def build_tfidf_matrix(
    texts: list[str],
    min_df: int = 3,
    max_df: float = 0.85,
) -> tuple[TfidfVectorizer, Any, list[str]]:
    """
    Fit TF-IDF on per-profile documents.
    Returns (vectorizer, X sparse matrix, feature_names)
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        min_df=min_df,
        max_df=max_df,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z']+\b",
        ngram_range=(1, 2),  # phrases like "emotionally intelligent"
    )
    X = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out().tolist()
    return vectorizer, X, feature_names


def mean_tfidf(X, mask: list[bool]):
    """
    Mean TF-IDF vector for a boolean mask of rows.
    Returns a 1 x n_features dense array (1D).
    """
    import numpy as np

    idx = np.where(mask)[0]
    if len(idx) == 0:
        return None

    v = X[idx].mean(axis=0)
    return v.A1  # flatten to 1D array


def top_terms_by_diff(feature_names: list[str], a_vec, b_vec, top_n: int = 25) -> pd.DataFrame:
    """
    Return top_n terms where (a_vec - b_vec) is largest.
    """
    import numpy as np

    diff = a_vec - b_vec
    order = np.argsort(diff)[::-1][:top_n]
    rows = [{"term": feature_names[i], "score": float(diff[i])} for i in order if diff[i] > 0]
    return pd.DataFrame(rows)


def distinctive_terms_two_group(
    df_text: pd.DataFrame,
    group_col: str,
    group_a: str,
    group_b: str,
    text_col: str = "fullText",
    top_n: int = 25,
    min_df: int = 3,
    max_df: float = 0.85,
) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[None, None]:
    """
    Compute distinctive TF-IDF terms for group_a vs group_b and group_b vs group_a.
    Returns (a_over_b_df, b_over_a_df)
    """
    df2 = df_text[df_text[text_col].astype(str).str.len() > 0].copy()
    if len(df2) < 5:
        return None, None

    texts = df2[text_col].astype(str).tolist()
    _, X, feature_names = build_tfidf_matrix(texts, min_df=min_df, max_df=max_df)

    mask_a = (df2[group_col].astype(str) == group_a).tolist()
    mask_b = (df2[group_col].astype(str) == group_b).tolist()

    a_vec = mean_tfidf(X, mask_a)
    b_vec = mean_tfidf(X, mask_b)
    if a_vec is None or b_vec is None:
        return None, None

    a_over_b = top_terms_by_diff(feature_names, a_vec, b_vec, top_n=top_n)
    b_over_a = top_terms_by_diff(feature_names, b_vec, a_vec, top_n=top_n)
    return a_over_b, b_over_a


def distinctive_terms_multi_group(
    df_text: pd.DataFrame,
    group_col: str,
    groups: list[str],
    text_col: str = "fullText",
    top_n: int = 20,
    min_df: int = 3,
    max_df: float = 0.85,
) -> dict[str, pd.DataFrame]:
    """
    For each group g, compute top terms where mean(g) - mean(not g) is largest.
    Returns dict: group -> dataframe(term, score)
    """
    df2 = df_text[df_text[text_col].astype(str).str.len() > 0].copy()
    results: dict[str, pd.DataFrame] = {}
    if len(df2) < 5:
        return results

    texts = df2[text_col].astype(str).tolist()
    _, X, feature_names = build_tfidf_matrix(texts, min_df=min_df, max_df=max_df)

    for g in groups:
        mask_g = (df2[group_col].astype(str) == g).tolist()
        mask_not = (df2[group_col].astype(str) != g).tolist()

        g_vec = mean_tfidf(X, mask_g)
        not_vec = mean_tfidf(X, mask_not)
        if g_vec is None or not_vec is None:
            continue

        results[g] = top_terms_by_diff(feature_names, g_vec, not_vec, top_n=top_n)

    return results


# -------------------------
# Main
# -------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Analyze demographics + text metrics + charts + TF-IDF for Date Me Directory"
    )
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
    ap.add_argument(
        "--charts-dir",
        type=Path,
        default=Path("data/charts"),
        help="Directory to save PNG charts (default: data/charts)",
    )
    ap.add_argument(
        "--no-charts",
        action="store_true",
        help="Disable chart generation",
    )

    # Step 5 args
    ap.add_argument(
        "--out-tables-dir",
        type=Path,
        default=Path("data/analysis/tables"),
        help="Directory to save TF-IDF tables as CSVs (default: data/analysis/tables)",
    )
    ap.add_argument(
        "--no-tfidf",
        action="store_true",
        help="Disable TF-IDF distinctive vocabulary tables",
    )
    ap.add_argument(
        "--tfidf-min-df",
        type=int,
        default=3,
        help="TF-IDF min_df (default: 3)",
    )
    ap.add_argument(
        "--tfidf-max-df",
        type=float,
        default=0.85,
        help="TF-IDF max_df (default: 0.85)",
    )
    ap.add_argument(
        "--tfidf-top-n",
        type=int,
        default=25,
        help="How many top terms to print/save per group (default: 25)",
    )
    ap.add_argument(
        "--min-group-size",
        type=int,
        default=20,
        help="Minimum profiles required for a group to be included (default: 20)",
    )

    args = ap.parse_args()

    profiles = load_profiles(args.input)
    df = pd.DataFrame(profiles)

    print(f"\n[dataset] profiles: {len(df)}")
    if len(df) == 0:
        return

    # ---------- Step 2: demographics ----------
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

    print("\n[gender]")
    if "gender" in df.columns:
        df["gender_norm"] = df["gender"].apply(normalize_gender)
        print(df["gender_norm"].value_counts(dropna=False).to_string())
    else:
        df["gender_norm"] = "unknown"
        print("  (no gender field found)")

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

    # Optional CSV export
    if args.out_metrics_csv:
        out_path = args.out_metrics_csv
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_path, index=False)
        print(f"\n[output] wrote per-profile stylistic metrics CSV: {out_path}")

    # ---------- Step 4: charts ----------
    if not args.no_charts:
        charts_dir = args.charts_dir
        ensure_dir(charts_dir)

        a = save_age_patterns_chart(out_df, charts_dir)
        b = save_exclam_boxplot(out_df, charts_dir)
        c = save_location_flex_chart(out_df, charts_dir)

        print("\n[charts]")
        if a:
            print(f"  wrote: {a}")
        else:
            print("  Graph A skipped (missing/invalid age or word_count)")

        if b:
            print(f"  wrote: {b}")
        else:
            print("  Graph B skipped (missing gender or exclam data)")

        if c:
            print(f"  wrote: {c}")
        else:
            print("  Graph C skipped (missing locationFlexibility)")

    # ---------- Step 5: TF-IDF distinctive vocabulary ----------
    if not args.no_tfidf:
        tables_dir = args.out_tables_dir
        tables_dir.mkdir(parents=True, exist_ok=True)

        df_text = df.copy()
        df_text["fullText"] = df_text["fullText"].astype(str)

        df_text["word_count_tmp"] = df_text["fullText"].apply(word_count)
        df_text = df_text[df_text["word_count_tmp"] > 0].copy()

        print("\n[tfidf] distinctive vocabulary tables")

        # A) Women vs Men
        df_text["gender_norm"] = df_text.get("gender_norm", "unknown").astype(str)
        gender_counts = df_text["gender_norm"].value_counts().to_dict()
        print(f"  gender counts (with text): {gender_counts}")

        if gender_counts.get("female", 0) >= args.min_group_size and gender_counts.get("male", 0) >= args.min_group_size:
            w_over_m, m_over_w = distinctive_terms_two_group(
                df_text=df_text,
                group_col="gender_norm",
                group_a="female",
                group_b="male",
                text_col="fullText",
                top_n=args.tfidf_top_n,
                min_df=args.tfidf_min_df,
                max_df=args.tfidf_max_df,
            )

            if w_over_m is not None and m_over_w is not None:
                print("\n  [women vs men] top distinctive terms (women)")
                print(w_over_m.to_string(index=False))

                print("\n  [women vs men] top distinctive terms (men)")
                print(m_over_w.to_string(index=False))

                w_over_m.to_csv(tables_dir / "tfidf_women_over_men.csv", index=False)
                m_over_w.to_csv(tables_dir / "tfidf_men_over_women.csv", index=False)

                print(f"\n  saved: {tables_dir / 'tfidf_women_over_men.csv'}")
                print(f"  saved: {tables_dir / 'tfidf_men_over_women.csv'}")
            else:
                print("  [women vs men] skipped (could not compute vectors)")
        else:
            print("  [women vs men] skipped (not enough profiles in female and/or male)")

        # B) Age cohorts
        df_text["age_cohort"] = df_text.get("age", None).apply(age_cohort_from_age)
        cohort_counts = df_text["age_cohort"].value_counts().to_dict()
        print(f"\n  age cohort counts (with text): {cohort_counts}")

        cohorts = [c for c, n in cohort_counts.items() if n >= args.min_group_size and c != "unknown"]
        if cohorts:
            results = distinctive_terms_multi_group(
                df_text=df_text,
                group_col="age_cohort",
                groups=cohorts,
                text_col="fullText",
                top_n=min(args.tfidf_top_n, 20),
                min_df=args.tfidf_min_df,
                max_df=args.tfidf_max_df,
            )

            for cohort, table in results.items():
                print(f"\n  [age cohort: {cohort}] top distinctive terms")
                print(table.to_string(index=False))
                out_path = tables_dir / f"tfidf_age_{cohort}.csv"
                table.to_csv(out_path, index=False)
                print(f"  saved: {out_path}")
        else:
            print("  [age cohorts] skipped (no cohort meets min group size)")

        # C) Location groups (if enough data)
        if "location" in df_text.columns:
            df_text["region"] = df_text["location"].fillna("").astype(str).str.strip().apply(last_location_token)
            df_text["region"] = df_text["region"].replace("", "unknown")

            region_counts = df_text["region"].value_counts()
            eligible_regions = region_counts[region_counts >= args.min_group_size].head(10).index.tolist()
            eligible_regions = [r for r in eligible_regions if r != "unknown"]

            print(f"\n  region groups eligible (>= {args.min_group_size} profiles): {eligible_regions}")

            if eligible_regions:
                results = distinctive_terms_multi_group(
                    df_text=df_text,
                    group_col="region",
                    groups=eligible_regions,
                    text_col="fullText",
                    top_n=min(args.tfidf_top_n, 20),
                    min_df=args.tfidf_min_df,
                    max_df=args.tfidf_max_df,
                )

                for region, table in results.items():
                    print(f"\n  [region: {region}] top distinctive terms")
                    print(table.to_string(index=False))
                    safe_region = re.sub(r"[^a-zA-Z0-9_]+", "_", str(region)).strip("_")
                    out_path = tables_dir / f"tfidf_region_{safe_region}.csv"
                    table.to_csv(out_path, index=False)
                    print(f"  saved: {out_path}")
            else:
                print("  [locations] skipped (no region meets min group size)")
        else:
            print("  [locations] skipped (no location field)")

    print("\n[done]\n")


if __name__ == "__main__":
    main()
