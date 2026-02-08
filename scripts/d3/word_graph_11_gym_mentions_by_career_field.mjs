#!/usr/bin/env node
/**
 * word_graph_11_gym_mentions_by_career_field.mjs
 *
 * Reads:  data/profiles_master.json
 * Writes: data/charts/d3/svg/word_graph_11_gym_mentions_by_career_field.svg
 * Opt:    --png (writes PNG too if `sharp` is installed)
 *
 * Usage:
 *   node scripts/d3/word_graph_11_gym_mentions_by_career_field.mjs
 *   node scripts/d3/word_graph_11_gym_mentions_by_career_field.mjs --png
 *   node scripts/d3/word_graph_11_gym_mentions_by_career_field.mjs --in data/profiles_master.json --out data/charts/d3/svg/...
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as d3 from "d3";
import { JSDOM } from "jsdom";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../..");

const DEFAULT_IN_JSON = path.join(REPO_ROOT, "data", "profiles_master.json");
const DEFAULT_OUT_SVG = path.join(
  REPO_ROOT,
  "data",
  "charts",
  "d3",
  "svg",
  "word_graph_11_gym_mentions_by_career_field.svg"
);
const DEFAULT_OUT_PNG = path.join(
  REPO_ROOT,
  "data",
  "charts",
  "d3",
  "png",
  "word_graph_11_gym_mentions_by_career_field.png"
);

const FIELDS_ORDER = ["STUDENT", "ARTS_HUMANITIES", "ENGINEERING", "MEDICINE", "OTHER"];
const FIELD_LABEL = {
  STUDENT: "Students",
  ARTS_HUMANITIES: "Arts & Humanities",
  ENGINEERING: "Engineering",
  MEDICINE: "Medicine/Health",
  OTHER: "Other",
};

// --- Regex patterns (same logic as your py scripts) ---
const studentPatterns = [
  "\\bstudent\\b",
  "\\bundergrad(uate)?\\b",
  "\\bgrad(uate)?\\s+student\\b",
  "\\bphd\\b",
  "\\bmaster'?s\\b",
  "\\bmajor(ing)?\\b",
  "\\buniversity\\b",
  "\\bcollege\\b",
  "\\bclass of\\b",
  "\\bcampus\\b",
];

const engineeringPatterns = [
  "\\bengineer(ing)?\\b",
  "\\bsoftware\\b",
  "\\bdeveloper\\b",
  "\\bprogrammer\\b",
  "\\bcoding\\b",
  "\\bcomputer science\\b",
  "\\bcs\\b",
  "\\bdata engineer\\b",
  "\\bmechanical\\b",
  "\\belectrical\\b",
  "\\bcivil\\b",
  "\\baerospace\\b",
  "\\bchemical\\b",
  "\\bindustrial\\b",
  "\\bsystems\\b",
  "\\brobot(ic|ics)\\b",
];

const medicinePatterns = [
  "\\bmedical\\b",
  "\\bmed\\s*student\\b",
  "\\bmedical\\s+student\\b",
  "\\bdoctor\\b",
  "\\bphysician\\b",
  "\\bmd\\b",
  "\\bdo\\b",
  "\\bnurse\\b",
  "\\brn\\b",
  "\\bpa\\b",
  "\\bparamedic\\b",
  "\\bemt\\b",
  "\\bpharmac(y|ist)\\b",
  "\\bdent(al|ist)\\b",
  "\\bveterin(ary|arian)\\b",
  "\\btherap(y|ist)\\b",
  "\\bphysical therapy\\b",
  "\\boccupational therapy\\b",
  "\\bclinical\\b",
  "\\bhospital\\b",
  "\\bpublic health\\b",
];

const artsPatterns = [
  "\\bart(ist|s)?\\b",
  "\\bwriter\\b",
  "\\bauthor\\b",
  "\\bpoet\\b",
  "\\bmusician\\b",
  "\\bsinger\\b",
  "\\bactor\\b",
  "\\btheat(re|er)\\b",
  "\\bdancer\\b",
  "\\bphotograph(er|y)\\b",
  "\\bpainter\\b",
  "\\bgraphic\\s+design(er)?\\b",
  "\\bdesigner\\b",
  "\\billustrat(or|ion)\\b",
  "\\bhistory\\b",
  "\\benglish\\b",
  "\\bphilosophy\\b",
  "\\blinguistics\\b",
  "\\bjournalis(m|t)\\b",
  "\\bcommunications\\b",
  "\\bliterature\\b",
  "\\bhumanities\\b",
];

const gymPatterns = [
  "\\bgym\\b",
  "\\bwork\\s*out\\b",
  "\\bworkout(s)?\\b",
  "\\bexercise\\b",
  "\\blift(ing)?\\b",
  "\\bweight\\s*lift(ing)?\\b",
  "\\bweightlifting\\b",
  "\\bweights\\b",
  "\\bcardio\\b",
  "\\bhiit\\b",
  "\\bcrossfit\\b",
  "\\brun(ning)?\\b",
  "\\bjog(ging)?\\b",
  "\\bcycle(ing)?\\b",
  "\\bspin\\b",
  "\\bswim(ming)?\\b",
  "\\byoga\\b",
  "\\bpilates\\b",
  "\\bhike(ing)?\\b",
  "\\bclimb(ing)?\\b",
  "\\bboulder(ing)?\\b",
  "\\bfitness\\b",
];

function compileAny(patterns) {
  return new RegExp(`(${patterns.join("|")})`, "i");
}

const RE_STUDENT = compileAny(studentPatterns);
const RE_ENGINEERING = compileAny(engineeringPatterns);
const RE_MEDICINE = compileAny(medicinePatterns);
const RE_ARTS = compileAny(artsPatterns);
const RE_GYM = compileAny(gymPatterns);

function ensureDir(filePath) {
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

function readJson(filePath) {
  if (!fs.existsSync(filePath)) throw new Error(`Missing input JSON: ${filePath}`);
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

// Tries to match your Python fulltext getter behavior
function getFullText(p) {
  const pd = p?.profileDetails ?? {};
  if (pd && typeof pd === "object") {
    for (const k of ["fullText", "full_text", "fulltext", "text", "body"]) {
      const v = pd[k];
      if (typeof v === "string" && v.trim()) return v;
    }
  }
  const v = p?.fullText;
  return typeof v === "string" ? v : "";
}

function extractCareerText(profile) {
  const chunks = [];

  for (const k of [
    "occupation",
    "job",
    "jobTitle",
    "title",
    "company",
    "industry",
    "education",
    "school",
    "major",
    "field",
    "career",
  ]) {
    const v = profile?.[k];
    if (typeof v === "string" && v.trim()) chunks.push(v);
  }

  const details = profile?.profileDetails;
  if (details && typeof details === "object") {
    const sections = details.sections;
    if (sections && typeof sections === "object") {
      for (const [sk, sv] of Object.entries(sections)) {
        if (typeof sv !== "string" || !sv.trim()) continue;
        const skL = String(sk).toLowerCase();
        if (["work", "job", "career", "education", "school", "major", "industry", "profession"].some((t) => skL.includes(t))) {
          chunks.push(sv);
        }
      }
    }

    for (const [k, v] of Object.entries(details)) {
      if (typeof v !== "string" || !v.trim()) continue;
      const kL = String(k).toLowerCase();
      if (["work", "job", "career", "education", "school", "major", "industry", "profession"].some((t) => kL.includes(t))) {
        chunks.push(v);
      }
    }
  }

  if (chunks.length === 0) chunks.push(getFullText(profile));
  return chunks.join("\n");
}

function classifyField(careerText) {
  const t = careerText ?? "";

  // medical student => MEDICINE
  if (/\bmed\s*student\b|\bmedical\s+student\b/i.test(t)) return "MEDICINE";

  if (RE_STUDENT.test(t)) return "STUDENT";
  if (RE_ENGINEERING.test(t)) return "ENGINEERING";
  if (RE_MEDICINE.test(t)) return "MEDICINE";
  if (RE_ARTS.test(t)) return "ARTS_HUMANITIES";
  return "OTHER";
}

function gymMentioned(fullText) {
  if (!fullText) return false;
  return RE_GYM.test(fullText);
}

function computeStats(profiles) {
  const totals = Object.fromEntries(FIELDS_ORDER.map((k) => [k, 0]));
  const hits = Object.fromEntries(FIELDS_ORDER.map((k) => [k, 0]));

  let totalAll = 0;
  let hitAll = 0;

  for (const p of profiles) {
    const field = classifyField(extractCareerText(p));
    const hit = gymMentioned(getFullText(p)) ? 1 : 0;
    totals[field] += 1;
    hits[field] += hit;
    totalAll += 1;
    hitAll += hit;
  }

  const rows = FIELDS_ORDER.map((k) => {
    const t = totals[k];
    const h = hits[k];
    const pct = t ? (h / t) * 100 : 0;
    return {
      key: k,
      label: FIELD_LABEL[k],
      total: t,
      gym: h,
      pct,
    };
  });

  return { rows, totalAll, hitAll };
}

function renderSvg({ rows, totalAll, hitAll }) {
  // Sort by pct descending for readability
  const data = [...rows].sort((a, b) => d3.descending(a.pct, b.pct));

  const width = 980;
  const height = 520;
  const margin = { top: 78, right: 180, bottom: 70, left: 260 };

  const overallPct = totalAll ? (hitAll / totalAll) * 100 : 0;

  const x = d3
    .scaleLinear()
    .domain([0, Math.max(5, (d3.max(data, (d) => d.pct) ?? 0) * 1.15)])
    .nice()
    .range([margin.left, width - margin.right]);

  const y = d3
    .scaleBand()
    .domain(data.map((d) => d.label))
    .range([margin.top, height - margin.bottom])
    .padding(0.22);

  const dom = new JSDOM(`<!doctype html><html><body></body></html>`);
  const body = d3.select(dom.window.document).select("body");

  const svg = body
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("style", "max-width: 100%; height: auto; display: block;")
    .style("font-family", "DejaVu Serif, Georgia, 'Times New Roman', serif")
    .style("font-size", "12px");

  svg.append("rect").attr("x", 0).attr("y", 0).attr("width", width).attr("height", height).attr("fill", "white");

  // Title + subtitle
  svg
    .append("text")
    .attr("x", margin.left)
    .attr("y", 34)
    .attr("font-size", 20)
    .attr("font-weight", 700)
    .text("Gym/exercise mentions by career field");

  svg
    .append("text")
    .attr("x", margin.left)
    .attr("y", 56)
    .attr("font-size", 12)
    .attr("fill", "#333")
    .text(`Overall: ${overallPct.toFixed(1)}% (${hitAll}/${totalAll}) mention gym/exercise`);

  // X axis
  svg
    .append("g")
    .attr("transform", `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat((d) => `${d}%`))
    .call((g) => g.selectAll("text").attr("font-size", 12));

  // Y axis
  svg
    .append("g")
    .attr("transform", `translate(${margin.left},0)`)
    .call(d3.axisLeft(y))
    .call((g) => g.selectAll("text").attr("font-size", 12));

  // Color palette (fun but readable)
  const palette = d3.schemeTableau10;
  const color = d3.scaleOrdinal(data.map((d) => d.label), palette);

  // Bars
  svg
    .append("g")
    .selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", x(0))
    .attr("y", (d) => y(d.label))
    .attr("height", y.bandwidth())
    .attr("width", (d) => x(d.pct) - x(0))
    .attr("fill", (d) => color(d.label))
    .attr("stroke", "#111")
    .attr("stroke-width", 0.6);

  // Labels at bar end
  svg
    .append("g")
    .selectAll("text")
    .data(data)
    .join("text")
    .attr("x", (d) => x(d.pct) + 8)
    .attr("y", (d) => (y(d.label) ?? 0) + y.bandwidth() / 2 + 4)
    .attr("font-size", 12)
    .text((d) => `${d.pct.toFixed(1)}% (${d.gym}/${d.total})`);

  // X axis label
  svg
    .append("text")
    .attr("x", (margin.left + (width - margin.right)) / 2)
    .attr("y", height - 18)
    .attr("text-anchor", "middle")
    .attr("font-size", 12)
    .text("Percent of profiles mentioning gym/exercise");

  return dom.window.document.querySelector("svg").outerHTML;
}

async function maybeWritePng(svgPath, pngPath) {
  try {
    const { default: sharp } = await import("sharp");
    const svgBuf = fs.readFileSync(svgPath);
    ensureDir(pngPath);
    await sharp(svgBuf).png().toFile(pngPath);
    console.log(`[out] ${pngPath}`);
  } catch {
    console.log("[note] PNG skipped (install `sharp` to enable --png output).");
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inPath = args.in ?? DEFAULT_IN_JSON;
  const outSvg = args.out ?? DEFAULT_OUT_SVG;
  const outPng = args.out_png ?? DEFAULT_OUT_PNG;

  const profiles = readJson(inPath);
  if (!Array.isArray(profiles)) throw new Error("profiles_master.json must be a list of profiles");

  const stats = computeStats(profiles);
  const svgText = renderSvg(stats);

  ensureDir(outSvg);
  fs.writeFileSync(outSvg, svgText, "utf8");
  console.log(`[out] ${outSvg}`);

  if (args.png) {
    await maybeWritePng(outSvg, outPng);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
