git add .
git commit -m 'message'
git push origin main

In practice, consistency is about being adaptable. Don't have much time? Scale it down. Don't have much energy? Do the easy version. Find different ways to show up depending on the circumstances. Let your habits change shape to meet the demands of the day.

Adaptability is the way of consistency.”

James Clear

Always ask the purpose of each commit before starting
Scrape and do in python

💘 Date Me Directory Data Analysis
Author: Treesa Abraham
Purpose: Analyze language patterns and demographics in dating profile self-presentations

🎯 The Work (Do in Order)
Step 1: Scrape the Data
Write scrape_all.py that:

Fetches the directory table from dateme.directory/browse
For each profile URL, fetches the detail page
Saves everything to data/profiles.json

Output: profiles.json with all profile data

Step 2: Analyze Demographics
Write analyze.py that:

Loads profiles.json into pandas
Calculates basic stats:

Age distribution (mean, median, ranges)
Gender breakdown
Location patterns
Location flexibility counts


Prints summary to console

Output: Understanding of who's in the dataset

Step 3: Add Text Analysis
Expand analyze.py to measure:

Profile length (word counts)
Sentence length averages
Exclamation point usage
Emoji counts
Questions asked

Output: Stylistic metrics for each profile

Step 4: Generate First Graphs
Add visualization code to create:
Graph A: Age Patterns

Bar chart: Average profile length by age group (18-25, 26-30, 31-35, 36-40, 41+)

Graph B: Stylistic Metrics

Box plot: Exclamation points per 100 words by gender

Graph C: Location Flexibility

Bar chart: Open to relocate vs Willing to travel vs Location-specific

Output: 3 PNG files in data/charts/

Step 5: Distinctive Vocabulary
Add TF-IDF analysis to find:

Most distinctive words used by women vs men
Most distinctive words by age group (Gen Z vs Millennials vs Gen X)
Most distinctive words by location (if enough data)

Output: Tables showing characteristic language patterns

Step 6: Advanced Graphs
Create remaining visualizations:
Gendered Language Patterns

Mosaic chart: How men/women use words like "adventure", "serious", "emotional"

What People Want

Word frequency from "Looking For" sections
Categorized bar charts

Profile Tone Classification

Humorous vs Serious (based on word choice)
Vulnerable vs Guarded (emotional vocabulary)
Distribution across demographics

Output: Full set of publication-ready charts



Step 7: Write Findings
Create findings.md that:

Explains each graph
Interprets patterns
Highlights surprising discoveries
Connects to broader dating culture observations


Notes from the 8 graphs created:
Graph 1: Views on Serious Relationships

Output: Written analysis ready to share

🎨 Graph Reference
These are the types of visualizations to create (inspired by "Nabokov's Favorite Word is Mauve"):

Gendered Language - How different groups frame the same concepts
Age Patterns - Profile behavior across age groups
Stylistic Metrics - Writing style (exclamation points, sentence length, formality)
Distinctive Vocabulary - Most characteristic words per demographic (TF-IDF)
What People Want - Common themes in "Looking For" sections
Profile Tone - Humorous/Serious, Vulnerable/Guarded distributions


📊 Example: Distinctive Vocabulary Output
Most Distinctive Words: Women vs Men
WOMEN SEEKING MEN          |  MEN SEEKING WOMEN
---------------------------|---------------------------
Emotionally intelligent    |  Laid-back
Partner                    |  Chill
Communication             |  Low-maintenance
Intentional               |  Easy-going
Therapy                   |  Drama-free
This tells a story about gendered expectations in dating culture.

💡 Key Principle
Build incrementally. Get scraping working, then add one analysis at a time, then add one graph at a time. Each step should produce something you can look at and verify before moving forward.




mathplotlab
seaborn graph visualization
d3
vercel

seaborn:
chore: add seaborn + shared plot style/save helpers
feat: seaborn exclamation boxplots (generation + gender)
feat: seaborn em-dash bucket bar chart
feat: seaborn grouped prevalence bar chart
chore: apply seaborn theme to remaining matplotlib charts
test: add graphs smoke-runner + output checks
docs: update graph workflow


Chart X.1 — Question + plan (hard gate)
 Define claim + “done” criteria (must match Seaborn intent)
 Confirm CSV schema matches standard (or fix upstream)
 Choose chart archetype (bar/grouped/dot/facet)
Commit: docs: plan d3 version for word_graph_XX
Chart X.2 — Build minimal correct chart (render + ordering together)
 Load CSV
 Render correct marks
 Enforce ordering + label mapping
 Save SVG
Commit: feat: add d3 chart for word_graph_XX
Chart X.3 — Polish only what’s necessary
 Apply house style (margins, font, title placement, legend)
 Fix overlap/clipping
Commit: style: polish d3 chart for word_graph_XX
Chart X.4 — Optional enhancements (only if interpretability improves)
 Annotations / reference lines / outliers / facets
Commit: feat: enhance d3 chart for word_graph_XX (only if used)
Chart X.5 — Verification (lightweight)
 Sanity check categories + min/max
 Confirm output path + naming convention
Commit: chore: verify d3 output for word_graph_XX



Edit graphs


## Static Site Build Checklist (3 commits per step)

Goal: publish a static report page (Vercel) that includes:
- 1) **marplot PNG**
- 2) **seaborn PNG**
- 3) **d3 SVG**
- 4) **write-ups for each chart**

---

### Step 1: Site foundation (3 commits)

- [x] **Commit 1.1 — `feat(site): add static site skeleton`**
  - [x] Add folders:
    - [x] `site/`
    - [x] `site/assets/charts/`
    - [x] `site/assets/images/`
    - [x] `site/data/`
    - [x] `site/writeups/`
  - [x] Add placeholder files:
    - [x] `site/index.html`
    - [x] `site/styles.css`
    - [x] `site/app.js` (can be empty for now)

- [x] **Commit 1.2 — `feat(site): add report page sections`**
  - [x] Build `site/index.html` sections:
    - [x] Overview
    - [x] Method
    - [x] Key findings
    - [x] Charts
    - [x] Appendix/Notes (optional)
  - [x] Add semantic wrappers (`header`, `main`, `section`, `footer`)
  - [x] Add classnames you’ll style later (`container`, `prose`, `grid`, etc.)

- [x] **Commit 1.3 — `docs(site): add local preview and update instructions`**
  - [x] Add `site/README.md` with:
    - [x] Local preview command: `python3 -m http.server --directory site 8000`
    - [x] Where to drop SVG/PNG files
    - [x] How to update captions/write-ups


---

### Step 2: Make it lovely (Option C aesthetics) (3 commits)

- [x] **Commit 2.1 — `style(site): add report typography and layout`**
  - [x] Update `site/styles.css` with:
    - [x] container width
    - [x] heading scale
    - [x] paragraph spacing
    - [x] link styles
    - [x] subtle background + section spacing

- [x] **Commit 2.2 — `style(site): add callouts and collapsible sections`**
  - [x] Add callout HTML blocks in `site/index.html` under Key findings:
    - [x] `<div class="callout">...</div>`
  - [x] Add `details/summary` for Method expansion
  - [x] Add CSS for `.callout`, `details`, `.muted`, etc.

- [ ] **Commit 2.3 — `style(site): add chart card grid and caption + writeup styling`**
  - [ ] Add CSS for:
    - [ ] `.grid` responsive layout
    - [ ] `.card` styling
    - [ ] `.chart` sizing with `aspect-ratio` + `object-fit: contain`
    - [ ] captions (`figcaption`)
    - [ ] `.writeup` (spacing/typography for per-chart writeups)
  - [ ] Add one sample chart card in HTML (placeholder)


---

### Step 3: Get real content on the page (3 commits)

- [ ] **Commit 3.1 — `feat(site): add initial chart assets`**
  - [ ] Copy the required set first:
    - [ ] `site/assets/images/<marplot>.png`
    - [ ] `site/assets/images/<seaborn>.png`
    - [ ] `site/assets/charts/<d3>.svg`
    - [ ] `site/writeups/<chart-id>.md` (or `.html`)
  - [ ] (Optional) Copy a few extra charts after the required set is in

- [ ] **Commit 3.2 — `feat(site): embed charts with captions + writeups`**
  - [ ] Add real `<figure class="card">` entries to `site/index.html`:
    - [ ] Use `<img>` for **both** `.png` and `.svg` embeds
    - [ ] `<figcaption>` = 1–2 line caption
    - [ ] Add a `.writeup` block under each chart **or** link to `site/writeups/...`
  - [ ] Make sure each chart has:
    - [ ] Visual (PNG/SVG)
    - [ ] Caption
    - [ ] Write-up (inline or linked)

- [ ] **Commit 3.3 — `feat(site): add findings write-up content`**
  - [ ] Put your write-up directly into `site/index.html` sections (or link out to `site/writeups/findings.html`)
  - [ ] Add 1–2 callouts tied to your actual results


---

### Step 4: Deploy to Vercel (3 commits)

- [ ] **Commit 4.1 — `docs(deploy): add Vercel static deployment steps`**
  - [ ] Add `site/DEPLOY.md` (or root `DEPLOY.md`) with:
    - [ ] Root Directory: `site`
    - [ ] Framework: `Other`
    - [ ] Build Command: *(blank)*
    - [ ] Output Directory: `.`
    - [ ] Note: do **not** include `/site/` in asset paths

- [ ] **Commit 4.2 — `chore(deploy): add vercel config`**
  - [ ] Add root `vercel.json`:
    - [ ] `{ "cleanUrls": true }` (optional but nice)

- [ ] **Commit 4.3 — `chore(site): prep static site for deployment`**
  - [ ] Verify all asset paths use either:
    - [ ] Rooted: `/assets/...`
    - [ ] or relative: `./assets/...`
  - [ ] Ensure `site/index.html` loads `styles.css` and `app.js`
  - [ ] Note: `.nojekyll` not required for Vercel


---

### Step 5: Make it maintainable (manifest + auto gallery) (3 commits)

- [ ] **Commit 5.1 — `feat(site): add chart manifest`**
  - [ ] Create `site/data/manifest.json` with chart metadata:
    - [ ] `id, title, file, type, section, caption`
    - [ ] `writeup` (either inline text or a path like `/writeups/<id>.html`)

- [ ] **Commit 5.2 — `feat(site): add manifest generator script`**
  - [ ] Add `scripts/site/generate_manifest.py` (or `.js`)
  - [ ] Reads:
    - [ ] `site/assets/charts/`
    - [ ] `site/assets/images/`
    - [ ] `site/writeups/`
  - [ ] Writes:
    - [ ] `site/data/manifest.json`

- [ ] **Commit 5.3 — `feat(site): render chart gallery from manifest`**
  - [ ] Update `site/app.js` to fetch `/data/manifest.json`
  - [ ] Generate the same `.card` markup you styled earlier:
    - [ ] `<img ...>` for charts (PNG/SVG)
    - [ ] `<figcaption>` for captions
    - [ ] `.writeup` for writeup text or a link to the writeup path
  - [ ] Replace manual chart HTML (or keep a small “featured” section)




----------------------------------------------------------------------------------------------------
# Updated Checklist (Repo-Accurate + Graph-Number Plan)

## ✅ Step 1: Site foundation (3 commits)

- [x] **Commit 1.1 — `feat(site): add static site skeleton`**
- [x] **Commit 1.2 — `feat(site): add report page sections`**
- [x] **Commit 1.3 — `docs(site): add local preview and update instructions`**

> All accurate and done.

---

## ✅ Step 2: Make it lovely (Option C aesthetics) (3 commits)

- [x] **Commit 2.1 — `style(site): add report typography and layout`**
- [x] **Commit 2.2 — `style(site): add callouts and collapsible sections`**
- [x] **Commit 2.3 — `style(site): add chart card grid and caption + writeup styling`**
  - [x] `.grid`, `.card`, `.chart-media`, `figcaption`, `.writeup` already exist in `site/styles.css`
  - [x] Sample card exists in `site/index.html`

> Your old checklist said 2.3 was pending. The repo says it’s done. The repo wins.

---

## 🧱 Step 3: Normalize the site structure for “Graph #” pages (3 commits)

- [x] **Commit 3.1 — `chore(site): normalize chart asset folders`**
  - **Goal:** remove the `matplotlip` landmine and make paths consistent.
  - [x] Rename folder:
    - [x] `site/assets/charts/matplotlip/` → `site/assets/charts/matplotlib/`
  - [x] Update any docs/strings that reference the old path:
    - [x] `site/index.html` (currently mentions `/matplotlib`, which is correct but not true yet)
  - [x] Optional cleanup (only if you want):
    - [x] Keep `site/assets/images/` empty or delete it later; right now everything is under `assets/charts/`

- [x] **Commit 3.2 — `fix(site): align manifest schema with frontend`**
  - **Goal:** pick one manifest shape and stop the JS from hallucinating.
  - [x] Decide the canonical manifest format: **graph-grouped** (matches your plan)
  - [x] Update `site/app.js` and `site/index.html` to use:
    - [x] `manifest.graphs[]` (NOT `manifest.charts[]`)
  - [x] Update `site/index.html` Charts blurb so it matches the real structure:
    - [x] Don’t claim a flat auto-gallery if you’re doing graph-number group pages

- [x] **Commit 3.3 — `feat(site): add graph renderer script for graph pages`**
  - **Goal:** make `site/graphs/*/*.html` actually work.
  - [x] Add missing file: `site/graph.js`
    - [x] Reads `data-graph` + `data-renderer` from `<main id="graph-page">`
    - [x] Loads the correct image from the manifest (or a predictable filename convention)
    - [x] Renders:
      - [x] Title
      - [x] Chart image (SVG/PNG)
      - [x] Caption (if available)
      - [x] Writeup link/inline (if available)

---

## 📚 Step 4: Implement the “Graph # hub” concept (3 commits)

- [ ] **Commit 4.1 — `feat(site): add per-graph hub pages`**
  - **Goal:** one page per graph number that shows all renderers together.
  - [ ] For each graph folder (01–06, 08–09):
    - [ ] Create `site/graphs/<id>/index.html`
    - [ ] Page includes three sections/cards:
      - [ ] Matplotlib PNG
      - [ ] Seaborn PNG
      - [ ] D3 SVG
    - [ ] Page includes:
      - [ ] Question
      - [ ] Method
      - [ ] Key finding(s)
      - [ ] Notes/caveats
  - _Note:_ You currently have renderer-specific pages only. This adds the combined view you want.

- [ ] **Commit 4.2 — `feat(site): convert homepage into graph directory`**
  - **Goal:** homepage links to graph hubs, not individual renderer cards.
  - [ ] Replace the auto “charts grid” on `site/index.html` with a Graph Directory grid:
    - [ ] “Graph 01” → `/graphs/01/`
    - [ ] … etc
  - [ ] Keep a smaller “Featured” strip if you want, but don’t duplicate everything.

- [ ] **Commit 4.3 — `feat(site): add initial writeups + findings tied to real graphs`**
  - [ ] Add writeup files (repo currently has no `site/writeups/*` files):
    - [ ] `site/writeups/graphs/01.md` (or `.html`)
    - [ ] Repeat for at least a few graphs
  - [ ] Update homepage Key Findings:
    - [ ] Replace placeholders with findings that cite specific graph numbers

---

## 🧰 Step 5: Make the manifest actually reflect your assets (3 commits)

**Right now:**
- You have the assets for many graphs
- But `site/data/charts_manifest.json` only lists 01–02, with blank file/url fields
- You also have a generator script that outputs a totally different schema (`charts[]`)

So we fix that.

- [ ] **Commit 5.1 — `feat(site): define graph-grouped manifest as canonical`**
  - [ ] Keep `site/data/charts_manifest.json` as the canonical manifest
  - [ ] Make it complete for graphs you already have (01–06, 08–09)
  - [ ] For each graph:
    - [ ] `graph_id`, `title`
    - [ ] `question`, `method`, `key_findings`, `notes`
    - [ ] `renderers.matplotlib[].url` pointing to real PNG path
    - [ ] `renderers.seaborn[].url` pointing to real PNG path
    - [ ] `renderers.d3[].url` pointing to real SVG path
    - [ ] Optional `writeup_path`

- [ ] **Commit 5.2 — `fix(site): update manifest generator to output graphs schema`**
  - [ ] Update `scripts/site/generate_charts_manifest.mjs` so it generates `graphs[]`, not `charts[]`
  - [ ] Make it detect graph id from filenames like:
    - [ ] `word_graph_01_...`
  - [ ] Make it resilient to multiple PNGs per renderer (Graph 02 has multiple variants)

- [ ] **Commit 5.3 — `feat(site): add page generator for graph hubs`**
  - You already have: `scripts/site/generate_graph_pages.mjs` (renderer pages)
  - [ ] Expand it to also generate:
    - [ ] `site/graphs/<id>/index.html` (hub page)
  - [ ] Or add a sibling script:
    - [ ] `scripts/site/generate_graph_hubs.mjs`

---

## 🚀 Step 6: Deploy to Vercel (3 commits)

> Still valid, just updated to match your actual paths.

- [ ] **Commit 6.1 — `docs(deploy): add Vercel static deployment steps`**
  - [ ] Add `DEPLOY.md` (root or `site/DEPLOY.md`)
  - [ ] Root Directory: `site`
  - [ ] Framework: `Other`
  - [ ] Build Command: *(blank)*
  - [ ] Output Directory: `.`
  - [ ] Note: no `/site/` in asset paths

- [ ] **Commit 6.2 — `chore(deploy): add vercel config`**
  - [ ] Add root `vercel.json` (optional)
    - [ ] `{ "cleanUrls": true }`

- [ ] **Commit 6.3 — `chore(site): preflight for deployment`**
  - [ ] Ensure every page uses consistent asset paths:
    - [ ] `../assets/...` or rooted `/assets/...` (pick one and stick to it)
  - [ ] Confirm `graph.js` exists and loads on graph pages
  - [ ] Confirm homepage directory links work

---

## 🧹 Optional cleanup (because you will forget later)

- [ ] **Commit O.1 — `chore(site): deprecate old chart gallery pages`**
  - [ ] Decide whether to keep:
    - [ ] `site/chart.html`
    - [ ] `site/topics/*`
  - [ ] If you keep them, update them to use `graphs[]` manifest
  - [ ] If not, remove or link them from somewhere “Archive”
