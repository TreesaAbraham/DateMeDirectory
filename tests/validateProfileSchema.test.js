const fs = require("fs");
const path = require("path");
const Ajv = require("ajv");
const addFormats = require("ajv-formats");

const fullSchemaPath = path.join(__dirname, "..", "schemas", "profile.schema.json");
const browseSchemaPath = path.join(__dirname, "..", "schemas", "profile.browse.schema.json");

const sampleValidPath = path.join(__dirname, "..", "data", "exampleProfile.json");
const sampleInvalidPath = path.join(__dirname, "..", "data", "exampleProfile.invalid.json");

const loadJson = (p) => JSON.parse(fs.readFileSync(p, "utf-8"));

describe("Minimal extraction schema", () => {
  test("at least one schema exists and example exists", () => {
    const hasFull = fs.existsSync(fullSchemaPath);
    const hasBrowse = fs.existsSync(browseSchemaPath);

    // at least one schema must be there
    expect(hasFull || hasBrowse).toBe(true);

    // example profile is part of the repo
    expect(fs.existsSync(sampleValidPath)).toBe(true);
  });

  test("valid example passes on whichever schema we have", () => {
    const hasFull = fs.existsSync(fullSchemaPath);
    const hasBrowse = fs.existsSync(browseSchemaPath);

    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);

    const sample = loadJson(sampleValidPath);

    if (hasFull) {
      const validateFull = ajv.compile(loadJson(fullSchemaPath));
      const ok = validateFull(sample);
      if (!ok) {
        console.error("Validation errors against full schema:", validateFull.errors);
      }
      expect(ok).toBe(true);
    } else if (hasBrowse) {
      const validateBrowse = ajv.compile(loadJson(browseSchemaPath));
      const ok = validateBrowse(sample);
      if (!ok) {
        console.error("Validation errors against browse schema:", validateBrowse.errors);
      }
      expect(ok).toBe(true);
    } else {
      throw new Error("No schema file found to validate against.");
    }
  });

  test("invalid example fails on strict schema if present", () => {
    if (!fs.existsSync(sampleInvalidPath)) return;
    if (!fs.existsSync(fullSchemaPath)) return;

    const ajv = new Ajv({ allErrors: true, strict: false });
    addFormats(ajv);

    const validate = ajv.compile(loadJson(fullSchemaPath));
    const valid = validate(loadJson(sampleInvalidPath));

    if (valid) {
      console.error("Unexpectedly valid:", loadJson(sampleInvalidPath));
    } else {
      console.error("Expected errors:", validate.errors);
    }

    expect(valid).toBe(false);
  });
});
