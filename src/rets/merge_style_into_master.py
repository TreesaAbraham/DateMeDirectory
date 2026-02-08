#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_JSON = REPO_ROOT / "data" / "profiles_master.json"
STYLE_JSON = REPO_ROOT / "data" / "directory" / "style_323.json"


def canonical_url(u: str) -> str:
    """Normalize URL for joining across minor formatting differences."""
    u = (u or "").strip()
    if not u:
        return ""
    p = urlsplit(u)
    scheme = (p.scheme or "").lower() or "https"
    netloc = (p.netloc or "").lower()
    path = (p.path or "").rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def normalize_style(raw: str | None) -> str | None:
    s = (raw or "").strip().lower()
    if not s:
        return None
    if s in {"mono", "monogamous", "monogamy"}:
        return "mono"
    if s in {"poly", "polyamorous", "polyamory"}:
        return "poly"
    if s in {"any"}:
        return "any"
    # handle combined labels from the directory table
    if s in {"mono poly", "poly mono"}:
        return "any"
    return None


def main() -> None:
    master = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    styles = json.loads(STYLE_JSON.read_text(encoding="utf-8"))

    # map style by canonical URL
    style_by_url = {}
    raw_by_url = {}
    for r in styles:
        u = canonical_url(r.get("profileUrl", ""))
        if not u:
            continue
        raw = r.get("style")
        raw_by_url[u] = raw
        style_by_url[u] = normalize_style(raw)

    matched = 0
    updated_norm = 0

    for p in master:
        u = canonical_url(p.get("profileUrl", ""))
        if not u:
            continue
        if u not in raw_by_url:
            continue

        matched += 1
        p["datingStyleRaw"] = raw_by_url[u]

        normed = style_by_url[u]
        if normed is not None:
            p["datingStyle"] = normed
            updated_norm += 1
        else:
            # if it doesn't normalize, clear datingStyle so it doesn't lie
            p.pop("datingStyle", None)

    MASTER_JSON.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Matched {matched} master profiles to style rows (expected 318).")
    print(f"Wrote normalized datingStyle for {updated_norm} profiles (expected ~311).")


if __name__ == "__main__":
    main()
