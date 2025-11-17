git add .
git commit -m 'message'
git push origin main

In practice, consistency is about being adaptable. Don't have much time? Scale it down. Don't have much energy? Do the easy version. Find different ways to show up depending on the circumstances. Let your habits change shape to meet the demands of the day.

Adaptability is the way of consistency.”

James Clear

Always ask the purpose of each commit before starting
Scrape and do in python

# 💘 Date Me Directory Data Extraction & Analysis (Python Only)

This project uses **Python exclusively** to collect and analyze data from the [Date Me Directory](https://dateme.directory/browse), a public listing of user-submitted "date me docs."  
The goal is to extract structured demographic data (from the directory table) and unstructured textual data (from individual profile pages), store it in **JSON format**, and later analyze it through **pandas DataFrames** for both quantitative and literary-style qualitative insights.

---

## ✅ Master Checklist (with Commit Messages)

### 🏗️ Setup & Planning
- [x] Create project folder and initialize Git repository  
  - Commit: `chore: initialize python project folder and git repo
- [x] Install required Python libraries (`requests`, `beautifulsoup4`, `pandas`, `lxml`)  
  - Commit: `chore: install required python dependencies`
- [x] Create a `requirements.txt` file  
  - Commit: `chore: add requirements.txt`
- [x] Define data schema for JSON storage  
  - Commit: `feat: define JSON schema for profile data`
- [x] Decide on folder structure for scripts and data outputs  
  - Commit: `chore: establish python project folder structure`
- [x] Add ethical and privacy statement to README  
  - Commit: `docs: add ethical and privacy section`
- [x] Create `.gitignore` (exclude `/data`, `/venv`, and cached files)  
  - Commit: `chore: add .gitignore for python project`
- [x] Make `/data/` directory for JSON and CSV outputs  
  - Commit: `chore: create data directory`
- [x] Test Python environment and verify GitHub connection  
  - Commit: `chore: verify python setup and git remote`
- [x] Commit all setup changes  
  - Commit: `chore: initial commit with python project setup`

---

### 🧩 Define JSON Schema
- [x] Define schema fields in Python (dictionary format):  
  - [x] `id`, `name`, `age`, `gender`, `interestedIn`, `location`, `locationFlexibility`, `profileUrl`, `scrapeTimestampIndex`, `scrapeTimestampDetail`, `profileDetails`  
  - Commit: `feat: define profile schema as python dictionary`
- [x] Save schema reference as `profile_schema.json`  
  - Commit: `docs: add JSON schema reference file`
- [x] Validate schema logic using test data  
  - Commit: `test: validate schema structure with sample record`

---

### 🧮 Script A – Index Scraper (Python)
**Goal:** Collect directory data and create `profiles_master.json`.

- [x] Create `scripts/scrape_index.py`  
  - Commit: `feat: create index scraper script`
- [x] Fetch the main directory page with `requests`  
  - Commit: `feat: add HTTP request to fetch directory HTML`
- [x] Parse HTML using `BeautifulSoup`  
  - Commit: `feat: parse directory table with BeautifulSoup`
- [x] Extract profile fields from table rows:
  - [ ] `name`
  - [ ] `age`
  - [ ] `gender`
  - [ ] `interestedIn`
  - [ ] `location`
  - [ ] `locationFlexibility`
  - [ ] `profileUrl`
  - Commit: `feat: extract directory row data`
- [x] Assign unique internal IDs (e.g., incremental or UUID)  
  - Commit: `chore: add id assignment function`
- [x] Create profile dictionaries following schema  
  - Commit: `feat: construct profile dictionaries`
- [ ] Initialize empty fields for details (`profileDetails`, `scrapeTimestampDetail`)  
  - Commit: `chore: initialize empty detail fields`
- [x] Save all records into `/data/profiles_master.json`  
  - Commit: `feat: save scraped directory data to JSON`
- [x] Add polite rate limits between requests using `time.sleep()`  
  - Commit: `perf: add rate limiting for ethical scraping`
- [x] Test and print summary (e.g., “552 profiles saved”)  
  - Commit: `test: validate scrape output summary`

**Output:**  
`profiles_master.json` — dataset containing directory-level info.

---

### 🧾 Script B – Profile Scraper (Python)
**Goal:** Enrich each record in `profiles_master.json` with full profile text.

- [x] Create `scripts/scrape_profiles.py`  
  - Commit: `feat: create detailed profile scraper script`
- [x] Load `profiles_master.json` into memory  
  - Commit: `chore: load JSON dataset`
- [x] For each profile:
  - [x] Fetch `profileUrl` using `requests`  
    - Commit: `feat: request individual profile pages`
  - [x] Parse HTML with `BeautifulSoup`  
    - Commit: `feat: parse profile page HTML`
    - Commit: `feat: extract longform profile sections`
  - [ ] Insert parsed data into `profileDetails` field  
    - Commit: `feat: add extracted details to profile object`
  - [ ] Update `scrapeTimestampDetail`  
    - Commit: `chore: add timestamp for detail scrape`
- [x] Save updated data to `profiles_master.json`  
  - Commit: `feat: save enriched JSON dataset`
- [x] Validate by checking record count and example entries  
  - Commit: `test: verify enriched data structure`

**Output:**  
Updated `profiles_master.json` with both directory and profile-level text.

---

### 📦 Data Handling & Versioning
- [ ] Store each run as versioned snapshots:
  - [ ] `profiles_master_raw_<date>.json` (after Script A)
  - [ ] `profiles_master_enriched_<date>.json` (after Script B)
  - [ ] `profiles_master.json` (latest active file)
  - Commit: `chore: add versioned JSON snapshots`
- [ ] Ensure IDs stay consistent between scrapes  
  - Commit: `chore: maintain stable profile IDs`
- [ ] Append new profiles if the site updates  
  - Commit: `feat: implement incremental scraping logic`
- [ ] Keep raw data backups in `/data/backups/`  
  - Commit: `chore: add backup routine for data`

---

### 🐍 Convert JSON to pandas DataFrames
**Goal:** Load the JSON data into pandas for analysis.

- [ ] Create `scripts/convert_to_dataframe.py`  
  - Commit: `feat: create JSON-to-DataFrame converter`
- [ ] Load `profiles_master.json` using Python’s `json` module  
  - Commit: `feat: load JSON file for conversion`
- [ ] Import `pandas` and convert list of dicts → DataFrame  
  - Commit: `feat: create pandas DataFrame from JSON`
- [ ] Split into two DataFrames:
  - [ ] `demographics_df` – id, age, gender, interestedIn, location, locationFlexibility  
  - [ ] `text_df` – id, aboutMe, whatImLookingFor, nonNegotiables, etc.  
  - Commit: `feat: separate structured and text DataFrames`
- [ ] Clean data (drop nulls, normalize case, convert types)  
  - Commit: `chore: clean and normalize DataFrame columns`
- [ ] Merge both DataFrames on `id` for full dataset  
  - Commit: `feat: merge demographic and text DataFrames`
- [ ] Export to `/data/processed/` as CSV files  
  - Commit: `feat: export pandas DataFrames to CSV`
- [ ] Verify shape and column names in each DataFrame  
  - Commit: `test: validate DataFrame structure and consistency`

---

### 🔍 Post-Scraping Analysis (Python + pandas)
**Goal:** Analyze quantitative and qualitative trends.

- [ ] Use pandas to compute:
  - [ ] Mean and median age  
  - [ ] Counts by gender and interestedIn  
  - [ ] Frequency of locationFlexibility categories  
  - Commit: `analysis: generate demographic summaries`
- [ ] Use text_df for qualitative coding:
  - [ ] Identify tone and diction  
  - [ ] Extract recurring motifs or keywords  
  - [ ] Relate word choices to demographics  
  - Commit: `analysis: perform text and tone analysis`
- [ ] Save analysis results to `/data/analysis_results/`  
  - Commit: `feat: save analysis outputs as CSV and JSON`
- [ ] Optionally visualize trends (matplotlib or seaborn)  
  - Commit: `feat: add data visualizations`
- [ ] Document insights in `analysis_report.md`  
  - Commit: `docs: summarize analysis results`

---

### 🧠 JSON Storage Rationale
- [ ] Use JSON as canonical format for raw data  
  - Commit: `docs: confirm JSON as canonical format`
- [ ] Parse JSON directly into pandas for analysis  
  - Commit: `docs: document JSON-to-pandas workflow`
- [ ] Export structured derivatives as CSVs for sharing  
  - Commit: `feat: create CSV exports from pandas`

| Format | Pros | Cons |
|--------|------|------|
| **JSON** | Nested, flexible, ideal for both raw and parsed text | Slightly larger, requires parsing |
| **CSV** | Simple for numeric summaries | Poor at storing nested/long text |
| **pandas** | Enables statistical + textual analysis | Requires Python environment |

---

### 🧱 Full Python Workflow Summary
- [ ] Step 1: Define schema and folder setup  
  - Commit: `chore: finalize schema and project setup`
- [ ] Step 2: Run `scrape_index.py` → generate `profiles_master.json`  
  - Commit: `feat: complete index scraping`
- [ ] Step 3: Run `scrape_profiles.py` → enrich JSON with details  
  - Commit: `feat: complete profile scraping`
- [ ] Step 4: Run `convert_to_dataframe.py` → create pandas DataFrames  
  - Commit: `feat: convert JSON to pandas DataFrames`
- [ ] Step 5: Clean, analyze, and export summary results  
  - Commit: `analysis: clean and analyze pandas DataFrames`
- [ ] Step 6: Version and back up data files  
  - Commit: `chore: back up JSON and CSV outputs`
- [ ] Step 7: Document insights and publish anonymized findings  
  - Commit: `docs: publish analysis summary`

---

### ⚖️ Ethical Guidelines
- [ ] Confirm data source is public and scraping complies with `robots.txt`  
  - Commit: `docs: verify scraping compliance`
- [ ] Use data solely for academic or non-commercial research  
  - Commit: `docs: declare academic research purpose`
- [ ] Remove or hash identifying information before analysis  
  - Commit: `data: anonymize sensitive fields`
- [ ] Store raw and processed data securely  
  - Commit: `chore: enforce local data security`
- [ ] Credit the original site (Date Me Directory) in any publications  
  - Commit: `docs: add data source acknowledgment`

---

### 🪪 Metadata
- [ ] **Author:** Treesa Abraham  
- [ ] **Language:** Python 3  
- [ ] **Libraries:** `requests`, `beautifulsoup4`, `pandas`, `lxml`, `json`  
- [ ] **Data Storage Format:** JSON (raw), CSV (derived), pandas DataFrames (analysis)  
- [ ] **Purpose:** Python-based qualitative and quantitative data analysis of public self-presentations  
- [ ] **Version:** 3.0 – November 2025  
  - Commit: `chore: update metadata for Python-only version`
