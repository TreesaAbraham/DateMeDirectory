# scripts/report_profile_platforms.py
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

def norm(s: str) -> str:
    return (s or "").strip()

def classify_platform(url: str) -> str:
    if not url:
        return "missing_url"
    u = urlparse(url)
    netloc = (u.netloc or "").lower()
    path = (u.path or "").lower()

    if "bit.ly" in netloc or "tinyurl.com" in netloc:
        return "shortener"

    if "docs.google.com" in netloc:
        if "/document/" in path:
            return "google_docs"
        if "/presentation/" in path:
            return "google_slides"
        if "/viewer" in path or "/gview" in path:
            return "google_viewer"
        return "docs_google_other"

    if "drive.google.com" in netloc:
        return "google_drive_file"

    if "notion.so" in netloc or "notion.site" in netloc:
        return "notion"

    if "dropbox.com" in netloc or "paper.dropbox.com" in netloc:
        return "dropbox"

    if "carrd.co" in netloc:
        return "carrd"

    if "neocities.org" in netloc:
        return "neocities"

    return "custom_site"

def is_pdf_like(url: str) -> bool:
    if not url:
        return False
    u = urlparse(url)
    # direct .pdf in the URL itself
    if u.path.lower().endswith(".pdf"):
        return True

    # google viewer often stores the real file in ?url=...
    qs = parse_qs(u.query)
    for key in ("url", "q"):
        if key in qs:
            for val in qs[key]:
                val = unquote(val).lower()
                if ".pdf" in val:
                    return True
    return False

def pdf_viewer_flag(url: str) -> str | None:
    if not url:
        return None
    u = urlparse(url)
    netloc = (u.netloc or "").lower()
    path = (u.path or "").lower()

    # docs.google.com/viewer or gview with a pdf inside
    if "docs.google.com" in netloc and ("/viewer" in path or "/gview" in path) and is_pdf_like(url):
        return "google_viewer_pdf"
    # drive file that looks like a pdf
    if "drive.google.com" in netloc and is_pdf_like(url):
        return "drive_pdf"
    # direct pdf anywhere
    if is_pdf_like(url):
        return "direct_pdf"
    return None

def shortener_flag(url: str) -> bool:
    if not url:
        return False
    netloc = (urlparse(url).netloc or "").lower()
    return ("bit.ly" in netloc) or ("tinyurl.com" in netloc)

def main() -> None:
    ap = argparse.ArgumentParser(description="Report platform breakdown + flags for tricky URLs (PDF viewers, shorteners).")
    ap.add_argument("input_json", type=Path, help="Path to JSON list of profiles")
    ap.add_argument("--top", type=int, default=25, help="How many flagged examples to print")
    args = ap.parse_args()

    profiles = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise SystemExit("[error] input_json must be a list")

    platform_counts = Counter()
    flag_counts = Counter()
    flagged_examples = defaultdict(list)

    for p in profiles:
        pid = norm(p.get("id"))
        name = norm(p.get("name"))
        url = norm(p.get("profileUrl"))

        plat = p.get("docPlatform") or classify_platform(url)
        platform_counts[plat] += 1

        pdf_flag = pdf_viewer_flag(url)
        if pdf_flag:
            flag_counts[pdf_flag] += 1
            flagged_examples[pdf_flag].append((pid, name, url))

        if shortener_flag(url):
            flag_counts["shortener"] += 1
            flagged_examples["shortener"].append((pid, name, url))

        # Helpful: “google docs” links that are *not* /document/d/
        if "docs.google.com" in (urlparse(url).netloc or "").lower() and plat not in ("google_docs", "google_slides"):
            flag_counts["docs_google_nonstandard"] += 1
            flagged_examples["docs_google_nonstandard"].append((pid, name, url))

    total = len(profiles)
    print(f"[summary] total profiles: {total}\n")

    print("[platform counts]")
    for k, v in platform_counts.most_common():
        print(f"{k:24} {v}")
    print()

    print("[flags]")
    if not flag_counts:
        print("(none)")
    else:
        for k, v in flag_counts.most_common():
            print(f"{k:24} {v}")
    print()

    top = max(1, args.top)
    for flag, items in flagged_examples.items():
        print(f"[examples] {flag} (showing up to {top})")
        for pid, name, url in items[:top]:
            print(f"- {pid} | {name} | {url}")
        print()

if __name__ == "__main__":
    main()
