// site/app.js
// Homepage logic:
// - Render Graph Directory (one card per graph -> /graphs/<id>/)
// - Optional Featured strip (small list, not a full gallery)

async function loadManifest() {
  const res = await fetch("/data/charts_manifest.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Manifest load failed: HTTP ${res.status}`);
  return res.json();
}

function graphsFromManifest(manifest) {
  return Array.isArray(manifest?.graphs) ? manifest.graphs : [];
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function hasRenderer(graph, key) {
  const list = graph?.renderers?.[key];
  return Array.isArray(list) && list.length > 0;
}

function rendererSummary(graph) {
  const parts = [];
  if (hasRenderer(graph, "matplotlib")) parts.push("Matplotlib");
  if (hasRenderer(graph, "seaborn")) parts.push("Seaborn");
  if (hasRenderer(graph, "d3")) parts.push("D3");
  return parts.length ? parts.join(" · ") : "No renderers linked yet";
}

function graphCard(graph) {
  const id = String(graph?.graph_id ?? "").trim();
  const title = String(graph?.title ?? `Graph ${id}`).trim() || `Graph ${id}`;
  const href = `/graphs/${encodeURIComponent(id)}/`;

  const q = String(graph?.question ?? "").trim();
  const subtitle = q ? q : "Open hub page to see all renderers + context.";
  const renderers = rendererSummary(graph);

  return `
    <article class="card">
      <h3 class="card-title">
        <a href="${href}">${escapeHtml(title)}</a>
      </h3>
      <p class="card-body muted">${escapeHtml(subtitle)}</p>
      <p class="muted" style="margin-top:0.75rem;">
        <strong>Renderers:</strong> ${escapeHtml(renderers)}
      </p>
      <p style="margin-top:0.75rem;">
        <a href="${href}">View graph hub</a>
      </p>
    </article>
  `;
}

// Optional: featured charts. Keep this SMALL.
// Use renderer-entry IDs from the manifest, or just feature graph hubs.
const FEATURED_GRAPH_IDS = ["01", "02", "05"]; // change or empty to disable

function featuredCard(graph) {
  const id = String(graph?.graph_id ?? "").trim();
  const title = String(graph?.title ?? `Graph ${id}`).trim() || `Graph ${id}`;
  const href = `/graphs/${encodeURIComponent(id)}/`;
  const renderers = rendererSummary(graph);

  return `
    <article class="card">
      <h3 class="card-title">
        <a href="${href}">${escapeHtml(title)}</a>
      </h3>
      <p class="card-body muted">
        Quick jump to the hub page.
      </p>
      <p class="muted" style="margin-top:0.75rem;">
        <strong>Renderers:</strong> ${escapeHtml(renderers)}
      </p>
      <p style="margin-top:0.75rem;">
        <a href="${href}">Open</a>
      </p>
    </article>
  `;
}

async function main() {
  const dirEl = document.getElementById("graph-directory");
  const featuredEl = document.getElementById("featured-grid");

  // If someone deletes the section, just do nothing quietly.
  if (!dirEl && !featuredEl) return;

  try {
    const manifest = await loadManifest();
    const graphs = graphsFromManifest(manifest);

    // Directory
    if (dirEl) {
      if (!graphs.length) {
        dirEl.innerHTML = `
          <article class="card">
            <h3 class="card-title">No graphs found</h3>
            <p class="card-body muted">
              <code>data/charts_manifest.json</code> loaded, but <code>graphs[]</code> is empty.
            </p>
          </article>
        `;
      } else {
        // Sort by numeric graph id (01, 02, 03...)
        const sorted = [...graphs].sort((a, b) => {
          const ai = parseInt(String(a?.graph_id ?? ""), 10);
          const bi = parseInt(String(b?.graph_id ?? ""), 10);
          return (Number.isNaN(ai) ? 999 : ai) - (Number.isNaN(bi) ? 999 : bi);
        });

        dirEl.innerHTML = sorted.map(graphCard).join("");
      }
    }

    // Featured
    if (featuredEl) {
      const featured = graphs.filter((g) => FEATURED_GRAPH_IDS.includes(String(g?.graph_id ?? "").trim()));
      if (!featured.length) {
        featuredEl.innerHTML = `
          <article class="card">
            <h3 class="card-title">No featured charts yet</h3>
            <p class="card-body muted">
              Edit <code>FEATURED_GRAPH_IDS</code> in <code>site/app.js</code>.
            </p>
          </article>
        `;
      } else {
        featuredEl.innerHTML = featured.map(featuredCard).join("");
      }
    }
  } catch (err) {
    const msg = (err && err.message) ? err.message : String(err);

    if (dirEl) {
      dirEl.innerHTML = `
        <article class="card">
          <h3 class="card-title">Couldn’t load directory</h3>
          <p class="card-body muted">${escapeHtml(msg)}</p>
          <p class="muted">Check that <code>/data/charts_manifest.json</code> is reachable.</p>
        </article>
      `;
    }
    if (featuredEl) {
      featuredEl.innerHTML = `
        <article class="card">
          <h3 class="card-title">Couldn’t load featured</h3>
          <p class="card-body muted">${escapeHtml(msg)}</p>
        </article>
      `;
    }

    console.error(err);
  }
}

main();
