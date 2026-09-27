# Website preview

Latest local refresh: **23 September 2026**, fifteen draft articles across seventeen static pages. Build link/anchor validation passed; the new `/articles/ruqyah-psychological-distress/` route returns HTTP 200 with 16 numbered citations and 16 backlinks. Local preview: [http://127.0.0.1:8765/articles/ruqyah-psychological-distress/](http://127.0.0.1:8765/articles/ruqyah-psychological-distress/), hidden server PID 26052. The hosted version below still contains six articles. Rebuilding a local preview does not automatically deploy it.

The user requested a primitive website while research continues on 11 September 2026. It is an explicitly labelled **private draft preview**. No article has been promoted to `ready`.

## Authored source and generated output

- `content/articles/*.md`: canonical episode articles, unchanged by site rendering.
- `content/pages/*.md`: canonical portal introduction and project/method page.
- `website/build.py`: static generator with a reviewed-only default and explicit `--preview` draft mode.
- `website/site.css`: responsive typography and layout; no client JavaScript, remote fonts, tracking, media or runtime service dependencies.
- `dist/`: ignored generated site. Index, about page, fifteen article pages, stylesheet, robots file and build manifest.
- Numbered footnotes appear in first-use order, including inside tables. Every occurrence has a return link. Native contents/collection disclosures work without JavaScript.

## Build and preview

```powershell
.\.venv\Scripts\python.exe -m pip install -r website/requirements.txt
.\.venv\Scripts\python.exe website/build.py --preview
.\.venv\Scripts\python.exe -u -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Use a fresh output directory for a different article set, e.g. `--output out/reviewed`. The generator rejects unexpected/stale files to prevent draft pages remaining in a later reviewed-only output. `--preview` adds noindex metadata and disallows crawling; **these are not access control**. Keep the hosted draft Site owner-private.

## Registered private Site

- Site ID: `appgprj_6aa4012326c8819184330c7a63d291e9`.
- Sanitized checkout: `C:/Users/Hamza/Documents/GitHub/Islam-and-Jinn-preview`.
- The authoritative hosting manifest is in that checkout's `.openai/hosting.json`. Reuse this Site; never register another one on continuation.
- The research Git repository is never pushed to Sites. Export only the allowlisted article Markdown, page Markdown, renderer, styles and static output:

```powershell
.\.venv\Scripts\python.exe -m website.export_preview C:/Users/Hamza/Documents/GitHub/Islam-and-Jinn-preview
```

The exporter refuses a destination inside the research repository and rejects unexpected/stale files in the checkout. Use the Sites skills to commit/push the sanitized checkout, package its `dist`, save the exact pushed revision and privately deploy. Do not persist credentials or change the audience as a shortcut.

## Validation and continuation

- Twelve tests include a regression for table footnotes being numbered after later paragraph citations and a missing-reference failure.
- Build validation checks all fifteen HTML routes, asset/internal links, heading IDs and every exact footnote backlink.
- Desktop portal and phone-sized article inspected. Episode 6 at a 390-pixel viewport has no page-level horizontal overflow; tables have a local scrolling region. A citation jump and return were exercised in the browser.
- Site is a reading preview, not completion of the encyclopedia. Continue episode 14 and the article/reference backlog in `HANDOFF.md`. When article coverage changes, update the authored progress statements in `content/pages/about.md` as well as the research ledgers.
- Before a public release: complete editorial/reference review, use reviewed-only output, update the project page and explicitly resolve the requested audience. Do not infer publication readiness from a passing build.

## Confirmed deployment

Owner-private deployment succeeded on 11 September 2026: [Open Jinn in Islam](https://jinn-in-islam-reading.hamzasghaier10-0.chatgpt.site). The app browser handoff returned queued; local browser QA succeeded before deployment.

- Version 1: `appgprj_6aa4012326c8819184330c7a63d291e9~appgver_059674a761188191833d3a548281df0d`.
- Deployment: `appgdep_6aa403f52e688191bf6a21d02f0cad32`.
- Sanitized-source SHA: `071e9ce86997b3cad06be837a5ecb5a68ef49be0`.
- Archive: `data/exports/jinn-reading-preview.tar.gz`; 12 files, generated output plus manifest, inspected before saving.

Packaging recovery: the curated 0.1.58 plugin directory disappeared during the turn. The bundled 0.1.66 package-site.mjs selected Windows system Bash, which misread Windows paths. Git Bash ran the official shell helper, but tar interpreted C: archive names as remote hosts. The successful invocation used C:/Program Files/Git/bin/bash.exe, the bundled skills/sites-hosting/scripts/package-site.sh, and /c/Users/... paths for the helper, project and archive. No manual archive substitute or plugin edit was needed. Rediscover the installed helper if it moves again; do not recreate the registered Site.

