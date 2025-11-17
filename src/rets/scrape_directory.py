import os
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin
from datetime import datetime
import hashlib

import requests
from bs4 import BeautifulSoup

# You can override this in your .env later if you want
DIRECTORY_URL = os.getenv(
    "DIRECTORY_URL",
    "https://dateme.directory/browse?gender=&desired-gender=&min-age=&max-age=&location="
)


def fetch_directory_html(url: str = DIRECTORY_URL) -> str:
    """
    Fetch the raw HTML for the Date Me Directory browse page.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def _clean_text(text: str) -> str:
    """
    Normalize whitespace: strip and collapse internal spaces.
    """
    return " ".join(text.split())


def parse_directory_rows(html: str) -> List[Dict]:
    """
    Parse the directory table into a list of dicts.

    Each profile dict contains:
      - name
      - age (int or None)
      - gender
      - interestedIn (list of tokens, e.g. ["M", "NB"])
      - location
      - locationFlexibility
      - profileUrl (full URL)
      - lastUpdated (YYYY-MM-DD string)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Assume the main directory is in a <table>. If there are multiple, we use the first.
    table = soup.find("table")
    if table is None:
        raise RuntimeError("Could not find a <table> element on the directory page")

    # Some pages use <tbody>, some don't. Be defensive.
    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr")

    profiles: List[Dict] = []

    for row in rows:
        # Only consider real data rows with <td> cells
        cells = row.find_all("td")
        if len(cells) < 9:
            # Header row or weird row, skip it
            continue

        # Column order from the site:
        # 0: Name (with link to profile)
        # 1: Age
        # 2: Gender
        # 3: InterestedIn
        # 4: Style
        # 5: Location
        # 6: LocationFlexibility
        # 7: Contact
        # 8: LastUpdated

        name_cell = cells[0]

        # Name (text inside the <a> or cell)
        name = _clean_text(name_cell.get_text(strip=True))

        # Profile URL from the <a> tag (if it exists)
        link = name_cell.find("a")
        profile_url: Optional[str] = None
        if link and link.has_attr("href"):
            href = link["href"]
            profile_url = urljoin(DIRECTORY_URL, href)

        # Age
        age_text = _clean_text(cells[1].get_text(strip=True))
        try:
            age = int(age_text)
        except ValueError:
            age = None

        # Gender (single token like "M", "F", "NB")
        gender = _clean_text(cells[2].get_text(strip=True))

        # Interested in (can be "M", "F NB", etc.)
        interested_raw = _clean_text(cells[3].get_text(" ", strip=True))
        interested_in = [token for token in interested_raw.split(" ") if token]

        # Location (can be many words, we keep as one normalized string)
        location = _clean_text(cells[5].get_text(" ", strip=True))

        # Location flexibility (e.g. "Flexible", "Some", "None")
        location_flexibility = _clean_text(cells[6].get_text(strip=True))

        # Last updated (YYYY-MM-DD string from the table)
        last_updated = _clean_text(cells[8].get_text(strip=True))

        profile = {
            "name": name,
            "age": age,
            "gender": gender,
            "interestedIn": interested_in,
            "location": location,
            "locationFlexibility": location_flexibility,
            "profileUrl": profile_url,
            "lastUpdated": last_updated,
            # Detail fields to be filled in by a later step
            "profileDetails": {},           # will eventually hold parsed doc content
            "scrapeTimestampDetail": None,  # will become an ISO timestamp string
        }




        profiles.append(profile)

    return profiles

def make_profile_id(profile: Dict) -> str:
    """
    Build a stable internal ID for a profile.

    Format: usr_<10 hex chars>, matching pattern: ^usr_[0-9a-f]{10}$

    We use a SHA1 hash of key fields (heavily anchored on profileUrl)
    so that IDs are:
      - Deterministic: same profile -> same ID across runs
      - Very unlikely to collide
    """
    key_parts = [
        profile.get("profileUrl") or "",
        profile.get("name") or "",
        str(profile.get("age") or ""),
        profile.get("gender") or "",
        " ".join(profile.get("interestedIn") or []),
        profile.get("location") or "",
    ]
    key = "|".join(key_parts)
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return f"usr_{digest[:10]}"


def assign_ids(profiles: List[Dict]) -> List[Dict]:
    """
    Add an 'id' field to each profile dict in-place and return the list.

    Ensures IDs are unique within this run. Collisions are astronomically
    unlikely, but we still guard against them because paranoia is healthy.
    """
    seen: set[str] = set()

    for profile in profiles:
        pid = make_profile_id(profile)
        base_pid = pid
        counter = 1

        # In the microscopic chance of a collision, tweak the last chars
        while pid in seen:
            suffix = f"{counter:x}"
            pid = base_pid[:-len(suffix)] + suffix
            counter += 1

        seen.add(pid)
        profile["id"] = pid

    return profiles


def save_profiles_to_json(profiles: List[Dict]) -> None:
    """
    Save the full list of profiles into:
      - data/directory/directory-YYYYMMDD-HHMMSS.json  (snapshot)
      - data/directory/latest.json                     (pointer to latest)
      - data/profiles_master.json                      (canonical master dump)
    """
    # Directory for timestamped + latest files
    data_dir = os.path.join("data", "directory")
    os.makedirs(data_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snapshot_path = os.path.join(data_dir, f"directory-{timestamp}.json")
    latest_path = os.path.join(data_dir, "latest.json")

    # Path for master JSON (one level up, in /data/)
    master_path = os.path.join("data", "profiles_master.json")

    # Write snapshot
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    # Write/overwrite latest
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    # Write/overwrite master
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"Saved snapshot: {snapshot_path}")
    print(f"Updated latest: {latest_path}")
    print(f"Wrote master file: {master_path}")



def main() -> None:
    print(f"Fetching directory HTML from: {DIRECTORY_URL}")
    html = fetch_directory_html()
    profiles = parse_directory_rows(html)

    # 🔹 NEW: assign stable internal IDs
    profiles = assign_ids(profiles)

    print(f"Extracted {len(profiles)} profiles")

    if profiles:
        print("\nSample profile:")
        print(json.dumps(profiles[0], indent=2, ensure_ascii=False))

    save_profiles_to_json(profiles)



if __name__ == "__main__":
    main()
