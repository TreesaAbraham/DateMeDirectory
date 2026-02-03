// site/graph_hub.js
// Graph hub page renderer.
// Reads: <main id="graph-hub" data-graph="01"></main>
// Loads: /data/charts_manifest.json (graph-grouped)
// Renders: Question/Method/Key Findings/Notes + 3 renderer cards (Matplotlib/Seaborn/D3)

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function rendererLabel(renderer) {
  const r = String(renderer || "").toLowerCase();
  if (r === "d3") return "D3";
  if (r === "seaborn") return "Seaborn";
  if (r === "matplotlib") return "Matplotlib";
  return renderer || "Unknown";
}

// From nested routes (/graphs/01/), always use rooted URLs
function toRootedUrl(url) {
  const u = String(url ?? "").trim();
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return u;
  return `/${u}`; // "assets/..." -> "/assets/..."
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

// Pick first entry for each renderer by default.
function pickFirstEntry(graph, renderer) {
  const list = graph?.renderers?.[renderer];
  if (!Array.isArray(list) || list.length === 0) return null;
  return list[0];
}

function rendererCard({ graphId, renderer, entry }) {
  const label = rendererLabel(renderer);
  const url = toRootedUrl(entry?.url || "");

  // /graphs/<id>/matplotlib.html, seaborn.html, d3.html
  const detailHref = `/graphs/${encodeURIComponent(graphId)}/${encodeURIComponent(renderer)}.html`;

  return `
    <article class="card chart-card">
      <div class="chart-card-header">
        <h3 class="card-title">${escapeHtml(label)}</h3>
        <span class="badge" title="Rendered with ${escapeHtml(label)}">${escapeHtml(label)}</span>
      </div>

      ${
        url
          ? `
        <figure class="chart-figure">
          <div class="chart-media" aria-label="${escapeHtml(label)} chart">
            <img class="chart-img" src="${escapeHtml(url)}" alt="${escapeHtml(label)} chart for Graph ${escapeHtml(graphId)}" loading="lazy" />
          </div>
        </figure>
      `
          : `
        <p class="muted">No URL linked for ${escapeHtml(label)} in the manifest.</p>
      `
      }

      <div class="chart-links">
        <a class="small-link" href="${detailHref}">Open renderer page</a>
      </div>
    </article>
  `;
}

async function loadWriteup(writeupPath) {
  const url = toRootedUrl(writeupPath);
  if (!url) return null;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Writeup not found (${res.status})`);
  return res.text();
}

function contextBlock(graph) {
  const question = String(graph?.question || "").trim();
  const method = String(graph?.method || "").trim();
  const notes = String(graph?.notes || "").trim();
  const findings = Array.isArray(graph?.key_findings) ? graph.key_findings : [];

  return `
    <article class="card">
      <h3 class="card-title">Context</h3>
      <div class="prose">
        ${question ? `<h4>Question</h4><p>${escapeHtml(question)}</p>` : `<p class="muted">No question yet.</p>`}

        <h4>Method</h4>
        ${method ? `<p>${escapeHtml(method)}</p>` : `<p class="muted">No method yet.</p>`}

        <h4>Key findings</h4>
        ${
          findings.length
            ? `<ul>${findings.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>`
            : `<p class="muted">No key findings yet.</p>`
        }

        ${notes ? `<h4>Notes</h4><p>${escapeHtml(notes)}</p>` : ""}
      </div>
    </article>
  `;
}

async function main() {
  const mount = document.getElementById("graph-hub");
  if (!mount) return;

  const graphId = mount.getAttribute("data-graph") || "";
  if (!graphId) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Missing graph id</h2>
        <p class="muted">Add <code>data-graph="01"</code> to <code>&lt;main id="graph-hub"&gt;</code>.</p>
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
          <p><a href="/#charts">Back to homepage</a></p>
        </div>
      `;
      return;
    }

    const title = String(graph?.title || "").trim() || `Graph ${graphId}`;

    const mEntry = pickFirstEntry(graph, "matplotlib");
    const sEntry = pickFirstEntry(graph, "seaborn");
    const dEntry = pickFirstEntry(graph, "d3");

    // Writeup: prefer any renderer entry’s writeup, otherwise conventional path
    const writeupPath =
      (mEntry?.writeup || sEntry?.writeup || dEntry?.writeup || "").trim() ||
      `writeups/graphs/${graphId}.txt`;

    mount.innerHTML = `
      <section class="section">
        <div class="container">
          <div class="section-header prose">
            <h2 style="margin:0;">${escapeHtml(title)}</h2>
            <p class="muted" style="margin-top:0.35rem;">
              One graph, three renderers.
              <span class="muted"> · </span>
              <a href="/#charts">Back to homepage</a>
            </p>
          </div>

          <div class="grid">
            ${contextBlock(graph)}
            ${mEntry ? rendererCard({ graphId, renderer: "matplotlib", entry: mEntry }) : `<article class="card"><h3 class="card-title">Matplotlib</h3><p class="muted">No entry yet.</p></article>`}
            ${sEntry ? rendererCard({ graphId, renderer: "seaborn", entry: sEntry }) : `<article class="card"><h3 class="card-title">Seaborn</h3><p class="muted">No entry yet.</p></article>`}
            ${dEntry ? rendererCard({ graphId, renderer: "d3", entry: dEntry }) : `<article class="card"><h3 class="card-title">D3</h3><p class="muted">No entry yet.</p></article>`}
          </div>

          <div class="writeup" style="margin-top:1rem;">
            <h3 class="writeup-title">Writeup</h3>
            <div id="hub-writeup" class="muted">Loading writeup…</div>
          </div>
        </div>
      </section>
    `;

    const writeupEl = document.getElementById("hub-writeup");
    try {
      const text = await loadWriteup(writeupPath);
      writeupEl.innerHTML = `<pre style="white-space:pre-wrap;margin:0;">${escapeHtml(text)}</pre>`;
    } catch (werr) {
      writeupEl.innerHTML = `<p class="muted">${escapeHtml(werr.message || String(werr))}</p>`;
    }
  } catch (err) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Couldn’t load graph hub</h2>
        <p class="muted">${escapeHtml(err.message || String(err))}</p>
      </div>
    `;
    console.error(err);
  }
}

main();
