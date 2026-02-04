// site/graph_hub.js
// Graph hub page renderer.
// Reads: <main id="graph-hub" data-graph="04"></main>
// Loads: /data/charts_manifest.json
// Renders: Context + ALL renderer outputs (Matplotlib/Seaborn/D3) + writeup

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

// From nested routes (/graphs/04/), always use rooted URLs
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

function detailHref(graphId, renderer, entryId) {
  const base = `/graphs/${encodeURIComponent(graphId)}/${encodeURIComponent(renderer)}.html`;
  if (!entryId) return base;
  return `${base}?chart=${encodeURIComponent(entryId)}`;
}

function contextBlock(graph) {
  const question = String(graph?.question || "").trim();
  const notes = String(graph?.notes || "").trim();

  const methodVal = graph?.method;
  const methodList = Array.isArray(methodVal)
    ? methodVal
    : (methodVal ? [String(methodVal)] : []);

  const findings = Array.isArray(graph?.key_findings) ? graph.key_findings : [];

  const methodHtml = methodList.length
    ? `<ol>${methodList.map((m) => `<li>${escapeHtml(m)}</li>`).join("")}</ol>`
    : `<p class="muted">No method yet.</p>`;

  const findingsHtml = findings.length
    ? `<ul>${findings.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>`
    : `<p class="muted">No key findings yet.</p>`;

  return `
    <article class="card">
      <h3 class="card-title">Context</h3>
      <div class="prose">
        ${question ? `<h4>Question</h4><p>${escapeHtml(question)}</p>` : `<p class="muted">No question yet.</p>`}
        <h4>Method</h4>
        ${methodHtml}
        <h4>Key findings</h4>
        ${findingsHtml}
        ${notes ? `<h4>Notes</h4><p>${escapeHtml(notes)}</p>` : ""}
      </div>
    </article>
  `;
}

// Renders ALL entries for a renderer
function rendererSection({ graphId, renderer, entries }) {
  const label = rendererLabel(renderer);

  if (!entries.length) {
    return `
      <article class="card chart-card">
        <div class="chart-card-header">
          <h3 class="card-title">${escapeHtml(label)}</h3>
          <span class="badge">${escapeHtml(label)}</span>
        </div>
        <p class="muted">No ${escapeHtml(label)} outputs linked in the manifest yet.</p>
      </article>
    `;
  }

  const multiple = entries.length > 1;

  const figures = entries
    .map((entry, idx) => {
      const url = toRootedUrl(entry?.url || "");
      const entryId = String(entry?.id || "").trim();
      const link = detailHref(graphId, renderer, entryId);

      const ordinal = multiple ? ` ${idx + 1}/${entries.length}` : "";
      const title = `${label}${ordinal}`;

      if (!url) {
        return `
          <div class="muted" style="margin-top:0.75rem;">
            Missing url for ${escapeHtml(label)} entry ${escapeHtml(entryId || String(idx + 1))}.
          </div>
        `;
      }

      // Chart is NOT a link. Only "Open this version" is a link.
      return `
        <figure class="chart-figure" style="margin-top:0.75rem;">
          <div class="chart-media" aria-label="${escapeHtml(title)} chart">
            <img src="${escapeHtml(url)}" alt="${escapeHtml(title)} chart" loading="lazy" />
          </div>
          <div class="muted" style="margin-top:0.35rem;">
            <a class="small-link" href="${escapeHtml(link)}">Open this version</a>
          </div>
        </figure>
      `;
    })
    .join("");

  return `
    <article class="card chart-card">
      <div class="chart-card-header">
        <h3 class="card-title">${escapeHtml(label)}</h3>
        <span class="badge">${escapeHtml(label)}</span>
      </div>
      ${figures}
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

async function main() {
  const mount = document.getElementById("graph-hub");
  if (!mount) return;

  const graphId = mount.getAttribute("data-graph") || "";
  if (!graphId) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Missing graph id</h2>
        <p class="muted">Add <code>data-graph="04"</code> to <code>&lt;main id="graph-hub"&gt;</code>.</p>
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

    const title = String(graph?.title || "").trim() || `Graph ${graphId}`;

    const mEntries = getRendererEntries(graph, "matplotlib");
    const sEntries = getRendererEntries(graph, "seaborn");
    const dEntries = getRendererEntries(graph, "d3");

    // Writeup: prefer any renderer entry’s writeup, otherwise default
    const writeupPath =
      (mEntries[0]?.writeup || sEntries[0]?.writeup || dEntries[0]?.writeup || "").trim() ||
      `writeups/graphs/${graphId}.txt`;

    mount.innerHTML = `
      <section class="section">
        <div class="container">
          <div class="section-header prose">
            <h2 style="margin:0;">${escapeHtml(title)}</h2>
          </div>

          <div class="grid">
            ${contextBlock(graph)}
            ${rendererSection({ graphId, renderer: "matplotlib", entries: mEntries })}
            ${rendererSection({ graphId, renderer: "seaborn", entries: sEntries })}
            ${rendererSection({ graphId, renderer: "d3", entries: dEntries })}
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
