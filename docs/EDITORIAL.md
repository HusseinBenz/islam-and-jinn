# Editorial and reference rules

## Voice

Write from within Islam: jinn are part of Allah's creation and belong to the unseen. Use clear, welcoming English. Avoid sensationalism or repeatedly distancing ordinary religious statements with “Muslims allegedly believe.” Where interpretation is disputed, identify whose view is being explained and represent disagreement fairly.

Faith and careful sourcing belong together. Qur'anic revelation, a hadith report, a scholar's interpretation, an experiment and someone's experience are different kinds of evidence. An account can be documented without its interpretation being independently proven. Never present a testimony or controversial causal theory as a medical finding, diagnose readers, encourage fear of neighbours, or recommend abandoning professional care.

## Source dependence

The deliverable is an English article, not translated subtitles. Work directly from the Arabic transcript, retaining meaningful content and section order while removing spoken repetition and presentation logistics. Use numbered inline citations with a References section at the bottom and backlinks, in the style of Wikipedia.

The channel sets the topic, sequence and claims to investigate. Independent sources verify claims and references; they must not be used to invent what a missing episode said. Preserve the presenter's distinctions and opposing arguments. Do not claim affiliation with or endorsement by al-Sabeel.

## Article metadata

Required fields: `title`, `slug`, `description`, `order`, `tags`, `source_videos`, `status`, `reviewed_at`. Status progresses through `draft`, `reference-review`, `ready`. Only `ready` articles enter the published encyclopedia.

Use ordinary Markdown footnotes (`[^source-id]` and `[^source-id]: ...`). The renderer must number them in reading order, collect them at the article footer and provide return links. Include the source type, creator, title, publication details, precise locator, URL and access date as appropriate. Video citations link to exact timestamps.

## Reference registry

Each entry includes `id`, `type`, `mentions` (episode ID, start/end time, exact Arabic mention), `claim`, `title`, `creators`, `url`, `locator`, `verification_status`, `support`, `checked_at`, `notes`.

Statuses: `extracted` → `identified` → `verified`, or `unresolved` / `contradicted`. “Verified” means the identified source was independently inspected at the cited locator, not merely found by a search result or repeated in another video. `support` separately records `supports`, `partial`, `does-not-support`, or `testimony-only`.

Keep direct quotations short and accurate. Prefer original paraphrases. Modern translations and recordings can be copyrighted even when the underlying religious text is ancient. The user's permission confirmation for the source videos is recorded in `PERMISSIONS.md`; it does not automatically grant rights to third-party material quoted within them.
