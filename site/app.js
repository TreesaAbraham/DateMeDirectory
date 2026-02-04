// site/app.js
// Homepage Graph Directory renderer.
// Order comes from /data/charts_manifest.json exactly as written (NO sorting).
// Cards show NO preview images (carousel shows favorites).

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

function renderCarouselMedia(item) {
  const url = toRootedUrl(item.url);
  const title = item.title || "Favorite chart";

  if (url.toLowerCase().endsWith(".svg")) {
    return `
      <object
        data="${escapeHtml(url)}"
        type="image/svg+xml"
        class="carousel-object"
        aria-label="${escapeHtml(title)}"
      ></object>
    `;
  }

  return `<img src="${escapeHtml(url)}" alt="${escapeHtml(title)}" loading="lazy" />`;
}

function carouselHtml(items) {
  // NOTE: urls MUST be site URLs (/assets/...), not /Users/...
  const slides = items
    .map((it, i) => {
      const href = it.href ? toRootedUrl(it.href) : "";
      const caption = it.caption ? `<div class="muted" style="margin-top:0.5rem;">${escapeHtml(it.caption)}</div>` : "";

      return `
        <div class="carousel-slide" data-idx="${i}" aria-hidden="${i === 0 ? "false" : "true"}">
          <div class="carousel-media">
            ${renderCarouselMedia(it)}
          </div>
          ${
            href
              ? `<div class="muted" style="margin-top:0.35rem;"><a class="small-link" href="${escapeHtml(href)}">Open graph</a></div>`
              : ""
          }
          ${caption}
        </div>
      `;
    })
    .join("");

  const dots = items
    .map((_, i) => `<button class="carousel-dot" type="button" aria-label="Go to slide ${i + 1}" data-go="${i}"></button>`)
    .join("");

  return `
    <article class="card" style="margin-bottom:1rem;">
      <div class="chart-card-header" style="display:flex; justify-content:space-between; align-items:center; gap:1rem;">
        <h3 class="card-title" style="margin:0;">Featured graphs</h3>

        <div class="carousel-controls">
          <button class="carousel-btn" type="button" data-dir="-1" aria-label="Previous">←</button>
          <button class="carousel-btn" type="button" data-dir="1" aria-label="Next">→</button>
        </div>
      </div>

      <div class="carousel" data-carousel="favorites">
        <div class="carousel-viewport">
          ${slides}
        </div>
        <div class="carousel-dots" aria-label="Slide selector">
          ${dots}
        </div>
      </div>
    </article>
  `;
}

function wireCarousel(root) {
  const viewport = root.querySelector(".carousel-viewport");
  const slides = Array.from(root.querySelectorAll(".carousel-slide"));
  const dots = Array.from(root.querySelectorAll(".carousel-dot"));
  const prevNext = Array.from(root.querySelectorAll(".carousel-btn"));

  if (!viewport || slides.length === 0) return;

  let idx = 0;

  function apply(nextIdx) {
    idx = (nextIdx + slides.length) % slides.length;

    slides.forEach((s, i) => {
      const active = i === idx;
      s.classList.toggle("is-active", active);
      s.setAttribute("aria-hidden", active ? "false" : "true");
    });

    dots.forEach((d, i) => d.classList.toggle("is-active", i === idx));
  }

  prevNext.forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.getAttribute("data-dir")) || 0;
      apply(idx + dir);
    });
  });

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      const go = Number(dot.getAttribute("data-go"));
      if (Number.isFinite(go)) apply(go);
    });
  });

  // init
  apply(0);
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

    // Your featured picks (USE SITE URLS, NOT /Users/... PATHS)
    const featured = [
      {
        title: "Graph 02 (D3)",
        url: "/assets/charts/d3/word_graph_02_exclam_per100k_by_generation_per_profile.svg",
        href: "/graphs/02/d3.html",
        caption: "Exclamation usage per generation (per profile).",
      },
      {
        title: "Graph 08 (Seaborn, Looking for Women)",
        url: "/assets/charts/seaborn/word_graph_08_sentence_complexity_looking_for_F_seaborn.png",
        href: "/graphs/08/seaborn.html",
        caption: "Sentence complexity distribution (target = women).",
      },
      {
        title: "Graph 05 (D3)",
        url: "/assets/charts/d3/word_graph_05_distinctive_bayarea_vs_uk_london.svg",
        href: "/graphs/05/d3.html",
        caption: "Distinctive words: Bay Area vs UK/London.",
      },
    ];

    const cards = graphs.map(graphCardHtml).join("");

    mount.innerHTML = `
      <section class="section">
        <div class="container">
          ${carouselHtml(featured)}
          <div class="grid">
            ${cards}
          </div>
        </div>
      </section>
    `;

    // Wire carousel after HTML is in the DOM
    const car = mount.querySelector('[data-carousel="favorites"]');
    if (car) wireCarousel(car);
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
