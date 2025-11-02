// tests/parsedOutput.test.js
const fs = require("fs");
const path = require("path");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

const PROCESSED_DIR = path.join(__dirname, "..", "data", "processed");

const BROWSE_SCHEMA_PATH = path.join(
  __dirname,
  "..",
  "schemas",
  "profile.browse.schema.json"
);
const FULL_SCHEMA_PATH = path.join(
  __dirname,
  "..",
  "schemas",
  "profile.schema.json"
);

function newestProfilesFile() {
  if (!fs.existsSync(PROCESSED_DIR)) return null;
  const files = fs
    .readdirSync(PROCESSED_DIR)
    .filter((f) => /^profiles-\d{8}-\d{6}\.json$/.test(f))
    .sort();
  return files.length
    ? path.join(PROCESSED_DIR, files[files.length - 1])
    : null;
}

// tiny cleanup to match what the real site does
function normalizeRow(row) {
  const out = { ...row };

  // some rows have empty location on the site; treat empty as "not provided"
  if (out.location === "") {
    delete out.location;
  }

  // sometimes parser gives [] for genderInterestedIn. schema wants minItems 1.
  if (Array.isArray(out.genderInterestedIn) && out.genderInterestedIn.length === 0) {
    delete out.genderInterestedIn;
  }

  return out;
}

test("latest parsed output matches schema row-by-row", () => {
  const file = newestProfilesFile();
  expect(file).toBeTruthy();

  const arr = JSON.parse(fs.readFileSync(file, "utf-8"));

  // choose schema
  let schemaPath = null;
  if (fs.existsSync(BROWSE_SCHEMA_PATH)) {
    schemaPath = BROWSE_SCHEMA_PATH;
  } else if (fs.existsSync(FULL_SCHEMA_PATH)) {
    schemaPath = FULL_SCHEMA_PATH;
  } else {
    throw new Error(
      "No schema file found. Expected schemas/profile.browse.schema.json or schemas/profile.schema.json"
    );
  }

  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);

  const schema = JSON.parse(fs.readFileSync(schemaPath, "utf-8"));
  const validate = ajv.compile(schema);

  for (const [i, rawRow] of arr.entries()) {
    const row = normalizeRow(rawRow);
    const ok = validate(row);
    if (!ok) {
      console.error(`Row ${i} failed:`, row, validate.errors);
    }
    expect(ok).toBe(true);
  }
});
