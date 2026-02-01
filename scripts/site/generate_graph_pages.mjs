// scripts/site/generate_graph_pages.mjs
// Run: node scripts/site/generate_graph_pages.mjs
// Generates ONLY: site/graphs/{03,04,05,06,08,09}/{matplotlib,seaborn,d3}.html

import fs from "fs";
import path from "path";

const SITE_DIR = path.resolve("site");
const MANIFEST_PATH = path.join(SITE_DIR, "data", "charts_manifest.json");
const OUT_DIR = path.join(SITE_DIR, "graphs");

// Change this list whenever you want different graph folders/pages generated.
const TARGET_GRAPH_IDS = ["03", "04", "05", "06", "08", "09"];

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function normalizeGraphId(id) {
  // Accept 3 or "3", return "03"
  const n = String(id).trim();
  const num = Number(n);
  if (!Number.isFinite(num)) return n;
  return String(num).padStart(2, "0");
}

function htmlPage({ graphId, renderer }) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Graph ${graphId} (${renderer})</title>
    <link rel="stylesheet" href="../../styles.css" />
  </head>
  <body>
    <main id="graph-page" data-graph="${graphId}" data-renderer="${renderer}"></main>
    <script src="../../graph.js" defer></script>
  </body>
</html>
`;
}

function readManifestGraphs() {
  if (!fs.existsSync(MANIFEST_PATH)) return [];
  try {
    const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf8"));
    return Array.isArray(manifest.graphs) ? manifest.graphs : [];
  } catch (e) {
    console.warn(`Warning: could not parse manifest at ${MANIFEST_PATH}`);
    return [];
  }
}

function main() {
  const manifestGraphs = readManifestGraphs();
  const manifestIdSet = new Set(manifestGraphs.map(g => normalizeGraphId(g.graph_id)));

  ensureDir(OUT_DIR);

  const targets = TARGET_GRAPH_IDS.map(normalizeGraphId);

  for (const graphId of targets) {
    const graphDir = path.join(OUT_DIR, graphId);
    ensureDir(graphDir);

    // Generate the three renderer pages (even if the graph isn't in the manifest yet).
    for (const renderer of ["matplotlib", "seaborn", "d3"]) {
      const outPath = path.join(graphDir, `${renderer}.html`);
      fs.writeFileSync(outPath, htmlPage({ graphId, renderer }), "utf8");
    }

    if (!manifestIdSet.has(graphId)) {
      console.warn(
        `Note: Graph ${graphId} pages generated, but graph_id "${graphId}" not found in charts_manifest.json`
      );
    }
  }

  console.log(`Generated graph pages for: ${targets.join(", ")}`);
  console.log(`Output folder: ${OUT_DIR}`);
}

main();
