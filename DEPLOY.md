# Deploying to Vercel (Static)

This project is a static site located in `site/` and requires **no build step**.

## Vercel Project Settings

When importing the repo into Vercel, set:

- **Root Directory:** `site`
- **Framework Preset:** `Other`
- **Build Command:** (leave blank)
- **Output Directory:** `.`

## Asset Path Rule

Because `site/` becomes the deployment root, do **not** include `/site/` in any URLs.

Use rooted asset paths everywhere, e.g.:

- `/styles.css`
- `/app.js`
- `/graph.js`
- `/graph_hub.js`
- `/data/charts_manifest.json`
- `/assets/charts/...`

## Local Preflight

From repo root, run:

```bash
python3 -m http.server --directory site 8000
