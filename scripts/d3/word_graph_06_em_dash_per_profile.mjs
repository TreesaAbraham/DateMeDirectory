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
  "data/charts/graphscsv/word_graph_06_em_dash_per_profile.csv"
);

const DEFAULT_OUT = path.join(
  REPO_ROOT,
  "data/charts/d3/svg/word_graph_06_em_dash_per_profile.svg"
);

const DEFAULT_OUT_PNG = path.join(
  REPO_ROOT,
  "data/charts/d3/png/word_graph_06_em_dash_per_profile.png"
);

// Padded viewBox so edge/rotated labels don't get clipped in embeds
const VB_PAD_X = 80; // left/right breathing room (covers y-axis label + ticks)
const VB_PAD_Y = 50; // top/bottom breathing room

function ensureDir(p) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
}

function readCsvOrDie(inPath) {
  if (!fs.existsSync(inPath)) throw new Error(`CSV not found: ${inPath}`);
  return fs.readFileSync(inPath, "utf8");
}

// Tiny CLI parser: --key value, plus boolean flags like --png
function parseArgs(argv) {
  const out = { png: false };
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
  return out;
}

function parseRows(csvText) {
  const rows = d3.csvParse(csvText);

  // Validate expected columns (lightweight)
  const required = new Set(["id", "word_count", "em_dash_count", "bucket"]);
  const cols = new Set(rows.columns ?? []);
  for (const r of required) {
    if (!cols.has(r)) throw new Error(`Missing column "${r}" in CSV`);
  }

  return rows.map((r) => ({
    id: String(r.id ?? "").trim(),
    word_count: Number(r.word_count),
    em_dash_count: Number(r.em_dash_count),
    bucket: String(r.bucket ?? "").trim(),
  }));
}

function bucketOrderKey(b) {
  // enforce: 0,1,2,3,4,5+
  if (b === "5+") return 999;
  const n = Number(b);
  return Number.isFinite(n) ? n : 1000;
}

function buildCounts(rows) {
  const counts = d3.rollup(
    rows,
    (v) => v.length,
    (d) => d.bucket
  );

  // Ensure all canonical buckets exist, even if count=0
  const canonical = ["0", "1", "2", "3", "4", "5+"];
  for (const c of canonical) {
    if (!counts.has(c)) counts.set(c, 0);
  }

  // Return in canonical order
  return canonical
    .slice()
    .sort((a, b) => bucketOrderKey(a) - bucketOrderKey(b))
    .map((b) => ({
      bucket: b,
      count: counts.get(b) ?? 0,
    }));
}

function renderSvg(data, opts) {
  const {
    width,
    height,
    marginTop,
    marginRight,
    marginBottom,
    marginLeft,
    title,
    subtitle,
    barColor,
    textColor,
    axisColor,
    bgColor,
    fontFamily,
  } = opts;

  const x = d3
    .scaleBand()
    .domain(data.map((d) => d.bucket))
    .range([marginLeft, width - marginRight])
    .padding(0.25);

  const yMax = d3.max(data, (d) => d.count) ?? 1;

  const y = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([height - marginBottom, marginTop]);

  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const body = d3.select(dom.window.document).select("body");

  const svg = body
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")

    // Natural export size
    .attr("width", width)
    .attr("height", height)

    // Responsive embed + padding against clipping
    .attr(
      "viewBox",
      `${-VB_PAD_X} ${-VB_PAD_Y} ${width + VB_PAD_X * 2} ${height + VB_PAD_Y * 2}`
    )
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("style", "max-width: 100%; height: auto; display: block;")

    .style("font-family", fontFamily)
    .style("font-size", "12px");

  // Background: cover padded viewBox so labels don't spill onto page bg
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
    .attr("font-weight", 700)
    .text(title);

  // Subtitle
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 52)
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text(subtitle);

  // Bars
  svg
    .append("g")
    .selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", (d) => x(d.bucket))
    .attr("y", (d) => y(d.count))
    .attr("width", x.bandwidth())
    .attr("height", (d) => y(0) - y(d.count))
    .attr("rx", 4)
    .attr("fill", barColor)
    .attr("opacity", 0.9);

  // Bar labels
  svg
    .append("g")
    .selectAll("text.val")
    .data(data)
    .join("text")
    .attr("x", (d) => (x(d.bucket) ?? 0) + x.bandwidth() / 2)
    .attr("y", (d) => y(d.count) - 6)
    .attr("text-anchor", "middle")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text((d) => d.count);

  // X axis
  const xAxis = d3.axisBottom(x).tickSizeOuter(0);
  const xG = svg
    .append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(xAxis);

  xG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  xG.selectAll("text").attr("fill", textColor).attr("font-size", 12).attr("font-weight", 600);

  // X axis label
  svg
    .append("text")
    .attr("x", (marginLeft + (width - marginRight)) / 2)
    .attr("y", height - 10)
    .attr("text-anchor", "middle")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text("Em dash count bucket per profile");

  // Y axis
  const yAxis = d3.axisLeft(y).ticks(6);
  const yG = svg
    .append("g")
    .attr("transform", `translate(${marginLeft}, 0)`)
    .call(yAxis);

  yG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  yG.selectAll("text").attr("fill", textColor).attr("font-size", 11);

  // Y axis label (rotated, needs padding -> viewBox handles it)
  const yLabelX = 14;
  const yLabelY = (marginTop + (height - marginBottom)) / 2;

  svg
    .append("text")
    .attr("x", yLabelX)
    .attr("y", yLabelY)
    .attr("transform", `rotate(-90, ${yLabelX}, ${yLabelY})`)
    .attr("text-anchor", "middle")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text("Number of profiles");

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

  const csvText = readCsvOrDie(inPath);
  const rows = parseRows(csvText);
  const counts = buildCounts(rows);

  const title = args.title ?? "Em dash usage by profile";
  const subtitle =
    args.subtitle ??
    "Distribution of em dash counts per profile, binned into buckets (0, 1, 2, 3, 4, 5+).";

  const svgText = renderSvg(counts, {
    width: 900,
    height: 520,
    marginTop: 80,
    marginRight: 30,
    marginBottom: 60,
    marginLeft: 60,
    title,
    subtitle,
    barColor: args.barColor ?? "#FF5555",
    textColor: args.textColor ?? "#EAEAEA",
    axisColor: args.axisColor ?? "#EAEAEA",
    bgColor: args.bgColor ?? "#0B0B0F",
    fontFamily:
      args.fontFamily ??
      '"DejaVu Serif", Georgia, "Times New Roman", Times, serif',
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
