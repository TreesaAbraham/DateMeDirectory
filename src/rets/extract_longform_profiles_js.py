import argparse
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

LOGGER = logging.getLogger(__name__)


def clean_text(raw: str) -> str:
    """
    Normalize whitespace, remove extra blank lines.
    """
    lines = [line.strip() for line in raw.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


async def fetch_page_text(
    page,
    url: str,
    timeout_ms: int = 60000,
    post_load_wait_ms: int = 4000,
) -> str:
    """
    Use Playwright to load a JS-heavy page and return the body text.

    Strategy:
    1. Try waiting for 'networkidle'.
    2. If that times out, fall back to 'domcontentloaded'.
    3. Then wait a fixed amount of time for JS to render content.
    """
    LOGGER.info("Loading %s", url)

    # First attempt: try networkidle
    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
    except Exception as e:
        LOGGER.warning(
            "networkidle wait failed for %s: %s; retrying with domcontentloaded",
            url,
            e,
        )
        # Fallback: just wait for basic DOM to be ready
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

    # Give JS time to render Notion blocks, etc.
    await page.wait_for_timeout(post_load_wait_ms)

    # Get all visible text in the body
    body_text = await page.inner_text("body")
    cleaned = clean_text(body_text)

    return cleaned


async def process_profiles_js(
    input_path: Path,
    output_path: Path,
    delay_seconds: float,
    timeout_ms: int,
    post_load_wait_ms: int,
) -> None:
    LOGGER.info("Loading JS-only profiles from %s", input_path)
    with input_path.open("r", encoding="utf-8") as f:
        profiles = json.load(f)

    total = len(profiles)
    LOGGER.info("Loaded %d JS-heavy profiles", total)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        updated = 0

        for idx, profile in enumerate(profiles, start=1):
            profile_id = profile.get("id", f"<no-id-{idx}>")
            url = profile.get("profileUrl")

            if not url:
                LOGGER.warning("Profile %s has no profileUrl; skipping", profile_id)
                continue

            LOGGER.info("(%d/%d) Scraping %s (%s)", idx, total, profile_id, url)

            try:
                full_text = await fetch_page_text(
                    page,
                    url,
                    timeout_ms=timeout_ms,
                    post_load_wait_ms=post_load_wait_ms,
                )
            except Exception as e:
                LOGGER.error("Failed to scrape JS profile %s (%s): %s", profile_id, url, e)
                continue

            if not full_text or len(full_text) < 50:
                LOGGER.warning(
                    "Profile %s (%s) returned very little text (%d chars)",
                    profile_id,
                    url,
                    len(full_text or ""),
                )

            details = profile.get("profileDetails") or {}
            details["fullText"] = full_text
            profile["profileDetails"] = details
            profile["scrapeTimestampDetail"] = datetime.now(timezone.utc).isoformat()

            updated += 1

            # Gentle delay so you don't hammer hosts
            time.sleep(delay_seconds)

        await browser.close()

    LOGGER.info("Successfully updated %d JS profiles with fullText", updated)

    LOGGER.info("Saving updated JS profiles to %s", output_path)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use Playwright to extract longform text from JS-heavy profiles"
    )
    parser.add_argument("input_json", type=Path, help="Path to profiles_js_only.json")
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to output JSON with fullText populated",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Delay in seconds between profiles (default: 3.0)",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60000,
        help="Per-page timeout in milliseconds (default: 60000)",
    )
    parser.add_argument(
        "--post-load-wait-ms",
        type=int,
        default=4000,
        help="Extra wait after load in milliseconds (default: 4000)",
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
    asyncio.run(
        process_profiles_js(
            input_path=args.input_json,
            output_path=args.output_json,
            delay_seconds=args.delay,
            timeout_ms=args.timeout_ms,
            post_load_wait_ms=args.post_load_wait_ms,
        )
    )


if __name__ == "__main__":
    main()
