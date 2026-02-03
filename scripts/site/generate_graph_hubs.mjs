// scripts/site/generate_graph_hubs.mjs
// Generates hub pages at: site/graphs/<id>/index.html
//
// Each hub page:
// - mounts <main id="graph-hub" data-graph="01"></main>
// - loads /graph_hub.js which reads /data/charts_manifest.json
// - shows Context + renderer cards + loads writeup txt
//
// Run from repo root:
//   node scripts/site/generate_graph_hubs.mjs

import { promises as fs } from "node:fs";
import path from "node:path";

const REPO_ROOT = process.cwd();
const SITE_DIR = path.join(REPO_ROOT, "site");
const MANIFEST_PATH = path.join(SITE_DIR, "data", "charts_manifest.json");
const GRAPHS_DIR = path.join(SITE_DIR, "graphs");

function pad2(n) {
  return String(n).padStart(2, "0");
}

function normalizeGraphId(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return "";
  const num = Number(s);
  if (Number.isFinite(num)) return pad2(num);
  if (/^\d{2}$/.test(s)) return s;
  return s;
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function hubHtml({ graphId, title }) {
  const safeTitle = escapeHtml(title || `Graph ${graphId}`);
  const safeId = escapeHtml(graphId);

  // Rooted asset paths so nested routes work on Vercel (/graphs/01/)
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${safeTitle} · Date Me Directory</title>
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a class="site-title" href="/">Date Me Directory</a>
    </div>
  </header>

  <main id="graph-hub" data-graph="${safeId}"></main>

  <footer class="site-footer">
    <div class="container muted">
      Generated hub page for Graph ${safeId}.
    </div>
  </footer>

  <script src="/graph_hub.js" defer></script>
</body>
</html>
`;
}

async function readManifest() {
  const text = await fs.readFile(MANIFEST_PATH, "utf8");
  const manifest = JSON.parse(text);
  const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];
  return { manifest, graphs };
}

async function ensureDir(p) {
  await fs.mkdir(p, { recursive: true });
}

async function writeFile(p, content) {
  await fs.writeFile(p, content, "utf8");
}

async function main() {
  const { graphs } = await readManifest();
  await ensureDir(GRAPHS_DIR);

  if (!graphs.length) {
    console.log("No graphs found in manifest. Nothing to generate.");
    return;
  }

  // Sort by numeric id if possible
  const sorted = [...graphs].sort((a, b) => {
    const ai = parseInt(String(a?.graph_id ?? ""), 10);
    const bi = parseInt(String(b?.graph_id ?? ""), 10);
    return (Number.isNaN(ai) ? 999 : ai) - (Number.isNaN(bi) ? 999 : bi);
  });

  let count = 0;

  for (const g of sorted) {
    const graphId = normalizeGraphId(g?.graph_id);
    if (!graphId) continue;

    const title = String(g?.title || `Graph ${graphId}`).trim() || `Graph ${graphId}`;
    const outDir = path.join(GRAPHS_DIR, graphId);
    const outPath = path.join(outDir, "index.html");

    await ensureDir(outDir);
    await writeFile(outPath, hubHtml({ graphId, title }));

    count += 1;
  }

  console.log(`Generated ${count} hub pages in ${path.relative(REPO_ROOT, GRAPHS_DIR)}/`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
// site/graph_hub.js