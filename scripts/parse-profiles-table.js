// scripts/parse-profiles-table.js
// Parse the actual table at https://dateme.directory/browse
// into our processed JSON format.
//
// This is the version that:
// - handles blank location cells
// - trims very long locations
// - normalizes M/F/NB
// - normalizes "M NB" → ["male","nonbinary"]
// - writes to data/processed/ like the other scripts

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");
const crypto = require("crypto");

const RAW_DIR = path.join(__dirname, "..", "data", "raw");
const PROCESSED_DIR = path.join(__dirname, "..", "data", "processed");

// ---------- helpers ----------

// find latest crawl folder: data/raw/browse-YYYYMMDD-HHMMSS
function newestCrawlFolder() {
  if (!fs.existsSync(RAW_DIR)) return null;
  const dirs = fs
    .readdirSync(RAW_DIR)
    .filter((d) => /^browse-\d{8}-\d{6}$/.test(d))
    .sort();
  return dirs.length ? path.join(RAW_DIR, dirs[dirs.length - 1]) : null;
}

function readHtmlFiles(folder) {
  const files = fs.readdirSync(folder).filter((f) => f.endsWith(".html")).sort();
  return files.map((f) => ({
    name: f,
    html: fs.readFileSync(path.join(folder, f), "utf-8"),
  }));
}

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function todayIso() {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

// make a stable-ish id from name+location
function makeId(name, location) {
  const basis = `${name || ""}|${location || ""}`.toLowerCase();
  return "usr_" + crypto.createHash("md5").update(basis).digest("hex").slice(0, 10);
}

// normalize gender from M/F/NB
function normGender(s) {
  if (!s) return undefined;
  const t = s.trim().toLowerCase();
  if (t === "m" || t === "male") return "male";
  if (t === "f" || t === "female") return "female";
  if (t === "nb" || t === "nonbinary" || t === "non-binary") return "nonbinary";
  return undefined;
}

// normalize "M NB", "F", "Any"
function normInterestedIn(s) {
  if (!s) return undefined;
  const pieces = s
    .split(/[\s,]+/)
    .map((p) => p.trim())
    .filter(Boolean);
  if (!pieces.length) return undefined;

  const out = new Set();
  for (const p of pieces) {
    const t = p.toLowerCase();
    if (t === "any") {
      out.add("male");
      out.add("female");
      out.add("nonbinary");
      continue;
    }
    if (t === "m" || t === "male") out.add("male");
    else if (t === "f" || t === "female") out.add("female");
    else if (t === "nb" || t === "nonbinary" || t === "non-binary") out.add("nonbinary");
  }
  return out.size ? Array.from(out) : undefined;
}

function normLocationFlex(s) {
  if (!s) return undefined;
  const t = s.trim().toLowerCase();
  if (t.includes("none")) return "none";
  if (t.includes("flex")) return "flexible";
  if (t.includes("some")) return "some";
  return undefined;
}

// ---------- core extractor ----------

function extractFromTable(html) {
  const $ = cheerio.load(html);

  // find the table that actually has Name/Age headers
  let table = null;
  $("table").each((_, el) => {
    const headerText = $(el).find("thead, tr").first().text().toLowerCase();
    if (headerText.includes("name") && headerText.includes("age")) {
      table = $(el);
      return false;
    }
  });

  if (!table) return [];

  const rows = [];

  // assume table order:
  // 0: Name
  // 1: Age
  // 2: Gender
  // 3: InterestedIn
  // 4: Style (we can ignore for now)
  // 5: Location
  // 6: LocationFlexibility
  // 7: Contact (not in schema, so skipping)
  // 8: LastUpdated
  table.find("tbody tr").each((_, tr) => {
    const tds = $(tr).find("td");
    if (!tds.length) return;

    const name = $(tds[0]).text().trim();
    if (!name) return; // skip empty rows

    const ageText = $(tds[1]).text().trim();
    const genderText = $(tds[2]).text().trim();
    const interestedText = $(tds[3]).text().trim();
    // const style = $(tds[4]).text().trim(); // not in minimal schema
    let location = $(tds[5]).text().trim();
    const locationFlexText = $(tds[6]).text().trim();
    const lastUpdatedText = $(tds[8]).text().trim();

    const age = Number(ageText) || undefined;
    const gender = normGender(genderText);
    const genderInterestedIn = normInterestedIn(interestedText);
    let locationFlexibility = normLocationFlex(locationFlexText);
    const lastUpdated = lastUpdatedText || todayIso();

    // handle blank location from site
    if (location === "") {
      location = undefined;
    } else {
      // trim wild long locations people type like 30 cities
      if (location.length > 1000) {
        location = location.slice(0, 1000);
      }
    }

    // sometimes locationFlexibility is still undefined but site said "some"
    // normLocationFlex already handled that, so we're good

    const id = makeId(name, location);

    const rec = {
      id,
      name,
      age,
      gender,
      genderInterestedIn,
      location,
      locationFlexibility,
      lastUpdated,
    };

    // drop undefineds
    Object.keys(rec).forEach((k) => rec[k] === undefined && delete rec[k]);

    rows.push(rec);
  });

  return rows;
}

// ---------- main ----------

async function main() {
  const folder = newestCrawlFolder();
  if (!folder) {
    console.error("No crawl folder found in data/raw. Run `npm run fetch:browse` first.");
    process.exit(1);
  }

  const pages = readHtmlFiles(folder);
  if (!pages.length) {
    console.error(`No HTML files in ${folder}`);
    process.exit(1);
  }

  const all = [];
  for (const { name, html } of pages) {
    const rows = extractFromTable(html);
    rows.forEach((r) => (r._source = name));
    all.push(...rows);
  }

  // dedupe by id+name
  const map = new Map();
  for (const r of all) {
    const key = `${r.id}::${r.name}`;
    if (!map.has(key)) {
      map.set(key, r);
    }
  }

  const unique = [...map.values()].map(({ _source, ...rest }) => rest);

  ensureDir(PROCESSED_DIR);
  const base = path.basename(folder).replace("browse-", "profiles-");
  const outJson = path.join(PROCESSED_DIR, `${base}.json`);
  const outNdjson = path.join(PROCESSED_DIR, `${base}.ndjson`);

  fs.writeFileSync(outJson, JSON.stringify(unique, null, 2), "utf-8");
  fs.writeFileSync(outNdjson, unique.map((r) => JSON.stringify(r)).join("\n") + "\n", "utf-8");

  console.log(`✅ Parsed ${unique.length} profile(s) from table.`);
  console.log(`📝 JSON:   ${path.relative(path.join(__dirname, ".."), outJson)}`);
  console.log(`📝 NDJSON: ${path.relative(path.join(__dirname, ".."), outNdjson)}`);
}

main().catch((err) => {
  console.error("💥 parse failed:", err);
  process.exit(1);
});
