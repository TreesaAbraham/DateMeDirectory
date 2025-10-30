// scripts/fetch-directory-paginated.js
// Crawls the DateMe Directory browse listing with "next page" heuristics.
// Saves every page HTML and a crawl manifest for reproducibility.

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");

const START_URL = "https://dateme.directory/browse";

// config via env or defaults
const MAX_PAGES = Number(process.env.MAX_PAGES || 50);
const REQUEST_DELAY_MS = Number(process.env.REQUEST_DELAY_MS || 1500);

// polite headers
const DEFAULT_HEADERS = {
  "user-agent":
    "DateMeDirectoryDataBot/1.0 (+https://example.com; contact: research@example.com)",
  accept: "text/html,application/xhtml+xml",
};

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function tsFolder() {
  // timestamp folder yyyyMMdd-HHmmss
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
}

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function safeJoin(...parts) {
  return path.join(...parts).replace(/\\/g, "/");
}

function absolutizeUrl(base, href) {
  try {
    return new URL(href, base).toString();
  } catch {
    return null;
  }
}

function guessNextUrl(currentUrl, $) {
  // 1) <a rel="next" href="...">
  const relNextHref = $('a[rel="next"]').attr("href");
  if (relNextHref) {
    const out = absolutizeUrl(currentUrl, relNextHref);
    if (out) return out;
  }

  // 2) Pagination link with "Next" text
  const nextTextHref = $('a:contains("Next"), a:contains("Load more")').first().attr("href");
  if (nextTextHref) {
    const out = absolutizeUrl(currentUrl, nextTextHref);
    if (out) return out;
  }

  // 3) Button with data-next or aria-controls referencing a next URL in data attribute
  const dataNext = $('[data-next],[data-next-url]').first();
  const dataHref = dataNext.attr("data-next") || dataNext.attr("data-next-url");
  if (dataHref) {
    const out = absolutizeUrl(currentUrl, dataHref);
    if (out) return out;
  }

  // 4) Embedded JSON-ish hint: look for `"next":"..."`
  const html = $.root().html() || "";
  const m = html.match(/"next"\s*:\s*"([^"]+)"/i);
  if (m && m[1]) {
    const out = absolutizeUrl(currentUrl, m[1]);
    if (out) return out;
  }

  // 5) Page param heuristic: ?page=N or &page=N
  try {
    const u = new URL(currentUrl);
    const hasPage = u.searchParams.has("page");
    const n = hasPage ? Number(u.searchParams.get("page")) || 1 : 1;
    const nextN = n + 1;

    // Only attempt if we saw pagination elements at all
    const sawPagination =
      $('a[rel="next"]').length ||
      $('a:contains("Next"), a:contains("Load more")').length ||
      /\bpage\b/i.test(html);
    if (sawPagination) {
      if (!hasPage) u.searchParams.set("page", String(nextN));
      else u.searchParams.set("page", String(nextN));
      return u.toString();
    }
  } catch {
    // ignore
  }

  return null;
}

async function fetchHtml(url) {
  const res = await fetch(url, { headers: DEFAULT_HEADERS, redirect: "follow" });
  const text = await res.text();
  return { status: res.status, ok: res.ok, url: res.url, html: text };
}

async function main() {
  const startedAt = new Date().toISOString();

  // Create a crawl session folder
  const session = tsFolder();
  const baseOut = path.join(__dirname, "..", "data", "raw", `browse-${session}`);
  ensureDir(baseOut);

  const manifestPath = safeJoin(baseOut, "manifest.json");
  const pages = [];

  let currentUrl = START_URL;
  let pageIndex = 1;
  let seen = new Set();

  while (pageIndex <= MAX_PAGES) {
    if (seen.has(currentUrl)) {
      console.warn(`🔁 Already fetched ${currentUrl}. Stopping to avoid a loop.`);
      break;
    }
    seen.add(currentUrl);

    console.log(`➡️  Fetching [${pageIndex}/${MAX_PAGES}] ${currentUrl}`);
    const { status, ok, url, html } = await fetchHtml(currentUrl);

    const filename = `page-${String(pageIndex).padStart(3, "0")}.html`;
    const htmlPath = safeJoin(baseOut, filename);
    fs.writeFileSync(htmlPath, html, "utf-8");

    const meta = {
      index: pageIndex,
      requestedUrl: currentUrl,
      finalUrl: url,
      status,
      ok,
      savedAs: path.basename(htmlPath),
      savedAt: new Date().toISOString(),
      length: html.length,
    };
    pages.push(meta);

    // Persist manifest as we go, in case we stop mid-crawl
    fs.writeFileSync(
      manifestPath,
      JSON.stringify(
        {
          startedAt,
          session,
          startUrl: START_URL,
          maxPages: MAX_PAGES,
          delayMs: REQUEST_DELAY_MS,
          pages,
        },
        null,
        2
      ),
      "utf-8"
    );

    if (!ok) {
      console.warn(`⚠️  Status ${status} at ${url}. Stopping pagination.`);
      break;
    }

    // Parse HTML to find next page
    const $ = cheerio.load(html);
    const nextUrl = guessNextUrl(url, $);

    if (!nextUrl) {
      console.log("No next page found. Crawl complete.");
      break;
    }

    // Gentle delay between requests
    await sleep(REQUEST_DELAY_MS);
    currentUrl = nextUrl;
    pageIndex++;
  }

  console.log(`\n Saved ${pages.length} page(s) to ${baseOut}`);
  console.log(` Manifest: ${manifestPath}`);

  // Exit non-zero if we fetched nothing
  if (pages.length === 0) process.exit(1);
}

main().catch((err) => {
  console.error(" Pagination fetch failed:", err);
  process.exit(1);
});
