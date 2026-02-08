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

function rendererLabel(renderer) {
  const r = String(renderer || "").toLowerCase();
  if (r === "d3") return "D3";
  if (r === "seaborn") return "Seaborn";
  if (r === "matplotlib") return "Matplotlib";
  return renderer ? String(renderer) : "";
}

function graphId2(id) {
  const s = String(id ?? "").trim();
  // Already "02"? keep it. If "2", pad to "02".
  return /^\d{2}$/.test(s) ? s : String(Number(s)).padStart(2, "0");
}

function featuredCardsHtml() {
  // Curated featured set (you can swap these anytime).
  // IMPORTANT: do not show "Graph ##" in the label, only renderer.
  const featured = [
    {
      label: "D3",
      title: "Exclamation marks by generation (per profile)",
      url: "assets/charts/d3/word_graph_02_exclam_per100k_by_generation_per_profile.svg",
      href: "/graphs/02/d3.html",
    },
    {
      label: "Seaborn (F)",
      title: "Sentence complexity (looking for women)",
      url: "assets/charts/seaborn/word_graph_08_sentence_complexity_looking_for_F_seaborn.png",
      href: "/graphs/08/seaborn.html?chart=08-seaborn-word_graph_08_sentence_complexity_looking_for_F_seaborn",
    },
    {
      label: "D3",
      title: "Distinctive words: SF Bay Area vs UK/London",
      url: "assets/charts/d3/word_graph_05_distinctive_bayarea_vs_uk_london.svg",
      href: "/graphs/05/d3.html",
    },
  ];

  const cards = featured
    .map((c) => {
      const label = escapeHtml(c.label);
      const title = escapeHtml(c.title);
      const href = escapeHtml(c.href);
      const url = escapeHtml(c.url);

      return `
        <article class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__kicker">${label}</div>
            <a class="chart-card__link" href="${href}">Open</a>
          </div>
          <h3 class="chart-card__title">${title}</h3>
          <div class="chart-card__media">
            <img class="chart-card__img" src="${url}" alt="${title}" loading="lazy" />
          </div>
        </article>
      `.trim();
    })
    .join("\n");

  return `<div class="chart-grid">${cards}</div>`;
}

function graphDirectoryCardsHtml(graphs) {
  // Directory cards (no preview images). Uses manifest ordering.
  const cards = graphs
    .map((g) => {
      const id = graphId2(g.id);
      const title = escapeHtml(g.title || `Graph ${id}`);
      const href = `/graphs/${id}/`;
      return `
        <a class="dir-card" href="${escapeHtml(href)}">
          <div class="dir-card__id">Graph ${escapeHtml(id)}</div>
          <div class="dir-card__title">${title}</div>
        </a>
      `.trim();
    })
    .join("\n");

  return `<div class="dir-grid">${cards}</div>`;
}

async function loadManifest() {
  const res = await fetch("/data/charts_manifest.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load charts_manifest.json: ${res.status}`);
  return res.json();
}

function normalizeManifest(manifest) {
  // Expecting: [{ id: "01", title: "...", ... }, ...]
  // But tolerate common shapes.
  if (Array.isArray(manifest)) return manifest;

  if (manifest && Array.isArray(manifest.graphs)) return manifest.graphs;

  // If it's graph-grouped object: { "01": {...}, "02": {...} }
  if (manifest && typeof manifest === "object") {
    const entries = Object.entries(manifest)
      .filter(([k]) => /^\d+$/.test(String(k)))
      .map(([k, v]) => ({ id: k, ...(v || {}) }));
    if (entries.length) {
      // sort numeric by id
      entries.sort((a, b) => Number(a.id) - Number(b.id));
      return entries;
    }
  }

  return [];
}

function renderHomepage({ graphs }) {
  const featuredRoot = document.querySelector("#featured");
  if (featuredRoot) {
    featuredRoot.innerHTML = featuredCardsHtml();
  }

  const dirRoot = document.querySelector("#graph-directory");
  if (dirRoot) {
    dirRoot.innerHTML = graphDirectoryCardsHtml(graphs);
  }
}

(async function main() {
  try {
    const manifest = await loadManifest();
    const graphs = normalizeManifest(manifest);
    renderHomepage({ graphs });
  } catch (err) {
    console.error(err);
    const featuredRoot = document.querySelector("#featured");
    if (featuredRoot) {
      featuredRoot.innerHTML = `<div class="callout error">Failed to load charts. Check console.</div>`;
    }
  }
})();
