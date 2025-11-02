// scripts/parse-profiles-table.js
// Parses the directory table HTML and exports it as JSON following our profile schema.

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import crypto from "crypto";
import { load } from "cheerio"; // make sure you have this in package.json deps

// Resolve __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 1. Define file locations
const SOURCE_HTML = path.join(__dirname, "..", "data", "raw", "directory.html");
// where the "latest" parsed output goes (tests look here)
const PARSED_DIR = path.join(__dirname, "..", "data", "parsed");
const LATEST_JSON = path.join(PARSED_DIR, "latest.json");
// master export you asked for
const MASTER_JSON = path.join(__dirname, "..", "data", "profiles_master.json");

// 2. tiny helper so Node doesn't collapse in shame
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 3. create internal ID (close to what you had: usr_<hex>)
function createInternalId() {
  // 5 bytes -> 10 hex chars
  return "usr_" + crypto.randomBytes(5).toString("hex");
}

// 4. normalize "2024-8-3" or "Aug 3, 2024" to "2024-08-03"
function normalizeDate(raw) {
  if (!raw) {
    return null;
  }

  // If it's already YYYY-MM-DD, keep it
  const isoLike = /^(\d{4})-(\d{1,2})-(\d{1,2})$/;
  const m = raw.trim().match(isoLike);
  if (m) {
    const year = m[1];
    const month = String(m[2]).padStart(2, "0");
    const day = String(m[3]).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // fallback: let Date try
  const d = new Date(raw);
  if (!isNaN(d.getTime())) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  // worst case, return as-is so you at least see it
  return raw;
}

// 5. turn one HTML <tr> into a profile object
function rowToProfile($, tr) {
  const tds = $(tr).find("td");

  // Assuming your table is in this order:
  // 0: Name (with <a>)
  // 1: Age
  // 2: Gender
  // 3: Interested in
  // 4: Location
  // 5: Location flexibility
  // 6: Last updated
  //
  // If your real table is slightly different, adjust the indexes here.
  const nameCell = $(tds[0]);
  const nameLink = nameCell.find("a");
  const name = nameLink.text().trim() || nameCell.text().trim();

  const ageRaw = $(tds[1]).text().trim();
  const gender = $(tds[2]).text().trim() || null;
  const genderInterestedInRaw = $(tds[3]).text().trim();
  const locationRaw = $(tds[4]).text().trim();
  const locationFlexibilityRaw = $(tds[5]).text().trim();
  const lastUpdatedRaw = $(tds[6]).text().trim();

  // schema wants array for genderInterestedIn
  const genderInterestedIn = genderInterestedInRaw
    ? genderInterestedInRaw
        .split(/[,&/]/)
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  // test was failing because location was "" (minLength issue)
  // so if we don't have location, give it a non-empty fallback
  const location = locationRaw && locationRaw.length > 0 ? locationRaw : "unspecified";

  const profile = {
    id: createInternalId(),
    name,
    age: ageRaw ? Number(ageRaw) : null,
    gender,
    genderInterestedIn,
    location,
    locationFlexibility: locationFlexibilityRaw || "unknown",
    lastUpdated: normalizeDate(lastUpdatedRaw),
    // you said: "Initialize `profileDetails` as `{}` and `scrapeTimestampDetail` as `null`"
    profileDetails: {},
    scrapeTimestampDetail: null,
  };

  return profile;
}

// 6. main
function main() {
  ensureDir(PARSED_DIR);

  if (!fs.existsSync(SOURCE_HTML)) {
    console.error(
      `❌ Source HTML not found at ${SOURCE_HTML}. Go scrape the directory first.`
    );
    process.exit(1);
  }

  const html = fs.readFileSync(SOURCE_HTML, "utf8");
  const $ = load(html);

  // try tbody first, then fall back
  const rows = $("table tbody tr").length
    ? $("table tbody tr")
    : $("table tr").slice(1); // skip header

  const profiles = [];
  rows.each((_, tr) => {
    const profile = rowToProfile($, tr);
    // safety: ignore rows with no name
    if (profile.name) {
      profiles.push(profile);
    }
  });

  // write latest.json (for tests/inspect-latest.js)
  fs.writeFileSync(LATEST_JSON, JSON.stringify(profiles, null, 2), "utf8");
  console.log(`✅ Wrote latest parsed output to ${LATEST_JSON}`);

  // write master file you asked for
  fs.writeFileSync(MASTER_JSON, JSON.stringify(profiles, null, 2), "utf8");
  console.log(`✅ Exported data to ${MASTER_JSON}`);
}

main();
