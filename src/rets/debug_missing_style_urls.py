#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_JSON = REPO_ROOT / "data" / "profiles_master.json"
STYLE_JSON = REPO_ROOT / "data" / "directory" / "style_323.json"

def canonical_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    p = urlsplit(u)
    return urlunsplit((p.scheme, p.netloc, p.path.rstrip("/"), "", ""))

def main():
    master = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    styles = json.loads(STYLE_JSON.read_text(encoding="utf-8"))

    master_urls = {canonical_url(p.get("profileUrl","")) for p in master if p.get("profileUrl")}
    style_urls = {canonical_url(r.get("profileUrl","")) for r in styles if r.get("profileUrl")}

    missing = sorted(u for u in master_urls if u and u not in style_urls)

    print(f"Master URLs: {len(master_urls)}")
    print(f"Style URLs : {len(style_urls)}")
    print(f"Missing    : {len(missing)}\n")

    for u in missing:
        print(u)

if __name__ == "__main__":
    main()
