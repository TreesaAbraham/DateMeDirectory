#!/usr/bin/env node
/* scripts/d3/word_graph_10_mosaic_kids_by_style_d3.mjs */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { csvParse } from "d3-dsv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// -------- Paths (repo-relative) --------
const REPO_ROOT = path.resolve(__dirname, "..", "..");

const DEFAULT_IN_CSV = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_10_kids_mentions_by_style_mosaic_counts.csv"
);

const DEFAULT_OUT_SVG = path.join(
  REPO_ROOT,
  "data/charts/d3/word_graph_10_mosaic_kids_by_style.svg"
);

// -------- Config --------
const STYLE_ORDER = ["mono", "poly", "any"];
const BUCKET_ORDER = ["No kids mention", "Kids mention"];

const STYLE_COLORS = {
  mono: "#D2042D", // cherry red
  poly: "#F4B400", // marigold yellow
  any: "#FFCBA4",  // peach
};

const KIDS_TOPIC_TERMS = [
  "baby", "babies", "child", "children", "kid", "kids",
  "parent", "parents", "mom", "dad", "mother", "father",
  "stepkid", "stepkids", "stepchild", "stepchildren",
  "coparent", "co-parent", "custody",
].sort();

const NEGATION_EXAMPLES = [
  "childfree / child-free",
  "“no kids”",
  "“don’t want kids/children”",
  "“not looking for kids”",
];

function usageAndExit() {
  console.log(`Usage:
  node scripts/d3/word_graph_10_mosaic_kids_by_style_d3.mjs \\
    --in  data/charts/graphscsv/word_graph_10_kids_mentions_by_style_mosaic_counts.csv \\
    --out data/charts/d3/word_graph_10_mosaic_kids_by_style.svg
`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { inCsv: DEFAULT_IN_CSV, outSvg: DEFAULT_OUT_SVG };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--in") args.inCsv = argv[++i];
    else if (a === "--out") args.outSvg = argv[++i];
    else if (a === "-h" || a === "--help") usageAndExit();
    else {
      console.error(`Unknown arg: ${a}`);
      usageAndExit();
    }
  }
  return args;
}

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return { r, g, b };
}

function lighten(hex, factor) {
  // factor: 0 = original, 1 = white
  const { r, g, b } = hexToRgb(hex);
  const rr = Math.round(r + (255 - r) * factor);
  const gg = Math.round(g + (255 - g) * factor);
  const bb = Math.round(b + (255 - b) * factor);
  return `rgb(${rr},${gg},${bb})`;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function wrapTerms(terms, perLine = 3) {
  const lines = [];
  for (let i = 0; i < terms.length; i += perLine) {
    lines.push(terms.slice(i, i + perLine).join(", "));
  }
  return lines;
}

function main() {
  const { inCsv, outSvg } = parseArgs(process.argv);

  const raw = fs.readFileSync(inCsv, "utf-8");
  const rows = csvParse(raw);

  // Lookup (style,bucket) -> count
  const counts = new Map(); // key = `${style}||${bucket}`
  const styleTotals = new Map(); // style -> total
  for (const s of STYLE_ORDER) styleTotals.set(s, 0);

  for (const r of rows) {
    const style = String(r.datingStyle || "").trim().toLowerCase();
    const bucket = String(r.kids_bucket || "").trim();
    const count = Number(r.count || 0);

    if (!STYLE_ORDER.includes(style)) continue;
    if (!BUCKET_ORDER.includes(bucket)) continue;

    counts.set(`${style}||${bucket}`, count);
    styleTotals.set(style, (styleTotals.get(style) || 0) + count);
  }

  const grandTotal = [...styleTotals.values()].reduce((a, b) => a + b, 0);
  if (!grandTotal) throw new Error("Grand total is 0. Check your CSV.");

  // ---------- SVG layout ----------
  const W = 1200;
  const H = 650;

  const margin = { top: 80, right: 30, bottom: 40, left: 40 };
  const legendW = 320;
  const gap = 24;

  const mosaicX = margin.left;
  const mosaicY = margin.top;
  const mosaicW = W - margin.left - margin.right - legendW - gap;
  const mosaicH = H - margin.top - margin.bottom;

  const legendX = mosaicX + mosaicW + gap;
  const legendY = mosaicY;
  const legendH = mosaicH;

const fontFamily =
  `-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,Noto Sans,Liberation Sans,sans-serif`;

  // ---------- Mosaic rectangles ----------
  let x = mosaicX;
  const rects = [];
  const labels = [];

  for (const s of STYLE_ORDER) {
    const sTotal = styleTotals.get(s) || 0;
    if (!sTotal) continue;

    const colW = (sTotal / grandTotal) * mosaicW;

    const noCnt = counts.get(`${s}||No kids mention`) ?? 0;
    const yesCnt = counts.get(`${s}||Kids mention`) ?? 0;

    const noH = (noCnt / sTotal) * mosaicH;
    const yesH = (yesCnt / sTotal) * mosaicH;

    const base = STYLE_COLORS[s] || "#999999";
    const fillNo = lighten(base, 0.65);
    const fillYes = lighten(base, 0.25);

    // We'll draw from top-down visually (y decreases upwards), so compute y from top
    const yYes = mosaicY;
    const yNo = mosaicY + yesH;

    rects.push({ x, y: yYes, w: colW, h: yesH, fill: fillYes, stroke: "#000" });
    rects.push({ x, y: yNo, w: colW, h: noH, fill: fillNo, stroke: "#000" });

    labels.push({
      text: `${s} (n=${sTotal})`,
      x: x + colW / 2,
      y: mosaicY - 10,
      anchor: "middle",
      size: 16,
      weight: 600,
    });

    if (yesH > 0) {
      labels.push({
        text: `Yes\n${yesCnt} (${((yesCnt / sTotal) * 100).toFixed(1)}%)`,
        x: x + colW / 2,
        y: yYes + yesH / 2,
        anchor: "middle",
        size: 14,
        weight: 400,
        multiline: true,
      });
    }
    if (noH > 0) {
      labels.push({
        text: `No\n${noCnt} (${((noCnt / sTotal) * 100).toFixed(1)}%)`,
        x: x + colW / 2,
        y: yNo + noH / 2,
        anchor: "middle",
        size: 14,
        weight: 400,
        multiline: true,
      });
    }

    x += colW;
  }

  // ---------- Legend ----------
  const termLines = wrapTerms(KIDS_TOPIC_TERMS, 3);
  const legendLines = [
    "Style colors:",
    "• mono = cherry red",
    "• poly = marigold",
    "• any  = peach",
    "",
    "Kids-topic terms scanned:",
    "",
    ...termLines,
    "",
    "Negation phrases excluded:",
    ...NEGATION_EXAMPLES.map((l) => `• ${l}`),
    "",
    "Rule:",
    "Kids-topic words only count",
    "as YES if not negated.",
  ];

  // ---------- Compose SVG ----------
  const svg = [];
  svg.push(`<?xml version="1.0" encoding="UTF-8"?>`);
  svg.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`);

  svg.push(`<rect x="0" y="0" width="${W}" height="${H}" fill="white" />`);

  svg.push(
    `<text x="${W / 2}" y="32" text-anchor="middle" font-family="${fontFamily}" font-size="20" font-weight="700">
      ${esc("Kids mentions by dating style (mosaic)")}
    </text>`
  );
  svg.push(
    `<text x="${W / 2}" y="56" text-anchor="middle" font-family="${fontFamily}" font-size="14">
      ${esc("Negations excluded (e.g., “don’t want kids” counted as No)")}
    </text>`
  );

  for (const r of rects) {
    svg.push(
      `<rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" fill="${r.fill}" stroke="${r.stroke}" stroke-width="1" />`
    );
  }

  for (const l of labels) {
    const weight = l.weight ?? 400;
    const size = l.size ?? 14;

    if (l.multiline) {
      const parts = String(l.text).split("\n");
      svg.push(
        `<text x="${l.x}" y="${l.y}" text-anchor="${l.anchor}" font-family="${fontFamily}" font-size="${size}" font-weight="${weight}">`
      );
      const dyStart = -(parts.length - 1) * 0.6;
      parts.forEach((p, i) => {
        const dy = i === 0 ? `${dyStart}em` : `1.2em`;
        svg.push(`<tspan x="${l.x}" dy="${dy}">${esc(p)}</tspan>`);
      });
      svg.push(`</text>`);
    } else {
      svg.push(
        `<text x="${l.x}" y="${l.y}" text-anchor="${l.anchor}" font-family="${fontFamily}" font-size="${size}" font-weight="${weight}">
          ${esc(l.text)}
        </text>`
      );
    }
  }

  svg.push(
    `<rect x="${legendX}" y="${legendY}" width="${legendW}" height="${legendH}" fill="white" stroke="#000" stroke-width="1" rx="10" />`
  );

  const legendPadding = 14;
  const lineH = 18;
  let ty = legendY + legendPadding + 8;

  for (const line of legendLines) {
    svg.push(
      `<text x="${legendX + legendPadding}" y="${ty}" text-anchor="start" font-family="${fontFamily}" font-size="12">
        ${esc(line)}
      </text>`
    );
    ty += lineH;
  }

  svg.push(`</svg>`);

  fs.mkdirSync(path.dirname(outSvg), { recursive: true });
  fs.writeFileSync(outSvg, svg.join("\n"), "utf-8");

  console.log(`Wrote SVG: ${outSvg}`);
}

main();
