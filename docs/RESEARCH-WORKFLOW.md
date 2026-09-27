# Reproducible research workflow

Run commands from the repository root in PowerShell. Use the isolated interpreter; activation is unnecessary.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-research.txt
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe scripts/corpus.py discover
.\.venv\Scripts\python.exe scripts/corpus.py metadata
```

Review `data/catalog/candidates.json` before acquisition. `selection` must be `core`, `companion`, `compilation`, `excerpt`, or `excluded`, with a reason. Membership is a human editorial decision. `pending` and `excluded` rows are never downloaded automatically. Only one process should write this ledger at a time.

```powershell
.\.venv\Scripts\python.exe scripts/corpus.py download
.\.venv\Scripts\python.exe scripts/corpus.py normalize
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Each command is resumable. Use `--ids VIDEO_ID` for a bounded subset. Do not use `--refresh` casually: it recontacts YouTube. Commands log subprocess output in `data/logs/`; inspect a failed attempt before retrying. No audio/video is downloaded. `--keep-video` retains the original VTT during subtitle conversion; `--skip-download` prevents media download.

The default FFmpeg/Deno location is the user's supplied asset directory. On another machine, set `$env:YTDLP_ASSETS` to a directory containing those tools. Do not commit local executables or environments.

## Folder map

| Folder | Purpose | Git/publication |
| --- | --- | --- |
| `data/raw/channel/` | Original first-party inventory snapshot | Local only |
| `data/raw/metadata/` | Full video metadata and descriptions | Local only |
| `data/raw/subtitles/VIDEO_ID/` | Original Arabic VTT and converted SRT | Local only |
| `data/transcripts/VIDEO_ID/` | Cleaned Arabic Markdown and timestamped segments | Local only |
| `data/catalog/` | Sanitized inventory, progress and hash reports | Tracked, not site assets |
| `data/references/` | Extracted reference and verification records | Tracked |
| `data/translations/` | Authored English translation segments and source hashes | Tracked research drafts; not site assets |
| `data/exports/translations/` | Generated English SRT drafts and original-cue maps | Local only |
| `research/episodes/` | Original editorial notes and coverage records | Tracked, not site assets |
| `content/` | Canonical English Markdown pages | Tracked; only reviewed pages publish |

## Working on an episode

1. Claim one episode ID in the task ledger/handoff.
2. Read `segments.ar.json` in complete successive timestamp ranges. Record reviewed ranges without gaps. The normalization pass is not a reading/review pass.
3. Create an original outline, a compact source/claim map and an ASR uncertainty list in `research/episodes/VIDEO_ID.md`.
4. Add every encountered source to `data/references/`; do not silently drop hard-to-identify references.
5. Independently inspect each reference. Search snippets help discovery; they do not prove support. Preserve exact source locators and the result of checking them.
6. Translate and adapt into polished English in `content/articles/` with the episode's section order, tags and Markdown footnotes. The user confirmed permission in `PERMISSIONS.md`. Write articles directly from the Arabic captions; mark meaningful omissions and outstanding source checks. Full English subtitle translations are outside scope as of 21 September 2026.
7. Update status only after the artifact exists and passes review. Commit the bounded work and update `docs/HANDOFF.md`.

## Tool documentation

Acquisition follows [yt-dlp's official subtitle options](https://github.com/yt-dlp/yt-dlp#subtitle-options): request automatic captions explicitly, use the `ar-orig` track to avoid YouTube's machine translation, retain VTT, and convert with FFmpeg. Version used: `2026.8.19`.

## Index, validation and archive commands

```powershell
.\.venv\Scripts\python.exe -m scripts.work_packages
.\.venv\Scripts\python.exe -m scripts.validate
.\.venv\Scripts\python.exe -m scripts.export_corpus
```

`work_packages` refreshes derived indexes and creates missing research packages; it preserves existing episode notes and enriched description reference records. `candidates.json` is authoritative for status. `episodes.json` is a derived selected-video/navigation index. Run writers sequentially.

The ZIP in `data/exports/` contains all 23 ordered Arabic SRT/VTT sets, cleaned Markdown, segment JSON and hash reports. It is a local research download, not a public website asset.

An optional attempt to obtain YouTube's English machine translations hit HTTP 429 for most requested tracks. Exactly one draft was obtained (`nJv0h3zXbb0`); it is labelled unreviewed. The optional attempt was stopped, and all Arabic files were successfully downloaded and converted separately. A single Google Translate connectivity probe also returned 429; no batch translation was attempted. This is an archived access record. English subtitle acquisition/translation is no longer required; use Arabic directly for article writing.

## Archived tooling: timed English translations (outside current scope)

The user removed this deliverable on 21 September 2026. The following records the earlier workflow for preserved research artifacts only. Do not follow it as a work queue or require subtitle completion for articles.

The first complete authored draft is `data/translations/3sVCCYYmuzU.en.draft.json`, covering all normalized source indices **0–1157 inclusive**. English export: `data/exports/translations/3sVCCYYmuzU.en.complete-draft.srt`. There is no remaining untranslated index in episode 5. Complete draft coverage is **1/23**; reviewed translations remain **0/23**. Follow `research/translations/3sVCCYYmuzU-review.md` for 105 segment notes and source mappings. The final cue retains the original 2.119-second overhang beyond the video metadata duration; audiovisual review must resolve it.

Append English text with a `source_segment_index` referring to the zero-based index in the original normalized Arabic JSON. Keep the translation distinct from the article: preserve the speaker's statements, qualifications and attribution; put editorial repairs in `review_notes`. Source index 25 has a bracketed provisional **[not]**, because the auto-captions contradict the immediately following sentence about children. Audio review must resolve it.

```powershell
.\.venv\Scripts\python.exe -m scripts.translations
.\.venv\Scripts\python.exe -m scripts.translations --export
```

The command validates hashes of both the normalized Arabic file and original SRT, rejects duplicate/unordered indices and false completion claims, and prints the first untranslated index. Export creates a labelled partial or complete **draft**, with original timestamps and a separate mapping back to Arabic cue numbers. The output has one English cue per translated normalized segment, rather than repeating YouTube's rolling-caption carryover cues. No text is translated by the exporter itself. Readability and audiovisual accuracy still need review.

Do not edit the source hashes to silence a mismatch: reconcile the translation with the changed Arabic source first. Full coverage is distinct from editorial review. Keep `reviewed_at` null until review is actually performed. The regular corpus validator and derived summary now inspect these translation artifacts too.
