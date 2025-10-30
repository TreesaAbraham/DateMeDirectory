// scripts/fetch-directory.js
// Fetches the main browse page and saves raw HTML under data/raw/

const fs = require("fs");                // Node's file system: read/write files like a civilized raccoon.
const path = require("path");            // Path utilities so you stop hardcoding slashes like it's 1999.

// Node 18+ has global fetch. Your CI uses Node 20, so we're good.
const URL_TO_FETCH = "https://dateme.directory/browse";  // The target page. One job, one URL.

async function main() {                  // Async function because network I/O isn’t instant, despite your optimism.
  const startedAt = new Date().toISOString();  // Timestamp for when we *started* the fetch. Metadata is your future alibi.

  // Output paths
  const outDir = path.join(__dirname, "..", "data", "raw");  // Resolve to project/data/raw no matter where you run it from.
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true }); // Create the folder tree if it doesn't exist.

  const stamp = new Date()               // Create a file-safe timestamp like 20251030-142233
    .toISOString()                       // ISO time so your files sort lexicographically. We like order.
    .replace(/[-:]/g, "")                // Kill separators ( - : ) that make filenames annoying.
    .replace(/\..+/, "")                 // Drop milliseconds because you’re not that precise.
    .replace("T", "-");                  // Replace 'T' with '-' for readability: YYYYMMDD-HHMMSS

  const htmlPath = path.join(outDir, `browse-${stamp}.html`);      // Where the raw HTML will live.
  const metaPath = path.join(outDir, `browse-${stamp}.meta.json`); // Where the fetch metadata will live.

  // Be polite with a UA. Some sites block the default.
  const res = await fetch(URL_TO_FETCH, {  // Perform the HTTP request. Yes, await it.
    headers: {
      "user-agent":
        "DateMeDirectoryDataBot/1.0 (+https://example.com; contact: research@example.com)", // Don’t be anonymous; it’s sketchy.
      "accept": "text/html,application/xhtml+xml",  // Hint we want HTML, not a random download.
    },
    redirect: "follow",                   // If they redirect, follow it like a well-trained script.
  });

  const status = res.status;              // Numeric HTTP status (200, 404, etc.).
  const ok = res.ok;                      // Boolean: true for 2xx, false otherwise.

  const html = await res.text();          // Slurp the response body as text. This is your page HTML.

  // Write HTML
  fs.writeFileSync(htmlPath, html, "utf-8");    // Save the raw HTML so you can parse it later or regret nothing.

  // Write a little metadata for sanity
  const meta = {                          // Bundle context so future-you knows what happened.
    url: URL_TO_FETCH,                    // Source URL, in case you somehow forget.
    startedAt,                            // When we started the request.
    fetchedAt: new Date().toISOString(),  // When we finished. Close enough for government work.
    status,                               // HTTP status code recorded for posterity.
    ok,                                   // Was it a “success” by fetch standards.
    length: html.length,                  // HTML length. Useful for spotting empty or truncated responses.
    output: path.relative(path.join(__dirname, ".."), htmlPath), // Nice relative path for logs/CI.
  };
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), "utf-8"); // Save the metadata next to the HTML.

  if (!ok) {                              // If the status isn’t 2xx, complain and fail the process.
    console.error(`Fetch completed but not OK (status ${status}). See ${metaPath}`);
    process.exit(1);                      // Non-zero exit so CI and your conscience both notice.
  }

  console.log(`✅ Saved HTML to ${htmlPath}`);     // Friendly confirmation for humans.
  console.log(`📝 Saved metadata to ${metaPath}`); // Ditto for the metadata.
}

main().catch((err) => {                   // Global catch so the script doesn't crash silently.
  console.error("💥 Fetch failed:", err.message); // Print the error message like adults.
  process.exit(1);                        // Non-zero exit because failure should actually fail.
});
