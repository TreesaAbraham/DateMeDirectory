# Deploying to Vercel (Static)

This project is a static site located in `site/` and requires **no build step**.

## Vercel Dashboard Setup

1. Create a new Vercel project and import the repo.
2. In **Build & Output Settings**, set:
   - **Root Directory:** `site`
   - **Framework Preset:** `Other`
   - **Build Command:** *(leave blank / override and leave empty)*
   - **Output Directory:** `.`

Vercel supports configuring/overriding build behavior in the dashboard and via `vercel.json`.  
See: “Configuring a Build” and Project Configuration docs. :contentReference[oaicite:0]{index=0}

## Required URL + Asset Conventions

Because Vercel will deploy `site/` as the project root:

- ✅ Use **rooted paths** everywhere:
  - CSS: `/styles.css`
  - JS: `/app.js`, `/graph.js`, `/graph_hub.js`
  - Manifest: `/data/charts_manifest.json`
  - Images/charts: `/assets/...`
- ❌ Do not include `/site/` in any URL or asset path

## Optional: Clean URLs

If you add `vercel.json` with:

```json
{ "cleanUrls": true }
