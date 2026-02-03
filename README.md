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

- [x] **Commit 4.1 — `feat(site): add per-graph hub pages`**
  - **Goal:** one page per graph number that shows all renderers together.
  - [x] For each graph folder (01–06, 08–09):
    - [x] Create `site/graphs/<id>/index.html`
    - [x] Page includes three sections/cards:
      - [x] Matplotlib PNG
      - [x] Seaborn PNG
      - [x] D3 SVG
    - [x] Page includes:
      - [x] Question
      - [x] Method
      - [x] Key finding(s)
      - [x] Notes/caveats
  - _Note:_ You currently have renderer-specific pages only. This adds the combined view you want.

- [x] **Commit 4.2 — `feat(site): convert homepage into graph directory`**
  - **Goal:** homepage links to graph hubs, not individual renderer cards.
  - [x] Replace the auto “charts grid” on `site/index.html` with a Graph Directory grid:
    - [x] “Graph 01” → `/graphs/01/`
    - [x] … etc
  - [x] Keep a smaller “Featured” strip if you want, but don’t duplicate everything.

- [x] **Commit 4.3 — `feat(site): add initial writeups + findings tied to real graphs`**
  - [x] Add writeup files (repo currently has no `site/writeups/*` files):
    - [x] `site/writeups/graphs/01.md` (or `.html`)
    - [x] Repeat for at least a few graphs
  - [x] Update homepage Key Findings:
    - [x] Replace placeholders with findings that cite specific graph numbers

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












The purpose of this CSV file is to represent the relationship between gender (Male and Female) and the usage of a bucket (Uses bucket and Does not use bucket) in a serious relationship context. The 'count' column indicates the number of individuals in each category combination.
# Generated by: word_graph_01_mosaic.py
# Represents: Contingency table of gender vs. "serious relationship" language bucket usage
# Negation-aware: Phrases like "not looking for serious relationship" are excluded from "Uses bucket"
# Bucket terms: love, loving, relationship, relationships, stability, stable, dating, partner, partners, marriage, married, family, commitment, committed, serious, long term, kids, children, compatible, longterm
# Min hits: 1 (minimum non-negated matches to count as "Uses bucket")
# Negation window: 8 words before a term triggers negation exclusion

Based on the data collected: 200 of the 213 male profiles contained serious language or (93.90%) while 90 of the 96 female profiles contained serious language (93.75%). This indicates a high prevalence of serious relationship language usage among both genders

Why this data matters: Understanding the prevalence of serious relationship language can provide insights into dating preferences and communication styles among different genders 
It also provides us insight in the type of people who are using DateMe directory: most of them are looking for serious relationships (regardless of gender). 
This is arguably understandable since the majority of people building datemedocs are in late 20s-40s age range and are likely looking for long-term commitments.





# Generated by: word_graph_02_exclam_per100k_by_generation_outliers_dots.py
# Represents: Exclamation mark usage per 100k words by generation with outliers indicated
# Outliers: Points outside 1.5*IQR from Q1 and Q3
# Generations: Gen Z (born 1997-2012), Millennial (born 1981-1996), Gen X (born 1965-1980), Boomer (born 1946-1964)
# Min word count: 100 (minimum words in profile to be included)
# Min exclam count: 1 (minimum exclamation marks in profile to be included)
# Age calculated based on birth year as of 2025
# Why this data matters: Analyzing exclamation mark usage can provide insights into communication styles and emotional expressiveness across different generations. Higher usage may indicate a more enthusiastic or informal tone in profiles, which could influence perceptions in online dating contexts.
Based on the data collected, we can observe variations in exclamation mark usage across different generations.
Notably, Gen Z appear to have a higher frequency of exclamation mark usage per 100k words compared to other generations, suggesting a more expressive communication style. This trend may reflect generational differences in online communication preferences and social norms. Understanding these patterns can help tailor communication strategies for dating platforms to better engage users from different age groups.
Also note that boomers have the lowest exclamation mark usage, which may indicate a more reserved or formal communication style compared to younger generations. (it could also be because there are fewer boomers on the platform overall, leading to less data)
This information is valuable for dating platforms aiming to enhance user experience by aligning communication styles with generational preferences.


This data analyzes the number of exclamation points per 100k words by generation (gen z, millenial, gen x, boomer) and age. It includes user IDs, ages, birth years, generations, total words written, total exclamation points used, and calculated exclamation points per 100k words.
This data includes any outliers that were outside (Q1 - 1.5*IQR, Q3 + 1.5*IQR))
Although Gen Z still had the most exclamation points per 100k words on average, Millenials had more higher end outliers than Gen Z. (5 from 1500-2000, 3 from 2000-2500, 2 from 2500-3000, 1 from 3000-3500, 1 from 3500-4000)
This graph supplements the main analysis by showing that while Gen Z uses more exclamation points on average, Millenials have a larger number of high-usage outliers. This suggests that while Gen Z may generally be more expressive in their writing, there are Millenials who are exceptionally expressive, potentially indicating different communication styles or contexts of use between the generations.



In order to calculate the prevalence of bay area style words and uk/london style words in different user groups, we first need to define the word sets for each style based on their distinctiveness in the respective regions. Then, we can analyze the text data from users in the ALL_US, BAY_AREA, and UK_LONDON groups to count occurrences of these words and compute their prevalence per 10,000 words. Finally, we can visualize the results using a bar graph and output the data to a CSV file for further analysis.
We took the most distinctive words from bay area vs non-bay area (from word_graph_04) to define bay area style words, and the most distinctive words from uk/london vs non-uk/london (from word_graph_04) to define uk/london style words. Then we calculated how often these words appear in the text of users from ALL_US, BAY_AREA, and UK_LONDON groups to determine their prevalence per 10,000 words.
We did the same for UK/LONDON style words, using the distinctive words identified from the UK
Then, we created a bar graph to visualize the prevalence of both bay area style words and uk/london style words across the three user groups. The x-axis represents the user groups (ALL_US, BAY_AREA, UK_LONDON), while the y-axis shows the prevalence per 10,000 words. Each group has two bars: one for bay area style words and another for uk/london style words. This visualization helps to compare how frequently these distinctive words are used by different user groups.
Finally, we saved the calculated prevalence data into a CSV file named "word_style_prevalence.csv" for further analysis and reference. This file contains columns for user group, bay area style word prevalence, and uk/london style word prevalence./london vs non-uk/london comparison.




Measuring: do bay area stle words and uk/london-style words show up more than usual?
- x-axis: word set (bay area style words vs uk/london style words)
- y-axis: prevalence per 10k words
    - if I took 10,000 random words from ALL_US, how many of them would be bay area style words vs uk/london style words
Two bars: bay word set= words most distinctive for bay area and uk word set = words most distinctive for uk/london
- for each bar, show prevalence in ALL_US group vs prevalence in bay area or uk/london group
- output csv with data used to build graph

Observations: 
In all US profiles, bay area style words and uk/london style words show similar prevalence (~262 vs ~261 per 10k words).
In bay area profiles, bay area style words show higher prevalence (~370 per 10k words) compared to uk/london style words (~258 per 10k words).

in order to calculate prevale
nce of bay area style words and uk/london style words in different user groups, we first need to define the word sets for each style based on their distinctiveness in the respective regions. Then, we can analyze the text data from users in the ALL_US, BAY_AREA, and UK_LONDON groups to count occurrences of these words and compute their prevalence per 10,000 words. Finally, we can visualize the results using a bar graph and output the data to a CSV file for further analysis.
we took the most distinctive words from bay area vs non-bay area (from word_graph_04) to define bay area style words, and the most distinctive words from uk/london vs non-uk/london (from word_graph_04) to define uk/london style words. Then we calculated how often these words appear in the text of users from ALL_US, BAY_AREA, and UK_LONDON groups to determine their prevalence per 10,000 words.
We did the same for UK/LONDON style words, using the distinctive words identified from the UK/LONDON vs non-UK/LONDON comparison.

Then through script 9, we calculated the prevalence of these word sets in the text data from users in the ALL_US, BAY_AREA, and UK_LONDON groups. The results show that bay area style words are more prevalent in bay area profiles, while uk/london style words are more prevalent in uk/london profiles, confirming the distinct linguistic characteristics of these regions.




There are several graphs calculating word complexity based on who the user was looking for.
There were 9 categories:
- Female looking for  Female
- Female looking for Male
- Female looking for Non-Binary

- Male looking for  Female
- Male looking for Male
- Male looking for Non-Binary

- Non-Binary looking for Female
- Non-Binary looking for Male
- Non-Binary looking for Non-Binary

The data above represents individual user records with the following fields:
- User ID
- Gender
- Looking For
- Number of Words Used
Using this data, please generate a summary of average word complexity for each of the nine categories listed above.
To calculate the average word complexity for each of the nine categories based on the provided user data, we can follow these steps:
1. Initialize a dictionary to hold the total word complexity and count of users for each category.
2. Iterate through each user record, extract the relevant fields, and update the totals and counts in the dictionary based

We then built sepearate graphs for each category using the calculated averages. on the user's on the extracted data.
We made sure the graphs were based on the gender the person was looking for. 

While all fields had similar word complexity percentage (around 12-15%), we observed some variations
Regardless of which gender the user was looking for women always had at least 1% word complextity compared to millenial
This could indicate that wommen may be using more complex language when searching for partners compared to men in order to seem more sophisticated or appealing.
That or they just read a lot more novels (aka smut, this is for you Lorenzo). And know how to use big words.



To calculate the most distinctive words for us vs non-us users, we analyzed the text data from user profiles in both groups. We counted the occurrences of each word in the profiles and computed their z-scores to determine how distinctive they are for each group. The words with the highest positive z-scores in the US group are considered most distinctive for US users, while those with the highest negative z-scores in the non-US group are considered most distinctive for non-US users. This analysis helps us understand the linguistic differences between users from these regions.

1. Data Input & Classification

Reads user profiles from profiles_master.json
Uses the location field to classify each user as "US" or "NON_US" via a heuristic classifier that looks for:
Explicit markers: "USA", "United States", ZIP codes
US state abbreviations and names (e.g., "SC", "California")
Non-US country hints (e.g., "London", "Canada")
2. Text Extraction & Tokenization

Extracts profile text (tries multiple fallback fields like fullText, full_text, etc.)
Tokenizes into words using regex: [a-zA-Z']+ (letters + apostrophes)
Filters out:
Words shorter than 6 letters (configurable)
100+ common English stopwords ("the", "and", "people", etc.)
3. Statistical Scoring
Counts occurrences of each word in US and NON_US profiles
Calculates z-scores for each word using:
Positive z-scores → distinctive for US users
Negative z-scores → distinctive for non-US users
The prior acts as a smoothing mechanism to avoid overweighting rare words
4. Output Generation

Creates a side-by-side table visualization (PNG + SVG)
Exports CSV with rankings, word counts, and z-scores
Top 20 words per column (configurable via --top_n)
Key Gotchas & Design Choices
⚠️ Minimum word length is now 6 letters (changed from implicit default)

This filters out common 1–5 letter noise and focuses on meaningful, content-bearing words
⚠️ Location classification is heuristic-based

Not 100% accurate; relies on pattern matching, not geocoding
Ambiguous locations (e.g., "Europe" without country) get skipped
⚠️ Z-scores, not raw counts

A word appearing 100 times in US profiles might have lower distinctiveness than a word appearing 20 times, if it appears even less in non-US profiles (relative rarity matters)
Sample Output
Your CSV shows words like:

US distinctive: "google" (z=3.73), "business" (z=2.85), "travel" (z=2.82)
Non-US distinctive: "london" (z=-4.20), "listening" (z=-3.15), "interest" (z=-3.05)
This reveals that US profiles emphasize tech/business/leisure, while non-US emphasize place references and interests.

This data matters because it highlights linguistic and thematic differences in how users from different regions present themselves in dating profiles. Understanding these distinctions can inform platform localization, marketing strategies, and user engagement approaches tailored to regional preferences and cultural contexts.

it was interesting to see that the most distinctive words for US users were related to technology and business (e.g., "google", "business", "technology"), while non-US users had more location-specific and interest-related words (e.g., "london", "listening", "interest"). This suggests that US users may focus more on professional and tech-savvy identities, whereas non-US users might emphasize their interests and locations more prominently in their profiles.
This may also indicate what users from different regions prioritize when presenting themselves on dating platforms, which can be valuable for tailoring user experiences and marketing strategies.



This chart was initially supposed to calculated the likelieness of AI based on the use of EM dashes in text. However, after analysis, it was determined that the presence of EM dashes did not significantly correlate with AI-generated text in a meaningful way. Therefore, this chart was repurposed to show the distribution of EM dash usage across the dataset, providing insights into how frequently EM dashes are used in general writing within the analyzed texts.

