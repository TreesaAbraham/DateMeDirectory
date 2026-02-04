// site/graph.js
// Renderer page for ONE graph + ONE renderer.
// Used by pages like: /graphs/01/matplotlib.html, /graphs/01/seaborn.html, /graphs/01/d3.html
//
// Expected HTML:
// <main id="graph-page" data-graph="01" data-renderer="matplotlib"></main>
//
// Behavior:
// - shows only the selected chart (via ?chart=<id>) or the first entry
// - NO context, NO writeup, NO renderer pill/capsule UI

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

function getSelectedEntry(entries) {
  const params = new URLSearchParams(window.location.search);
  const chartId = (params.get("chart") || "").trim();
  if (!chartId) return entries[0] || null;
  return entries.find((e) => String(e?.id || "").trim() === chartId) || entries[0] || null;
}

function isImageUrl(url) {
  const u = String(url || "").toLowerCase();
  return u.endsWith(".png") || u.endsWith(".jpg") || u.endsWith(".jpeg") || u.endsWith(".webp") || u.endsWith(".gif") || u.endsWith(".svg");
}

function chartEmbedHtml(url, title) {
  const safeUrl = escapeHtml(url);
  const safeTitle = escapeHtml(title);

  // If it's an image, show <img>. If it's an html (common for D3), use <iframe>.
  if (isImageUrl(url)) {
    return `<img src="${safeUrl}" alt="${safeTitle}" loading="lazy" style="max-width:100%;height:auto;" />`;
  }

  return `
    <iframe
      src="${safeUrl}"
      title="${safeTitle}"
      loading="lazy"
      style="width:100%;height:70vh;border:0;border-radius:12px;background:transparent;"
    ></iframe>
  `;
}

async function main() {
  const mount = document.getElementById("graph-page");
  if (!mount) return;

  const graphId = (mount.getAttribute("data-graph") || "").trim();
  const renderer = (mount.getAttribute("data-renderer") || "").trim();

  if (!graphId || !renderer) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Missing page attributes</h2>
        <p class="muted">
          Add <code>data-graph="01"</code> and <code>data-renderer="matplotlib"</code> to
          <code>&lt;main id="graph-page"&gt;</code>.
        </p>
      </div>
    `;
    return;
  }

  try {
    const manifest = await loadManifest();
    const graph = findGraph(manifest, graphId);

    if (!graph) {
      mount.innerHTML = `
        <div class="container prose">
          <h2>Graph not found</h2>
          <p class="muted">No graph with id <code>${escapeHtml(graphId)}</code> in the manifest.</p>
        </div>
      `;
      return;
    }

    const entries = getRendererEntries(graph, renderer);
    if (!entries.length) {
      mount.innerHTML = `
        <div class="container prose">
          <h2>No outputs found</h2>
          <p class="muted">No entries for <code>${escapeHtml(renderer)}</code> on graph <code>${escapeHtml(graphId)}</code>.</p>
          <p><a class="small-link" href="/index.html">Back to charts</a></p>
        </div>
      `;
      return;
    }

    const entry = getSelectedEntry(entries);
    const url = toRootedUrl(entry?.url || "");
    const graphTitle = String(graph?.title || "").trim() || `Graph ${graphId}`;

    const chartTitle = entry?.title
      ? String(entry.title).trim()
      : `${graphTitle}`;

    mount.innerHTML = `
      <section class="section">
        <div class="container prose">
          <h1 style="margin-bottom:0.25rem;">${escapeHtml(graphTitle)}</h1>
          <p style="margin-top:0;">
            <a class="small-link" href="/index.html">Back to charts</a>
          </p>
        </div>

        <div class="container" style="margin-top:1rem;">
          <article class="card">
            <div class="chart-media" aria-label="${escapeHtml(chartTitle)}">
              ${url ? chartEmbedHtml(url, chartTitle) : `<p class="muted">Missing chart URL in manifest.</p>`}
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
        <p><a class="small-link" href="/index.html">Back to charts</a></p>
      </div>
    `;
    console.error(err);
  }
}

main();
