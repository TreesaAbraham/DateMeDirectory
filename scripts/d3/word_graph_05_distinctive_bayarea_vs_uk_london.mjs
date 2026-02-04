#!/usr/bin/env node
/**
 * word_graph_05_distinctive_bayarea_vs_uk_london.mjs
 *
 * Input CSV:
 *   rank,BAY_AREA_word,BAY_AREA_count,BAY_AREA_z,UK_word,UK_count,UK_z
 *
 * Output SVG:
 *   data/charts/d3/svg/word_graph_05_distinctive_bayarea_vs_uk_london.svg
 *
 * Optional PNG (if sharp installed):
 *   data/charts/d3/png/word_graph_05_distinctive_bayarea_vs_uk_london.png
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as d3 from "d3";
import { JSDOM } from "jsdom";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const DEFAULT_IN = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_05_distinctive_bayarea_vs_uk_london.csv"
);

const DEFAULT_OUT = path.join(
  REPO_ROOT,
  "data/charts/d3/svg/word_graph_05_distinctive_bayarea_vs_uk_london.svg"
);

const DEFAULT_OUT_PNG = path.join(
  REPO_ROOT,
  "data/charts/d3/png/word_graph_05_distinctive_bayarea_vs_uk_london.png"
);

// Padded viewBox so edge labels don't get clipped in embeds
const VB_PAD_X = 140; // left/right breathing room
const VB_PAD_Y = 60;  // top/bottom breathing room

function ensureDirForFile(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function readCsvOrDie(inPath) {
  if (!fs.existsSync(inPath)) throw new Error(`CSV not found: ${inPath}`);
  return fs.readFileSync(inPath, "utf8");
}

// Tiny CLI parser: --key value, plus boolean flags like --png
function parseArgs(argv) {
  const out = { top: 20, png: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);

    if (key === "png") {
      out.png = true;
      continue;
    }

    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      out[key] = next;
      i++;
    } else {
      out[key] = true;
    }
  }
  if (out.top != null) out.top = Number(out.top) || 20;
  return out;
}

function parseRows(csvText) {
  const rows = d3.csvParse(csvText);
  return rows
    .map((r) => ({
      rank: Number(r.rank),
      bay_word: String(r.BAY_AREA_word ?? "").trim(),
      bay_count: Number(r.BAY_AREA_count),
      bay_z: Number(r.BAY_AREA_z),
      uk_word: String(r.UK_word ?? "").trim(),
      uk_count: Number(r.UK_count),
      uk_z: Number(r.UK_z),
    }))
    .filter((r) => Number.isFinite(r.rank))
    .sort((a, b) => a.rank - b.rank);
}

function buildLong(rows, topN) {
  const sliced = rows.slice(0, topN);
  const long = [];

  for (const r of sliced) {
    if (r.bay_word) {
      long.push({
        side: "Bay Area",
        word: r.bay_word,
        count: r.bay_count,
        z: Number.isFinite(r.bay_z) ? r.bay_z : 0,
        rank: r.rank,
      });
    }
    if (r.uk_word) {
      const uz = Number.isFinite(r.uk_z) ? r.uk_z : 0;
      long.push({
        side: "UK/London",
        word: r.uk_word,
        count: r.uk_count,
        z: -Math.abs(uz), // force negative to the left
        rank: r.rank,
      });
    }
  }
  return long;
}

function renderSvg(data, opts) {
  const {
    width,
    rowH,
    marginTop,
    marginRight,
    marginBottom,
    marginLeft,
    title,
    subtitle,
    leftColor,
    rightColor,
    bgColor,
    textColor,
    axisColor,
    mutedText,
    fontFamily,
  } = opts;

  const ordered = data
    .slice()
    .sort((a, b) => (a.rank - b.rank) || (a.side === "Bay Area" ? -1 : 1));

  const height = marginTop + marginBottom + ordered.length * rowH;

  const maxAbs = d3.max(ordered, (d) => Math.abs(d.z)) ?? 1;
  const bound = Math.max(1, maxAbs) * 1.12;

  const x = d3
    .scaleLinear()
    .domain([-bound, bound])
    .range([marginLeft, width - marginRight])
    .nice();

  const yMid = (_d, i) => marginTop + i * rowH + rowH / 2;

  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const document = dom.window.document;
  const body = d3.select(document).select("body");

  const svg = body
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")

    // Keep natural size for export…
    .attr("width", width)
    .attr("height", height)

    // …but make it responsive + padded when embedded
    .attr(
      "viewBox",
      `${-VB_PAD_X} ${-VB_PAD_Y} ${width + VB_PAD_X * 2} ${height + VB_PAD_Y * 2}`
    )
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("style", "max-width: 100%; height: auto; display: block;")

    .style("font-family", fontFamily)
    .style("font-size", "12px");

  // Background covers the *entire padded viewBox*
  svg
    .append("rect")
    .attr("x", -VB_PAD_X)
    .attr("y", -VB_PAD_Y)
    .attr("width", width + VB_PAD_X * 2)
    .attr("height", height + VB_PAD_Y * 2)
    .attr("fill", bgColor);

  // Title
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 32)
    .attr("fill", textColor)
    .attr("font-size", 18)
    .attr("font-weight", 800)
    .text(title);

  // Subtitle
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 54)
    .attr("fill", textColor)
    .attr("font-size", 12.5)
    .attr("opacity", 0.9)
    .text(subtitle);

  // Side headers
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", marginTop - 14)
    .attr("text-anchor", "start")
    .attr("fill", leftColor)
    .attr("font-size", 12.5)
    .attr("font-weight", 800)
    .text("UK/London distinctive (−z)");

  svg
    .append("text")
    .attr("x", width - marginRight)
    .attr("y", marginTop - 14)
    .attr("text-anchor", "end")
    .attr("fill", rightColor)
    .attr("font-size", 12.5)
    .attr("font-weight", 800)
    .text("Bay Area distinctive (+z)");

  // Zero line
  svg
    .append("line")
    .attr("x1", x(0))
    .attr("x2", x(0))
    .attr("y1", marginTop - 6)
    .attr("y2", height - marginBottom + 2)
    .attr("stroke", axisColor)
    .attr("stroke-width", 1.4)
    .attr("opacity", 0.9);

  // Bottom axis
  const axis = d3.axisBottom(x).ticks(6).tickFormat(d3.format(".1f"));
  const axisG = svg
    .append("g")
    .attr("transform", `translate(0, ${height - marginBottom + 12})`)
    .call(axis);

  axisG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.75);
  axisG.selectAll("text").attr("fill", mutedText).attr("font-size", 11);

  // Bars
  svg
    .append("g")
    .selectAll("rect.bar")
    .data(ordered)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => Math.min(x(0), x(d.z)))
    .attr("y", (_d, i) => marginTop + i * rowH + 6)
    .attr("width", (d) => Math.abs(x(d.z) - x(0)))
    .attr("height", rowH - 12)
    .attr("rx", 3)
    .attr("ry", 3)
    .attr("fill", (d) => (d.side === "Bay Area" ? rightColor : leftColor))
    .attr("opacity", 0.92);

  // Word labels (outside bar ends)
  svg
    .append("g")
    .selectAll("text.word")
    .data(ordered)
    .join("text")
    .attr("class", "word")
    .attr("x", (d) => (d.side === "Bay Area" ? x(d.z) + 8 : x(d.z) - 8))
    .attr("y", (_d, i) => yMid(_d, i) + 4)
    .attr("text-anchor", (d) => (d.side === "Bay Area" ? "start" : "end"))
    .attr("fill", textColor)
    .attr("font-size", 12.2)
    .attr("font-weight", 650)
    .text((d) => d.word);

  // Value labels near center
  const fmt = d3.format(".2f");
  svg
    .append("g")
    .selectAll("text.val")
    .data(ordered)
    .join("text")
    .attr("class", "val")
    .attr("x", (d) => (d.side === "Bay Area" ? x(0) - 8 : x(0) + 8))
    .attr("y", (_d, i) => yMid(_d, i) + 4)
    .attr("text-anchor", (d) => (d.side === "Bay Area" ? "end" : "start"))
    .attr("fill", mutedText)
    .attr("font-size", 11)
    .attr("opacity", 0.95)
    .text((d) => fmt(d.z));

  // Axis label
  svg
    .append("text")
    .attr("x", marginLeft + (width - marginLeft - marginRight) / 2)
    .attr("y", height - 14)
    .attr("text-anchor", "middle")
    .attr("fill", mutedText)
    .attr("font-size", 12)
    .text("Z-score (distinctiveness)");

  // Return just the SVG markup
  const svgNode = document.querySelector("svg");
  return `<?xml version="1.0" encoding="UTF-8"?>\n${svgNode.outerHTML}\n`;
}

async function maybeWritePng(svgPath, pngPath) {
  try {
    const { default: sharp } = await import("sharp");
    const svgBuf = fs.readFileSync(svgPath);
    ensureDirForFile(pngPath);
    await sharp(svgBuf).png().toFile(pngPath);
    console.log(`[out] ${pngPath}`);
  } catch {
    console.log("[note] PNG skipped (install `sharp` if you want PNG output).");
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const inPath = args.in ? path.resolve(args.in) : DEFAULT_IN;
  const outPath = args.out ? path.resolve(args.out) : DEFAULT_OUT;
  const outPngPath = args.outPng ? path.resolve(args.outPng) : DEFAULT_OUT_PNG;

  const topN = args.top ?? 20;

  const csvText = readCsvOrDie(inPath);
  const rows = parseRows(csvText);
  const long = buildLong(rows, topN);

  const svgText = renderSvg(long, {
    width: Number(args.width ?? 980),
    rowH: Number(args.rowH ?? 26),
    marginTop: Number(args.marginTop ?? 92),
    marginRight: Number(args.marginRight ?? 70),
    marginBottom: Number(args.marginBottom ?? 54),
    marginLeft: Number(args.marginLeft ?? 70),

    title: args.title ?? "Most distinctive words: SF Bay Area vs UK/London",
    subtitle:
      args.subtitle ??
      `Top ${topN} per side. Bars are z-scores (Bay positive, UK negative).`,

    // Colors + styling (match the “dark site” look)
    bgColor: args.bgColor ?? "#000000",
    textColor: args.textColor ?? "#FFFFFF",
    mutedText: args.mutedText ?? "rgba(255,255,255,0.75)",
    axisColor: args.axisColor ?? "rgba(255,255,255,0.55)",

    leftColor: args.leftColor ?? "#B84CF0",  // UK/London
    rightColor: args.rightColor ?? "#2F6FED", // Bay Area

    fontFamily:
      args.fontFamily ??
      'ui-serif, Georgia, "Times New Roman", Times, serif',
  });

  ensureDirForFile(outPath);
  fs.writeFileSync(outPath, svgText, "utf8");
  console.log(`[out] ${outPath}`);

  if (args.png || args.outPng) {
    await maybeWritePng(outPath, outPngPath);
  }
}

main().catch((e) => {
  console.error(e?.stack ?? String(e));
  process.exit(1);
});
