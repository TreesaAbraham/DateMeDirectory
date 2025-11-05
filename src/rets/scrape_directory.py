from __future__ import annotations
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from jsonschema import validate
import jsonschema
from src.settings import Settings
from src.utils.http import session_get
from src.utils.io import ensure_snapshot_paths, write_text, write_json

def parse_directory(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    # TODO: adjust selectors to the real site
    for a in soup.select("table a[href], .directory a[href]"):
        name = a.get_text(strip=True)
        href = a.get("href")
        if name and href:
            rows.append({"name": name, "profileUrl": href})
    return rows

def main():
    load_dotenv()
    s = Settings()
    paths = ensure_snapshot_paths(s.snapshot_stamp)

    resp = session_get(s.directory_url, timeout=s.timeout_seconds)
    resp.raise_for_status()
    write_text(paths["raw_dir"] / "directory.html", resp.text)

    rows = parse_directory(resp.text)

    dir_schema = json.loads(open("schemas/directory_row.schema.json").read())
    for i, row in enumerate(rows, 1):
        try:
            validate(row, dir_schema)
        except jsonschema.ValidationError as e:
            raise SystemExit(f"Row {i} failed schema: {e.message} @ {list(e.path)}")

    write_json(paths["processed_dir"] / "directory_rows.json", rows)
    print(f"[directory] {len(rows)} rows")

if __name__ == "__main__":
    main()
