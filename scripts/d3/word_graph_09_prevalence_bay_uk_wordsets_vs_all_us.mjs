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
  "data/charts/graphscsv/word_graph_09_prevalence_bay_uk_wordsets_vs_all_us.csv"
);

const OUT_DIR_SVG = path.join(REPO_ROOT, "data/charts/d3/svg");
const OUT_DIR_PNG = path.join(REPO_ROOT, "data/charts/d3/png");

const GROUP_ORDER = ["ALL_US", "BAY_AREA", "UK_LONDON"];
const GROUP_LABEL = {
  ALL_US: "All US",
  BAY_AREA: "SF Bay Area",
  UK_LONDON: "UK / London",
};

const SERIES = [
  { key: "bay_wordset_rate_per_10k", label: "Bay wordset / 10k", color: "#2F855A" }, // green
  { key: "uk_wordset_rate_per_10k", label: "UK wordset / 10k", color: "#7B2CBF" },  // purple
];

function ensureDirForFile(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function parseArgs(argv) {
  const out = {};
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

function toNumber(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : NaN;
}

function readCsvOrDie(inPath) {
  if (!fs.existsSync(inPath)) throw new Error(`CSV not found: ${inPath}`);
  return fs.readFileSync(inPath, "utf8");
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

function renderSvg(data, opts) {
  const {
    width,
    height,
    marginTop,
    marginRight,
    marginBottom,
    marginLeft,
    bgColor,
    textColor,
    axisColor,
    title,
    subtitle,
  } = opts;

  const groups = GROUP_ORDER.filter((g) => data.some((d) => d.group === g));

  const yMax = d3.max(data, (d) =>
    d3.max(SERIES, (s) => d[s.key])
  ) ?? 0;

  const x0 = d3
    .scaleBand()
    .domain(groups)
    .range([marginLeft, width - marginRight])
    .paddingInner(0.28);

  const x1 = d3
    .scaleBand()
    .domain(SERIES.map((s) => s.key))
    .range([0, x0.bandwidth()])
    .padding(0.25);

  const y = d3
    .scaleLinear()
    .domain([0, yMax * 1.12])
    .nice()
    .range([height - marginBottom, marginTop]);

  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const body = d3.select(dom.window.document).select("body");

  const svg = body
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  // Background
  svg
    .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height)
    .attr("fill", bgColor);

  // Title top-right (so it won't fight the plot)
  svg
    .append("text")
    .attr("x", width - marginRight)
    .attr("y", 32)
    .attr("text-anchor", "end")
    .attr("fill", textColor)
    .attr("font-size", 18)
    .attr("font-weight", 800)
    .text(title);

  svg
    .append("text")
    .attr("x", width - marginRight)
    .attr("y", 52)
    .attr("text-anchor", "end")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text(subtitle);

  // Gridlines
  svg
    .append("g")
    .selectAll("line.grid")
    .data(y.ticks(6))
    .join("line")
    .attr("x1", marginLeft)
    .attr("x2", width - marginRight)
    .attr("y1", (d) => y(d))
    .attr("y2", (d) => y(d))
    .attr("stroke", axisColor)
    .attr("opacity", 0.10);

  // Bars
  const g = svg.append("g");

  const groupG = g
    .selectAll("g.group")
    .data(groups)
    .join("g")
    .attr("class", "group")
    .attr("transform", (d) => `translate(${x0(d)},0)`);

  groupG
    .selectAll("rect.bar")
    .data((group) => {
      const row = data.find((d) => d.group === group);
      return SERIES.map((s) => ({
        group,
        seriesKey: s.key,
        seriesLabel: s.label,
        color: s.color,
        value: row ? row[s.key] : NaN,
      }));
    })
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => x1(d.seriesKey))
    .attr("width", x1.bandwidth())
    .attr("y", (d) => (Number.isFinite(d.value) ? y(d.value) : y(0)))
    .attr("height", (d) =>
      Number.isFinite(d.value) ? y(0) - y(d.value) : 0
    )
    .attr("rx", 6)
    .attr("fill", (d) => d.color)
    .attr("opacity", 0.95);

  // Value labels above bars
  groupG
    .selectAll("text.val")
    .data((group) => {
      const row = data.find((d) => d.group === group);
      return SERIES.map((s) => ({
        group,
        seriesKey: s.key,
        value: row ? row[s.key] : NaN,
      }));
    })
    .join("text")
    .attr("class", "val")
    .attr("x", (d) => (x1(d.seriesKey) ?? 0) + x1.bandwidth() / 2)
    .attr("y", (d) => (Number.isFinite(d.value) ? y(d.value) - 8 : y(0)))
    .attr("text-anchor", "middle")
    .attr("fill", textColor)
    .attr("font-size", 11)
    .attr("font-weight", 700)
    .attr("opacity", 0.95)
    .text((d) => (Number.isFinite(d.value) ? d.value.toFixed(1) : ""));

  // X axis
  const xAxis = d3
    .axisBottom(x0)
    .tickFormat((d) => GROUP_LABEL[d] ?? d);

  const xG = svg
    .append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(xAxis);

  xG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  xG.selectAll("text").attr("fill", textColor).attr("font-size", 12).attr("font-weight", 700);

  // Y axis
  const yAxis = d3.axisLeft(y).ticks(6);
  const yG = svg
    .append("g")
    .attr("transform", `translate(${marginLeft},0)`)
    .call(yAxis);

  yG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  yG.selectAll("text").attr("fill", textColor).attr("font-size", 11);

  // Y label
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", marginTop - 18)
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .attr("opacity", 0.9)
    .text("Rate per 10,000 tokens");

  // Legend (top-left)
  const legend = svg
    .append("g")
    .attr("transform", `translate(${marginLeft}, ${60})`);

  const leg = legend
    .selectAll("g.item")
    .data(SERIES)
    .join("g")
    .attr("class", "item")
    .attr("transform", (d, i) => `translate(${i * 190},0)`);

  leg
    .append("rect")
    .attr("x", 0)
    .attr("y", -10)
    .attr("width", 14)
    .attr("height", 14)
    .attr("rx", 3)
    .attr("fill", (d) => d.color)
    .attr("opacity", 0.95);

  leg
    .append("text")
    .attr("x", 20)
    .attr("y", 2)
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text((d) => d.label);

  return body.html();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const inPath = args.in ? path.resolve(args.in) : DEFAULT_IN;

  const outBase =
    args.outBase ?? "word_graph_09_prevalence_bay_uk_wordsets_vs_all_us";

  const wantPng = Boolean(args.png);

  const csvText = readCsvOrDie(inPath);
  const rowsRaw = d3.csvParse(csvText);

  const required = new Set([
    "group",
    "docs",
    "total_tokens",
    "bay_wordset_rate_per_10k",
    "uk_wordset_rate_per_10k",
  ]);

  const cols = new Set(rowsRaw.columns ?? []);
  for (const r of required) {
    if (!cols.has(r)) throw new Error(`Missing column "${r}" in CSV`);
  }

  const data = rowsRaw.map((r) => ({
    group: String(r.group ?? "").trim(),
    docs: toNumber(r.docs),
    total_tokens: toNumber(r.total_tokens),
    bay_wordset_rate_per_10k: toNumber(r.bay_wordset_rate_per_10k),
    uk_wordset_rate_per_10k: toNumber(r.uk_wordset_rate_per_10k),
  }));

  const title = "Wordset prevalence by group";
  const subtitle = "Bay-area wordset vs UK/London wordset (rates per 10k tokens)";

  const svg = renderSvg(data, {
    width: 980,
    height: 520,
    marginTop: 110,
    marginRight: 40,
    marginBottom: 70,
    marginLeft: 80,
    bgColor: "#0B0B0F",
    textColor: "#EAEAEA",
    axisColor: "#EAEAEA",
    title,
    subtitle,
  });

  const outSvg = path.join(OUT_DIR_SVG, `${outBase}.svg`);
  ensureDirForFile(outSvg);
  fs.writeFileSync(outSvg, svg, "utf8");
  console.log(`[out] ${outSvg}`);

  if (wantPng) {
    const outPng = path.join(OUT_DIR_PNG, `${outBase}.png`);
    await maybeWritePng(outSvg, outPng);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
