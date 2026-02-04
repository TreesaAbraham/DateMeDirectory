#!/usr/bin/env node
/**
 * word_graph_02_exclam_per100k_by_generation_per_profile
 *
 * Reads per-profile exclamation usage normalized per 100k words,
 * groups by generation, and renders:
 * - boxplot (Q1/median/Q3 + Tukey whiskers)
 * - jittered points per profile
 * - outliers highlighted (Tukey fences)
 *
 * Input CSV (expected columns):
 *   id,generation,exclam_per_100k  (others allowed)
 *
 * Output:
 *   data/charts/d3/svg/word_graph_02_exclam_per100k_by_generation_per_profile.svg
 */

import fs from "node:fs";
import path from "node:path";
import { Command } from "commander";
import { JSDOM } from "jsdom";
import { csvParse } from "d3-dsv";
import { select } from "d3-selection";
import { scaleBand, scaleLinear } from "d3-scale";
import { axisBottom, axisLeft } from "d3-axis";

// ---------- Defaults ----------

const REPO_ROOT = process.cwd();

const DEFAULT_IN = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_02_exclam_per100k_by_generation_per_profile.csv"
);

const DEFAULT_OUT = path.join(
  REPO_ROOT,
  "data/charts/d3/svg/word_graph_02_exclam_per100k_by_generation_per_profile.svg"
);

const TITLE = "Exclamation use by generation (per 100k words)";
const X_LABEL = "Generation";
const Y_LABEL = "Exclamation points per 100k words";

// stable order
const GEN_ORDER = ["Gen Z", "Millennial", "Gen X", "Boomer"];

// Theme (light blue everywhere)
const LIGHT_BLUE = "#7dd3fc"; // light sky blue
const THEME = {
  primary: LIGHT_BLUE,
  grid: "rgba(125, 211, 252, 0.18)",
  boxFill: "rgba(125, 211, 252, 0.12)",
  pointFill: "rgba(125, 211, 252, 0.35)",
  softText: "rgba(125, 211, 252, 0.78)",
};

// ---------- Helpers ----------

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeText(filePath, contents) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, contents, "utf8");
}

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function mustNumber(x, label) {
  const n = Number(x);
  if (!Number.isFinite(n)) throw new Error(`Non-numeric ${label}: ${x}`);
  return n;
}

function isFiniteNumber(x) {
  return typeof x === "number" && Number.isFinite(x);
}

// deterministic jitter helpers
function hashString(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function seeded01(seed) {
  // xorshift32
  let x = seed || 123456789;
  x ^= x << 13;
  x ^= x >>> 17;
  x ^= x << 5;
  return (x >>> 0) / 4294967296;
}

// quantile with linear interpolation
function quantile(sortedVals, q) {
  const n = sortedVals.length;
  if (n === 0) return NaN;
  if (q <= 0) return sortedVals[0];
  if (q >= 1) return sortedVals[n - 1];

  const pos = (n - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;

  const left = sortedVals[base];
  const right = sortedVals[Math.min(base + 1, n - 1)];
  return left + rest * (right - left);
}

function boxStats(values) {
  const vals = values.filter(isFiniteNumber).slice().sort((a, b) => a - b);
  const n = vals.length;
  if (n === 0) return null;

  const q1 = quantile(vals, 0.25);
  const med = quantile(vals, 0.5);
  const q3 = quantile(vals, 0.75);
  const iqr = q3 - q1;

  const lowFence = q1 - 1.5 * iqr;
  const highFence = q3 + 1.5 * iqr;

  // whiskers = most extreme points inside fences
  let whiskerLow = vals[0];
  let whiskerHigh = vals[n - 1];

  for (let i = 0; i < n; i++) {
    if (vals[i] >= lowFence) {
      whiskerLow = vals[i];
      break;
    }
  }
  for (let i = n - 1; i >= 0; i--) {
    if (vals[i] <= highFence) {
      whiskerHigh = vals[i];
      break;
    }
  }

  return { n, q1, med, q3, iqr, lowFence, highFence, whiskerLow, whiskerHigh, vals };
}

// ---------- Drawing ----------

function draw({ rows, outPath, width, height }) {
  const margin = { top: 70, right: 30, bottom: 80, left: 90 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // group by generation
  const byGen = new Map();
  for (const r of rows) {
    if (!r.generation || !isFiniteNumber(r.exclam_per_100k)) continue;
    if (!byGen.has(r.generation)) byGen.set(r.generation, []);
    byGen.get(r.generation).push(r);
  }

  const gens = GEN_ORDER.filter((g) => byGen.has(g)).concat(
    [...byGen.keys()].filter((g) => !GEN_ORDER.includes(g)).sort()
  );

  if (gens.length === 0) {
    throw new Error("No usable rows found. Check generation/exclam_per_100k columns.");
  }

  // stats + y domain
  const statsByGen = new Map();
  let globalMax = 0;

  for (const gen of gens) {
    const vals = byGen.get(gen).map((d) => d.exclam_per_100k);
    const st = boxStats(vals);
    if (!st) continue;
    statsByGen.set(gen, st);
    globalMax = Math.max(globalMax, st.whiskerHigh, ...st.vals);
  }

  if (!(globalMax > 0)) globalMax = 1;

  const x = scaleBand().domain(gens).range([0, innerW]).padding(0.25);
  const y = scaleLinear().domain([0, globalMax * 1.05]).range([innerH, 0]).nice();

  // DOM/SVG
  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const document = dom.window.document;

  const svg = select(document)
  .select("body")
  .append("svg")
  .attr("xmlns", "http://www.w3.org/2000/svg")
  .attr("width", width)
  .attr("height", height)
  .style(
    "font-family",
    '"DejaVu Serif", Georgia, "Times New Roman", Times, serif'
  )
  .style("font-size", "12px");

/* Background: solid black */
svg
  .append("rect")
  .attr("x", 0)
  .attr("y", 0)
  .attr("width", width)
  .attr("height", height)
  .attr("fill", "#000000");


  // Title
  svg
    .append("text")
    .attr("x", width / 2)
    .attr("y", 32)
    .attr("text-anchor", "middle")
    .attr("font-size", 18)
    .attr("font-weight", 700)
    .attr("fill", THEME.primary)
    .text(TITLE);

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  // gridlines
  g.append("g")
    .selectAll("line.gridline")
    .data(y.ticks(7))
    .join("line")
    .attr("x1", 0)
    .attr("x2", innerW)
    .attr("y1", (d) => y(d))
    .attr("y2", (d) => y(d))
    .attr("stroke", THEME.grid)
    .attr("stroke-width", 1);

  // axes
  const yAxisG = g.append("g").call(axisLeft(y).ticks(7));
  const xAxisG = g.append("g").attr("transform", `translate(0,${innerH})`).call(axisBottom(x));

  // style axes (domain line, tick lines, tick text)
  function styleAxis(axisG) {
    axisG.selectAll(".domain").attr("stroke", THEME.primary).attr("stroke-width", 1.2);
    axisG.selectAll(".tick line").attr("stroke", THEME.primary).attr("stroke-width", 1.0);
    axisG.selectAll(".tick text").attr("fill", THEME.primary);
  }
  styleAxis(yAxisG);
  styleAxis(xAxisG);

  // axis labels
  svg
    .append("text")
    .attr("x", margin.left + innerW / 2)
    .attr("y", height - 26)
    .attr("text-anchor", "middle")
    .attr("font-size", 13)
    .attr("font-weight", 600)
    .attr("fill", THEME.primary)
    .text(X_LABEL);

  svg
    .append("text")
    .attr("transform", `translate(26,${margin.top + innerH / 2}) rotate(-90)`)
    .attr("text-anchor", "middle")
    .attr("font-size", 13)
    .attr("font-weight", 600)
    .attr("fill", THEME.primary)
    .text(Y_LABEL);

  // Draw per generation
  for (const gen of gens) {
    const st = statsByGen.get(gen);
    if (!st) continue;

    const bandX = x(gen);
    const bandW = x.bandwidth();
    const cx = bandX + bandW / 2;

    const boxW = bandW * 0.55;

    // whisker line
    g.append("line")
      .attr("x1", cx)
      .attr("x2", cx)
      .attr("y1", y(st.whiskerLow))
      .attr("y2", y(st.whiskerHigh))
      .attr("stroke", THEME.primary)
      .attr("stroke-width", 1.2);

    // whisker caps
    g.append("line")
      .attr("x1", cx - boxW * 0.35)
      .attr("x2", cx + boxW * 0.35)
      .attr("y1", y(st.whiskerLow))
      .attr("y2", y(st.whiskerLow))
      .attr("stroke", THEME.primary)
      .attr("stroke-width", 1.2);

    g.append("line")
      .attr("x1", cx - boxW * 0.35)
      .attr("x2", cx + boxW * 0.35)
      .attr("y1", y(st.whiskerHigh))
      .attr("y2", y(st.whiskerHigh))
      .attr("stroke", THEME.primary)
      .attr("stroke-width", 1.2);

    // box
    g.append("rect")
      .attr("x", cx - boxW / 2)
      .attr("y", y(st.q3))
      .attr("width", boxW)
      .attr("height", Math.max(0, y(st.q1) - y(st.q3)))
      .attr("fill", THEME.boxFill)
      .attr("stroke", THEME.primary)
      .attr("stroke-width", 1.2);

    // median
    g.append("line")
      .attr("x1", cx - boxW / 2)
      .attr("x2", cx + boxW / 2)
      .attr("y1", y(st.med))
      .attr("y2", y(st.med))
      .attr("stroke", THEME.primary)
      .attr("stroke-width", 2);

    // points (with Tukey outliers)
    const pts = byGen.get(gen);
    for (const d of pts) {
      const base = hashString(`${d.id || ""}|${gen}|${d.exclam_per_100k}`);
      const r01 = seeded01(base);
      const jitter = (r01 - 0.5) * boxW * 0.95;

      const isOutlier = d.exclam_per_100k < st.lowFence || d.exclam_per_100k > st.highFence;

      g.append("circle")
        .attr("cx", cx + jitter)
        .attr("cy", y(d.exclam_per_100k))
        .attr("r", isOutlier ? 3.2 : 2.2)
        .attr("fill", isOutlier ? "none" : THEME.pointFill)
        .attr("stroke", THEME.primary)
        .attr("stroke-width", isOutlier ? 1.6 : 0.9)
        .attr("opacity", isOutlier ? 1 : 0.95);
    }

    // n label
    g.append("text")
      .attr("x", cx)
      .attr("y", innerH + 30)
      .attr("text-anchor", "middle")
      .attr("font-size", 10.5)
      .attr("fill", THEME.softText)
      .text(`n=${st.n}`);
  }

  // write SVG
  const svgText = dom.serialize().match(/<svg[\s\S]*<\/svg>/)?.[0];
  if (!svgText) throw new Error("Failed to serialize SVG.");
  writeText(outPath, svgText);
  console.log(`[ok] wrote SVG: ${outPath}`);
}

// ---------- CLI ----------

function main() {
  const program = new Command();
  program
    .option("--in <path>", "Input CSV path", DEFAULT_IN)
    .option("--out <path>", "Output SVG path", DEFAULT_OUT)
    .option("--width <n>", "SVG width", (v) => mustNumber(v, "width"), 1150)
    .option("--height <n>", "SVG height", (v) => mustNumber(v, "height"), 620);

  program.parse(process.argv);
  const opts = program.opts();

  const inPath = path.resolve(opts.in);
  const outPath = path.resolve(opts.out);

  if (!fs.existsSync(inPath)) {
    throw new Error(`CSV not found: ${inPath}`);
  }

  const raw = readText(inPath);
  const df = csvParse(raw);

  const rows = df
    .map((d) => ({
      id: (d.id ?? "").trim(),
      generation: (d.generation ?? "").trim(),
      exclam_per_100k: Number(d.exclam_per_100k),
    }))
    .filter((d) => d.generation && Number.isFinite(d.exclam_per_100k));

  draw({ rows, outPath, width: opts.width, height: opts.height });
}

main();
