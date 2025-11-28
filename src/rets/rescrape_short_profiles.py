# src/rets/rescrape_short_profiles.py

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import re
import time

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/118.0 Safari/537.36"
)


def classify_platform(url: str) -> str:
    # keep in sync with tag_short_profiles_platform.py
    if not url:
        return "unknown"

    netloc = (urlparse(url).netloc or "").lower()
    path = (urlparse(url).path or "").lower()

    if "bit.ly" in netloc or "tinyurl.com" in netloc:
        return "shortener"

    if "docs.google.com" in netloc:
        if "/document/" in path:
            return "google_docs"
        if "/presentation/" in path:
            return "google_slides"
        return "google_docs_other"

    if "drive.google.com" in netloc:
        return "google_drive_file"

    if "notion.so" in netloc or "notion.site" in netloc:
        return "notion"

    if "dropbox.com" in netloc or "paper.dropbox.com" in netloc:
        if "paper.dropbox.com" in netloc or "/paper/" in path:
            return "dropbox_paper"
        return "dropbox_file"

    if "proton.me" in netloc:
        return "proton_drive"
    if "yandex.com" in netloc or "yandex.ru" in netloc:
        return "yandex_disk"

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

    return "custom_site"


def expand_url(url: str) -> str:
    """
    Follow redirects to find the final destination.
    Useful for bit.ly / tinyurl etc.
    """
    try:
        resp = requests.get(url, allow_redirects=True, timeout=20, headers={"User-Agent": USER_AGENT})
        return resp.url
    except Exception:
        return url


def extract_google_doc_text(doc_url: str) -> str | None:
    """
    For a Docs URL like:
      https://docs.google.com/document/d/<DOC_ID>/edit?usp=sharing
    try fetching:
      https://docs.google.com/document/d/<DOC_ID>/export?format=txt
    """
    m = re.search(r"/document/d/([^/]+)/", doc_url)
    if not m:
        return None
    doc_id = m.group(1)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    resp = requests.get(export_url, timeout=30, headers={"User-Agent": USER_AGENT})
    if resp.status_code != 200:
        return None
    text = resp.text.strip()
    return text or None


def rescrape_profile(profile: dict) -> tuple[dict, str]:
    """
    Try to improve fullText for a single profile.
    Returns (updated_profile, status_reason)
    """
    url = profile.get("profileUrl")
    details = profile.get("profileDetails") or {}
    old_text = (details.get("fullText") or "").strip()

    # If doc is clearly "not dating anymore" / very specific,
    # we treat it as final, no rescrape.
    if any(
        phrase.lower() in old_text.lower()
        for phrase in [
            "not currently looking",
            "no longer seeking",
            "i’ve met someone",
            "i'm seeing someone",
        ]
    ):
        return profile, "short_but_intentional"

    # Step 1: expand shorteners
    platform = classify_platform(url)
    final_url = url
    if platform == "shortener":
        final_url = expand_url(url)
        profile["expandedUrl"] = final_url
        platform = classify_platform(final_url)

    # Step 2: platform-specific logic
    new_text = None
    reason = "no_change"

    if platform == "google_docs":
        maybe_text = extract_google_doc_text(final_url)
        if maybe_text:
            new_text = maybe_text
            reason = "google_docs_export"

    # TODO: you could add google_slides -> export pdf + parse, etc.
    # For now we leave slides alone.

    # Other platforms largely require login or are truly short.

    if new_text and new_text.strip() and len(new_text.split()) > len(old_text.split()):
        # only overwrite if it looks strictly "better"
        details["fullText"] = new_text
        profile["profileDetails"] = details
        return profile, reason

    return profile, reason


def main(input_path: Path, output_path: Path) -> None:
    profiles = json.loads(input_path.read_text(encoding="utf-8"))

    updated = 0
    reasons: dict[str, int] = {}

    for p in profiles:
        new_p, reason = rescrape_profile(p)
        reasons[reason] = reasons.get(reason, 0) + 1
        if reason not in ("no_change", "short_but_intentional"):
            updated += 1
        p.update(new_p)
        time.sleep(0.5)  # be polite

    output_path.write_text(
        json.dumps(profiles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Rescrape complete. Profiles touched: {updated}/{len(profiles)}")
    print("Reason breakdown:")
    for r, count in reasons.items():
        print(f"{r:25} {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Re-scrape short profiles to improve fullText where possible."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to profiles_short_fulltext.tagged.json",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to output JSON with improved fullText",
    )
    args = parser.parse_args()

    main(args.input_json, args.output_json)
