# Date Me Directory — Static Report Site

This folder contains a plain static site (HTML/CSS/JS) intended to be hosted on Vercel (or anywhere that serves static files).

## Local preview

From the repo root:

```bash
python3 -m http.server --directory site 8000



Lovable,
look at websites I like, screenshot, show into ai
mini max


claude bot
- 24/7 personal assistant
''

ok c 

personality types
mono vs poly relationships
professions



1. add dating sytle and add to the website. 
- scrape for the 323 profiles
- should be a mosaic liek word graph 2. Do they bring up kids more often? or not?
- make d3 and seaborn, 
- integrate into html

2. second graph: profession and gym habits
- one we need to scrape their careers -- do not bother any that doesn't mention it.
- then make we scrape data about people's gym habits or exercise habits in general
- seaborn and d3
- add to html website

3. 






# Date Me Directory — Front-End Refresh (Playful Data Story) ✅ Checklist

Use this checklist to implement a UI refresh that blends **playful data-story energy** with **real statistical clarity**.

---

## ✅ Design spec (locked)

- [x] **Vibe:** B — Playful data story  
- [x] **Typography:** Georgia everywhere  
- [x] **Navigation:** Charts-first  
- [x] **Homepage stays:** Intro + Featured + Chart Directory (to hubs) + Appendix  
- [x] **Chart pages:** Story card layout  
- [x] **Playfulness:** Medium  
- [x] **Primary CTA:** “Browse all charts”  

---

## ✅ Accent color roles (semantic)

- [x] **Accent 1:** Primary highlight (buttons, links, key badges)
- [x] **Accent 2:** Insight callouts / key finding boxes
- [x] **Accent 3:** Method callouts / technical notes
- [x] **Accent 4:** Featured charts framing
- [x] **Accent 5 (optional):** Appendix/metadata chips

> Rule: Color must have meaning. No random accent confetti.

---

## ✅ Constraints (do not break the site)

[ ] Do **not** rename files or folders
[ ] Do **not** change chart asset paths
[ ] Do **not** change data/manifest structure
[ ] Prefer **CSS + HTML only**
[ ] Only touch JS if absolutely needed for UI polish (must not affect routing/paths)

---

## ✅ Planned use of Cursor/Windsurf

### When we use them
[ ] Use Cursor/Windsurf during **Phase 1 only** (refactor-heavy work)

### What we use them for
[ ] Build/clean up CSS design system (typography, spacing, components)
[ ] Homepage layout polish (keep structure)
[ ] Apply Story card consistency to chart hubs/pages (only where necessary)

### What we do NOT use them for
[ ] Renaming files/folders
[ ] Editing asset paths
[ ] Reorganizing data/manifest files
[ ] “Rewrite the entire project” prompts

### Usage rules (to avoid burning free credits)
[ ] Work **one file at a time**
[ ] Include constraints in every prompt
[ ] Review diffs after each edit
[ ] Run local preview after each small batch

---

## ✅ Files expected to change (small commits)

[ ] `site/styles.css`
[ ] `site/index.html`

*(Only if necessary for Story card template work)*
[ ] `site/graph_hub.js`
[ ] Chart hub page HTML templates (if applicable)

---

## ✅ Workflow checklist

### Phase 0 — Safety snapshot
[x] Commit a snapshot before UI changes
[x] Confirm local preview works

### Phase 1 — Refactor (Cursor/Windsurf)
[x] Define design tokens (typography + spacing) in `site/styles.css`
[x] Create reusable components in CSS:
  [x] badges/chips (Accent 1/5)
  [x] Insight callout style (Accent 2)
  [x] Method callout style (Accent 3)
  [x] Featured framing style (Accent 4)
  [x] card + grid layout
[x] Update homepage framing in `site/index.html`:
  [x] Make “Browse all charts” the primary action
  [x] Featured section feels curated (not random)
  [x] Directory feels like the main destination
  [x] Appendix looks quiet but intentional

### Phase 2 — Final polish + QA (no Cursor/Windsurf required)
[ ] Standardize spacing and section rhythm across pages
[ ] Improve readability (line height, max width, header hierarchy)
[ ] Confirm responsive behavior (mobile/tablet/desktop)
[ ] Confirm keyboard focus styles are visible
[ ] Confirm contrast is readable for callouts and text
[ ] Verify no links 404 and no charts break

---

## ✅ Story card chart page template (consistency)

Every chart page should follow this structure:

[ ] Title
[ ] Hook line (1 sentence, playful)
[ ] “What you’re looking at” (1–2 sentences, factual)
[ ] Chart (large, centered)
[ ] Key takeaway (Insight callout)
[ ] Method notes (Method callout; optional collapsible)
[ ] Back to directory (Charts-first navigation)

---

## ✅ Pre-merge quality checks

### Visual
[ ] Georgia is applied site-wide
[ ] Headings and spacing are consistent
[ ] Insight vs Method callouts are visually distinct
[ ] Featured charts feel curated

### Functional
[ ] Homepage links do not 404
[ ] Directory links route correctly to hubs
[ ] Chart pages load SVG/PNG/D3 outputs correctly
[ ] No asset paths changed

---

## ✅ Commit message examples

[ ] `chore(site): snapshot before UI refresh`
[ ] `style(site): define playful data-story theme`
[ ] `style(site): polish homepage hierarchy + charts-first CTA`
 [ ] `style(site): standardize story-card chart pages`

