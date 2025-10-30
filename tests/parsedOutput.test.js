const fs = require("fs");
const path = require("path");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

const PROCESSED_DIR = path.join(__dirname, "..", "data", "processed");
const SCHEMA_PATH = path.join(__dirname, "..", "schemas", "profile.schema.json");

function newestProfilesFile() {
  if (!fs.existsSync(PROCESSED_DIR)) return null;
  const files = fs.readdirSync(PROCESSED_DIR)
    .filter((f) => /^profiles-\d{8}-\d{6}\.json$/.test(f))
    .sort();
  return files.length ? path.join(PROCESSED_DIR, files[files.length - 1]) : null;
}

test("latest parsed output matches schema row-by-row", () => {
  const file = newestProfilesFile();
  expect(file).toBeTruthy();

  const arr = JSON.parse(fs.readFileSync(file, "utf-8"));
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);
  const schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, "utf-8"));
  const validate = ajv.compile(schema);

  for (const [i, row] of arr.entries()) {
    const ok = validate(row);
    if (!ok) {
      console.error(`Row ${i} failed:`, row, validate.errors);
    }
    expect(ok).toBe(true);
  }
});
