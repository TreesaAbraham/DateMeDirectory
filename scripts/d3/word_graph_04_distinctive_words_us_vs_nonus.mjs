#!/usr/bin/env node
/**
 * word_graph_04_distinctive_words_us_vs_nonus.mjs
 *
 * Input CSV columns:
 *   rank,US_word,US_count,US_z,NON_US_word,NON_US_count,NON_US_z
 *
 * Output SVG:
 *   data/charts/d3/svg/word_graph_04_distinctive_words_us_vs_nonus.svg
 *
 * Chart:
 *   Diverging bar chart of z-scores:
 *     - NON_US_z to the left (negative)
 *     - US_z to the right (positive)
 *   Labels show the word on each side.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { JSDOM } from "jsdom";
import { csvParse } from "d3-dsv";
import { select } from "d3-selection";
import { scaleLinear, scaleBand } from "d3-scale";
import { axisBottom } from "d3-axis";
import { max, min } from "d3-array";
import { format } from "d3-format";

// -------- paths --------
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..", "..");

const DEFAULT_IN = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_04_distinctive_us_vs_nonus.csv"
);

const DEFAULT_OUT = path.join(
  REPO_ROOT,
  "data/charts/d3/svg/word_graph_04_distinctive_words_us_vs_nonus.svg"
);

// -------- args --------
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
const outPath = args.out ? path.resolve(args.out) : DEFAULT_OUT;

// -------- style (match SF vs Bay/UK look) --------
const BG_COLOR = args.bgColor ?? "#121212";
const TEXT_COLOR = args.textColor ?? "rgba(255,255,255,0.92)";
const MUTED_TEXT = args.mutedText ?? "rgba(255,255,255,0.65)";
const GRID_COLOR = args.gridColor ?? "rgba(255,255,255,0.18)";
const GRID_OPACITY = args.gridOpacity ? Number(args.gridOpacity) : 1;

const US_COLOR = args.usColor ?? "#3b82f6";       // bright blue
const NONUS_COLOR = args.nonUsColor ?? "#a855f7"; // purple

const FONT_FAMILY =
  args.fontFamily ?? 'ui-serif, Georgia, "Times New Roman", Times, serif';

function toNum(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : null;
}

async function readCsv(p) {
  const raw = await fs.readFile(p, "utf-8");
  const rows = csvParse(raw);

  const required = [
    "rank",
    "US_word",
    "US_count",
    "US_z",
    "NON_US_word",
    "NON_US_count",
    "NON_US_z",
  ];
  for (const c of required) {
    if (!rows.columns.includes(c)) {
      throw new Error(`Missing required column "${c}". Found: ${rows.columns.join(", ")}`);
    }
  }

  const cleaned = rows
    .map((r) => {
      const rank = toNum(r.rank);
      const usWord = String(r.US_word ?? "").trim();
      const nonWord = String(r.NON_US_word ?? "").trim();
      const usZ = toNum(r.US_z);
      const nonZ = toNum(r.NON_US_z);

      if (rank == null || !usWord || !nonWord || usZ == null || nonZ == null) return null;

      return {
        rank,
        usWord,
        nonWord,
        usZ,
        nonZ,
        usCount: toNum(r.US_count) ?? null,
        nonCount: toNum(r.NON_US_count) ?? null,
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.rank - b.rank);

  if (cleaned.length === 0) throw new Error("No usable rows after cleaning.");
  return cleaned;
}

function svgToString(document) {
  const svg = document.querySelector("svg");
  return `<?xml version="1.0" encoding="UTF-8"?>\n${svg.outerHTML}\n`;
}

function draw(rows) {
  // layout: more generous like your screenshot
  const rowH = 26;
  const topPad = 84;
  const bottomPad = 54;
  const height = topPad + bottomPad + rows.length * rowH;

  const width = 980;
  const margin = { top: topPad, right: 70, bottom: bottomPad, left: 70 };

  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // symmetric x domain around 0
  const minZ = min(rows, (d) => d.nonZ) ?? -1;
  const maxZ = max(rows, (d) => d.usZ) ?? 1;
  const bound = Math.max(Math.abs(minZ), Math.abs(maxZ)) * 1.12;

  const x = scaleLinear().domain([-bound, bound]).range([0, innerW]);

  const y = scaleBand()
    .domain(rows.map((d) => String(d.rank)))
    .range([0, innerH])
    .paddingInner(0.34);

  const dom = new JSDOM(`<!DOCTYPE html><body></body>`);
  const document = dom.window.document;

  const svg = select(document.body)
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", BG_COLOR)
    .style("font-family", FONT_FAMILY)
    .style("fill", TEXT_COLOR);

  // Side headers like the screenshot
  svg
    .append("text")
    .attr("x", margin.left)
    .attr("y", 30)
    .attr("font-size", 14)
    .attr("font-weight", 700)
    .attr("fill", NONUS_COLOR)
    .text("Non-US distinctive (−z)");

  svg
    .append("text")
    .attr("x", width - margin.right)
    .attr("y", 30)
    .attr("text-anchor", "end")
    .attr("font-size", 14)
    .attr("font-weight", 700)
    .attr("fill", US_COLOR)
    .text("US distinctive (+z)");

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  // gridlines
  const ticks = x.ticks(6);
  g.append("g")
    .selectAll("line.grid")
    .data(ticks)
    .join("line")
    .attr("class", "grid")
    .attr("x1", (d) => x(d))
    .attr("x2", (d) => x(d))
    .attr("y1", 0)
    .attr("y2", innerH)
    .attr("stroke", GRID_COLOR)
    .attr("opacity", GRID_OPACITY);

  // zero line (stronger)
  g.append("line")
    .attr("x1", x(0))
    .attr("x2", x(0))
    .attr("y1", 0)
    .attr("y2", innerH)
    .attr("stroke", "rgba(255,255,255,0.55)")
    .attr("stroke-width", 1.4);

  // Bars: Non-US (negative)
  g.append("g")
    .selectAll("rect.nonus")
    .data(rows)
    .join("rect")
    .attr("class", "nonus")
    .attr("x", (d) => x(Math.min(0, d.nonZ)))
    .attr("y", (d) => y(String(d.rank)))
    .attr("width", (d) => Math.abs(x(d.nonZ) - x(0)))
    .attr("height", y.bandwidth())
    .attr("rx", 3)
    .attr("ry", 3)
    .attr("fill", NONUS_COLOR)
    .attr("opacity", 0.92);

  // Bars: US (positive)
  g.append("g")
    .selectAll("rect.us")
    .data(rows)
    .join("rect")
    .attr("class", "us")
    .attr("x", x(0))
    .attr("y", (d) => y(String(d.rank)))
    .attr("width", (d) => Math.abs(x(d.usZ) - x(0)))
    .attr("height", y.bandwidth())
    .attr("rx", 3)
    .attr("ry", 3)
    .attr("fill", US_COLOR)
    .attr("opacity", 0.92);

  // Words on bars (white, bold-ish)
  g.append("g")
    .selectAll("text.wordLeft")
    .data(rows)
    .join("text")
    .attr("class", "wordLeft")
    .attr("x", (d) => x(d.nonZ) - 8)
    .attr("y", (d) => y(String(d.rank)) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", "end")
    .attr("font-size", 12.2)
    .attr("font-weight", 650)
    .attr("fill", TEXT_COLOR)
    .text((d) => d.nonWord);

  g.append("g")
    .selectAll("text.wordRight")
    .data(rows)
    .join("text")
    .attr("class", "wordRight")
    .attr("x", (d) => x(d.usZ) + 8)
    .attr("y", (d) => y(String(d.rank)) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", "start")
    .attr("font-size", 12.2)
    .attr("font-weight", 650)
    .attr("fill", TEXT_COLOR)
    .text((d) => d.usWord);

  // z-score labels near center, small + muted (like screenshot)
  const fmt = format(".2f");

  g.append("g")
    .selectAll("text.zLeft")
    .data(rows)
    .join("text")
    .attr("class", "zLeft")
    .attr("x", (d) => x(0) - 8)
    .attr("y", (d) => y(String(d.rank)) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", "end")
    .attr("font-size", 11)
    .attr("fill", MUTED_TEXT)
    .text((d) => fmt(d.nonZ));

  g.append("g")
    .selectAll("text.zRight")
    .data(rows)
    .join("text")
    .attr("class", "zRight")
    .attr("x", (d) => x(0) + 8)
    .attr("y", (d) => y(String(d.rank)) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", "start")
    .attr("font-size", 11)
    .attr("fill", MUTED_TEXT)
    .text((d) => fmt(d.usZ));

  // bottom axis (subtle)
  const axis = axisBottom(x).ticks(6).tickFormat(format(".1f"));
  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(axis)
    .call((sel) => sel.selectAll("text").attr("fill", MUTED_TEXT))
    .call((sel) =>
      sel.selectAll("path,line").attr("stroke", "rgba(255,255,255,0.28)").attr("opacity", 1)
    );

  // axis label
  svg
    .append("text")
    .attr("x", margin.left + innerW / 2)
    .attr("y", height - 18)
    .attr("text-anchor", "middle")
    .attr("font-size", 12)
    .attr("fill", MUTED_TEXT)
    .text("Z-score (distinctiveness)");

  return { document };
}

async function main() {
  try {
    await fs.access(inPath);
  } catch {
    throw new Error(`CSV not found: ${inPath}`);
  }

  await fs.mkdir(path.dirname(outPath), { recursive: true });

  const rows = await readCsv(inPath);
  const { document } = draw(rows);

  await fs.writeFile(outPath, svgToString(document), "utf-8");
  console.log(`[wrote] ${outPath}`);
}

main().catch((err) => {
  console.error(String(err?.stack ?? err));
  process.exit(1);
});
