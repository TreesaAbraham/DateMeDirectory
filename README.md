git add .
git commit -m 'message'
git push origin main

In practice, consistency is about being adaptable. Don't have much time? Scale it down. Don't have much energy? Do the easy version. Find different ways to show up depending on the circumstances. Let your habits change shape to meet the demands of the day.

Adaptability is the way of consistency.”

James Clear

# 💘 Date Me Directory Data Extraction & Analysis

This project collects and analyzes data from the [Date Me Directory](https://dateme.directory/browse), a public listing of user-submitted "date me docs."  
The goal is to extract structured demographic data (from the directory table) and unstructured textual data (from individual profile pages), then perform qualitative and literary-style analysis of dating self-presentations.

---

## Master Checklist (with Commit Messages)

### 🏗️ Setup & Planning
- [x] Create project folder and initialize Git repository  
  - Commit: `chore: initialize project folder and git repo`
- [x] Install required libraries for scraping (`requests`, `BeautifulSoup`, etc.)  
  - Commit: `chore: install scraping dependencies`
- [x] Define data schema in JSON format  
  - Commit: `feat: define base JSON schema for profiles`
- [x] Decide on consistent folder structure for data outputs  
  - Commit: `chore: establish folder structure for data storage`
- [x] Add ethical and privacy statement to documentation  
  - Commit: `docs: add ethical and privacy statement`
- [x] Create `.gitignore` to exclude data snapshots and raw HTML  
  - Commit: `chore: add .gitignore for data and cache files`
- [X] Make `/data/` directory for storing JSON and HTML outputs  
  - Commit: `chore: create data directory`
- [X] Write `README.md` with overview, schema, and scraping workflow  
  - Commit: `docs: add detailed project README`
- [x] Test Python environment and verify GitHub remote connection  
  - Commit: `chore: verify environment and git remote`
- [x] Commit initial setup  
  - Commit: `chore: initial commit with project structure`

- [x] Validate schema using sample data  
  - Commit: `test: validate JSON schema with example profile`

---

### Script A – Index Scraper
**Goal:** Collect directory data and create a master JSON file.

- [x] Fetch the main directory page (`https://dateme.directory/browse`)  
  - Commit: `feat: add initial request to fetch directory page`
- [x] Handle pagination or “load more” logic  
  - Commit: `feat: implement pagination handling for directory`
- [x] Extract each profile row’s data  
  - Commit: `feat: parse profile table for name, age, gender, etc.`
- [x] Assign unique internal `id` to each person  
  - Commit: `chore: add id assignment logic for profiles`
- [x] Create JSON objects using schema  
  - Commit: `feat: build profile objects according to schema`
- [ ] Initialize `profileDetails` as `{}` and `scrapeTimestampDetail` as `null`  
  - Commit: `chore: initialize empty detail fields for profiles`
- [ ] Save results to `profiles_master.json`  
  - Commit: `feat: export directory data to profiles_master.json`
- [ ] Archive raw HTML snapshots  
  - Commit: `chore: save raw HTML snapshots for reproducibility`
- [ ] Add polite rate limits between requests  
  - Commit: `perf: add request delay to prevent rate limiting`
- [ ] Verify JSON output integrity  
  - Commit: `test: verify JSON structure from Script A`

**Output:**  
`profiles_master.json` — canonical dataset with directory-level info.

---

### Script B – Profile Scraper
**Goal:** Visit each `profileUrl` from the JSON dataset and extract detailed text sections.

- [ ] Load `profiles_master.json`  
  - Commit: `chore: load master dataset for profile enrichment`
- [ ] For each profile:
  - [ ] Fetch profile page using `profileUrl`  
    - Commit: `feat: request individual profile pages`
  - [ ] Save raw HTML locally  
    - Commit: `chore: store raw HTML for each profile`
  - [ ] Extract text sections: “About Me,” “What I’m Looking For,” “Green Flags,” “Non-negotiables,” “First Date Ideas”  
    - Commit: `feat: parse longform text fields from profile pages`
  - [ ] Insert parsed text into `profileDetails`  
    - Commit: `feat: merge parsed details into JSON objects`
  - [ ] Update `scrapeTimestampDetail`  
    - Commit: `chore: record timestamp for detail scrape`
- [ ] Save enriched dataset back to `profiles_master.json`  
  - Commit: `feat: update profiles_master.json with enriched data`
- [ ] Add randomized delay between requests  
  - Commit: `perf: randomize request delays for ethical scraping`
- [ ] Validate sample enriched entries  
  - Commit: `test: verify enriched JSON entries after scraping`

**Output:**  
Updated `profiles_master.json` with both directory and profile data.

---

### Data Handling & Versioning
- [ ] Save versioned snapshots:
  - [ ] `profiles_master_raw_<date>.json` (after Script A)
  - [ ] `profiles_master_enriched_<date>.json` (after Script B)
  - [ ] `profiles_master.json` (current file)
  - Commit: `chore: version data snapshots`
- [ ] Ensure `id`s remain stable between runs  
  - Commit: `chore: verify ID consistency between runs`
- [ ] Append new profiles for future scrapes  
  - Commit: `feat: add logic for appending new profiles`
- [ ] Backup raw data securely  
  - Commit: `chore: create backup routine for JSON files`

---

### JSON Storage Rationale
- [ ] Use JSON as canonical format for both scripts  
  - Commit: `docs: confirm JSON as canonical data format`
- [ ] Preserve nested `profileDetails` fields  
  - Commit: `chore: verify nested field structure`
- [ ] Support later CSV exports or DB imports  
  - Commit: `docs: note compatibility with future data pipelines`


### Full Workflow Summary
- [ ] Step 1: Define schema and create project folders  
  - Commit: `chore: finalize schema and folder setup`
- [ ] Step 2: Run Script A → scrape directory → produce `profiles_master.json`  
  - Commit: `feat: complete initial directory scrape`
- [ ] Step 3: Run Script B → enrich profiles with text → update file  
  - Commit: `feat: complete detail scraping phase`
- [ ] Step 4: Backup versions in `/data/` folder  
  - Commit: `chore: store backup versions`
- [ ] Step 5: Convert data to CSV for stats (optional)  
  - Commit: `feat: export CSV summaries`
- [ ] Step 6: Conduct literary and rhetorical analysis  
  - Commit: `analysis: conduct qualitative evaluation`
- [ ] Step 7: Publish anonymized results  
  - Commit: `docs: publish anonymized report`

---

### Ethical Guidelines
- [ ] Confirm data is from a public directory  
  - Commit: `docs: verify public data usage`
- [ ] Restrict use to academic or non-commercial analysis  
  - Commit: `docs: state research-only purpose`
- [ ] Remove or hash identifying information  
  - Commit: `data: anonymize sensitive fields`
- [ ] Respect `robots.txt` and TOS  
  - Commit: `chore: confirm scraping compliance`
- [ ] Maintain local secure storage  
  - Commit: `chore: secure raw dataset storage`
- [ ] Cite Date Me Directory as source  
  - Commit: `docs: add data source citation`

---

### Metadata
- [ ] **Author:** Treesa Abraham  
- [ ] **Purpose:** Qualitative + Literary Data Analysis on Public Digital Self-Representation  
- [ ] **Version:** 1.0 – October 2025  
  - Commit: `chore: finalize project version metadata`

