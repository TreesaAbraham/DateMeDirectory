// site/app.js
// Homepage Graph Directory renderer.
// Order comes from /data/charts_manifest.json exactly as written (NO sorting).
// Cards show NO preview images (carousel will handle favorites elsewhere).

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

function detailHref(graphId, renderer, entryId) {
  const base = `/graphs/${encodeURIComponent(graphId)}/${encodeURIComponent(renderer)}.html`;
  if (!entryId) return base;
  return `${base}?chart=${encodeURIComponent(entryId)}`;
}

function toRootedUrl(url) {
  const u = String(url ?? "").trim();
  if (!u) return "";
  if (u.startsWith("http://") || u.startsWith("https://")) return u;
  if (u.startsWith("/")) return u;
  return `/${u}`;
}

function rendererLabel(renderer) {
  const r = String(renderer || "").toLowerCase();
  if (r === "d3") return "D3";
  if (r === "seaborn") return "Seaborn";
  if (r === "matplotlib") return "Matplotlib";
  return renderer || "Unknown";
}

function countRendererEntries(graph, renderer) {
  const arr = graph?.renderers?.[renderer];
  return Array.isArray(arr) ? arr.length : 0;
}

function findGraph(manifest, graphId) {
  const graphs = Array.isArray(manifest?.graphs) ? manifest.graphs : [];
  return graphs.find((g) => String(g?.graph_id) === String(graphId));
}

function getRendererEntries(graph, renderer) {
  const list = graph?.renderers?.[renderer];
  return Array.isArray(list) ? list : [];
}

function pickEntryById(entries, entryId) {
  if (!Array.isArray(entries) || !entries.length) return null;
  if (!entryId) return entries[0];
  return entries.find((e) => String(e?.id) === String(entryId)) || entries[0];
}

// For previews in the carousel only.
// SVG => <object> so it scales; others => <img>
function renderPreviewHtml(url, title) {
  const u = toRootedUrl(url);
  if (!u) return `<div class="muted">Missing chart URL</div>`;

  if (u.toLowerCase().endsWith(".svg")) {
    return `
      <object
        data="${escapeHtml(u)}"
        type="image/svg+xml"
        class="carousel-object"
        aria-label="${escapeHtml(title)} preview"
      ></object>
    `;
  }

  return `<img src="${escapeHtml(u)}" alt="${escapeHtml(title)} preview" loading="lazy" />`;
}

function favoritesCarouselHtml(manifest) {
  // Hard-coded favorites (stable + explicit, so your work doesn’t “mysteriously change” later).
  const favorites = [
    {
      graphId: "02",
      renderer: "d3",
      entryId: "02-d3-word_graph_02_exclam_per100k_by_generation_per_profile",
      label: "Graph 02 • D3",
    },
    {
      graphId: "08",
      renderer: "seaborn",
      entryId: "08-seaborn-word_graph_08_sentence_complexity_looking_for_F_seaborn",
      label: "Graph 08 • Seaborn (F)",
    },
    {
      graphId: "05",
      renderer: "d3",
      entryId: "05-d3-word_graph_05_distinctive_bayarea_vs_uk_london",
      label: "Graph 05 • D3",
    },
  ];

  const slides = favorites
    .map((f) => {
      const graph = findGraph(manifest, f.graphId);
      const entries = getRendererEntries(graph, f.renderer);
      const entry = pickEntryById(entries, f.entryId);

      const graphTitle = String(graph?.title || "").trim() || `Graph ${f.graphId}`;
      const rLabel = rendererLabel(f.renderer);
      const href = detailHref(f.graphId, f.renderer, f.entryId);

      const previewTitle = `${graphTitle} (${rLabel})`;
      const preview = entry?.url
        ? renderPreviewHtml(entry.url, previewTitle)
        : `<div class="muted">Favorite not found in manifest.</div>`;

      return `
        <div class="carousel-slide">
          <article class="card chart-card" style="margin:0;">
            <div class="chart-card-header">
              <h3 class="card-title" style="margin:0;">${escapeHtml(f.label)}</h3>
            </div>

            <div class="chart-media" aria-label="${escapeHtml(previewTitle)}">
              ${preview}
            </div>

            <div class="muted" style="margin-top:0.5rem;">
              <div style="font-weight:700; color:inherit;">${escapeHtml(graphTitle)}</div>
              <a class="small-link" href="${escapeHtml(href)}" style="display:inline-block; margin-top:0.25rem;">
                Open this chart
              </a>
            </div>
          </article>
        </div>
      `;
    })
    .join("");

  return `
    <section class="section" style="padding-top:0;">
      <div class="container">
        <div class="prose" style="margin-bottom:0.75rem;">
          <h2 style="margin:0;">Favorites</h2>
          <p class="muted" style="margin:0.25rem 0 0;">
            Three graphs I actually like (a rare event).
          </p>
        </div>

        <div class="carousel" aria-label="Favorite graphs carousel">
          ${slides}
        </div>

        <style>
          /* Carousel layout (scoped to this page fragment) */
          .carousel {
            display: grid;
            grid-auto-flow: column;
            grid-auto-columns: minmax(320px, 1fr);
            gap: 1rem;
            overflow-x: auto;
            padding-bottom: 0.5rem;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
          }
          .carousel-slide { scroll-snap-align: start; }

          /* Make previews fit like your “good” example */
          .carousel .chart-media {
            width: 100%;
            aspect-ratio: 16 / 9;
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            overflow: hidden;
            display: grid;
            place-items: center;
          }
          .carousel .chart-media img,
          .carousel .chart-media object {
            width: 100%;
            height: 100%;
            display: block;
          }
          .carousel .chart-media img {
            object-fit: contain;
          }
          .carousel-object {
            /* SVG objects behave better with explicit sizing */
            width: 100%;
            height: 100%;
          }
        </style>
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
  // Mount target: try common ids first, then fall back to the first <main>.
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
    const cards = graphs.map(graphCardHtml).join("");

    mount.innerHTML = `
      ${favoritesCarouselHtml(manifest)}
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
