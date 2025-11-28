from pathlib import Path
import argparse
import json
import logging

LOGGER = logging.getLogger(__name__)


def merge_js_longform(
    main_path: Path,
    js_path: Path,
    output_path: Path,
) -> None:
    """
    Merge fullText from JS-scraped profiles into the main profiles file.

    Strategy:
    - Load main profiles (all accessible profiles).
    - Load JS-only profiles (Notion/Compass) that already have fullText.
    - Build a lookup by id for JS profiles.
    - For each profile in main:
        - If there's a matching JS profile with fullText, overwrite
          profileDetails.fullText and optionally scrapeTimestampDetail.
    - Save to output_path.
    """
    LOGGER.info("Loading main profiles from %s", main_path)
    with main_path.open("r", encoding="utf-8") as f:
        main_profiles = json.load(f)

    LOGGER.info("Loading JS profiles with text from %s", js_path)
    with js_path.open("r", encoding="utf-8") as f:
        js_profiles = json.load(f)

    js_by_id = {p.get("id"): p for p in js_profiles if p.get("id")}

    updated = 0
    total = len(main_profiles)

    for profile in main_profiles:
        pid = profile.get("id")
        if not pid:
            continue

        js_profile = js_by_id.get(pid)
        if not js_profile:
            continue

        js_details = js_profile.get("profileDetails") or {}
        full_text = js_details.get("fullText")
        if not full_text:
            continue

        details = profile.get("profileDetails") or {}
        details["fullText"] = full_text
        profile["profileDetails"] = details

        # propagate scrapeTimestampDetail if present
        if "scrapeTimestampDetail" in js_profile:
            profile["scrapeTimestampDetail"] = js_profile["scrapeTimestampDetail"]

        updated += 1

    LOGGER.info(
        "Merged JS fullText into %d profiles out of %d main profiles",
        updated,
        total,
    )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(main_profiles, f, indent=2, ensure_ascii=False)

    LOGGER.info("Saved merged profiles to %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge JS-scraped fullText back into main profiles_accessible JSON"
    )
    parser.add_argument(
        "main_json",
        type=Path,
        help="Path to main profiles_accessible.with_text.json",
    )
    parser.add_argument(
        "js_json",
        type=Path,
        help="Path to profiles_js_only.with_text.json",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to merged output JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    merge_js_longform(args.main_json, args.js_json, args.output_json)


if __name__ == "__main__":
    main()
