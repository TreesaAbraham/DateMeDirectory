# scripts/build_text_queue.py
import argparse
import json
import re
from collections import Counter
from pathlib import Path

INTENTIONAL_SHORT_PHRASES = [
    "not currently looking",
    "no longer seeking",
    "i’ve met someone",
    "i'm seeing someone",
    "im seeing someone",
]

def word_count(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text))

def get_fulltext(profile: dict) -> str:
    details = profile.get("profileDetails") or {}
    return (details.get("fullText") or "").strip()

def is_intentional_short(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in INTENTIONAL_SHORT_PHRASES)

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build a JSON queue of profiles whose fullText is missing/too short."
    )
    ap.add_argument("input_json", type=Path, help="Main profiles JSON (list)")
    ap.add_argument("output_json", type=Path, help="Queue output JSON")
    ap.add_argument("--min-words", type=int, default=120, help="Minimum words required")
    ap.add_argument(
        "--include-intentional-short",
        action="store_true",
        help="Include intentional short profiles (default excludes them)",
    )
    args = ap.parse_args()

    profiles = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("input_json must be a list of profiles")

    queue = []
    platform_counts = Counter()
    reasons = Counter()

    for p in profiles:
        ft = get_fulltext(p)
        wc = word_count(ft)

        if wc >= args.min_words:
            continue

        if (not args.include_intentional_short) and is_intentional_short(ft):
            reasons["excluded_intentional_short"] += 1
            continue

        reason = "missing_fullText" if wc == 0 else f"under_{args.min_words}_words"
        reasons[reason] += 1

        platform = p.get("docPlatform") or "unknown"
        platform_counts[platform] += 1

        # keep the whole profile so your rescrapers have URL/id/details
        queue.append(p)

    args.output_json.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[done] queued {len(queue)} profiles -> {args.output_json}")
    print("[reasons]")
    for k, v in reasons.most_common():
        print(f"  {k:28} {v}")
    print("[docPlatform]")
    for k, v in platform_counts.most_common():
        print(f"  {k:28} {v}")

if __name__ == "__main__":
    main()
