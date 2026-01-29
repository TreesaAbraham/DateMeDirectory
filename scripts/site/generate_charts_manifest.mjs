// scripts/site/generate_charts_manifest.mjs
// Scans site/assets/charts/{d3,seaborn,matplotlib} for .svg/.png and writes site/data/charts_manifest.json

import { promises as fs } from "node:fs";
import path from "node:path";

const REPO_ROOT = process.cwd();
const SITE_DIR = path.join(REPO_ROOT, "site");
const CHARTS_DIR = path.join(SITE_DIR, "assets", "charts");
const OUT_PATH = path.join(SITE_DIR, "data", "charts_manifest.json");

const RENDERERS = ["d3", "seaborn", "matplotlib"];
const ALLOWED_EXT = new Set([".svg", ".png"]);

function titleFromFilename(filename) {
  const base = filename.replace(path.extname(filename), "");
  return base
    .replace(/^chart[_-]?\d+[_-]?/i, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^./, (c) => c.toUpperCase()) || base;
}

async function listFiles(dir) {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((e) => e.isFile())
      .map((e) => e.name)
      .filter((name) => ALLOWED_EXT.has(path.extname(name).toLowerCase()))
      .sort((a, b) => a.localeCompare(b, "en"));
  } catch (err) {
    if (err && err.code === "ENOENT") return [];
    throw err;
  }
}

async function main() {
  await fs.mkdir(path.dirname(OUT_PATH), { recursive: true });

  const charts = [];

  for (const renderer of RENDERERS) {
    const rendererDir = path.join(CHARTS_DIR, renderer);
    const files = await listFiles(rendererDir);

    for (const file of files) {
      const url = `assets/charts/${renderer}/${file}`;
      charts.push({
        id: `${renderer}/${file}`,
        title: titleFromFilename(file),
        renderer, // "d3" | "seaborn" | "matplotlib"
        format: path.extname(file).slice(1).toLowerCase(), // "svg" | "png"
        url,
        caption: "", // fill later (optional)
        writeup: "" // e.g., "writeups/chart_09.md" (optional)
      });
    }
  }

  const manifest = {
    generated_at: new Date().toISOString(),
    count: charts.length,
    charts
  };

  await fs.writeFile(OUT_PATH, JSON.stringify(manifest, null, 2) + "\n", "utf8");
  console.log(`Wrote ${charts.length} charts to ${path.relative(REPO_ROOT, OUT_PATH)}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
