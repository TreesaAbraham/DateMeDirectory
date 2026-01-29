// site/app.js
// Loads site/data/charts_manifest.json and renders chart cards into #charts-grid

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

function cardTemplate(chart) {
  const title = escapeHtml(chart.title || chart.id);
  const caption = escapeHtml(chart.caption || "");
  const badge = rendererLabel(chart.renderer);
  const url = chart.url; // must be a site-relative URL like "assets/charts/d3/foo.svg"
  const writeup = (chart.writeup || "").trim();

  const writeupLink = writeup
    ? `<a class="small-link" href="${escapeHtml(writeup)}">Writeup</a>`
    : "";

  return `
    <article class="card chart-card" data-renderer="${escapeHtml(chart.renderer || "")}">
      <div class="chart-card-header">
        <h3 class="card-title">${title}</h3>
        <span class="badge" title="Rendered with ${escapeHtml(badge)}">${escapeHtml(badge)}</span>
      </div>

      <div class="chart-frame" aria-label="${title}">
        <img class="chart-img" src="${escapeHtml(url)}" alt="${title}" loading="lazy" />
      </div>

      ${
        caption
          ? `<p class="card-body">${caption}</p>`
          : `<p class="card-body muted">No caption yet. Add it in <code>site/data/charts_manifest.json</code>.</p>`
      }

      ${writeupLink ? `<div class="chart-links">${writeupLink}</div>` : ""}
    </article>
  `;
}

async function loadManifest() {
  const res = await fetch("./data/charts_manifest.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load manifest: ${res.status} ${res.statusText}`);
  return res.json();
}

async function renderCharts() {
  const grid = document.getElementById("charts-grid");
  if (!grid) return;

  try {
    const manifest = await loadManifest();
    const charts = Array.isArray(manifest.charts) ? manifest.charts : [];

    if (charts.length === 0) {
      grid.innerHTML = `
        <article class="card">
          <h3 class="card-title">No charts found</h3>
          <p class="card-body muted">
            Run the generator script to populate <code>site/data/charts_manifest.json</code>.
          </p>
        </article>
      `;
      return;
    }

    grid.innerHTML = charts.map(cardTemplate).join("");
  } catch (err) {
    grid.innerHTML = `
      <article class="card">
        <h3 class="card-title">Couldn’t load charts</h3>
        <p class="card-body muted">${escapeHtml(err.message || String(err))}</p>
        <p class="card-body muted">
          Make sure <code>site/data/charts_manifest.json</code> exists and is valid JSON.
        </p>
      </article>
    `;
    console.error(err);
  }
}

renderCharts();
