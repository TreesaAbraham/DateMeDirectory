#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


REPO_ROOT = Path(__file__).resolve().parents[2]

MASTER_JSON = REPO_ROOT / "data" / "profiles_master.json"
OUT_JSON = REPO_ROOT / "data" / "directory" / "style_323.json"

DIRECTORY_URL = "https://dateme.directory/browse?gender=&desired-gender=&min-age=&max-age=&location="
SITE_ORIGIN = "https://dateme.directory"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def canonical_url(u: str) -> str:
    """Normalize for matching: strip query/fragment and trailing slash."""
    u = (u or "").strip()
    if not u:
        return ""
    parts = urlsplit(u)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def load_master_urls() -> set[str]:
    data = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    urls = set()
    for p in data:
        u = canonical_url(p.get("profileUrl", ""))
        if u:
            urls.add(u)
    return urls


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
    }
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.text


def find_directory_table(soup: BeautifulSoup):
    tables = soup.find_all("table")
    if not tables:
        raise RuntimeError("No <table> found. If the page is JS-rendered, we’ll need Playwright.")
    best = None
    best_cols = -1
    for t in tables:
        tr = t.find("tr")
        if not tr:
            continue
        cols = len(tr.find_all(["th", "td"]))
        if cols > best_cols:
            best_cols = cols
            best = t
    if not best:
        raise RuntimeError("Could not identify the directory table.")
    return best


def build_header_map(table) -> dict[str, int]:
    """
    Try to find a real header row. If the fetched HTML has no headers,
    return {} and we'll fall back to fixed indices.
    """
    thead = table.find("thead")
    if thead:
        tr = thead.find("tr")
        if tr:
            cells = tr.find_all(["th", "td"])
            text = [norm(c.get_text(" ", strip=True)) for c in cells]
            if any(t in {"name", "age", "gender", "interestedin", "style"} for t in text):
                return {t: i for i, t in enumerate(text) if t}

    for tr in table.find_all("tr"):
        if tr.find_all("th"):
            text = [norm(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            return {t: i for i, t in enumerate(text) if t}

    return {}


def header_index(hmap: dict[str, int], *candidates: str) -> int | None:
    for c in candidates:
        k = norm(c)
        if k in hmap:
            return hmap[k]
    return None


def normalize_style(raw: str) -> str | None:
    s = norm(raw)
    if not s:
        return None
    if s in {"mono", "monogamous"}:
        return "mono"
    if s in {"poly", "polyamorous"}:
        return "poly"
    if s in {"any"}:
        return "any"
    return raw.strip()


def main() -> None:
    master_urls = load_master_urls()

    html = fetch_html(DIRECTORY_URL)
    soup = BeautifulSoup(html, "html.parser")
    table = find_directory_table(soup)

    hmap = build_header_map(table)

    # Try header-based first
    idx_name = header_index(hmap, "name")
    idx_style = header_index(hmap, "style")

    # Fallback: if headers aren't in the fetched HTML, use known positions
    # From your screenshot: Name=0, Age=1, Gender=2, InterestedIn=3, Style=4
    if idx_name is None or idx_style is None:
        idx_name = 0
        idx_style = 4
        print("Header row not found in HTML; using fallback indices Name=0, Style=4")

    results = []
    rows = table.find_all("tr")[1:]  # if no header row, first row might be data; that's fine

    for row in rows:
        cells = row.find_all("td")
        if not cells or len(cells) <= max(idx_name, idx_style):
            continue

        name_cell = cells[idx_name]
        link = name_cell.find("a", href=True)
        if not link:
            continue

        profile_url = canonical_url(urljoin(SITE_ORIGIN, link["href"].strip()))

        # ONLY keep the 323 you already have
        if profile_url not in master_urls:
            continue

        style_raw = cells[idx_style].get_text(" ", strip=True)
        results.append({"profileUrl": profile_url, "style": normalize_style(style_raw)})

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(results)} rows to {OUT_JSON}")


if __name__ == "__main__":
    main()
