// site/app.js
// Homepage renderer.
// - Populates #featured with 3 curated charts (no extra header/section injected).
// - Populates #graph-directory with manifest-ordered graph cards (no preview images).
// - Does NOT inject any <code>site/data/charts_manifest.json</code> text (avoids pill styling).

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// From nested routes, always use rooted URLs
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

function featuredCardsHtml() {
  // Hard-coded featured items (curated).
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

  return featured
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

        ${question ? `<p class="muted" style="margin:0.35rem 0 0;">${escapeHtml(question)}</p>` : ""}

        <p class="muted" style="margin:0.35rem 0 0;">${escapeHtml(meta)}</p>

        <div class="muted" style="margin-top:0.5rem;">
          <a class="small-link" href="${escapeHtml(href)}">Open graph hub</a>
        </div>
      </div>
    </article>
  `;
}

async function main() {
  // 1) Featured graphs: ONLY fill the existing #featured container.
  const featuredMount = document.getElementById("featured");
  if (featuredMount) {
    featuredMount.innerHTML = featuredCardsHtml();
  }

  // 2) Graph directory: ONLY fill the existing #graph-directory container.
  const dirMount = document.getElementById("graph-directory");
  if (!dirMount) return;

  try {
    const manifest = await loadManifest();
    const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];

    if (!graphs.length) {
      dirMount.innerHTML = `
        <article class="card">
          <h3 class="card-title">No graphs found</h3>
          <p class="card-body muted">The manifest loaded, but <span class="inline-path">graphs[]</span> is empty.</p>
        </article>
      `;
      return;
    }

    // IMPORTANT: DO NOT sort. Manifest order is your curated order.
    dirMount.innerHTML = graphs.map(graphCardHtml).join("");
  } catch (err) {
    dirMount.innerHTML = `
      <article class="card">
        <h3 class="card-title">Couldn’t load directory</h3>
        <p class="card-body muted">${escapeHtml(err.message || String(err))}</p>
        <p class="card-body muted">Check that <span class="inline-path">/data/charts_manifest.json</span> is reachable.</p>
      </article>
    `;
    console.error(err);
  }
}

main();
