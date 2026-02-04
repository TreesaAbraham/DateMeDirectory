// site/graph.js
// Renderer detail page script.
// Expected page path: /graphs/<graphId>/<renderer>.html
// Optional query: ?chart=<entryId>
// Renders: Header + ONE chart only (no context, no writeup)

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&quot;")
    .replaceAll("'", "&#039;");
}

function rendererLabel(renderer) {
  const r = String(renderer || "").toLowerCase();
  if (r === "d3") return "D3";
  if (r === "seaborn") return "Seaborn";
  if (r === "matplotlib") return "Matplotlib";
  return renderer || "Unknown";
}

function toRootedUrl(url) {
  const u = String(url ?? "").trim();
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return u;
  return `/${u}`;
}

async function loadManifest() {
  const res = await fetch("/data/charts_manifest.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load manifest: HTTP ${res.status}`);
  return res.json();
}

function findGraph(manifest, graphId) {
  const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];
  return graphs.find((g) => String(g?.graph_id) === String(graphId));
}

function getRendererEntries(graph, renderer) {
  const list = graph?.renderers?.[renderer];
  return Array.isArray(list) ? list : [];
}

function pickEntry(entries, entryId) {
  if (!entries.length) return null;
  if (!entryId) return entries[0];
  const match = entries.find((e) => String(e?.id) === String(entryId));
  return match || entries[0];
}

function parseRoute() {
  // /graphs/04/d3.html  -> ["graphs","04","d3.html"]
  const parts = window.location.pathname.split("/").filter(Boolean);
  const graphsIdx = parts.indexOf("graphs");
  const graphId = graphsIdx >= 0 ? parts[graphsIdx + 1] : "";
  const rendererFile = graphsIdx >= 0 ? parts[graphsIdx + 2] : "";
  const renderer = rendererFile ? rendererFile.replace(/\.html$/i, "") : "";
  return { graphId, renderer };
}

function getChartParam() {
  const params = new URLSearchParams(window.location.search);
  return params.get("chart") || "";
}

function renderChartHtml(url, title) {
  const u = toRootedUrl(url);

  // If it's an SVG file, use <object> so it scales nicely.
  if (u.toLowerCase().endsWith(".svg")) {
    return `
      <object data="${escapeHtml(u)}" type="image/svg+xml" class="chart-object" aria-label="${escapeHtml(title)}"></object>
    `;
  }

  // Default: image
  return `<img src="${escapeHtml(u)}" alt="${escapeHtml(title)}" loading="lazy" />`;
}

async function main() {
  // Your detail pages probably mount into <main id="graph"></main>.
  // If your HTML uses a different id, change it here.
  const mount = document.getElementById("graph") || document.querySelector("main");
  if (!mount) return;

  const { graphId, renderer } = parseRoute();
  const entryId = getChartParam();

  if (!graphId || !renderer) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Bad route</h2>
        <p class="muted">Expected URL like <code>/graphs/04/d3.html</code>.</p>
      </div>
    `;
    return;
  }

  try {
    const manifest = await loadManifest();
    const graph = findGraph(manifest, graphId);
    if (!graph) throw new Error(`Graph ${graphId} not found in manifest.`);

    const entries = getRendererEntries(graph, renderer);
    if (!entries.length) throw new Error(`No ${rendererLabel(renderer)} outputs linked for Graph ${graphId}.`);

    const entry = pickEntry(entries, entryId);
    if (!entry?.url) throw new Error(`Missing url for this chart entry.`);

    const pageTitle = String(graph?.title || "").trim() || `Graph ${graphId}`;
    const rLabel = rendererLabel(renderer);

    // Back goes to the graph hub, not the homepage.
    const backHref = `/graphs/${encodeURIComponent(graphId)}/`;

    mount.innerHTML = `
      <section class="section">
        <div class="container">
          <div class="prose" style="margin-bottom:1rem;">
            <h1 style="margin-bottom:0.35rem;">${escapeHtml(pageTitle)}</h1>

            <div style="display:flex; gap:0.75rem; align-items:baseline; flex-wrap:wrap;">
              <div class="muted">Renderer: <span class="renderer-text">${escapeHtml(rLabel)}</span></div>
              <span class="muted">•</span>
              <a class="small-link" href="${escapeHtml(backHref)}">Back to charts</a>
            </div>
          </div>

          <article class="card chart-card">
            <div class="chart-media" aria-label="${escapeHtml(pageTitle)} ${escapeHtml(rLabel)} chart">
              ${renderChartHtml(entry.url, `${pageTitle} (${rLabel})`)}
            </div>
          </article>
        </div>
      </section>
    `;
  } catch (err) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Couldn’t load chart</h2>
        <p class="muted">${escapeHtml(err.message || String(err))}</p>
      </div>
    `;
    console.error(err);
  }
}

main();
