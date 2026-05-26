# Netlify + Independent CText Proxy Setup

This project now supports a long-running CText proxy (`server/ctextProxyServer.js`) for more stable variant search results.

## 1) Deploy proxy with free subdomain (Render)

Use Render Blueprint from this repo (`render.yaml`):

1. Open:
   - `https://render.com/deploy?repo=https://github.com/Lingyue-001/mathesis`
2. Select the `mathesis-ctext-proxy` web service.
3. Set env var:
   - `CTEXT_PROXY_ALLOW_ORIGIN=https://<your-netlify-site>.netlify.app`
4. Deploy and wait until `Live`.
5. Verify:
   - `https://<your-proxy>.onrender.com/healthz`
   - expected: `{ "ok": true, ... }`

## 2) Point Netlify site to this proxy

In Netlify Site settings -> Environment variables, add:

- `CTEXT_PROXY_ORIGIN=https://<your-proxy>.onrender.com`

Then trigger a new deploy on Netlify.

`src/transcriptions/tei_hanshu/1a.html` reads this value at build time and sets `window.__CTEXT_PROXY_ORIGIN`.

## 3) Verify on deployed site

Open:

- `/transcriptions/tei_hanshu/1a/?ctextDebug=1&ctextRefresh=1`

Important:

- use `/1a/` (directory route), not `/1a.html`.
- `/1a.html` is now auto-redirected to `/1a/`.

Then double-click a highlighted node and check:

- debug line shows `Source: middleware (https://<your-proxy>.onrender.com)`
- variants do not fall back to `-` for normal searchable cases.

## 4) Emergency fallback

If proxy is down, you can still force JSON source via URL:

- `?ctextSource=json`
