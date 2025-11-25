from __future__ import annotations
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from src.settings import Settings
from src.utils.io import ensure_snapshot_paths, write_text, write_json, read_json


def pick_text(soup: BeautifulSoup, selector: str) -> str | None:
    """
    Helper to grab text from the first element matching a CSS selector.
    Very generic on purpose.
    """
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


def extract_full_text(html: str) -> str:
    """
    Very rough v1 longform extractor:
    - Collect text from paragraphs, list items, and headings.
    - Normalize whitespace.
    - Join into one big string.

    This is optional but useful; you can ignore it if you only care
    about directory-level fields for now.
    """
    soup = BeautifulSoup(html, "lxml")

    texts: list[str] = []

    # Paragraphs
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if t:
            texts.append(t)

    # List items
    for li in soup.find_all("li"):
        t = li.get_text(" ", strip=True)
        if t:
            texts.append(t)

    # Headings (in case they contain important text)
    for tag in ["h1", "h2", "h3"]:
        for h in soup.find_all(tag):
            t = h.get_text(" ", strip=True)
            if t:
                texts.append(t)

    # Deduplicate a bit while preserving order (optional)
    seen = set()
    uniq_texts = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            uniq_texts.append(t)

    return "\n\n".join(uniq_texts)


def main() -> None:
    """
    Pipeline:

    1. Load canonical directory data from data/directory/latest.json.
    2. For each row, try to fetch profileUrl with requests.
       - On success: optionally extract longform text and mark as accessible.
       - On failure: keep the directory fields, mark as inaccessible.
    3. Write enriched profiles to data/processed/<stamp>/profiles.json
       and a log of failures to profiles_skipped.json.
    """
    load_dotenv()
    settings = Settings()

    # Prepare snapshot directories: data/raw/<stamp>, data/processed/<stamp>, data/latest/
    paths = ensure_snapshot_paths(settings.snapshot_stamp)

    directory_latest = Path("data/directory/latest.json")
    if not directory_latest.exists():
        raise SystemExit(
            "data/directory/latest.json not found.\n"
            "Run the directory scraper first, e.g.:\n"
            "    python -m src.rets.scrape_directory"
        )

    # This is your canonical table with id, name, age, gender, location, lastUpdated, etc.
    rows = read_json(directory_latest)
    if not isinstance(rows, list):
        raise SystemExit("Expected latest.json to contain a list of profiles")

    parsed: list[dict] = []
    skipped: list[dict] = []

    total = len(rows)
    print(f"[profiles] starting detailed scrape for {total} profiles")

    for idx, row in enumerate(rows, start=1):
        # Start from the directory row; DO NOT rebuild id/name/age/etc. from the doc
        profile = dict(row)
        url = profile.get("profileUrl")

        # Make sure profileDetails exists and is at least an object
        if "profileDetails" not in profile or profile["profileDetails"] is None:
            profile["profileDetails"] = {}

        # Default: we don't know yet whether the doc is accessible
        profile["docAccessible"] = False
        profile["scrapeTimestampDetail"] = None

        if not url:
            print(f"[warn] #{idx}/{total}: missing profileUrl, keeping directory data only")
            skipped.append(
                {
                    "id": profile.get("id"),
                    "url": None,
                    "reason": "missing_profileUrl",
                }
            )
            parsed.append(profile)
            continue

        # Polite delay between requests
        time.sleep(settings.request_delay_ms / 1000.0)

        # 1) HTTP fetch with error handling
        try:
            resp = requests.get(
                url,
                timeout=settings.timeout_seconds,
                headers={
                    "User-Agent": settings.user_agent,
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
        except requests.RequestException as e:
            print(f"[warn] #{idx}/{total}: network error for {url}: {e.__class__.__name__}")
            skipped.append(
                {
                    "id": profile.get("id"),
                    "url": url,
                    "reason": "request_exception",
                    "detail": str(e),
                }
            )
            # Keep directory data; just no doc details
            parsed.append(profile)
            continue

        status = resp.status_code
        if status >= 400:
            print(f"[warn] #{idx}/{total}: HTTP {status} for {url}, keeping directory data only")
            skipped.append(
                {
                    "id": profile.get("id"),
                    "url": url,
                    "reason": "http_status",
                    "status": status,
                }
            )
            parsed.append(profile)
            continue

        # 2) Save raw HTML so you can inspect or re-parse later if needed
        # Use id if present, otherwise hash the URL
        pid = profile.get("id")
        if pid and isinstance(pid, str):
            raw_name = f"profile_{pid}.html"
        else:
            raw_name = f"profile_{hashlib.md5(url.encode()).hexdigest()[:12]}.html"

        try:
            write_text(paths["raw_dir"] / raw_name, resp.text)
        except Exception as e:
            print(f"[warn] #{idx}/{total}: failed to write raw HTML for {url}: {e}")
            skipped.append(
                {
                    "id": profile.get("id"),
                    "url": url,
                    "reason": "raw_write_error",
                    "detail": str(e),
                }
            )
            parsed.append(profile)
            continue

        # 3) Optionally extract longform text (you can ignore this if you only care about directory fields)
        try:
            full_text = extract_full_text(resp.text)
        except Exception as e:
            print(f"[warn] #{idx}/{total}: parse error for {url}: {e}")
            skipped.append(
                {
                    "id": profile.get("id"),
                    "url": url,
                    "reason": "parse_error",
                    "detail": str(e),
                }
            )
            parsed.append(profile)
            continue

        # Attach detail info without overwriting directory fields
        if full_text:
            profile["profileDetails"]["fullText"] = full_text
        profile["scrapeTimestampDetail"] = datetime.utcnow().isoformat() + "Z"
        profile["docAccessible"] = True

        parsed.append(profile)

    # Write outputs
    write_json(paths["processed_dir"] / "profiles.json", parsed)
    if skipped:
        write_json(paths["processed_dir"] / "profiles_skipped.json", skipped)

    print(
        f"[profiles] done. {len(parsed)} profiles written, "
        f"{len(skipped)} with doc access issues (see profiles_skipped.json)."
    )


if __name__ == "__main__":
    main()
