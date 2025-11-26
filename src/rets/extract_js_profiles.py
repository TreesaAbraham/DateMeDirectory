from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import logging

LOGGER = logging.getLogger(__name__)

JS_DOMAINS = [
    "notion.so",
    "notion.site",
    "compass.com",      # adjust as needed for actual Compass host
    "compassmeet.com",  # if that's the domain, change to real one you see
]


def is_js_heavy_profile(url: str) -> bool:
    if not url:
        return False
    netloc = urlparse(url).netloc.lower()
    return any(domain in netloc for domain in JS_DOMAINS)


def extract_js_profiles(input_path: Path, output_path: Path) -> None:
    LOGGER.info("Loading profiles from %s", input_path)
    with input_path.open("r", encoding="utf-8") as f:
        profiles = json.load(f)

    js_profiles = [p for p in profiles if is_js_heavy_profile(p.get("profileUrl"))]

    LOGGER.info("Found %d JS-heavy profiles (Notion/Compass/etc.)", len(js_profiles))
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(js_profiles, f, indent=2, ensure_ascii=False)
    LOGGER.info("Saved JS-heavy profiles to %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Notion/Compass (JS-heavy) profiles into a separate JSON file"
    )
    parser.add_argument("input_json", type=Path, help="Path to profiles_accessible.json")
    parser.add_argument("output_json", type=Path, help="Path to profiles_js_only.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    extract_js_profiles(args.input_json, args.output_json)


if __name__ == "__main__":
    main()
