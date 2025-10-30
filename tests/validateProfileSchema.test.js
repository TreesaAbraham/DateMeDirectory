const fs = require("fs");
const path = require("path");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

const schemaPath = path.join(__dirname, "..", "schemas", "profile.schema.json");
const sampleValidPath = path.join(__dirname, "..", "data", "exampleProfile.json");
const sampleInvalidPath = path.join(__dirname, "..", "data", "exampleProfile.invalid.json");

const loadJson = (p) => JSON.parse(fs.readFileSync(p, "utf-8"));

describe("Minimal extraction schema", () => {
  test("files exist", () => {
    expect(fs.existsSync(schemaPath)).toBe(true);
    expect(fs.existsSync(sampleValidPath)).toBe(true);
  });

  test("valid example passes", () => {
    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);

    const validate = ajv.compile(loadJson(schemaPath));
    const valid = validate(loadJson(sampleValidPath));

    if (!valid) console.error("Validation errors (expected pass):", validate.errors);
    expect(valid).toBe(true);
  });

  test("invalid example fails (smoke test)", () => {
    // Only run if invalid file exists
    if (!fs.existsSync(sampleInvalidPath)) return;

    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);

    const validate = ajv.compile(loadJson(schemaPath));
    const valid = validate(loadJson(sampleInvalidPath));

    // Print errors so failures are informative
    if (valid) console.error("Unexpectedly valid:", loadJson(sampleInvalidPath));
    else console.error("Expected errors:", validate.errors);

    expect(valid).toBe(false);
  });
});
