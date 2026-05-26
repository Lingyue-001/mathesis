# eleventy-symbolic-math

A research website built with Eleventy to explore symbolic math, calendrical systems, and cross-tradition textual relationships via graph data.

## Current scope (existing branch)
- Goal: Build a searchable site from a Neo4j node-edge database.
- Focus: Relations between numbers, mathematical operations, and symbolic/cosmological systems in early Chinese astronomical texts.
- Visualization intent: Make the scientific/algorithmic system and the philosophical/symbolic system visible side-by-side, including how a single number aggregates multiple symbolic contexts.
- Long-term intent: Expand to multiple texts and traditions to reveal patterns missed by classical philology alone.

## Planned scope (new branch)
- Goal: A Sanskrit manuscript visualization platform with scans, transcription, and translation.
- Interaction: Align transcription/translation to the manuscript image; reflect materiality of the manuscript in the UI.
- Search: Flexible matching (stems, inflectional variants, sandhi, compound subparts) and collection building (e.g., all occurrences of a word).
- OCR tool integration: Use an existing tool for segmentation + recognition; implement post-correction from the author’s paper and integrate into a user-friendly workflow.

## Project notes
- For current status and prioritized todos, see `NOTE_当前需求清单和待办_Current_Status_and_Todo.md`.
- For completed changes and retrospectives, see `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`.

## Data sources and workflow (current)
- Search/data pages load from `src/data.json`.
- Visualization page loads from CSV exports in `static/` (see `static/node-export.csv` and `static/relationship-export.csv`).
- If you update Neo4j data, ensure both JSON and CSV exports stay in sync, or establish a single source of truth.

## Data pipeline (proposed)
- Canonical source: Neo4j graph.
- Export step: Neo4j -> JSON for Eleventy, and (if needed) CSV for visualization.
- Document the exact export command or script here once stabilized.

## Development
- Start: `npm run start`
- Build: `npm run build`
- Debug query flags reference: `DEBUG_FLAGS_REFERENCE.md` (auto-generated from `src/js/debugFlags.mjs`)
- Beginner quick guide: `DEBUG_FLAGS_QUICKSTART.md`

## Environment And Migration
- Node version pin: `.nvmrc` (`20`)
- Environment variable template: `.env.example`
- Python dependency snapshot: `requirements.txt`
- Windows migration + verification notes: `迁移说明_Windows环境与验证.md`
- Environment matrix and installer notes: `环境清单_安装矩阵_Environment_Matrix.md`
- Local Node scripts now auto-load `.env` and `.env.local` without overriding existing shell or deploy-platform env vars.
- One-command helpers:
  - `npm run setup:mac`
  - `npm run setup:windows`
  - `npm run verify:install`

## Debug Flags Navigation (Quick Index)
- If you want a simple “what should I click/use now” guide:
  - `DEBUG_FLAGS_QUICKSTART.md`
- If you want full parameter table and exact defaults:
  - `DEBUG_FLAGS_REFERENCE.md`
- If you need to add or change a debug URL flag:
  - `src/js/debugFlags.mjs`
- If you need to check how the page actually consumes flags:
  - `src/transcriptions/tei_hanshu/1a.html`
- If you need to change how docs are auto-generated:
  - `scripts/generate-debug-flags-doc.mjs`

## Independent CText proxy (recommended for stable variant search)
- Local run: `npm run start:ctext-proxy` (default `http://localhost:8787`).
- Health check: `GET /healthz`.
- Deploy guide (Render free subdomain + Netlify env wiring):
  - `NETLIFY_CTEXT_PROXY_SETUP.md`
- Netlify build-time env var for frontend default proxy:
  - `CTEXT_PROXY_ORIGIN=https://<your-proxy>.onrender.com`

## Log Navigation (Timeline + Tag)
- Timeline source (primary): `LOG_已完成改动和复盘_Completed_Changes_and_Retrospective.md`
- Tag-grouped view (auto-generated): `LOG_按标签视图_By_Tag.md`
- Update command: `npm run generate:log-by-tag`

### CText lookup (dev middleware)
- API: `/api/ctext/search?q=<term>`
- Cache: responses are cached under `tmp/ctext_cache/` (default TTL: 6h).
- Force refresh: add `&refresh=1`.
- Global throttle: requests are serialized (concurrency=1) with gap `CTEXT_GLOBAL_GAP_MS` (default `1200` ms).
- Fetch mode:
  - `CTEXT_FETCH_MODE=browser` (default): use Playwright persistent browser session, fallback to HTTP on browser errors.
  - `CTEXT_FETCH_MODE=http`: use plain HTTP requests only.
- For browser mode, install dependency once:
  - `npm i -D playwright`

### Static CText cache build (for GitHub Pages)
- Step 1, build a candidate cache from local middleware results:
  - `npm run build:ctext-cache -- --base http://127.0.0.1:8080 --mapped-text src/transcriptions/tei_hanshu/1a.xml --timeout 90000 --delay 250`
- Step 2, inspect the candidate outputs:
  - Candidate cache: `tmp/ctext-static-build/ctext-cache.candidate.json`
  - Build report: `tmp/ctext-static-build/ctext-cache.report.json`
- Step 3, publish the inspected candidate to the frontend cache file:
  - `npm run promote:ctext-cache`
- Manual补词（例如单独补 `黃鐘,鐘,五`）:
  - `npm run build:ctext-cache -- --base http://127.0.0.1:8080 --terms 黃鐘,鐘,五 --timeout 30000`
- Safe-build rules:
  - The builder bypasses middleware cache by default (`refresh=1`) so stale localhost results are not reused.
  - The builder rebuilds from scratch by default and does not merge the existing published cache unless `--merge-existing` is passed.
  - The builder uses `curl` for localhost collection by default; pass `--transport fetch` only for debugging transport differences.
  - Entries with positive `hitCount` but empty `stats` text groups are rejected and never promoted.
- Published frontend cache file:
  - `static/ctext-cache.json`
- Frontend source mode:
  - `ctextSource=auto`: localhost uses middleware; non-localhost uses static cache.
  - Optional override: `?ctextSource=middleware` or `?ctextSource=json` or `?ctextSource=cache`.
- Parser fixture tests:
  - `npm run test:ctext-stats-parser`

## Deployment checklist (GitHub Pages)
1) Pages source set to **GitHub Actions** (not `/docs` branch).
2) Build output matches workflow artifact path (`dist`).
3) `pathPrefix` set for project site (`/mathesis/`) in production.
4) All asset/route links use Eleventy `| url` filter or base-aware fetch.
5) Push a change and verify CSS/JS/network requests in the deployed site.
