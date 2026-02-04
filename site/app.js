// site/app.js
// Homepage Graph Directory renderer.
// Order comes from /data/charts_manifest.json exactly as written (NO sorting).
// Cards show NO preview images.
// Shows a "Featured graphs" section at the top with 3 selected charts.

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

function graphHref(graphId) {
  return `/graphs/${encodeURIComponent(graphId)}/`;
}

function countRendererEntries(graph, renderer) {
  const arr = graph?.renderers?.[renderer];
  return Array.isArray(arr) ? arr.length : 0;
}

function renderChartHtml(url, title) {
  const u = toRootedUrl(url);

  // SVG: use <object> so it scales properly inside responsive containers
  if (u.toLowerCase().endsWith(".svg")) {
    return `
      <object
        data="${escapeHtml(u)}"
        type="image/svg+xml"
        class="chart-object"
        aria-label="${escapeHtml(title)}"
        style="width:100%; height:100%; display:block;"
      ></object>
    `;
  }

  // Raster: normal img
  return `
    <img
      src="${escapeHtml(u)}"
      alt="${escapeHtml(title)}"
      loading="lazy"
      style="width:100%; height:100%; object-fit:contain; display:block;"
    />
  `;
}

function featuredSectionHtml() {
  // Hard-coded featured items (because you are curating, not auto-generating).
  // If you change filenames later, update them here.
  const featured = [
    {
      label: "D3 • Graph 02",
      title: "Exclamation marks by generation (per profile)",
      url: "assets/charts/d3/word_graph_02_exclam_per100k_by_generation_per_profile.svg",
      href: "/graphs/02/d3.html",
    },
    {
      label: "Seaborn • Graph 08 (F)",
      title: "Sentence complexity (looking for women)",
      url: "assets/charts/seaborn/word_graph_08_sentence_complexity_looking_for_F_seaborn.png",
      href: "/graphs/08/seaborn.html?chart=08-seaborn-word_graph_08_sentence_complexity_looking_for_F_seaborn",
    },
    {
      label: "D3 • Graph 05",
      title: "Distinctive words: SF Bay Area vs UK/London",
      url: "assets/charts/d3/word_graph_05_distinctive_bayarea_vs_uk_london.svg",
      href: "/graphs/05/d3.html",
    },
  ];

  const cards = featured
    .map((f) => {
      const chart = renderChartHtml(f.url, f.title);

      return `
        <article class="card chart-card">
          <div class="chart-card-header">
            <h3 class="card-title" style="margin:0;">${escapeHtml(f.label)}</h3>
            <a class="small-link" href="${escapeHtml(f.href)}">Open</a>
          </div>

          <div class="muted" style="margin:0.35rem 0 0.75rem;">
            ${escapeHtml(f.title)}
          </div>

          <div
            class="chart-media"
            style="
              width: 100%;
              aspect-ratio: 16 / 9;
              overflow: hidden;
              display: grid;
              place-items: center;
            "
          >
            ${chart}
          </div>
        </article>
      `;
    })
    .join("");

  return `
    <section class="section">
      <div class="container">
        <div class="prose" style="margin-bottom:0.75rem;">
          <h2 style="margin:0;">Featured graphs</h2>
          <p class="muted" style="margin:0.35rem 0 0;">
            My personal favorites.
          </p>
        </div>

        <div class="grid">
          ${cards}
        </div>
      </div>
    </section>
  `;

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

    // IMPORTANT: DO NOT sort. Manifest order is your curated order.
    const directoryCards = graphs.map(graphCardHtml).join("");

    mount.innerHTML = `
      ${featuredSectionHtml()}

      <section class="section">
        <div class="container">
          <div class="prose" style="margin-bottom:0.75rem;">
            <h2 style="margin:0;">Graph directory</h2>
            <p class="muted" style="margin:0.35rem 0 0;">
              This directory is generated from <code>site/data/charts_manifest.json</code>.
            </p>
          </div>

          <div class="grid">
            ${directoryCards}
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
