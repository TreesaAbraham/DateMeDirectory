// site/app.js
// Homepage Graph Directory renderer.
// Uses /data/charts_manifest.json
// IMPORTANT:
// - Does NOT render "Featured graphs" at all.
// - Does NOT inject <code>...</code> anywhere (prevents pill styling).
// - Only fills the existing #graph-directory grid defined in index.html.
// - Manifest order is preserved (NO sorting).

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadManifest() {
  const res = await fetch("/data/charts_manifest.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load manifest: HTTP ${res.status}`);
  return res.json();
}

function graphHref(graphId) {
  return `/graphs/${encodeURIComponent(graphId)}/`;
}

function countRendererEntries(graph, renderer) {
  const arr = graph?.renderers?.[renderer];
  return Array.isArray(arr) ? arr.length : 0;
}

function graphCardHtml(graph) {
  const id = String(graph?.graph_id ?? "").trim();
  const title = String(graph?.title ?? "").trim() || `Graph ${id}`;
  const question = String(graph?.question ?? "").trim();
  const href = graphHref(id);

  const nM = countRendererEntries(graph, "matplotlib");
  const nS = countRendererEntries(graph, "seaborn");
  const nD = countRendererEntries(graph, "d3");

  const metaBits = [];
  if (nM) metaBits.push(`Matplotlib: ${nM}`);
  if (nS) metaBits.push(`Seaborn: ${nS}`);
  if (nD) metaBits.push(`D3: ${nD}`);
  const meta = metaBits.length ? metaBits.join(" • ") : "No renders linked";

  return `
    <article class="card">
      <div class="prose">
        <h3 style="margin:0;">
          <a href="${escapeHtml(href)}" class="small-link" style="font-size:1.05em;">
            ${escapeHtml(title)}
          </a>
        </h3>

        ${
          question
            ? `<p class="muted" style="margin:0.35rem 0 0;">${escapeHtml(question)}</p>`
            : ""
        }

        <p class="muted" style="margin:0.35rem 0 0;">${escapeHtml(meta)}</p>

        <div class="muted" style="margin-top:0.5rem;">
          <a class="small-link" href="${escapeHtml(href)}">Open graph hub</a>
        </div>
      </div>
    </article>
  `;
}

async function main() {
  // This is the grid in your index.html under the Graph directory section.
  const grid =
    document.getElementById("graph-directory") ||
    document.getElementById("app") ||
    document.getElementById("charts");

  if (!grid) return;

  try {
    const manifest = await loadManifest();
    const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];

    if (!graphs.length) {
      grid.innerHTML = `
        <article class="card">
          <h3 class="card-title">No graphs found</h3>
          <p class="card-body muted">
            The manifest loaded, but graphs[] is empty.
          </p>
        </article>
      `;
      return;
    }

    // IMPORTANT: DO NOT sort. Manifest order is your curated order.
    grid.innerHTML = graphs.map(graphCardHtml).join("");
  } catch (err) {
    grid.innerHTML = `
      <article class="card">
        <h3 class="card-title">Couldn’t load directory</h3>
        <p class="card-body muted">${escapeHtml(err.message || String(err))}</p>
        <p class="card-body muted">Check that /data/charts_manifest.json is reachable.</p>
      </article>
    `;
    console.error(err);
  }
}

main();
