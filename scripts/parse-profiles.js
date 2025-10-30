// scripts/parse-profiles.js
// Parses crawled browse pages into structured profile rows.
// Output: data/processed/profiles-<session>.json (array) + .ndjson

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

// ---------- config ----------
const RAW_DIR = path.join(__dirname, "..", "data", "raw");
const PROCESSED_DIR = path.join(__dirname, "..", "data", "processed");
const SCHEMA_PATH = path.join(__dirname, "..", "schemas", "profile.schema.json");
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validate = ajv.compile(JSON.parse(fs.readFileSync(SCHEMA_PATH, "utf-8")));

// ---------- utils ----------
function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

function listSubdirs(p) {
  return fs.existsSync(p)
    ? fs.readdirSync(p).filter((f) => fs.statSync(path.join(p, f)).isDirectory())
    : [];
}

function newestCrawlFolder() {
  const dirs = listSubdirs(RAW_DIR)
    .filter((d) => /^browse-\d{8}-\d{6}$/.test(d))
    .sort(); // ISO-ish timestamp sorts lexicographically
  return dirs.length ? dirs[dirs.length - 1] : null;
}

function readHtmlFiles(folderPath) {
  if (!fs.existsSync(folderPath)) return [];
  const files = fs.readdirSync(folderPath).filter((f) => f.endsWith(".html"));
  files.sort();
  return files.map((f) => ({
    name: f,
    html: fs.readFileSync(path.join(folderPath, f), "utf-8"),
  }));
}

function textOf($, el) {
  return $(el).text().replace(/\s+/g, " ").trim();
}

function toInt(maybe) {
  const n = Number(String(maybe).replace(/[^\d]/g, ""));
  return Number.isFinite(n) && n > 0 ? n : undefined;
}

function normGender(s) {
  if (!s) return undefined;
  const t = s.toLowerCase();
  if (/^f(emale)?\b/.test(t)) return "female";
  if (/^m(ale)?\b/.test(t)) return "male";
  if (/non\s*binary|nonbinary|nb\b/.test(t)) return "nonbinary";
  return undefined;
}

function normFlex(s) {
  if (!s) return undefined;
  const t = s.toLowerCase();
  if (/^none$|stay put|no relo/.test(t)) return "none";
  if (/flex|open|anywhere|remote/.test(t)) return "flexible";
  if (/some|maybe|depends/.test(t)) return "some";
  return undefined;
}

function isoDateToday() {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

// Make a deterministic-ish ID even if site doesn’t give one.
// Prefer data-id or href slug; fallback to a hash-ish of name+location.
const crypto = require("crypto");
function computeId({ rawId, href, name, location }) {
  if (rawId) return String(rawId);
  if (href) {
    try {
      const u = new URL(href, "https://dateme.directory");
      const slug = u.pathname.replace(/^\/+|\/+$/g, "").split("/").pop();
      if (slug) return slug;
    } catch {}
  }
  const basis = `${name || ""}|${location || ""}`.toLowerCase();
  return "usr_" + crypto.createHash("md5").update(basis).digest("hex").slice(0, 10);
}

// ---------- extraction heuristics ----------
/**
 * We try a few common card/table structures:
 * - .profile-card, .card-profile, [data-profile], li.profile, tr.profile
 * - Each card might have:
 *    name: .name, .title, h2, h3, a.card-title
 *    age:  .age, .meta, text like "23 • F • NYC"
 *    gender: .gender or inferred from meta text
 *    location: .location, .city, .meta
 *    interested in: badges/chips with text "seeking: ...", "interested in ..."
 *    link/id: a[href], data-id
 */
function extractProfilesFromHtml(html) {
  const $ = cheerio.load(html);

  // Candidate containers
  const candidates = $(
    ".profile-card, .card-profile, [data-profile], li.profile, tr.profile, .profileRow, .profile, .result-card"
  );
  const rows = candidates.length ? candidates : $(".card, .row, article, li, tr");

  const results = [];

  rows.each((_, el) => {
    const row = $(el);

    // try to find an anchor per row
    const a = row.find('a[href*="/profile/"], a[href*="/p/"], a[href*="profiles"]').first();
    const href = a.attr("href");

    // name candidates
    const name =
      textOf($, row.find(".name").first()) ||
      textOf($, row.find(".title").first()) ||
      textOf($, row.find("h2").first()) ||
      textOf($, row.find("h3").first()) ||
      textOf($, a.first());

    // age candidates
    let ageText =
      textOf($, row.find(".age").first()) ||
      textOf($, row.find(".meta").first()) ||
      textOf($, row.find(".details").first()) ||
      textOf($, row);
    const age = toInt((ageText.match(/\b(\d{2})\b/) || [])[1]);

    // gender
    let genderText =
      textOf($, row.find(".gender").first()) ||
      (ageText.match(/\b(male|female|non[-\s]?binary|nb)\b/i) || [])[0];
    const gender = normGender(genderText);

    // location
    let location =
      textOf($, row.find(".location").first()) ||
      textOf($, row.find(".city").first()) ||
      (ageText.match(/\b(?:[A-Z][a-z]+(?:,?\s+[A-Z]{2})?)\b/) || [])[0] ||
      undefined;

    // genderInterestedIn (chips or text like "seeking: men, women")
    let interestText =
      textOf($, row.find('[class*="chip"],[class*="badge"],[class*="tag"]').filter((_, n) => {
        const t = $(n).text().toLowerCase();
        return /seek|interested|looking/.test(t);
      })) ||
      (ageText.match(/(seek|interested|looking)\s*[:\-]?\s*([a-z,\s\-]+)/i) || [])[2];

    let genderInterestedIn = [];
    if (interestText) {
      const norm = interestText.toLowerCase();
      if (/\bmen|male|guys?\b/.test(norm)) genderInterestedIn.push("male");
      if (/\bwomen|female|girls?\b/.test(norm)) genderInterestedIn.push("female");
      if (/\bnon[-\s]?binary|nb\b/.test(norm)) genderInterestedIn.push("nonbinary");
    }
    genderInterestedIn = [...new Set(genderInterestedIn)];
    if (!genderInterestedIn.length) genderInterestedIn = undefined;

    // locationFlexibility (very heuristic)
    const flexText =
      textOf($, row.find(".relocation, .mobility, .remote, .travel").first()) || ageText;
    const locationFlexibility = normFlex(flexText);

    // raw id hints
    const rawId = row.attr("data-id") || row.attr("id");
    const id = computeId({ rawId, href, name, location });

    // lastUpdated isn't on list pages; set to today for extraction snapshot
    const lastUpdated = isoDateToday();

    // require at least a name to count as a profile row
    if (name) {
      const rec = {
        id,
        name,
        age,
        gender,
        genderInterestedIn,
        location,
        locationFlexibility,
        lastUpdated,
        // optional debug crumbs to help tuning (not in schema -> we don't include them)
      };

      // Only include properties defined in the minimal schema
      // Remove undefineds for cleanliness
      Object.keys(rec).forEach((k) => rec[k] === undefined && delete rec[k]);

      // Validate against schema; skip records that fail
      const ok = validate(rec);
      if (!ok) {
        // Soft log for tuning; you can flip this to hard fail if you want
        // console.error("Skip invalid record:", validate.errors, rec);
        return;
      }

      results.push(rec);
    }
  });

  return results;
}

// ---------- main ----------
async function main() {
  const session = newestCrawlFolder();
  if (!session) {
    console.error("No crawl session found under data/raw/. Run fetch:browse or fetch:browse:all first.");
    process.exit(1);
  }
  const inputDir = path.join(RAW_DIR, session);
  ensureDir(PROCESSED_DIR);

  const pages = readHtmlFiles(inputDir);
  if (!pages.length) {
    console.error(`No HTML files in ${inputDir}`);
    process.exit(1);
  }

  const all = [];
  for (const { name, html } of pages) {
    const rows = extractProfilesFromHtml(html);
    rows.forEach((r) => (r._source = name)); // attach source page for traceability (not in final output)
    all.push(...rows);
  }

  // Deduplicate by id + name
  const key = (r) => `${r.id}::${r.name}`;
  const map = new Map();
  for (const r of all) {
    if (!map.has(key(r))) map.set(key(r), r);
  }
  const unique = [...map.values()].map(({ _source, ...rest }) => rest);

  const base = `profiles-${session}`;
  const outJson = path.join(PROCESSED_DIR, `${base}.json`);
  const outNdjson = path.join(PROCESSED_DIR, `${base}.ndjson`);

  fs.writeFileSync(outJson, JSON.stringify(unique, null, 2), "utf-8");
  fs.writeFileSync(outNdjson, unique.map((r) => JSON.stringify(r)).join("\n") + "\n", "utf-8");

  console.log(`✅ Parsed ${unique.length} profile(s) from ${pages.length} page(s).`);
  console.log(`📝 JSON:   ${path.relative(path.join(__dirname, ".."), outJson)}`);
  console.log(`📝 NDJSON: ${path.relative(path.join(__dirname, ".."), outNdjson)}`);
}

main().catch((e) => {
  console.error("💥 Parse failed:", e);
  process.exit(1);
});
