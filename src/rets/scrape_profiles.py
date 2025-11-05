from __future__ import annotations
import hashlib, json, re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jsonschema import validate
import jsonschema
from src.settings import Settings
from src.utils.http import session_get
from src.utils.io import ensure_snapshot_paths, read_json, write_text, write_json

def stable_id(seed: str) -> str:
    return "usr_" + hashlib.sha1(seed.encode()).hexdigest()[:10]

def pick_text(soup, sel):
    el = soup.select_one(sel)
    return el.get_text(strip=True) if el else None

def parse_profile(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    name = pick_text(soup, "h1.profile-name") or pick_text(soup, "h1, h2") or "Unknown"
    age_text = pick_text(soup, ".age, .profile-age")
    m = re.search(r"\d+", age_text or "")
    age = int(m.group()) if m else None
    gender = (pick_text(soup, ".gender") or "other").lower()
    location = pick_text(soup, ".location") or "Unknown"
    flex = (pick_text(soup, ".location-flex") or "some").lower()
    last_updated = pick_text(soup, ".last-updated") or "2024-01-01"
    interested_raw = pick_text(soup, ".interested-in") or ""
    tokens = [t.strip().lower() for t in re.split("[,|/]", interested_raw) if t.strip()]
    tokens = [t for t in tokens if t in {"male","female","nonbinary","other"}] or ["other"]

    return {
        "id": stable_id(f"{name}|{url}"),
        "name": name,
        "age": age,
        "gender": gender if gender in {"male","female","nonbinary","other"} else "other",
        "genderInterestedIn": sorted(set(tokens)),
        "location": location,
        "locationFlexibility": flex if flex in {"none","some","high"} else "some",
        "lastUpdated": last_updated,
        "profileUrl": url
    }

def main():
    load_dotenv()
    s = Settings()
    paths = ensure_snapshot_paths(s.snapshot_stamp)
    rows = read_json(paths["processed_dir"] / "directory_rows.json")

    prof_schema = json.loads(open("schemas/profile.schema.json").read())
    out = []
    for row in rows:
        url = row["profileUrl"]
        resp = session_get(url, timeout=s.timeout_seconds)
        resp.raise_for_status()
        write_text(paths["raw_dir"] / f"profile_{hashlib.md5(url.encode()).hexdigest()[:12]}.html", resp.text)
        data = parse_profile(resp.text, url)
        try:
            validate(data, prof_schema)
        except jsonschema.ValidationError as e:
            raise SystemExit(f"Profile failed schema: {e.message} @ {list(e.path)} for {url}")
        out.append(data)

    write_json(paths["processed_dir"] / "profiles.json", out)
    print(f"[profiles] {len(out)} profiles")

if __name__ == "__main__":
    main()
