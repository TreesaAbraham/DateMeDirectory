// site/graph.js
// Renders a graph page based on:
//   <main id="graph-page" data-graph="01" data-renderer="d3"></main>
// Uses canonical manifest: /data/charts_manifest.json (graph-grouped)

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function rendererLabel(renderer) {
  if (!renderer) return "Unknown";
  const r = renderer.toLowerCase();
  if (r === "d3") return "D3";
  if (r === "seaborn") return "Seaborn";
  if (r === "matplotlib") return "Matplotlib";
  return renderer;
}

// Make URLs safe to use from nested pages like /graphs/01/d3.html
function normalizeSiteUrl(url) {
  const u = String(url ?? "").trim();
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return u;
  // manifest uses "assets/..." which needs to become "/assets/..." for nested pages
  return `/${u}`;
}

function getQueryParam(name) {
  try {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
  } catch {
    return null;
  }
}

// Try absolute first (best for nested routes), then fall back to relative
async function loadManifest() {
  const candidates = [
    "/data/charts_manifest.json",
    "../../data/charts_manifest.json",
    "../data/charts_manifest.json",
    "./data/charts_manifest.json"
  ];

  let lastErr = null;

  for (const path of candidates) {
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status} for ${path}`);
      return res.json();
    } catch (err) {
      lastErr = err;
    }
  }

  throw lastErr || new Error("Failed to load manifest");
}

function findGraph(manifest, graphId) {
  const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];
  return graphs.find((g) => String(g?.graph_id) === String(graphId));
}

function pickChartEntry(graph, renderer, preferredId) {
  const entries = graph?.renderers?.[renderer];
  const list = Array.isArray(entries) ? entries : [];

  if (!list.length) return null;

  if (preferredId) {
    const match = list.find((e) => String(e?.id) === String(preferredId));
    if (match) return match;
  }

  return list[0]; // default: first chart for that renderer
}

function buildPageHtml({ graphId, renderer, graphTitle, graph, entry }) {
  const badge = rendererLabel(renderer);
  const title = graphTitle || (graphId ? `Graph ${graphId}` : "Graph");
  const chartUrl = normalizeSiteUrl(entry?.url || "");
  const caption = String(entry?.caption || "").trim();
  const writeupPath = normalizeSiteUrl(entry?.writeup || "");

  const question = String(graph?.question || "").trim();
  const method = String(graph?.method || "").trim();
  const notes = String(graph?.notes || "").trim();
  const findings = Array.isArray(graph?.key_findings) ? graph.key_findings : [];

  const findingsHtml = findings.length
    ? `<ul>${findings.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>`
    : `<p class="muted">No key findings yet.</p>`;

  const chartBlock = chartUrl
    ? `
      <figure class="chart-figure">
        <div class="chart-media" aria-label="${escapeHtml(title)} chart">
          <img class="chart-img" src="${escapeHtml(chartUrl)}" alt="${escapeHtml(title)} (${escapeHtml(badge)})" />
        </div>
        <figcaption>
          ${
            caption
              ? `<strong>Caption:</strong> ${escapeHtml(caption)}`
              : `<span class="muted">No caption yet.</span>`
          }
        </figcaption>
      </figure>
    `
    : `
      <article class="card">
        <h3 class="card-title">Chart file not linked</h3>
        <p class="card-body muted">
          Add a <code>url</code> for this renderer in <code>data/charts_manifest.json</code>.
        </p>
      </article>
    `;

  const writeupBlock = writeupPath
    ? `
      <div class="writeup">
        <h3 class="writeup-title">Writeup</h3>
        <p class="muted">
          This page links to a writeup file. If it doesn’t load, check the path in the manifest.
        </p>
        <div id="graph-writeup" class="muted">Loading writeup…</div>
      </div>
    `
    : `
      <div class="writeup">
        <h3 class="writeup-title">Writeup</h3>
        <p class="muted">No writeup linked yet.</p>
      </div>
    `;

  return `
    <section class="section">
      <div class="container">
        <div class="section-header prose">
          <h2 style="margin:0;">${escapeHtml(title)}</h2>
          <p class="muted" style="margin-top:0.35rem;">
            Renderer: <span class="badge" title="Rendered with ${escapeHtml(badge)}">${escapeHtml(badge)}</span>
            <span class="muted"> · </span>
            <a href="/#charts">Back to charts</a>
          </p>
        </div>

        <div class="grid">
          <article class="card chart-card">
            <div class="chart-card-header">
              <h3 class="card-title">${escapeHtml(title)}</h3>
              <span class="badge" title="Rendered with ${escapeHtml(badge)}">${escapeHtml(badge)}</span>
            </div>
            ${chartBlock}
          </article>

          <article class="card">
            <h3 class="card-title">Context</h3>
            <div class="prose">
              ${question ? `<h4>Question</h4><p>${escapeHtml(question)}</p>` : ""}
              <h4>Method</h4>
              ${method ? `<p>${escapeHtml(method)}</p>` : `<p class="muted">No method yet.</p>`}
              <h4>Key findings</h4>
              ${findingsHtml}
              ${notes ? `<h4>Notes</h4><p>${escapeHtml(notes)}</p>` : ""}
            </div>
          </article>
        </div>

        <div style="margin-top:1rem;">
          ${writeupBlock}
        </div>
      </div>
    </section>
  `;
}

async function loadWriteupInto(el, writeupUrl) {
  if (!el || !writeupUrl) return;
  try {
    const res = await fetch(writeupUrl, { cache: "no-store" });
    if (!res.ok) throw new Error(`Writeup not found (${res.status})`);
    const text = await res.text();
    // Plain text display for now. (We can add markdown rendering later.)
    el.innerHTML = `<pre style="white-space:pre-wrap;margin:0;">${escapeHtml(text)}</pre>`;
  } catch (err) {
    el.innerHTML = `<p class="muted">${escapeHtml(err.message || String(err))}</p>`;
  }
}

async function main() {
  const mount = document.getElementById("graph-page");
  if (!mount) return;

  const graphId = mount.getAttribute("data-graph") || "";
  const renderer = (mount.getAttribute("data-renderer") || "").toLowerCase();

  if (!graphId || !renderer) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Missing page metadata</h2>
        <p class="muted">
          This page needs <code>data-graph</code> and <code>data-renderer</code> on
          <code>&lt;main id="graph-page"&gt;</code>.
        </p>
      </div>
    `;
    return;
  }

  const preferredChartId = getQueryParam("chart") || mount.getAttribute("data-chart-id") || "";

  try {
    const manifest = await loadManifest();
    const graph = findGraph(manifest, graphId);

    if (!graph) {
      mount.innerHTML = `
        <div class="container prose">
          <h2>Graph not found</h2>
          <p class="muted">No graph with id <code>${escapeHtml(graphId)}</code> in <code>data/charts_manifest.json</code>.</p>
          <p><a href="/#charts">Back to charts</a></p>
        </div>
      `;
      return;
    }

    const graphTitle = String(graph?.title || "").trim() || `Graph ${graphId}`;
    const entry = pickChartEntry(graph, renderer, preferredChartId);

    if (!entry) {
      mount.innerHTML = `
        <div class="container prose">
          <h2>${escapeHtml(graphTitle)}</h2>
          <p class="muted">
            No entries found for renderer <code>${escapeHtml(renderer)}</code>.
            Add a renderer entry under <code>graphs[].renderers.${escapeHtml(renderer)}</code>.
          </p>
          <p><a href="/#charts">Back to charts</a></p>
        </div>
      `;
      return;
    }

    mount.innerHTML = buildPageHtml({
      graphId,
      renderer,
      graphTitle,
      graph,
      entry
    });

    // If there is a writeup URL, attempt to load it
    const writeupUrl = normalizeSiteUrl(entry?.writeup || "");
    const writeupEl = document.getElementById("graph-writeup");
    if (writeupUrl && writeupEl) {
      await loadWriteupInto(writeupEl, writeupUrl);
    }
  } catch (err) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Couldn’t load graph</h2>
        <p class="muted">${escapeHtml(err.message || String(err))}</p>
        <p><a href="/#charts">Back to charts</a></p>
      </div>
    `;
    console.error(err);
  }
}

main();
