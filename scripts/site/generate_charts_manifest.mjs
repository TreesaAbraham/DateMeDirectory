// scripts/site/generate_charts_manifest.mjs
// Generates the CANONICAL graph-grouped manifest at:
//   site/data/charts_manifest.json
//
// What it does:
// - Scans: site/assets/charts/{matplotlib,seaborn,d3}
// - Detects graph id from filenames like: word_graph_03_...
// - Outputs: { schema_version, generated_at, graphs: [...] }
// - MERGES with existing manifest so your text (question/method/key_findings/notes/title) stays.
//
// Run from repo root:
//   node scripts/site/generate_charts_manifest.mjs

import { promises as fs } from "node:fs";
import path from "node:path";

const REPO_ROOT = process.cwd();
const SITE_DIR = path.join(REPO_ROOT, "site");
const CHARTS_DIR = path.join(SITE_DIR, "assets", "charts");
const OUT_PATH = path.join(SITE_DIR, "data", "charts_manifest.json");

const RENDERERS = ["matplotlib", "seaborn", "d3"];
const ALLOWED_EXT = new Set([".png", ".svg"]);

// -------- helpers --------

function pad2(n) {
  return String(n).padStart(2, "0");
}

function normalizeGraphId(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return "";
  const num = Number(s);
  if (Number.isFinite(num)) return pad2(num);
  // if already "03", keep it
  if (/^\d{2}$/.test(s)) return s;
  return s;
}

// Extract graph id from filenames like:
// - word_graph_03_...
// - word-graph-3-...
// - graph_03_...
function graphIdFromFilename(filename) {
  const base = filename.toLowerCase();

  // word_graph_03_...
  let m = base.match(/word[_-]graph[_-]?(\d{1,2})[_-]/);
  if (m) return pad2(m[1]);

  // graph_03_...
  m = base.match(/graph[_-]?(\d{1,2})[_-]/);
  if (m) return pad2(m[1]);

  return null;
}

function slugForGraph(graphId) {
  return `graph-${normalizeGraphId(graphId)}`;
}

function urlFor(renderer, file) {
  return `assets/charts/${renderer}/${file}`;
}

async function fileExists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

async function readJsonIfExists(p) {
  try {
    const text = await fs.readFile(p, "utf8");
    return JSON.parse(text);
  } catch (err) {
    if (err && err.code === "ENOENT") return null;
    throw err;
  }
}

function stableSort(a, b) {
  return a.localeCompare(b, "en");
}

async function listFiles(dir) {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter((e) => e.isFile())
      .map((e) => e.name)
      .filter((name) => ALLOWED_EXT.has(path.extname(name).toLowerCase()))
      .sort(stableSort);
  } catch (err) {
    if (err && err.code === "ENOENT") return [];
    throw err;
  }
}

// Keep existing graph fields (title/question/method/key_findings/notes)
// but replace renderers with what we actually found on disk.
function mergeGraph(existing, incoming) {
  const g = existing ?? {};

  return {
    graph_id: incoming.graph_id,
    slug: g.slug || incoming.slug,
    title: g.title || incoming.title,
    question: g.question || "",
    method: Array.isArray(g.method) ? g.method : (g.method ? [String(g.method)] : []),
    key_findings: Array.isArray(g.key_findings) ? g.key_findings : [],
    notes: typeof g.notes === "string" ? g.notes : "",
    renderers: incoming.renderers
  };
}

function mergeEntry(existingEntry, incomingEntry) {
  // Preserve writeup if it existed; otherwise use the incoming default.
  const writeup =
    (existingEntry && typeof existingEntry.writeup === "string" && existingEntry.writeup.trim())
      ? existingEntry.writeup.trim()
      : incomingEntry.writeup;

  return {
    id: incomingEntry.id,
    file: incomingEntry.file,
    url: incomingEntry.url,
    writeup
  };
}

// -------- main build --------

async function main() {
  // Ensure output folder exists
  await fs.mkdir(path.dirname(OUT_PATH), { recursive: true });

  // Load existing canonical manifest if present (to preserve your text fields)
  const existingManifest = await readJsonIfExists(OUT_PATH);
  const existingGraphs = Array.isArray(existingManifest?.graphs) ? existingManifest.graphs : [];

  const existingById = new Map(
    existingGraphs.map((g) => [normalizeGraphId(g.graph_id), g])
  );

  // Scan assets and build a new graph map from disk
  const foundById = new Map(); // graph_id -> { renderers: {..} }

  for (const renderer of RENDERERS) {
    const rendererDir = path.join(CHARTS_DIR, renderer);
    const files = await listFiles(rendererDir);

    for (const file of files) {
      const gid = graphIdFromFilename(file);
      if (!gid) continue;

      if (!foundById.has(gid)) {
        foundById.set(gid, {
          graph_id: gid,
          slug: slugForGraph(gid),
          title: `Graph ${gid}`,
          renderers: { matplotlib: [], seaborn: [], d3: [] }
        });
      }

      const graph = foundById.get(gid);

      // entry id is stable-ish: graphId-renderer-basename
      const base = file.replace(path.extname(file), "");
      const entryId = `${gid}-${renderer}-${base}`;

      // Default writeup: writeups/graphs/<id>.txt (matches your current setup)
      const writeup = `writeups/graphs/${gid}.txt`;

      graph.renderers[renderer].push({
        id: entryId,
        file,
        url: urlFor(renderer, file),
        writeup
      });
    }
  }

  // Merge renderers + preserve existing text fields
  const mergedGraphs = [];

  // 1) all graphs found on disk (canonical for “what exists”)
  for (const [gid, incoming] of [...foundById.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const existing = existingById.get(gid);

    // Merge entries per renderer (preserve writeup if present in existing)
    const mergedRenderers = { matplotlib: [], seaborn: [], d3: [] };

    for (const renderer of RENDERERS) {
      const incomingList = Array.isArray(incoming.renderers?.[renderer]) ? incoming.renderers[renderer] : [];
      const existingList = Array.isArray(existing?.renderers?.[renderer]) ? existing.renderers[renderer] : [];

      const existingByFile = new Map(existingList.map((e) => [e.file, e]));

      mergedRenderers[renderer] = incomingList.map((ent) =>
        mergeEntry(existingByFile.get(ent.file), ent)
      );
    }

    const merged = mergeGraph(existing, { ...incoming, renderers: mergedRenderers });
    mergedGraphs.push(merged);
  }

  // 2) also keep any existing graphs that have NO assets found (optional but safe)
  //    This prevents accidental deletion if you’re mid-build.
  for (const [gid, g] of existingById.entries()) {
    if (!foundById.has(gid)) {
      mergedGraphs.push(g);
    }
  }

  const out = {
    schema_version: 1,
    generated_at: new Date().toISOString(),
    graphs: mergedGraphs
  };

  await fs.writeFile(OUT_PATH, JSON.stringify(out, null, 2) + "\n", "utf8");
  console.log(`Wrote ${mergedGraphs.length} graphs -> ${path.relative(REPO_ROOT, OUT_PATH)}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
