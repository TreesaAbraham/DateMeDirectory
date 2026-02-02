// site/app.js
// Renders: main chart grid (#charts-grid), chart detail (#chart-detail), topic pages (#topic-charts)

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

async function loadManifest(relativePrefix = ".") {
  const url = `${relativePrefix}/data/charts_manifest.json`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load manifest: ${res.status}`);
  return res.json();
}

/**
 * Manifest helpers (canonical = graph-grouped)
 */

function getGraphs(manifest) {
  return Array.isArray(manifest?.graphs) ? manifest.graphs : [];
}

function normalizeChartUrl(renderer, entry) {
  const url = String(entry?.url || "").trim();
  if (url) return url.replace(/^\.\//, "");
  const file = String(entry?.file || "").trim();
  if (file) return `assets/charts/${renderer}/${file}`;
  return "";
}

// Keeps legacy pages working by flattening graph-grouped manifest into chart cards.
function flattenChartsFromGraphs(graphs) {
  const charts = [];

  for (const g of graphs) {
    const graphId = String(g?.graph_id || "").trim();
    const graphTitle =
      String(g?.title || "").trim() ||
      (graphId ? `Graph ${graphId}` : "Graph");

    const renderers =
      g?.renderers && typeof g.renderers === "object" ? g.renderers : {};

    for (const [renderer, entries] of Object.entries(renderers)) {
      if (!Array.isArray(entries)) continue;

      for (const e of entries) {
        const id = String(e?.id || "").trim();
        if (!id) continue;

        charts.push({
          // chart-level fields used by the existing UI
          id,
          title: `${graphTitle} (${rendererLabel(renderer)})`,
          renderer,
          caption: String(e?.caption || "").trim(),
          url: normalizeChartUrl(renderer, e),
          writeup: String(e?.writeup || "").trim(),
          tags: Array.isArray(e?.tags)
            ? e.tags
            : Array.isArray(g?.tags)
              ? g.tags
              : [],

          // bring graph-level context into chart detail pages
          question: String(g?.question || "").trim(),
          method: String(g?.method || "").trim(),
          key_findings: Array.isArray(g?.key_findings) ? g.key_findings : [],
          notes: String(g?.notes || "").trim(),

          // extra context for future graph-hub pages / filtering
          graph_id: graphId,
          graph_title: graphTitle,
        });
      }
    }
  }

  return charts;
}

/**
 * Card templates
 */

function chartCard(chart, linkPrefix = ".") {
  const title = escapeHtml(chart.title || chart.id);
  const badge = rendererLabel(chart.renderer);
  const url = `${linkPrefix}/${chart.url}`.replaceAll("//", "/");
  const caption = escapeHtml(chart.caption || "");
  const id = encodeURIComponent(chart.id);

  return `
    <article class="card chart-card" data-renderer="${escapeHtml(
      chart.renderer || ""
    )}">
      <div class="chart-card-header">
        <h3 class="card-title">${title}</h3>
        <span class="badge" title="Rendered with ${escapeHtml(
          badge
        )}">${escapeHtml(badge)}</span>
      </div>

      <figure class="chart-figure">
        <div class="chart-media" aria-label="${title}">
          <img class="chart-img" src="${escapeHtml(
            url
          )}" alt="${title}" loading="lazy" />
        </div>

        <figcaption>
          ${
            caption
              ? `<strong>Caption:</strong> ${caption}`
              : `<span class="muted">No caption yet.</span>`
          }
        </figcaption>
      </figure>

      <div class="chart-links">
        <a class="small-link" href="${linkPrefix}/chart.html?id=${id}">View details</a>
      </div>
    </article>
  `;
}

function chartDetailTemplate(chart, linkPrefix = ".") {
  const title = escapeHtml(chart.title || chart.id);
  const badge = rendererLabel(chart.renderer);
  const url = `${linkPrefix}/${chart.url}`.replaceAll("//", "/");
  const caption = escapeHtml(chart.caption || "");
  const tags = Array.isArray(chart.tags) ? chart.tags : [];
  const tagBadges = tags.length
    ? tags.map((t) => `<span class="badge" title="Tag">${escapeHtml(t)}</span>`).join(" ")
    : `<span class="muted">No tags yet.</span>`;

  const method = escapeHtml(chart.method || "");
  const findings = Array.isArray(chart.key_findings) ? chart.key_findings : [];
  const findingsHtml = findings.length
    ? `<ul>${findings.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>`
    : `<p class="muted">No key findings yet. Add <code>key_findings</code> for this graph in the manifest.</p>`;

  const question = escapeHtml(chart.question || "");
  const notes = escapeHtml(chart.notes || "");

  return `
    <div class="chart-detail">
      <div class="chart-card-header">
        <h2 style="margin:0;">${title}</h2>
        <span class="badge" title="Rendered with ${escapeHtml(badge)}">${escapeHtml(badge)}</span>
      </div>

      <div style="margin-top:0.65rem;">
        ${tagBadges}
      </div>

      <figure class="chart-figure" style="margin-top:1rem;">
        <div class="chart-media" aria-label="${title}">
          <img class="chart-img" src="${escapeHtml(url)}" alt="${title}" />
        </div>
        <figcaption>
          ${caption ? `<strong>Caption:</strong> ${caption}` : `<span class="muted">No caption yet.</span>`}
        </figcaption>
      </figure>

      <div class="prose" style="margin-top:1rem;">
        ${question ? `<h3>Question</h3><p>${question}</p>` : ""}
        <h3>Method</h3>
        ${method ? `<p>${method}</p>` : `<p class="muted">No method yet. Add <code>method</code> for this graph in the manifest.</p>`}

        <h3>Key findings</h3>
        ${findingsHtml}

        ${notes ? `<h3>Notes</h3><p>${notes}</p>` : ""}
      </div>

      <div class="writeup" style="margin-top:1rem;">
        <h3 style="margin-top:0;">Write-up</h3>
        <div id="chart-writeup"></div>
      </div>
    </div>
  `;
}

/**
 * Page detection helpers
 */

function getQueryParam(name) {
  try {
    const url = new URL(window.location.href);
    return url.searchParams.get(name);
  } catch {
    return null;
  }
}

/**
 * Page renderers
 */

async function renderMainGrid() {
  const grid = document.getElementById("charts-grid");
  if (!grid) return;

  try {
    const manifest = await loadManifest(".");
    const graphs = getGraphs(manifest);
    const charts = flattenChartsFromGraphs(graphs);

    if (charts.length === 0) {
      grid.innerHTML = `
        <article class="card">
          <h3 class="card-title">No charts found</h3>
          <p class="card-body muted">Generate or edit <code>site/data/charts_manifest.json</code> (graph-grouped schema).</p>
        </article>
      `;
      return;
    }

    grid.innerHTML = charts.map((c) => chartCard(c, ".")).join("");
  } catch (err) {
    grid.innerHTML = `
      <article class="card">
        <h3 class="card-title">Couldn’t load charts</h3>
        <p class="card-body muted">${escapeHtml(err.message || String(err))}</p>
      </article>
    `;
    console.error(err);
  }
}

async function renderTopicPage() {
  const el = document.getElementById("topic-charts");
  if (!el) return;

  const tag = el.getAttribute("data-topic-tag") || "";
  const prefix = ".."; // topic pages live in /topics, so assets are one level up

  try {
    const manifest = await loadManifest(prefix);
    const graphs = getGraphs(manifest);
    const charts = flattenChartsFromGraphs(graphs);

    const filtered = charts.filter(
      (c) => Array.isArray(c.tags) && c.tags.includes(tag)
    );

    if (filtered.length === 0) {
      el.innerHTML = `
        <article class="card">
          <h3 class="card-title">No charts tagged “${escapeHtml(tag)}”</h3>
          <p class="card-body muted">
            Add <code>"tags": ["${escapeHtml(tag)}"]</code> to the relevant entries in
            <code>site/data/charts_manifest.json</code>.
          </p>
        </article>
      `;
      return;
    }

    el.innerHTML = filtered.map((c) => chartCard(c, prefix)).join("");
  } catch (err) {
    el.innerHTML = `
      <article class="card">
        <h3 class="card-title">Couldn’t load topic charts</h3>
        <p class="card-body muted">${escapeHtml(err.message || String(err))}</p>
      </article>
    `;
    console.error(err);
  }
}

async function renderChartDetail() {
  const el = document.getElementById("chart-detail");
  if (!el) return;

  const id = getQueryParam("id");
  if (!id) {
    el.innerHTML = `
      <h2>Missing chart id</h2>
      <p class="muted">Open this page like <code>chart.html?id=01-d3-01</code>.</p>
    `;
    return;
  }

  try {
    const manifest = await loadManifest(".");
    const graphs = getGraphs(manifest);
    const charts = flattenChartsFromGraphs(graphs);
    const chart = charts.find((c) => c.id === id);

    if (!chart) {
      el.innerHTML = `
        <h2>Chart not found</h2>
        <p class="muted">No chart with id <code>${escapeHtml(id)}</code> in the manifest.</p>
      `;
      return;
    }

    document.title = chart.title
      ? `${chart.title} | Date Me Directory`
      : "Chart | Date Me Directory";

    el.innerHTML = chartDetailTemplate(chart, ".");

    // Load writeup file if provided
    const writeupEl = document.getElementById("chart-writeup");
    const writeupPath = (chart.writeup || "").trim();

    if (!writeupPath) {
      writeupEl.innerHTML = `<p class="muted">No writeup linked. Add <code>writeup</code> in the manifest.</p>`;
      return;
    }

    try {
      const res = await fetch(`./${writeupPath}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`Writeup not found (${res.status})`);

      // For now: treat as plain text. (We can upgrade to markdown rendering later.)
      const text = await res.text();
      writeupEl.innerHTML = `<pre style="white-space:pre-wrap;margin:0;">${escapeHtml(text)}</pre>`;
    } catch (werr) {
      writeupEl.innerHTML = `<p class="muted">${escapeHtml(werr.message || String(werr))}</p>`;
    }
  } catch (err) {
    el.innerHTML = `
      <h2>Couldn’t load chart</h2>
      <p class="muted">${escapeHtml(err.message || String(err))}</p>
    `;
    console.error(err);
  }
}

/* Boot */
renderMainGrid();
renderTopicPage();
renderChartDetail();
