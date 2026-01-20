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
  "data/charts/graphscsv/word_graph_08_sentence_complexity_by_interest_gender_per_profile.csv"
);

const OUT_DIR_SVG = path.join(REPO_ROOT, "data/charts/d3/svg");
const OUT_DIR_PNG = path.join(REPO_ROOT, "data/charts/d3/png");

const COLORS = {
  M: "#2F6BFF",   // blue
  F: "#FF2EA6",   // fuschia
  NB: "#7B2CBF",  // purple
};

const TARGET_LABEL = {
  M: "Interested in men",
  F: "Interested in women",
  NB: "Interested in nonbinary people",
};

const SOURCE_ORDER = ["M", "F", "NB"];
const SOURCE_LABEL = { M: "Men", F: "Women", NB: "Nonbinary" };

function ensureDir(p) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
}

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

function readCsvOrDie(inPath) {
  if (!fs.existsSync(inPath)) throw new Error(`CSV not found: ${inPath}`);
  return fs.readFileSync(inPath, "utf8");
}

function canonicalGender(g) {
  const s = String(g ?? "").trim().toUpperCase();
  if (s === "M" || s === "MALE" || s === "MAN") return "M";
  if (s === "F" || s === "FEMALE" || s === "WOMAN") return "F";
  if (s === "NB" || s === "NONBINARY" || s === "NON-BINARY") return "NB";
  return "OTHER";
}

function toNumber(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : NaN;
}

function quantile(arr, q) {
  // arr must be sorted ascending
  if (arr.length === 0) return NaN;
  const pos = (arr.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (arr[base + 1] === undefined) return arr[base];
  return arr[base] + rest * (arr[base + 1] - arr[base]);
}

function summarize(rows) {
  // rows is already filtered to a single target_gender
  const bySource = d3.group(rows, (d) => d.source_gender);

  const out = [];
  for (const s of SOURCE_ORDER) {
    const vals = (bySource.get(s) ?? [])
      .map((d) => d.long_sentence_pct)
      .filter((v) => Number.isFinite(v))
      .sort(d3.ascending);

    if (vals.length === 0) {
      out.push({
        source_gender: s,
        n: 0,
        mean: NaN,
        median: NaN,
        q1: NaN,
        q3: NaN,
      });
      continue;
    }

    const mean = d3.mean(vals);
    const median = d3.median(vals);
    const q1 = quantile(vals, 0.25);
    const q3 = quantile(vals, 0.75);

    out.push({
      source_gender: s,
      n: vals.length,
      mean,
      median,
      q1,
      q3,
    });
  }
  return out;
}

function renderSvg(summary, opts) {
  const {
    width,
    height,
    marginTop,
    marginRight,
    marginBottom,
    marginLeft,
    title,
    subtitle,
    accentColor,
    textColor,
    axisColor,
    bgColor,
  } = opts;

  // x domain from min/max of q1/q3 (fallback to mean)
  const allNums = summary.flatMap((d) =>
    [d.q1, d.q3, d.mean].filter((v) => Number.isFinite(v))
  );
  const minX = d3.min(allNums) ?? 0;
  const maxX = d3.max(allNums) ?? 1;

  const pad = (maxX - minX) * 0.08 || 2;
  const x = d3
    .scaleLinear()
    .domain([Math.max(0, minX - pad), maxX + pad])
    .nice()
    .range([marginLeft, width - marginRight]);

  const y = d3
    .scaleBand()
    .domain(summary.map((d) => d.source_gender))
    .range([marginTop, height - marginBottom])
    .padding(0.35);

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

  // Title + subtitle
  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 32)
    .attr("fill", textColor)
    .attr("font-size", 18)
    .attr("font-weight", 700)
    .text(title);

  svg
    .append("text")
    .attr("x", marginLeft)
    .attr("y", 52)
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text(subtitle);

  // X axis
  const xAxis = d3.axisBottom(x).ticks(7).tickFormat((d) => `${d}%`);
  const xG = svg
    .append("g")
    .attr("transform", `translate(0, ${height - marginBottom})`)
    .call(xAxis);

  xG.selectAll("path,line").attr("stroke", axisColor).attr("opacity", 0.7);
  xG.selectAll("text").attr("fill", textColor).attr("font-size", 11);

  // X label
  svg
    .append("text")
    .attr("x", (marginLeft + (width - marginRight)) / 2)
    .attr("y", height - 10)
    .attr("text-anchor", "middle")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("opacity", 0.9)
    .text("Long sentence percentage (per profile)");

  // Y axis labels (custom so we can use Men/Women/NB)
  svg
    .append("g")
    .selectAll("text.y")
    .data(summary)
    .join("text")
    .attr("x", marginLeft - 12)
    .attr("y", (d) => (y(d.source_gender) ?? 0) + y.bandwidth() / 2 + 4)
    .attr("text-anchor", "end")
    .attr("fill", textColor)
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text((d) => SOURCE_LABEL[d.source_gender] ?? d.source_gender);

  // Draw IQR band + mean dot
  const g = svg.append("g");

  // IQR band
  g.selectAll("line.iqr")
    .data(summary.filter((d) => Number.isFinite(d.q1) && Number.isFinite(d.q3)))
    .join("line")
    .attr("x1", (d) => x(d.q1))
    .attr("x2", (d) => x(d.q3))
    .attr("y1", (d) => (y(d.source_gender) ?? 0) + y.bandwidth() / 2)
    .attr("y2", (d) => (y(d.source_gender) ?? 0) + y.bandwidth() / 2)
    .attr("stroke", accentColor)
    .attr("stroke-width", 10)
    .attr("stroke-linecap", "round")
    .attr("opacity", 0.35);

  // Mean dot
  g.selectAll("circle.mean")
    .data(summary.filter((d) => Number.isFinite(d.mean)))
    .join("circle")
    .attr("cx", (d) => x(d.mean))
    .attr("cy", (d) => (y(d.source_gender) ?? 0) + y.bandwidth() / 2)
    .attr("r", 7)
    .attr("fill", accentColor)
    .attr("opacity", 0.95);

  // Mean value labels (right of dot)
  g.selectAll("text.meanLabel")
    .data(summary.filter((d) => Number.isFinite(d.mean)))
    .join("text")
    .attr("x", (d) => x(d.mean) + 12)
    .attr("y", (d) => (y(d.source_gender) ?? 0) + y.bandwidth() / 2 + 4)
    .attr("fill", textColor)
    .attr("font-size", 11)
    .attr("font-weight", 700)
    .text((d) => `${d.mean.toFixed(1)}%  (n=${d.n})`);

  // Light vertical gridlines
  const ticks = x.ticks(7);
  svg
    .append("g")
    .selectAll("line.grid")
    .data(ticks)
    .join("line")
    .attr("x1", (d) => x(d))
    .attr("x2", (d) => x(d))
    .attr("y1", marginTop)
    .attr("y2", height - marginBottom)
    .attr("stroke", axisColor)
    .attr("opacity", 0.08);

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

async function writeOneTarget({ inPath, target, outBase, wantPng }) {
  const csvText = readCsvOrDie(inPath);
  const rowsRaw = d3.csvParse(csvText);

  // Validate required columns
  const required = new Set([
    "id",
    "source_gender",
    "target_gender",
    "word_count",
    "sentence_count",
    "long_sentence_pct",
    "interestedIn_raw",
  ]);
  const cols = new Set(rowsRaw.columns ?? []);
  for (const r of required) {
    if (!cols.has(r)) throw new Error(`Missing column "${r}" in CSV`);
  }

  const rows = rowsRaw.map((r) => ({
    id: String(r.id ?? "").trim(),
    source_gender: canonicalGender(r.source_gender),
    target_gender: canonicalGender(r.target_gender),
    word_count: toNumber(r.word_count),
    sentence_count: toNumber(r.sentence_count),
    long_sentence_pct: toNumber(r.long_sentence_pct),
    interestedIn_raw: String(r.interestedIn_raw ?? ""),
  }));

  const filtered = rows.filter(
    (d) => d.target_gender === target && d.source_gender !== "OTHER"
  );

  const summary = summarize(filtered);

  const accentColor = COLORS[target] ?? "#EAEAEA";
  const title = `Sentence complexity by gender (${TARGET_LABEL[target] ?? target})`;
  const subtitle =
    "Dot = mean long_sentence_pct. Band = 25th–75th percentile (IQR).";

  const svg = renderSvg(summary, {
    width: 980,
    height: 420,
    marginTop: 85,
    marginRight: 35,
    marginBottom: 60,
    marginLeft: 90,
    title,
    subtitle,
    accentColor,
    textColor: "#EAEAEA",
    axisColor: "#EAEAEA",
    bgColor: "#0B0B0F",
  });

  const outSvg = path.join(OUT_DIR_SVG, `${outBase}_${target}.svg`);
  ensureDir(outSvg);
  fs.writeFileSync(outSvg, svg, "utf8");
  console.log(`[out] ${outSvg}`);

  if (wantPng) {
    const outPng = path.join(OUT_DIR_PNG, `${outBase}_${target}.png`);
    await maybeWritePng(outSvg, outPng);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  const inPath = args.in ? path.resolve(args.in) : DEFAULT_IN;

  // Base name for outputs (we’ll append _M / _F / _NB)
  const outBase =
    args.outBase ??
    "word_graph_08_sentence_complexity_by_interest_gender_per_profile";

  const wantPng = Boolean(args.png || args.outPng);

  await writeOneTarget({ inPath, target: "M", outBase, wantPng });
  await writeOneTarget({ inPath, target: "F", outBase, wantPng });
  await writeOneTarget({ inPath, target: "NB", outBase, wantPng });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
