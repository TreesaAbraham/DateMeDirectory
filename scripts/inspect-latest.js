// scripts/inspect-latest.js
// Prints how many candidate elements we find per page and shows a snippet.

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");

const RAW_DIR = path.join(__dirname, "..", "data", "raw");

function listSubdirs(p) {
  return fs.existsSync(p)
    ? fs.readdirSync(p).filter((f) => fs.statSync(path.join(p, f)).isDirectory())
    : [];
}

function newestCrawlFolder() {
  const dirs = listSubdirs(RAW_DIR)
    .filter((d) => /^browse-\d{8}-\d{6}$/.test(d))
    .sort();
  return dirs.length ? dirs[dirs.length - 1] : null;
}

function readHtmlFiles(inputDirOrFile) {
  if (!inputDirOrFile) return [];
  if (fs.existsSync(inputDirOrFile) && fs.statSync(inputDirOrFile).isFile()) {
    return [{ name: path.basename(inputDirOrFile), html: fs.readFileSync(inputDirOrFile, "utf-8") }];
  }
  const files = fs.readdirSync(inputDirOrFile).filter((f) => f.endsWith(".html")).sort();
  return files.map((f) => ({ name: f, html: fs.readFileSync(path.join(inputDirOrFile, f), "utf-8") }));
}

function inspect(html) {
  const $ = cheerio.load(html);
  const selectors = [
    ".profile-card",
    ".card-profile",
    "[data-profile]",
    "li.profile",
    "tr.profile",
    ".profileRow",
    ".profile",
    ".result-card",
    // extra guesses:
    '[data-testid*="profile"]',
    'article:has([class*="name"]), div:has([class*="name"])'
  ];
  const sel = selectors.join(", ");
  const nodes = $(sel);
  const allCards = nodes.length;

  // try a “Next” link presence as a hint
  const hasNext = $('a[rel="next"]').length || $('a:contains("Next"), a:contains("Load more")').length;

  // sample text from the page
  const bodyText = $("body").text().replace(/\s+/g, " ").slice(0, 200);

  // peek any JSON blobs that look like Next.js
  const nextData = $('script#__NEXT_DATA__').html();
  return { allCards, hasNext: !!hasNext, bodyText, hasNextData: !!nextData, nextDataSample: nextData ? nextData.slice(0, 200) : null };
}

function main() {
  // Prefer paginated folder; else look for single-page HTML files
  const session = newestCrawlFolder();
  let inputs = [];
  if (session) {
    inputs = readHtmlFiles(path.join(RAW_DIR, session));
  } else {
    const files = fs.existsSync(RAW_DIR)
      ? fs.readdirSync(RAW_DIR).filter((f) => /^browse-\d{8}-\d{6}\.html$/.test(f)).sort()
      : [];
    if (files.length) {
      inputs = files.map((f) => ({ name: f, html: fs.readFileSync(path.join(RAW_DIR, f), "utf-8") }));
    }
  }

  if (!inputs.length) {
    console.error("No HTML found under data/raw. Run `npm run fetch:browse[:all]` first.");
    process.exit(1);
  }

  for (const { name, html } of inputs) {
    const info = inspect(html);
    console.log(`\n=== ${name} ===`);
    console.log(`candidates found: ${info.allCards}`);
    console.log(`has next link:    ${info.hasNext}`);
    console.log(`has __NEXT_DATA__: ${info.hasNextData}`);
    console.log(`body snippet:     "${info.bodyText}"`);
    if (info.hasNextData && info.nextDataSample) {
      console.log(`__NEXT_DATA__ sample: ${info.nextDataSample.replace(/\s+/g,' ').slice(0,180)}...`);
    }
  }
}

main();
