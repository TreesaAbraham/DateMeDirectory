# scripts/merge_fulltext_by_id.py
import argparse
import json
import re
from pathlib import Path

def word_count(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text))

def get_fulltext(p: dict) -> str:
    d = p.get("profileDetails") or {}
    return (d.get("fullText") or "").strip()

def set_fulltext(p: dict, text: str) -> None:
    d = p.get("profileDetails") or {}
    d["fullText"] = text
    p["profileDetails"] = d

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Merge profileDetails.fullText from updates JSON into base JSON by id."
    )
    ap.add_argument("base_json", type=Path, help="Main profiles JSON (list)")
    ap.add_argument("updates_json", type=Path, help="Updates JSON (list)")
    ap.add_argument("output_json", type=Path, help="Merged output JSON")
    ap.add_argument("--min-gain", type=int, default=1, help="Require at least this many extra words to overwrite")
    args = ap.parse_args()

    base = json.loads(args.base_json.read_text(encoding="utf-8"))
    updates = json.loads(args.updates_json.read_text(encoding="utf-8"))

    if not isinstance(base, list) or not isinstance(updates, list):
        raise SystemExit("Both base_json and updates_json must be lists")

    base_by_id = {p.get("id"): p for p in base if p.get("id")}
    touched = 0
    improved = 0
    missing = 0

    for u in updates:
        uid = u.get("id")
        if not uid or uid not in base_by_id:
            missing += 1
            continue

        b = base_by_id[uid]
        old = get_fulltext(b)
        new = get_fulltext(u)

        old_wc = word_count(old)
        new_wc = word_count(new)

        # only overwrite if it’s actually better
        if new_wc >= old_wc + args.min_gain and new_wc > 0:
            set_fulltext(b, new)

            # propagate timestamps/metadata if present
            if "scrapeTimestampDetail" in u:
                b["scrapeTimestampDetail"] = u["scrapeTimestampDetail"]
            for k in ["expandedUrl", "docPlatform"]:
                if k in u and u.get(k):
                    b[k] = u[k]

            improved += 1
        touched += 1

    args.output_json.write_text(
        json.dumps(base, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[done] wrote merged output -> {args.output_json}")
    print(f"[stats] updates_seen={len(updates)} touched={touched} improved={improved} updates_missing_in_base={missing}")

if __name__ == "__main__":
    main()

