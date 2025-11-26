import argparse
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": "DateMeDirectoryScraper/0.1 (contact: your-email@example.com)"
}


def extract_full_text_from_html(html: str) -> str:
    """
    Given raw HTML, return a cleaned full-text string.
    Removes script/style/noscript and collapses whitespace.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script / style / noscript tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    raw_text = soup.get_text(separator="\n")

    # Strip whitespace and remove empty lines
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]  # drop blank lines

    full_text = "\n".join(lines)
    return full_text


def fetch_google_doc_text(url: str, timeout: int = 20) -> str:
    """
    Given a Google Docs URL, try to convert it into an export=txt URL
    and return the plain text of the document.

    This only works if the doc is shared so that "anyone with the link can view".
    """
    parsed = urlparse(url)

    # Expect paths like: /document/d/<DOC_ID>/edit...
    match = re.search(r"/document/d/([^/]+)", parsed.path)
    if not match:
        raise ValueError(f"Could not extract Google Doc ID from URL: {url}")

    doc_id = match.group(1)

    export_path = f"/document/d/{doc_id}/export"
    export_query = {"format": "txt"}

    export_url = urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc or "docs.google.com",
            export_path,
            "",  # params
            urlencode(export_query),
            "",  # fragment
        )
    )

    LOGGER.debug("Fetching Google Doc export URL: %s", export_url)
    resp = requests.get(export_url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def add_query_param(url: str, key: str, value: str) -> str:
    """
    Append or override a query parameter on a URL.
    """
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query))
    query_params[key] = value
    new_query = urlencode(query_params)
    new_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    return new_url


def fetch_profile_text(url: str, timeout: int = 20) -> str:
    """
    Main entry point:
    - For Google Docs, use export?format=txt and return the raw text.
    - For Notion/Compass/other, fetch HTML and run BeautifulSoup cleaning.

    Returns a plain text string.
    """
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").lower()

    # 1. Google Docs special handling
    if "docs.google.com" in netloc and "/document/d/" in parsed.path:
        LOGGER.info("Detected Google Doc: using export=txt for %s", url)
        return fetch_google_doc_text(url, timeout=timeout)

    # 2. Notion: try a "simplified" public view (?pvs=4) and then parse HTML
    if "notion.so" in netloc or "notion.site" in netloc:
        LOGGER.info("Detected Notion page: attempting ?pvs=4 view for %s", url)
        notion_url = add_query_param(url, "pvs", "4")
        resp = requests.get(notion_url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return extract_full_text_from_html(resp.text)

    # 3. General fallback (includes Compass and random sites)
    LOGGER.debug("Fetching generic HTML for %s", url)
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return extract_full_text_from_html(resp.text)


def process_profiles(input_path: Path, output_path: Path, delay_seconds: float = 1.0) -> None:
    """
    Load profiles JSON, fetch and extract fullText for each accessible profile,
    and save updated JSON.
    """
    LOGGER.info("Loading profiles from %s", input_path)
    with input_path.open("r", encoding="utf-8") as f:
        profiles = json.load(f)

    updated_count = 0
    total = len(profiles)
    LOGGER.info("Loaded %d profiles", total)

    for idx, profile in enumerate(profiles, start=1):
        profile_id = profile.get("id", f"<no-id-{idx}>")
        url = profile.get("profileUrl")

        if not url:
            LOGGER.warning("Profile %s has no profileUrl; skipping", profile_id)
            continue

        LOGGER.info("(%d/%d) Fetching longform text for %s (%s)", idx, total, profile_id, url)

        try:
            full_text = fetch_profile_text(url)
        except Exception as e:
            LOGGER.error("Failed to fetch/parse profile %s (%s): %s", profile_id, url, e)
            continue

        # Ensure profileDetails exists
        details = profile.get("profileDetails") or {}

        # Overwrite or set fullText
        details["fullText"] = full_text
        profile["profileDetails"] = details

        # Update scrapeTimestampDetail
        profile["scrapeTimestampDetail"] = datetime.now(timezone.utc).isoformat()

        updated_count += 1

        # Polite rate limiting
        time.sleep(delay_seconds)

    LOGGER.info("Updated fullText for %d profiles", updated_count)

    LOGGER.info("Saving updated profiles to %s", output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract longform profile text into profileDetails.fullText"
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to input profiles_accessible.json",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to output JSON with fullText populated",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between HTTP requests (default: 1.0)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    process_profiles(
        input_path=args.input_json,
        output_path=args.output_json,
        delay_seconds=args.delay,
    )


if __name__ == "__main__":
    main()
