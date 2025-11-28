# src/rets/tag_short_profiles_platform.py

import json
import argparse
from pathlib import Path
from urllib.parse import urlparse


def classify_platform(url: str) -> str:
    if not url:
        return "unknown"

    netloc = (urlparse(url).netloc or "").lower()
    path = (urlparse(url).path or "").lower()

    # URL shorteners
    if "bit.ly" in netloc or "tinyurl.com" in netloc:
        return "shortener"

    # Google Docs / Slides / Drive
    if "docs.google.com" in netloc:
        if "/document/" in path:
            return "google_docs"
        if "/presentation/" in path:
            return "google_slides"
        return "google_docs_other"

    if "drive.google.com" in netloc:
        return "google_drive_file"

    # Notion
    if "notion.so" in netloc or "notion.site" in netloc:
        return "notion"

    # Dropbox
    if "dropbox.com" in netloc or "paper.dropbox.com" in netloc:
        if "paper.dropbox.com" in netloc or "/paper/" in path:
            return "dropbox_paper"
        return "dropbox_file"

    # Proton / Yandex cloud
    if "proton.me" in netloc:
        return "proton_drive"
    if "yandex.com" in netloc or "yandex.ru" in netloc:
        return "yandex_disk"

    # Coda / Firefly / etc
    if "coda.io" in netloc:
        return "coda"
    if "cuties.app" in netloc:
        return "cuties_app"
    if "datefirefly.com" in netloc:
        return "datefirefly"
    if "carrd.co" in netloc:
        return "carrd"
    if "twitter.com" in netloc or "x.com" in netloc:
        return "twitter"
    if "youtube.com" in netloc or "youtu.be" in netloc:
        return "youtube"

    # Catch-all for random custom sites
    return "custom_site"


def main(input_path: Path, output_path: Path) -> None:
    profiles = json.loads(input_path.read_text(encoding="utf-8"))

    for p in profiles:
        url = p.get("profileUrl")
        p["docPlatform"] = classify_platform(url)

    output_path.write_text(
        json.dumps(profiles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # simple stats
    from collections import Counter
    c = Counter(p["docPlatform"] for p in profiles)
    print("Platform counts:")
    for platform, count in c.most_common():
        print(f"{platform:15} {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tag short profiles with docPlatform"
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to profiles_short_fulltext.json",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to tagged output JSON",
    )
    args = parser.parse_args()

    main(args.input_json, args.output_json)
