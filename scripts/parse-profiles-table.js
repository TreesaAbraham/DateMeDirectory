// scripts/parse-profiles-table.js
// Build browse-level profile JSON objects that match schemas/profile.browse.schema.json

const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");
const crypto = require("crypto");

const RAW_DIR = path.join(__dirname, "..", "data", "raw");
const PROCESSED_DIR = path.join(__dirname, "..", "data", "processed");

function newestCrawlFolder() {
  if (!fs.existsSync(RAW_DIR)) return null;
  const dirs = fs
    .readdirSync(RAW_DIR)
    .filter((d) => /^browse-\d{8}-\d{6}$/.test(d))
    .sort();
  return dirs.length ? path.join(RAW_DIR, dirs[dirs.length - 1]) : null;
}

function readHtmlFiles(folder) {
  return fs
    .readdirSync(folder)
    .filter((f) => f.endsWith(".html"))
    .sort()
    .map((f) => ({
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

function makeId(name, location) {
  const basis = `${name || ""}|${location || ""}`.toLowerCase();
  return "usr_" + crypto.createHash("md5").update(basis).digest("hex").slice(0, 10);
}

function normGender(s) {
  if (!s) return undefined;
  const t = s.trim().toLowerCase();
  if (t === "m" || t === "male") return "male";
  if (t === "f" || t === "female") return "female";
  if (t === "nb" || t === "nonbinary" || t === "non-binary") return "nonbinary";
  return undefined;
}

function normInterestedIn(s) {
  if (!s) return undefined;
  const parts = s
    .split(/[\s,]+/)
    .map((p) => p.trim())
    .filter(Boolean);
  if (!parts.length) return undefined;

  const out = new Set();
  for (const p of parts) {
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

function extractFromTable(html) {
  const $ = cheerio.load(html);

  // find the right table
  let table = null;
  $("table").each((_, el) => {
    const header = $(el).find("thead, tr").first().text().toLowerCase();
    if (header.includes("name") && header.includes("age")) {
      table = $(el);
      return false;
    }
  });
  if (!table) return [];

  const out = [];

  table.find("tbody tr").each((_, tr) => {
    const tds = $(tr).find("td");
    if (!tds.length) return;

    const name = $(tds[0]).text().trim();
    if (!name) return;

    const ageText = $(tds[1]).text().trim();
    const genderText = $(tds[2]).text().trim();
    const interestedText = $(tds[3]).text().trim();
    // const style = $(tds[4]).text().trim();
    let location = $(tds[5]).text().trim();
    const locFlexText = $(tds[6]).text().trim();
    const lastUpdatedText = $(tds[8]).text().trim();

    // normalize
    const age = Number(ageText) || undefined;
    const gender = normGender(genderText);
    const genderInterestedIn = normInterestedIn(interestedText);
    const locationFlexibility = normLocationFlex(locFlexText);
    const lastUpdated = lastUpdatedText || todayIso();

    if (location === "") {
      location = undefined;
    } else if (location.length > 1000) {
      location = location.slice(0, 1000);
    }

    const id = makeId(name, location);

    // build object according to browse schema
    const rec = {
      id,
      name,
      lastUpdated
    };

    if (typeof age === "number") rec.age = age;
    if (gender) rec.gender = gender;
    if (Array.isArray(genderInterestedIn) && genderInterestedIn.length) {
      rec.genderInterestedIn = genderInterestedIn;
    }
    if (location) rec.location = location;
    if (locationFlexibility) rec.locationFlexibility = locationFlexibility;

    out.push(rec);
  });

  return out;
}

async function main() {
  const folder = newestCrawlFolder();
  if (!folder) {
    console.error("No crawl folder in data/raw. Run `npm run fetch:browse` first.");
    process.exit(1);
  }

  const pages = readHtmlFiles(folder);
  const all = [];

  for (const { name, html } of pages) {
    const rows = extractFromTable(html);
    rows.forEach((r) => (r._source = name));
    all.push(...rows);
  }

  // dedupe
  const seen = new Map();
  for (const r of all) {
    const key = `${r.id}::${r.name}`;
    if (!seen.has(key)) seen.set(key, r);
  }
  const unique = [...seen.values()].map(({ _source, ...rest }) => rest);

  ensureDir(PROCESSED_DIR);
  const base = path.basename(folder).replace("browse-", "profiles-");
  const outJson = path.join(PROCESSED_DIR, `${base}.json`);
  const outNdjson = path.join(PROCESSED_DIR, `${base}.ndjson`);

  fs.writeFileSync(outJson, JSON.stringify(unique, null, 2), "utf-8");
  fs.writeFileSync(
    outNdjson,
    unique.map((r) => JSON.stringify(r)).join("\n") + "\n",
    "utf-8"
  );

  console.log(`✅ Parsed ${unique.length} browse-level profile(s).`);
  console.log(`📝 JSON:   ${path.relative(path.join(__dirname, ".."), outJson)}`);
  console.log(`📝 NDJSON: ${path.relative(path.join(__dirname, ".."), outNdjson)}`);
}

main().catch((err) => {
  console.error("💥 Parse failed:", err);
  process.exit(1);
});
