// scripts/fetch-directory.js
// Fetches the main browse page and saves raw HTML under data/raw/

const fs = require("fs");
const path = require("path");

// Node 18+ has global fetch. Your CI uses Node 20, so we're good.
const URL_TO_FETCH = "https://dateme.directory/browse";

async function main() {
  const startedAt = new Date().toISOString();

  // Output paths
  const outDir = path.join(__dirname, "..", "data", "raw");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\..+/, "") // e.g. 20251030T141500
    .replace("T", "-");

  const htmlPath = path.join(outDir, `browse-${stamp}.html`);
  const metaPath = path.join(outDir, `browse-${stamp}.meta.json`);

  // Be polite with a UA. Some sites block the default.
  const res = await fetch(URL_TO_FETCH, {
    headers: {
      "user-agent":
        "DateMeDirectoryDataBot/1.0 (+https://example.com; contact: research@example.com)",
      "accept": "text/html,application/xhtml+xml",
    },
    redirect: "follow",
  });

  const status = res.status;
  const ok = res.ok;

  const html = await res.text();

  // Write HTML
  fs.writeFileSync(htmlPath, html, "utf-8");

  // Write a little metadata for sanity
  const meta = {
    url: URL_TO_FETCH,
    startedAt,
    fetchedAt: new Date().toISOString(),
    status,
    ok,
    length: html.length,
    output: path.relative(path.join(__dirname, ".."), htmlPath),
  };
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), "utf-8");

  if (!ok) {
    console.error(`Fetch completed but not OK (status ${status}). See ${metaPath}`);
    process.exit(1);
  }

  console.log(`✅ Saved HTML to ${htmlPath}`);
  console.log(`📝 Saved metadata to ${metaPath}`);
}

main().catch((err) => {
  console.error("💥 Fetch failed:", err.message);
  process.exit(1);
});
