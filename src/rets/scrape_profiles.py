from __future__ import annotations
import hashlib
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

from src.settings import Settings
from src.utils.io import ensure_snapshot_paths, write_text, write_json, read_json


def stable_id(seed: str) -> str:
    """
    Build a stable internal ID from a seed string.
    """
    return "usr_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def pick_text(soup: BeautifulSoup, selector: str) -> str | None:
    """
    Helper to grab text from the first element matching a CSS selector.
    """
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


def parse_profile(html: str, url: str) -> dict:
    """
    Parse a single profile HTML document into a structured dict.
    """
    soup = BeautifulSoup(html, "lxml")

    # Very defensive parsing – selectors are guesses with fallbacks.
    name = (
        pick_text(soup, "h1.profile-name")
        or pick_text(soup, "h1")
        or pick_text(soup, "h2")
        or "Unknown"
    )

    age_text = pick_text(soup, ".age, .profile-age")
    m = re.search(r"\d+", age_text or "")
    age = int(m.group()) if m else None

    gender_raw = (pick_text(soup, ".gender") or "").lower()
    gender = gender_raw if gender_raw in {"male", "female", "nonbinary", "other"} else "other"

    location = pick_text(soup, ".location") or "Unknown"

    flex_raw = (pick_text(soup, ".location-flex") or "").lower()
    location_flexibility = flex_raw if flex_raw in {"none", "some", "high"} else "some"

    last_updated = pick_text(soup, ".last-updated") or "2024-01-01"

    interested_raw = pick_text(soup, ".interested-in") or ""
    tokens = [t.strip().lower() for t in re.split(r"[,/|]", interested_raw) if t.strip()]
    gender_interested_in = [t for t in tokens if t in {"male", "female", "nonbinary", "other"}]
    if not gender_interested_in:
        gender_interested_in = ["other"]

    return {
        "id": stable_id(f"{name}|{url}"),
        "name": name,
        "age": age,
        "gender": gender,
        "genderInterestedIn": sorted(set(gender_interested_in)),
        "location": location,
        "locationFlexibility": location_flexibility,
        "lastUpdated": last_updated,
        "profileUrl": url,
    }


def main() -> None:
    """
    Load profiles_master.json, visit each profileUrl, parse + validate,
    and write out processed profiles plus a log of skipped ones.
    """
    load_dotenv()
    settings = Settings()

    # Prepare snapshot directories: data/raw/<stamp>, data/processed/<stamp>, data/latest/
    paths = ensure_snapshot_paths(settings.snapshot_stamp)

    master_path = Path("data/profiles_master.json")
    if not master_path.exists():
        raise SystemExit(
            "profiles_master.json not found.\n"
            "Run the directory scraper first, e.g.:\n"
            "    python -m src.rets.scrape_directory"
        )

    rows = read_json(master_path)

    schema_path = Path("schemas/profile.schema.json")
    if not schema_path.exists():
        raise SystemExit("schemas/profile.schema.json not found.")
    prof_schema = json.loads(schema_path.read_text(encoding="utf-8"))

    parsed: list[dict] = []
    skipped: list[dict] = []

    total = len(rows)
    print(f"[profiles] starting detailed scrape for {total} profiles")

    for idx, row in enumerate(rows, start=1):
        url = row.get("profileUrl")
        if not url:
            print(f"[warn] #{idx}/{total}: missing profileUrl, skipping")
            skipped.append(
                {
                    "url": None,
                    "reason": "missing_profileUrl",
                    "row": row,
                }
            )
            continue

        # polite delay
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
                    "url": url,
                    "reason": "request_exception",
                    "detail": str(e),
                }
            )
            continue

        status = resp.status_code
        if status >= 400:
            # This is where 401 / 403 / 404 / DNS-ish issues (if they reach here) get skipped
            print(f"[warn] #{idx}/{total}: HTTP {status} for {url}, skipping")
            skipped.append(
                {
                    "url": url,
                    "reason": "http_status",
                    "status": status,
                }
            )
            continue

        # 2) Save raw HTML
        raw_name = f"profile_{hashlib.md5(url.encode()).hexdigest()[:12]}.html"
        try:
            write_text(paths["raw_dir"] / raw_name, resp.text)
        except Exception as e:
            print(f"[warn] #{idx}/{total}: failed to write raw HTML for {url}: {e}")
            skipped.append(
                {
                    "url": url,
                    "reason": "raw_write_error",
                    "detail": str(e),
                }
            )
            continue

        # 3) Parse HTML into structured data
        try:
            data = parse_profile(resp.text, url)
        except Exception as e:
            print(f"[warn] #{idx}/{total}: parse error for {url}: {e}")
            skipped.append(
                {
                    "url": url,
                    "reason": "parse_error",
                    "detail": str(e),
                }
            )
            continue

        # 4) Schema validation
        try:
            validate(instance=data, schema=prof_schema)
        except ValidationError as e:
            print(
                f"[warn] #{idx}/{total}: schema validation failed for {url}: "
                f"{e.message} @ {list(e.path)}"
            )
            skipped.append(
                {
                    "url": url,
                    "reason": "schema_validation",
                    "detail": e.message,
                    "path": list(e.path),
                }
            )
            continue

        # 5) If we got here, this profile is good
        parsed.append(data)

    # Write outputs
    write_json(paths["processed_dir"] / "profiles.json", parsed)
    if skipped:
        write_json(paths["processed_dir"] / "profiles_skipped.json", skipped)

    print(
        f"[profiles] done. {len(parsed)} parsed successfully, "
        f"{len(skipped)} skipped. See {paths['processed_dir']} for details."
    )


if __name__ == "__main__":
    main()
