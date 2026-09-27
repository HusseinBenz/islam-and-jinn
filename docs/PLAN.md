# Delivery plan

Scope updated 21 September 2026: **English articles and independently checked references. English subtitle files are no longer a deliverable.** Read the Arabic captions directly, preserve episode/section traceability, and write readable Markdown articles. Retain existing subtitle drafts as research; completing or reviewing that backlog is not required.

## 1. Establish the corpus

1. Inspect repository and the supplied yt-dlp installation.
2. Identify both boundary videos using first-party metadata: title, ID, upload date, duration, channel and description.
3. Inventory channel uploads and playlists. Build an inclusive date-window candidate set; separate related full episodes, unrelated uploads, short clips, and external references.
4. Confirm the series using explicit cross-links, playlists and episode descriptions. Preserve selection reasons and exclusions. Do not assume every intervening channel upload belongs to the series.
5. Save `data/catalog/episodes.json` in chronological reading order, retaining the Arabic title and original sequence. Mark any unconfirmed membership.

Acceptance: both boundaries present, every included episode has provenance, all date-window candidates are accounted for, no external cited interview is silently treated as an al-Sabeel episode.

## 2. Acquire and normalize captions

1. Use yt-dlp with no audio/video download; request original Arabic automatic captions, preferably original VTT plus SRT conversion.
2. Preserve raw metadata, description, download logs and timestamps. Save files under stable episode IDs rather than Arabic titles.
3. Rate-limit requests, resume existing files, and record no-caption/access failures honestly. Never use browser credentials without a concrete need and authorization.
4. Validate cue syntax and time order; clean YouTube rolling-caption duplication without destroying repeated speech. Create readable Arabic Markdown and machine-readable timestamped segments.
5. Calculate SHA-256 hashes and a completeness report for every episode. Automated captions remain unverified speech recognition.

Acceptance: a nonempty validated SRT per available episode, original caption retained, cue/word counts and hashes recorded; unavailable episodes remain blocked, never silently skipped.

## 3. Process one episode at a time

1. Read the complete cleaned transcript in bounded timestamped chunks; record coverage.
2. Extract its outline and chapter order, main claims, named entities and every cited reference. Preserve ambiguous Arabic readings for investigation.
3. Write an original English article with title, introduction, ordered headers, paragraphs, tags, source-video ID, timestamp locators and numbered footnotes.
4. Distinguish scripture, hadith, tafsir/fiqh, historical claims, research, experiments, interviews, personal accounts and presenter's opinion.
5. Review the English article against the Arabic for meaning, religious terminology, names, attribution and important qualifications. Use targeted audio checks where caption ambiguity affects an article or citation. No sentence-by-sentence or timed English subtitle translation is required. Adaptation permission is recorded in `PERMISSIONS.md`.
6. Keep extraction notes and uncertain claims in research files, outside the public article.

Acceptance: full transcript reading logged; fluent article reviewed against Arabic; article follows episode structure; every source mention is recorded even when unverified. Timed English files are not an acceptance criterion.

## 4. Independently verify references (highest priority)

1. Assign stable IDs and retain episode, cue time, Arabic source mention, claim, source type and intended supporting passage.
2. Qur'an: verify surah/ayah and wording in a reliable text; credit any quoted translation and respect its licence.
3. Hadith: identify collection, book, number and exact report; record grading and grader, numbering variants, and scholarly disagreement.
4. Books/scholar opinions: inspect the cited edition/page or primary publication; separate interpretation from consensus claims.
5. Studies/experiments: identify authors, title, journal, year and DOI; examine methods and conclusion, and distinguish controlled study from anecdote.
6. Interviews/testimony: identify speaker and original recording, date and exact timestamp; verification of a recording does not establish its claimed supernatural cause.
7. Record canonical URL, date accessed, evidence locator, support assessment and unresolved questions. Never fabricate bibliographic detail.
8. Trace every article footnote to a registry record; unresolved material prevents that article's ready status.

Acceptance: each publishable factual claim has a checked supporting source; each source is labelled by type; citations resolve; scope and uncertainty remain faithful to the evidence.

## 5. Assemble the static encyclopedia

1. Only after corpus processing, derive navigation from the actual video units and sections.
2. Keep authored pages in `.md` with metadata for order, tags, description, episode IDs and review status.
3. Build a portal, article pages, video-order index, and source/methodology page. Use cross-links where useful without reorganizing away the original sequence.
4. Simple typographic design: deep ink, clear paper-like reading surface, restrained teal accents, generous article line height, responsive navigation and article contents.
5. Use numbered inline citations and article-footer references with backlinks. Static output must not require an API or database.
6. Keep raw captions, metadata, research logs and draft/unverified pages out of public output.

Acceptance: all included completed articles navigable; Markdown is canonical; no broken internal links, missing references, placeholder text, or source-data leakage; production build passes. Publish only the completed reviewed scope.

## 6. Quality and continuation

- Validate inventories, transcript parsing, reference integrity and static build.
- Review Arabic-to-English terminology, unsupported certainty and claims touching health.
- Make scoped commits: corpus tooling, corpus inventory, episode/reference batches, Markdown site, final verification.
- Update task ledger and handoff at every checkpoint: counts, completed IDs, current unit, concrete next command, blockers and last validation.
- Never equate scaffold completion with encyclopedia completion.
