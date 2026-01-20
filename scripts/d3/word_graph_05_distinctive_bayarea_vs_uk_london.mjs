#!/usr/bin/env node
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

function ensureDir(p) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
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
        z: -Math.abs(uz),
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
    textColor,
    axisColor,
  } = opts;

  const ordered = data
    .slice()
    .sort((a, b) => (a.rank - b.rank) || (a.side === "Bay Area" ? -1 : 1));

  const height = marginTop + marginBottom + ordered.length * rowH;

  const maxAbs = d3.max(ordered, (d) => Math.abs(d.z)) ?? 1;
  const x = d3
    .scaleLinear()
    .domain([-maxAbs, maxAbs])
    .range([marginLeft, width - marginRight])
    .nice();

  const yMid = (_d, i) => marginTop + i * rowH + rowH / 2;

  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const body = d3.select(dom.window.document).select("body");

  const svg = body
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 28)
    .attr("fill", textColor)
    .attr("font-size", 18)
    .attr("font-weight", 700)
    .text(title);

  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 48)
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text(subtitle);

  svg
    .append("line")
    .attr("x1", x(0))
    .attr("x2", x(0))
    .attr("y1", marginTop - 6)
    .attr("y2", height - marginBottom)
    .attr("stroke", axisColor)
    .attr("stroke-width", 1)
    .attr("opacity", 0.8);

  const axis = d3.axisBottom(x).ticks(6);
  const axisG = svg
    .append("g")
    .attr("transform", `translate(0, ${height - marginBottom + 6})`)
    .call(axis);

  axisG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  axisG.selectAll("text").attr("fill", textColor).attr("font-size", 11);

  svg
    .append("g")
    .selectAll("rect")
    .data(ordered)
    .join("rect")
    .attr("x", (d) => Math.min(x(0), x(d.z)))
    .attr("y", (_d, i) => marginTop + i * rowH + 6)
    .attr("width", (d) => Math.abs(x(d.z) - x(0)))
    .attr("height", rowH - 12)
    .attr("rx", 3)
    .attr("fill", (d) => (d.side === "Bay Area" ? rightColor : leftColor))
    .attr("opacity", 0.9);

  svg
    .append("g")
    .selectAll("text.word")
    .data(ordered)
    .join("text")
    .attr("x", (d) => (d.side === "Bay Area" ? x(d.z) + 6 : x(d.z) - 6))
    .attr("y", (_d, i) => yMid(_d, i) + 4)
    .attr("text-anchor", (d) => (d.side === "Bay Area" ? "start" : "end"))
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("font-weight", 600)
    .text((d) => d.word);

  svg
    .append("g")
    .selectAll("text.val")
    .data(ordered)
    .join("text")
    .attr("x", (d) => (d.side === "Bay Area" ? x(0) - 6 : x(0) + 6))
    .attr("y", (_d, i) => yMid(_d, i) + 4)
    .attr("text-anchor", (d) => (d.side === "Bay Area" ? "end" : "start"))
    .attr("fill", textColor)
    .attr("font-size", 11)
    .attr("opacity", 0.9)
    .text((d) => d3.format(".2f")(d.z));

  svg
    .append("text")
    .attr("x", x(maxAbs))
    .attr("y", marginTop - 12)
    .attr("text-anchor", "end")
    .attr("fill", rightColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text("Bay Area distinctive (+z)");

  svg
    .append("text")
    .attr("x", x(-maxAbs))
    .attr("y", marginTop - 12)
    .attr("text-anchor", "start")
    .attr("fill", leftColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text("UK/London distinctive (−z)");

  return body.html();
}

async function maybeWritePng(svgPath, pngPath) {
  try {
    const { default: sharp } = await import("sharp");
    const svgBuf = fs.readFileSync(svgPath);
    ensureDir(pngPath);
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
    width: 980,
    rowH: 26,
    marginTop: 80,
    marginRight: 40,
    marginBottom: 42,
    marginLeft: 40,
    title: args.title ?? "Most distinctive words: SF Bay Area vs UK/London",
    subtitle: `Top ${topN} per side. Bars are z-scores (Bay positive, UK negative).`,
    leftColor: "#B84CF0",   // UK/London
    rightColor: "#2F6FED",  // Bay Area
    textColor: "#EAEAEA",
    axisColor: "#EAEAEA",
  });

  ensureDir(outPath);
  fs.writeFileSync(outPath, svgText, "utf8");
  console.log(`[out] ${outPath}`);

  if (args.png || args.outPng) {
    await maybeWritePng(outPath, outPngPath);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
