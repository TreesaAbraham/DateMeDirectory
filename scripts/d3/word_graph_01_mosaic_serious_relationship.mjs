#!/usr/bin/env node
/**
 * D3 (Node) chart script
 * Graph 01: Mosaic plot (2x2) + definition panel
 *
 * Input CSV columns: row,col,count
 * Example:
 * row,col,count
 * Male,Uses bucket,200
 * Male,Does not use bucket,13
 * Female,Uses bucket,90
 * Female,Does not use bucket,6
 *
 * Output: SVG (two-panel layout)
 */

import fs from "node:fs";
import path from "node:path";
import { Command } from "commander";
import { JSDOM } from "jsdom";
import { csvParse } from "d3-dsv";
import { select } from "d3-selection";

// ---------- Defaults / constants ----------

const REPO_ROOT = process.cwd();

const DEFAULT_IN = path.join(
  REPO_ROOT,
  "data/charts/graphscsv/word_graph_01_mosaic_serious_relationship.csv"
);
const DEFAULT_OUT = path.join(
  REPO_ROOT,
  "data/charts/d3/svg/word_graph_01_mosaic_serious_relationship.svg"
);

const TITLE = "Use of serious relationship language in profiles (negation-aware)";

const ROW_ORDER = ["Male", "Female"];
const COL_ORDER = ["Uses bucket", "Does not use bucket"];

const NEGATION_WINDOW = 8;
const DEFINITION_LINES = [
  'Counts as "Uses bucket" if ≥ 1 non-negated match(es).',
  `Negation rule: ignore matches if a negation appears within ${NEGATION_WINDOW} words before the term.`
];

// Keep the same terms table content you used in the seaborn script
const SERIOUS_TERMS = [
  ["love", "loving"],
  ["relationship", "relationships"],
  ["stability", "stable"],
  ["dating", "partner"],
  ["partners", "marriage"],
  ["married", "family"],
  ["commitment", "committed"],
  ["serious", "long term"],
  ["long-term", "kids"],
  ["children", "compatible"],
  ["long-term", "longterm"]
];

const ROW_COLORS = {
  Male: "#1B5E20", // dark green
  Female: "#00897B" // teal
};

// Padded viewBox so edge/negative-position labels don't get clipped in embeds
const VB_PAD_X = 90; // left/right breathing room
const VB_PAD_Y = 40; // top/bottom breathing room

// ---------- Small helpers ----------

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function readText(p) {
  return fs.readFileSync(p, "utf8");
}

function writeText(p, s) {
  ensureDir(path.dirname(p));
  fs.writeFileSync(p, s, "utf8");
}

function mustNumber(x, label) {
  const n = Number(x);
  if (!Number.isFinite(n)) {
    throw new Error(`Non-numeric value for ${label}: ${x}`);
  }
  return n;
}

// ---------- SVG patterns for "hatch" ----------
// We emulate hatch by defining a pattern per row color:
// background = row color, diagonal lines = white with some opacity
function defineHatchPatterns(defs) {
  const lineColor = "rgba(255,255,255,0.75)";
  const size = 8; // pattern tile size

  for (const [rowName, baseColor] of Object.entries(ROW_COLORS)) {
    const id = `hatch-${rowName.toLowerCase()}`;

    const pat = defs
      .append("pattern")
      .attr("id", id)
      .attr("patternUnits", "userSpaceOnUse")
      .attr("width", size)
      .attr("height", size);

    // background
    pat
      .append("rect")
      .attr("width", size)
      .attr("height", size)
      .attr("fill", baseColor);

    // diagonal lines
    pat
      .append("path")
      .attr("d", `M -2 ${size} L ${size} -2 M 0 ${size + 2} L ${size + 2} 0`)
      .attr("stroke", lineColor)
      .attr("stroke-width", 2);
  }
}

// ---------- Main drawing ----------

function draw({ rows, cols, counts, outPath, width, height }) {
  // Layout
  const margin = { top: 70, right: 30, bottom: 30, left: 30 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // Two-panel layout (matches your matplotlib ratio vibe)
  const leftRatio = 2.2;
  const rightRatio = 1.3;
  const gap = 30;

  const totalRatio = leftRatio + rightRatio;
  const leftW = Math.floor((innerW - gap) * (leftRatio / totalRatio));
  const rightW = innerW - gap - leftW;

  const leftX = margin.left;
  const rightX = margin.left + leftW + gap;
  const topY = margin.top;

  // Mosaic area sizing (leave a header band above mosaic)
  const headerBand = 28;
  const mosaicH = innerH - 10; // small breathing room
  const mosaicY = topY + headerBand;
  const mosaicW = leftW;

  // Create DOM + SVG
  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const document = dom.window.document;

  const svg = select(document)
    .select("body")
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")

    // Keep natural size for export…
    .attr("width", width)
    .attr("height", height)

    // …but make it responsive + prevent clipping when embedded
    .attr(
      "viewBox",
      `${-VB_PAD_X} ${-VB_PAD_Y} ${width + VB_PAD_X * 2} ${height + VB_PAD_Y * 2}`
    )
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("style", "max-width: 100%; height: auto; display: block;")

    .style(
      "font-family",
      '"DejaVu Serif", Georgia, "Times New Roman", Times, serif'
    )
    .style("font-size", "12px");

  // Background: solid black (covers the original width/height area)
  // Note: because of padded viewBox, the “padding area” will show the page background.
  // If you want black everywhere, draw a bigger rect using the padded extents.
  // Background: cover the *entire* padded viewBox so edge labels don't spill onto page bg
svg
  .append("rect")
  .attr("x", -VB_PAD_X)
  .attr("y", -VB_PAD_Y)
  .attr("width", width + VB_PAD_X * 2)
  .attr("height", height + VB_PAD_Y * 2)
  .attr("fill", "#000000");


  // Global text styling: white text with a dark outline for readability everywhere
  svg.append("style").text(`
    text {
      fill: #ffffff;
      stroke: rgba(0,0,0,0.70);
      stroke-width: 3px;
      paint-order: stroke;
      stroke-linejoin: round;
    }
  `);

  // defs (patterns)
  const defs = svg.append("defs");
  defineHatchPatterns(defs);

  // Title
  svg
    .append("text")
    .attr("x", width / 2)
    .attr("y", 32)
    .attr("text-anchor", "middle")
    .attr("font-size", 18)
    .attr("font-weight", 700)
    .text(TITLE);

  // Totals
  const overallTotal = rows.reduce((acc, r) => {
    return acc + cols.reduce((a2, c) => a2 + (counts[`${r}||${c}`] ?? 0), 0);
  }, 0);

  if (overallTotal <= 0) {
    throw new Error("No counts to plot (overall total is 0).");
  }

  const rowTotals = Object.fromEntries(
    rows.map((r) => [
      r,
      cols.reduce((acc, c) => acc + (counts[`${r}||${c}`] ?? 0), 0)
    ])
  );

  const colTotals = Object.fromEntries(
    cols.map((c) => [
      c,
      rows.reduce((acc, r) => acc + (counts[`${r}||${c}`] ?? 0), 0)
    ])
  );

  // Left panel group
  const gLeft = svg.append("g").attr("transform", `translate(${leftX},0)`);

  // Mosaic frame (around mosaic area only)
  gLeft
    .append("rect")
    .attr("x", 0)
    .attr("y", mosaicY)
    .attr("width", mosaicW)
    .attr("height", mosaicH - headerBand)
    .attr("fill", "none")
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 1.2);

  // Column headers placed above mosaic using overall column split
  let colLabelX = 0;
  for (const c of cols) {
    const wFrac = colTotals[c] / overallTotal;
    const w = mosaicW * wFrac;

    gLeft
      .append("text")
      .attr("x", colLabelX + w / 2)
      .attr("y", topY + 20)
      .attr("text-anchor", "middle")
      .attr("font-size", 13)
      .attr("font-weight", 700)
      .text(c);

    colLabelX += w;
  }

  // Row labels + mosaic cells
  let yTop = mosaicY + (mosaicH - headerBand);
  for (const r of rows) {
    const rTotal = rowTotals[r];
    if (rTotal <= 0) continue;

    const rowH = (rTotal / overallTotal) * (mosaicH - headerBand);
    const y0 = yTop - rowH;

    // Row label on the left (note: x is negative, hence the padded viewBox)
    gLeft
      .append("text")
      .attr("x", -10)
      .attr("y", y0 + rowH / 2)
      .attr("text-anchor", "end")
      .attr("dominant-baseline", "middle")
      .attr("font-size", 14)
      .attr("font-weight", 700)
      .text(r);

    let xLeft = 0;
    for (const c of cols) {
      const v = counts[`${r}||${c}`] ?? 0;
      if (v <= 0) continue;

      const w = (v / rTotal) * mosaicW;

      const isHatch = c === "Does not use bucket";

      // Fill: solid for Uses, patterned for Does-not
      const fill = isHatch
        ? `url(#hatch-${r.toLowerCase()})`
        : ROW_COLORS[r] ?? "#6BAED6";

      // Cell rect
      gLeft
        .append("rect")
        .attr("x", xLeft)
        .attr("y", y0)
        .attr("width", w)
        .attr("height", rowH)
        .attr("fill", fill)
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 2)
        .attr("opacity", 0.9);

      // Count label
      const area = (w * rowH) / (mosaicW * (mosaicH - headerBand)); // normalized-ish
      const fs = area > 0.12 ? 18 : area > 0.06 ? 14 : 12;

      gLeft
        .append("text")
        .attr("x", xLeft + w / 2)
        .attr("y", y0 + rowH / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", fs)
        .attr("font-weight", 800)
        .text(String(v));

      xLeft += w;
    }

    yTop = y0;
  }

  // Right panel: Definition + rules + table
  const gRight = svg.append("g").attr("transform", `translate(${rightX},${topY})`);

  // Header
  gRight
    .append("text")
    .attr("x", 0)
    .attr("y", 0)
    .attr("text-anchor", "start")
    .attr("dominant-baseline", "hanging")
    .attr("font-size", 16)
    .attr("font-weight", 800)
    .text("Definition");

  // Rule lines
  const ruleStartY = 30;
  const ruleLineH = 16;

  DEFINITION_LINES.forEach((line, i) => {
    gRight
      .append("text")
      .attr("x", 0)
      .attr("y", ruleStartY + i * ruleLineH)
      .attr("text-anchor", "start")
      .attr("dominant-baseline", "hanging")
      .attr("font-size", 11.5)
      .text(line);
  });

  // Terms table
  const tableStartY = ruleStartY + DEFINITION_LINES.length * ruleLineH + 18;

  // Table header
  gRight
    .append("text")
    .attr("x", 0)
    .attr("y", tableStartY)
    .attr("text-anchor", "start")
    .attr("dominant-baseline", "hanging")
    .attr("font-size", 12)
    .attr("font-weight", 800)
    .text("Serious terms");

  // Column positions
  const col1X = 0;
  const col2X = Math.floor(rightW * 0.55);

  // Light guide line under header
  gRight
    .append("line")
    .attr("x1", 0)
    .attr("x2", rightW)
    .attr("y1", tableStartY + 18)
    .attr("y2", tableStartY + 18)
    .attr("stroke", "rgba(255,255,255,0.25)")
    .attr("stroke-width", 1);

  // Rows
  const rowY0 = tableStartY + 26;
  const rowH = 18;

  SERIOUS_TERMS.forEach((pair, i) => {
    const y = rowY0 + i * rowH;

    gRight
      .append("text")
      .attr("x", col1X)
      .attr("y", y)
      .attr("dominant-baseline", "hanging")
      .attr("font-size", 11.5)
      .text(pair[0]);

    gRight
      .append("text")
      .attr("x", col2X)
      .attr("y", y)
      .attr("dominant-baseline", "hanging")
      .attr("font-size", 11.5)
      .text(pair[1] ?? "");
  });

  // Subtle bounding box around right panel content
  gRight
    .append("rect")
    .attr("x", -8)
    .attr("y", -8)
    .attr("width", rightW + 16)
    .attr("height", innerH + 8)
    .attr("fill", "none")
    .attr("stroke", "rgba(255,255,255,0.18)")
    .attr("stroke-width", 1);

  // Serialize SVG
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
    .option("--height <n>", "SVG height", (v) => mustNumber(v, "height"), 550);

  program.parse(process.argv);
  const opts = program.opts();

  const csvPath = path.resolve(opts.in);
  const outPath = path.resolve(opts.out);

  if (!fs.existsSync(csvPath)) {
    throw new Error(`CSV not found: ${csvPath}`);
  }

  const raw = readText(csvPath);
  const df = csvParse(raw);

  // Validate + normalize
  const counts = {};
  for (const d of df) {
    const r = (d.row ?? "").trim();
    const c = (d.col ?? "").trim();
    const n = mustNumber(d.count, "count");

    if (!r || !c) continue;
    counts[`${r}||${c}`] = (counts[`${r}||${c}`] ?? 0) + n;
  }

  draw({
    rows: ROW_ORDER,
    cols: COL_ORDER,
    counts,
    outPath,
    width: opts.width,
    height: opts.height
  });
}

main();
