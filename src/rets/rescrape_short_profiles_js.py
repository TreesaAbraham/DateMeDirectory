# src/rets/rescrape_short_profiles_js.py

import argparse
import json
import logging
import re
import time
from pathlib import Path

from playwright.async_api import async_playwright  # type: ignore

LOGGER = logging.getLogger(__name__)


def word_count(text: str) -> int:
    if not text:
        return 0
    # cheap but robust enough
    return len(re.findall(r"\b\w+\b", text))


async def fetch_page_text(page, url: str, timeout_ms: int = 45000, post_load_wait_ms: int = 1500) -> str:
    """
    Load a page in Playwright and return the body inner text.
    Much dumber but more general than platform-specific hacks.
    """
    LOGGER.info("Loading %s", url)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as e:
        LOGGER.warning("goto domcontentloaded failed for %s: %s", url, e)
        # last resort: try again without special wait
        try:
            await page.goto(url, timeout=timeout_ms)
        except Exception as e2:
            LOGGER.error("Second goto failed for %s: %s", url, e2)
            return ""

    # extra wait for JS to settle a bit
    await page.wait_for_timeout(post_load_wait_ms)

    try:
        text = await page.inner_text("body")
    except Exception as e:
        LOGGER.error("Failed to get body text for %s: %s", url, e)
        return ""

    # Normalize whitespace a bit
    return re.sub(r"\s+\n", "\n", text).strip()


async def rescrape_short_profiles_js(
    input_path: Path,
    output_path: Path,
    delay_seconds: float = 0.75,
    timeout_ms: int = 45000,
    post_load_wait_ms: int = 1500,
) -> None:
    """
    Use Playwright to try to improve fullText for short profiles (<100 words).

    - Loads input JSON (short profiles only).
    - For each profile:
        * Loads profileUrl in Playwright
        * Gets body.inner_text()
        * If new text has strictly more words than existing fullText, overwrite.
    - Writes to output_path.
    """

    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Loading short profiles from %s", input_path)

    profiles = json.loads(input_path.read_text(encoding="utf-8"))
    total = len(profiles)
    LOGGER.info("Loaded %d short profiles", total)

    improved = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for idx, profile in enumerate(profiles, start=1):
            pid = profile.get("id", f"<no-id-{idx}>")
            url = profile.get("profileUrl")
            details = profile.get("profileDetails") or {}
            old_text = (details.get("fullText") or "").strip()
            old_wc = word_count(old_text)

            LOGGER.info("(%d/%d) [%s] %s (old_wc=%d)", idx, total, pid, url, old_wc)

            if not url:
                LOGGER.warning("Profile %s has no URL; skipping", pid)
                continue

            # Try to fetch via Playwright
            new_text = await fetch_page_text(
                page,
                url,
                timeout_ms=timeout_ms,
                post_load_wait_ms=post_load_wait_ms,
            )
            new_wc = word_count(new_text)

            LOGGER.info("Profile %s: new_wc=%d (old_wc=%d)", pid, new_wc, old_wc)

            # Only overwrite if we clearly got more content
            if new_wc > old_wc and new_wc >= 10:
                details["fullText"] = new_text
                profile["profileDetails"] = details
                improved += 1
                LOGGER.info("Updated profile %s fullText (wc %d -> %d)", pid, old_wc, new_wc)
            else:
                LOGGER.info("Kept existing fullText for %s", pid)

            time.sleep(delay_seconds)

        await browser.close()

    LOGGER.info("JS rescrape complete. Improved %d / %d profiles.", improved, total)

    output_path.write_text(
        json.dumps(profiles, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    LOGGER.info("Wrote updated short profiles to %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use Playwright to rescrape short profiles and improve fullText if possible."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to profiles_short_fulltext.rescraped.json",
    )
    parser.add_argument(
        "output_json",
        type=Path,
        help="Path to output JSON with JS-rescraped fullText",
    )
    args = parser.parse_args()

    import asyncio
    asyncio.run(
        rescrape_short_profiles_js(
            input_path=args.input_json,
            output_path=args.output_json,
        )
    )


if __name__ == "__main__":
    main()
