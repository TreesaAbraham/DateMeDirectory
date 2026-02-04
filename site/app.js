// site/app.js
// Homepage Graph Directory renderer.
// Order comes from /data/charts_manifest.json exactly as written (NO sorting).

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// From nested routes, always use rooted URLs when needed
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

function graphHref(graphId) {
  return `/graphs/${encodeURIComponent(graphId)}/`;
}

function pickPreview(graph) {
  // Prefer D3 preview, then seaborn, then matplotlib
  const d3 = graph?.renderers?.d3?.[0]?.url;
  const seaborn = graph?.renderers?.seaborn?.[0]?.url;
  const mpl = graph?.renderers?.matplotlib?.[0]?.url;
  return toRootedUrl(d3 || seaborn || mpl || "");
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
  const preview = pickPreview(graph);

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
      <div class="prose" style="margin-bottom:0.5rem;">
        <h3 style="margin:0;">
          <a href="${escapeHtml(href)}" class="small-link" style="font-size:1.05em;">
            ${escapeHtml(title)}
          </a>
        </h3>
        ${question ? `<p class="muted" style="margin:0.25rem 0 0;">${escapeHtml(question)}</p>` : ""}
        <p class="muted" style="margin:0.35rem 0 0;">${escapeHtml(meta)}</p>
      </div>

      ${
        preview
          ? `
            <figure class="chart-figure" style="margin:0;">
              <div class="chart-media" aria-label="${escapeHtml(title)} preview">
                <img src="${escapeHtml(preview)}" alt="${escapeHtml(title)} preview" loading="lazy" />
              </div>
            </figure>
          `
          : `<p class="muted">No preview image available.</p>`
      }

      <div class="muted" style="margin-top:0.5rem;">
        <a class="small-link" href="${escapeHtml(href)}">Open graph hub</a>
      </div>
    </article>
  `;
}

async function main() {
  // This should match whatever mount your index.html uses.
  // Common patterns: <main id="app"></main> or <section id="charts"></section>
  const mount =
    document.getElementById("app") ||
    document.getElementById("charts") ||
    document.querySelector("main");

  if (!mount) return;

  try {
    const manifest = await loadManifest();
    const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];

    if (!graphs.length) {
      mount.innerHTML = `
        <div class="container prose">
          <h2>No graphs found</h2>
          <p class="muted"><code>/data/charts_manifest.json</code> loaded, but <code>graphs[]</code> is empty.</p>
        </div>
      `;
      return;
    }

    // IMPORTANT: do NOT sort. Manifest order is your curated order.
    const cards = graphs.map(graphCardHtml).join("");

    mount.innerHTML = `
      <section class="section">
        <div class="container">
          <div class="grid">
            ${cards}
          </div>
        </div>
      </section>
    `;
  } catch (err) {
    mount.innerHTML = `
      <div class="container prose">
        <h2>Couldn’t load directory</h2>
        <p class="muted">${escapeHtml(err.message || String(err))}</p>
        <p class="muted">Check that <code>/data/charts_manifest.json</code> is reachable.</p>
      </div>
    `;
    console.error(err);
  }
}

main();
