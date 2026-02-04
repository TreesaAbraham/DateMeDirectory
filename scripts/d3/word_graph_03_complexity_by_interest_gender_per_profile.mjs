#!/usr/bin/env node
/**
 * word_graph_03_complexity_by_interest_gender_per_profile.mjs
 *
 * Input CSV columns:
 *   id,source_gender,target_gender,word_count,complex_pct,interestedIn_raw
 *
 * Output SVGs:
 *   data/charts/d3/svg/word_graph_03_word_complexity_looking_for_M.svg
 *   data/charts/d3/svg/word_graph_03_word_complexity_looking_for_F.svg
 *   data/charts/d3/svg/word_graph_03_word_complexity_looking_for_NB.svg
 *
 * Chart meaning:
 *   For each target_gender (M/F/NB), aggregate complex_pct by source_gender (M/F/NB),
 *   then draw a bar chart of mean word complexity (%).
 *
 * Default aggregation: weighted mean by word_count
 *   sum(complex_pct * word_count) / sum(word_count)
 *
 * CLI:
 *   node scripts/d3/word_graph_03_complexity_by_interest_gender_per_profile.mjs
 *   node ... --in path/to.csv --outdir data/charts/d3/svg
 *   node ... --unweighted
 *   node ... --textColor red
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { JSDOM } from "jsdom";
import { csvParse } from "d3-dsv";
import { select } from "d3-selection";
import { scaleBand, scaleLinear } from "d3-scale";
import { axisLeft, axisBottom } from "d3-axis";
import { max } from "d3-array";
import { format } from "d3-format";

// ---------------- Paths ----------------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..", "..");

const DEFAULT_IN = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_03_complexity_by_interest_gender_per_profile.csv"
);
const DEFAULT_OUTDIR = path.join(REPO_ROOT, "data/charts/d3/svg");

// ---------------- Args ----------------
function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) out[key] = true;
    else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

const args = parseArgs(process.argv);

const inPath = args.in ? path.resolve(args.in) : DEFAULT_IN;
const outDir = args.outdir ? path.resolve(args.outdir) : DEFAULT_OUTDIR;

const USE_WEIGHTED = args.unweighted ? false : true;

// ---- Styling defaults (your request) ----
const BG_COLOR = args.bgColor ?? "#000000"; // black background
const TEXT_COLOR = args.textColor ?? "#EDEDED"; // light text on black
const AXIS_COLOR = args.axisColor ?? "rgba(237,237,237,0.55)";
const GRID_COLOR = args.gridColor ?? "rgba(237,237,237,0.12)";

// serif text
const FONT_FAMILY =
  args.fontFamily ?? 'ui-serif, Georgia, "Times New Roman", Times, serif';

// Order and labels
const SOURCE_ORDER = ["M", "F", "NB"];
const TARGETS = ["M", "F", "NB"];

const LABEL = {
  M: "Men",
  F: "Women",
  NB: "Non-binary",
};

// Per-chart colors
const TARGET_COLOR = {
  M: "#2563EB", // blue
  F: "#e20093ff", // fuchsia
  NB: "#7C3AED", // purple
};

// --- Responsive embed + anti-clipping padding (same idea as Graph 01) ---
const VB_PAD_X = Number(args.vbPadX ?? 70); // left/right breathing room
const VB_PAD_Y = Number(args.vbPadY ?? 40); // top/bottom breathing room

// ---------------- Helpers ----------------
function normGender(g) {
  if (!g) return null;
  const s = String(g).trim().toUpperCase();
  if (s === "M" || s === "MALE" || s === "MAN") return "M";
  if (s === "F" || s === "FEMALE" || s === "WOMAN") return "F";
  if (s === "NB" || s === "NONBINARY" || s === "NON-BINARY") return "NB";
  return null;
}

function toNumber(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

function clampPct(x) {
  if (x == null) return null;
  if (x < 0) return 0;
  if (x > 100) return 100;
  return x;
}

async function readCsv(p) {
  const raw = await fs.readFile(p, "utf-8");
  const rows = csvParse(raw);

  const required = new Set([
    "id",
    "source_gender",
    "target_gender",
    "word_count",
    "complex_pct",
  ]);

  for (const col of required) {
    if (!rows.columns.includes(col)) {
      throw new Error(
        `Missing required column "${col}". Found: ${rows.columns.join(", ")}`
      );
    }
  }

  const cleaned = rows
    .map((r) => {
      const id = String(r.id ?? "").trim();
      const source = normGender(r.source_gender);
      const target = normGender(r.target_gender);
      const wordCount = toNumber(r.word_count);
      const pct = clampPct(toNumber(r.complex_pct));

      if (!id || !source || !target || wordCount == null || pct == null)
        return null;
      if (wordCount <= 0) return null;

      return {
        id,
        source_gender: source,
        target_gender: target,
        word_count: wordCount,
        complex_pct: pct,
      };
    })
    .filter(Boolean);

  return cleaned;
}

function aggregateForTarget(rows, target) {
  const subset = rows.filter((d) => d.target_gender === target);

  // Group by source_gender
  const bySource = new Map();
  for (const d of subset) {
    if (!bySource.has(d.source_gender)) {
      bySource.set(d.source_gender, {
        n: 0,
        sumPct: 0,
        sumW: 0,
        sumPctW: 0,
      });
    }
    const g = bySource.get(d.source_gender);
    g.n += 1;
    g.sumPct += d.complex_pct;
    g.sumW += d.word_count;
    g.sumPctW += d.complex_pct * d.word_count;
  }

  // Ensure all categories exist in output (stable ordering)
  return SOURCE_ORDER.map((sg) => {
    const g = bySource.get(sg);
    if (!g) {
      return {
        source_gender: sg,
        value: 0,
        n: 0,
        total_words: 0,
      };
    }
    const value = USE_WEIGHTED ? g.sumPctW / g.sumW : g.sumPct / g.n;
    return {
      source_gender: sg,
      value,
      n: g.n,
      total_words: g.sumW,
    };
  });
}

function svgToString(document) {
  const svg = document.querySelector("svg");
  const markup = svg.outerHTML;
  return `<?xml version="1.0" encoding="UTF-8"?>\n${markup}\n`;
}

// ---------------- Drawing ----------------
function drawBarChart({ data, target }) {
  // Layout
  const width = 900;
  const height = 520;
  const margin = { top: 90, right: 40, bottom: 70, left: 80 };

  const barColor = TARGET_COLOR[target] ?? "#888";

  const dom = new JSDOM(`<!DOCTYPE html><body></body>`);
  const document = dom.window.document;

  // Responsive SVG + padded viewBox to avoid clipping when embedded as <img>
  const vbX = -VB_PAD_X;
  const vbY = -VB_PAD_Y;
  const vbW = width + VB_PAD_X * 2;
  const vbH = height + VB_PAD_Y * 2;

  const svg = select(document.body)
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `${vbX} ${vbY} ${vbW} ${vbH}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("style", "max-width: 100%; height: auto; display: block;")
    .style("font-family", FONT_FAMILY)
    .style("font-size", "12px");

  // Background: use a rect (reliable for SVG-in-IMG), covering the *padded* viewBox
  svg
    .append("rect")
    .attr("x", vbX)
    .attr("y", vbY)
    .attr("width", vbW)
    .attr("height", vbH)
    .attr("fill", BG_COLOR);

  const title = `Word complexity (%) by profile gender`;
  const subtitle = `Looking for ${LABEL[target]} • ${
    USE_WEIGHTED ? "weighted by word_count" : "unweighted mean"
  }`;

  const nTotal = data.reduce((acc, d) => acc + d.n, 0);

  svg
    .append("text")
    .attr("x", margin.left)
    .attr("y", 34)
    .attr("font-size", 24)
    .attr("font-weight", 700)
    .attr("fill", barColor)
    .text(title);

  svg
    .append("text")
    .attr("x", margin.left)
    .attr("y", 60)
    .attr("font-size", 14)
    .attr("fill", TEXT_COLOR)
    .attr("opacity", 0.92)
    .text(subtitle);

  svg
    .append("text")
    .attr("x", width - margin.right)
    .attr("y", 34)
    .attr("text-anchor", "end")
    .attr("font-size", 12)
    .attr("fill", TEXT_COLOR)
    .attr("opacity", 0.85)
    .text(`n=${nTotal}`);

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const yMax = max(data, (d) => d.value) ?? 0;
  const yTop = Math.max(5, yMax * 1.15);

  const x = scaleBand().domain(SOURCE_ORDER).range([0, innerW]).padding(0.25);
  const y = scaleLinear().domain([0, yTop]).range([innerH, 0]);

  // Gridlines (subtle)
  g.append("g")
    .selectAll("line.grid")
    .data(y.ticks(6))
    .join("line")
    .attr("class", "grid")
    .attr("x1", 0)
    .attr("x2", innerW)
    .attr("y1", (d) => y(d))
    .attr("y2", (d) => y(d))
    .attr("stroke", GRID_COLOR)
    .attr("stroke-width", 1);

  // Axes
  const yAxis = axisLeft(y).ticks(6).tickFormat(format(".0f"));
  const xAxis = axisBottom(x).tickFormat((d) => LABEL[d] ?? d);

  g.append("g")
    .call(yAxis)
    .call((sel) =>
      sel.selectAll("text").attr("fill", TEXT_COLOR).attr("opacity", 0.9)
    )
    .call((sel) =>
      sel.selectAll("path,line").attr("stroke", AXIS_COLOR).attr("opacity", 1)
    );

  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(xAxis)
    .call((sel) =>
      sel.selectAll("text").attr("fill", TEXT_COLOR).attr("opacity", 0.9)
    )
    .call((sel) =>
      sel.selectAll("path,line").attr("stroke", AXIS_COLOR).attr("opacity", 1)
    );

  // Y label
  svg
    .append("text")
    .attr("x", 18)
    .attr("y", margin.top + innerH / 2)
    .attr("transform", `rotate(-90, 18, ${margin.top + innerH / 2})`)
    .attr("font-size", 13)
    .attr("fill", TEXT_COLOR)
    .attr("opacity", 0.95)
    .text("Word complexity (%)");

  // Bars
  const fmt1 = format(".1f");

  g.append("g")
    .selectAll("rect.bar")
    .data(data)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => x(d.source_gender))
    .attr("y", (d) => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.value))
    .attr("fill", barColor)
    .attr("opacity", (d) => (d.n === 0 ? 0.25 : 0.92));

  // Value labels
  g.append("g")
    .selectAll("text.value")
    .data(data)
    .join("text")
    .attr("class", "value")
    .attr("x", (d) => x(d.source_gender) + x.bandwidth() / 2)
    .attr("y", (d) => y(d.value) - 10)
    .attr("text-anchor", "middle")
    .attr("font-size", 14)
    .attr("font-weight", 700)
    .attr("fill", TEXT_COLOR)
    .text((d) => (d.n === 0 ? "–" : fmt1(d.value)));

  // n labels under bars
  g.append("g")
    .selectAll("text.n")
    .data(data)
    .join("text")
    .attr("class", "n")
    .attr("x", (d) => x(d.source_gender) + x.bandwidth() / 2)
    .attr("y", innerH + 42)
    .attr("text-anchor", "middle")
    .attr("font-size", 12)
    .attr("fill", TEXT_COLOR)
    .attr("opacity", 0.9)
    .text((d) => `n=${d.n}`);

  return { document };
}

// ---------------- Main ----------------
async function main() {
  // Existence checks
  try {
    await fs.access(inPath);
  } catch {
    throw new Error(`CSV not found: ${inPath}`);
  }

  await fs.mkdir(outDir, { recursive: true });

  const rows = await readCsv(inPath);

  if (rows.length === 0) {
    throw new Error("No usable rows after cleaning. Check CSV contents/types.");
  }

  for (const target of TARGETS) {
    const agg = aggregateForTarget(rows, target);

    const { document } = drawBarChart({ data: agg, target });

    const outPath = path.join(
      outDir,
      `word_graph_03_word_complexity_looking_for_${target}.svg`
    );

    await fs.writeFile(outPath, svgToString(document), "utf-8");
    console.log(`[wrote] ${outPath}`);
  }

  console.log(
    `[done] charts=3 | aggregation=${
      USE_WEIGHTED ? "weighted(word_count)" : "unweighted"
    }`
  );
}

main().catch((err) => {
  console.error(String(err?.stack ?? err));
  process.exit(1);
});
