// scripts/site/generate_graph_hubs.mjs
// Generates static hub pages at: site/graphs/<graphId>/index.html
// - NO "generated hub page..." footer
// - <title> in browser tab uses the hub title from the manifest

import fs from "node:fs";
import path from "node:path";

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return JSON.parse(raw);
}

/**
 * Best-effort: supports a few reasonable manifest shapes.
 * We try to extract per-graph titles from:
 * - manifest.graphs[]: { id, title }
 * - manifest.charts[]: { graph_id, graph_title }
 * - manifest[graphId].title (object keyed by graph id)
 */
function extractGraphTitleMap(manifest) {
  const map = new Map();

  // Case A: { graphs: [ { id, title }, ... ] }
  if (manifest && Array.isArray(manifest.graphs)) {
    for (const g of manifest.graphs) {
      const id = g?.id ?? g?.graph_id ?? g?.graphId;
      const title = g?.title ?? g?.graph_title ?? g?.graphTitle;
      if (id != null && title) map.set(String(id).padStart(2, "0"), String(title));
    }
  }

  // Case B: { charts: [ { graph_id, graph_title }, ... ] }
  if (manifest && Array.isArray(manifest.charts)) {
    for (const c of manifest.charts) {
      const id = c?.graph_id ?? c?.graphId ?? c?.id;
      const title = c?.graph_title ?? c?.graphTitle ?? c?.title;
      if (id != null && title) map.set(String(id).padStart(2, "0"), String(title));
    }
  }

  // Case C: object keyed by graph id, e.g. { "01": { title: "..." }, ... }
  if (manifest && typeof manifest === "object" && !Array.isArray(manifest)) {
    for (const [key, val] of Object.entries(manifest)) {
      if (!/^\d+$/.test(key)) continue;
      const id = String(key).padStart(2, "0");
      const title = val?.title ?? val?.graph_title ?? val?.graphTitle;
      if (title) map.set(id, String(title));
    }
  }

  return map;
}

function hubHtml({ graphId, title }) {
  const rawTitle = String(title || "").trim() || `Graph ${graphId}`;
  const safeId = escapeHtml(graphId);

  // What shows in the browser tab:
  const tabTitle = escapeHtml(`${rawTitle} · Date Me Directory`);


  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${tabTitle}</title>
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <header class="site-header">
    <div class="container">
      <a class="site-title" href="/">Date Me Directory</a>
    </div>
  </header>

  <main id="graph-hub" data-graph="${safeId}"></main>

  <script src="/graph_hub.js" defer></script>
</body>
</html>
`;
}

function main() {
  const repoRoot = process.cwd();
  const siteDir = path.join(repoRoot, "site");
  const dataDir = path.join(siteDir, "data");

  // You’ve been using this as canonical:
  const manifestPath = path.join(dataDir, "charts_manifest.json");
  if (!fs.existsSync(manifestPath)) {
    console.error(`Missing manifest: ${manifestPath}`);
    process.exit(1);
  }

  const manifest = readJson(manifestPath);
  const titleMap = extractGraphTitleMap(manifest);

  if (titleMap.size === 0) {
    console.error(
      "Could not extract any graph titles from charts_manifest.json. " +
        "Make sure it includes graph titles (e.g., graphs[] with {id,title} or charts[] with {graph_id, graph_title})."
    );
    process.exit(1);
  }

  const graphsOutDir = path.join(siteDir, "graphs");
  ensureDir(graphsOutDir);

  const graphIds = [...titleMap.keys()].sort((a, b) => Number(a) - Number(b));

  for (const graphId of graphIds) {
    const outDir = path.join(graphsOutDir, graphId);
    ensureDir(outDir);

    const outPath = path.join(outDir, "index.html");
    const html = hubHtml({ graphId, title: titleMap.get(graphId) });

    fs.writeFileSync(outPath, html, "utf8");
  }

  console.log(`Generated ${graphIds.length} hub page(s) in site/graphs/`);
}

main();
