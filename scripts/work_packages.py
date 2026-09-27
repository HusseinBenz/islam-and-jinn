"""Build deterministic indexes and unclaimed episode work packages; never overwrite notes."""
from __future__ import annotations
from collections import Counter
import hashlib
import re
from urllib.parse import urlparse
from scripts.corpus import CATALOG, RAW, ROOT, read_json, save_json, timestamp
from scripts.translations import process as inspect_translation

TITLES = {
    'GZRckyIXMBc': ('Common misconceptions about jinn', ['foundations', 'unseen', 'sightings']),
    'zyH4e-BOOks': ('The origin of jinn, moral responsibility, and the qarin', ['foundations', 'creation', 'qarin']),
    'MfKjHJzryRw': ('Kinds and appearances of jinn', ['foundations', 'ifrit', 'folklore']),
    'lbX5IegGFTY': ('Humans and jinn: abilities, authority, and prophethood', ['foundations', 'prophethood', 'Solomon']),
    '3sVCCYYmuzU': ('Jinn and human relationships: love, marriage, and offspring', ['scholarly-debate', 'relationships', 'testimony']),
    'nJv0h3zXbb0': ('Psychedelics and claims of encounters with jinn', ['consciousness', 'research', 'testimony']),
    'n8kkRim6ecs': ('Channelling and the New Age account of other worlds', ['new-age', 'channelling', 'comparative-religion']),
    'QXKDqDYCgdQ': ('A testimony of possession outside the Muslim world', ['testimony', 'possession']),
    'TZEpUvKGTAo': ('Meteors between astronomy, revelation, and mythology', ['astronomy', 'Quran', 'media']),
    'qG4k4vJUhaI': ('Time Bandits and the portrayal of evil in popular culture', ['media', 'theology']),
    'txkeVCL7eEI': ('Jerry Marzinsky and his interpretation of distressing voices', ['interviews', 'mental-health', 'possession']),
    'mnl6N1wSUxI': ('Ruqyah and possession: examining disputed claims', ['ruqyah', 'scholarly-debate']),
    'VGFfbluWmEo': ('Medicine, materialism, and the spiritual dimension', ['medicine', 'epistemology']),
    'LD9CCX7Y5uA': ('Four conversations on jinn, possession, and altered consciousness', ['interviews', 'consciousness']),
    'jKz9GLqhuPo': ('Quranic ruqyah and accounts of psychological distress', ['ruqyah', 'mental-health', 'testimony']),
    'xS-lcnRvjBc': ('A Muslim physician on science and spiritual explanations', ['interviews', 'medicine', 'epistemology']),
    '2vCEIAfCppY': ('Science, magic, and the project of Iblis', ['history', 'occultism', 'interpretation']),
    '-GeI1OO5WuY': ('An excerpt on the proposed connection between jinn and scientific knowledge', ['excerpt', 'history']),
    'pii9kBZj9i0': ('Luck and the portrayal of unseen beings in family films', ['media', 'theology']),
    'RGfYJFs_pM0': ('Medication and ruqyah: the proposed integrative approach', ['medicine', 'ruqyah', 'interviews']),
    'HdDilXwr_eg': ('Do spiritual entities help and protect people?', ['testimony', 'occultism', 'energy-healing']),
    'UNfXUJir00k': ('Twisted Yoga: spirituality, manipulation, and abuse', ['companion', 'media', 'spiritual-abuse']),
    'Gv8vBol0EAU': ('The scholarly debate over possession', ['scholarly-debate', 'possession', 'Quran', 'hadith']),
}


def main():
    rows = read_json(CATALOG / 'candidates.json')
    selected = [e for e in rows if e['selection'] != 'excluded']
    core_order = 0
    index = []
    source_links = {}
    for e in selected:
        vid = e['id']
        title, tags = TITLES[vid]
        if e['selection'] == 'core':
            core_order += 1
        e.update({'title_en': title, 'tags': tags, 'core_order': core_order if e['selection'] == 'core' else None})
        index.append({k: e.get(k) for k in ['id', 'core_order', 'window_order', 'selection', 'title_ar', 'title_en', 'upload_date', 'duration', 'url', 'tags', 'chapters', 'parent_video']})
        d = read_json(RAW / 'metadata' / f'{vid}.info.json')
        desc = d.get('description', '').split('شاهد حلقاتنا السابقة')[0].split('نعتمد على')[0]
        links = []
        for match in re.finditer(r'https?://[^\s<>]+', desc):
            url = match.group().rstrip('.,،)')
            if urlparse(url).hostname in ('x.com', 'www.facebook.com', 'facebook.com'):
                continue
            if vid in url:
                continue
            links.append(url)
            key = 'desc-' + hashlib.sha256(url.encode()).hexdigest()[:12]
            entry = source_links.setdefault(key, {
                'id': key, 'type': 'video' if 'youtu' in url else 'web', 'url': url,
                'title': None, 'creators': [], 'locator': None, 'claim': None,
                'verification_status': 'extracted', 'support': None, 'checked_at': None,
                'mentions': [], 'notes': 'URL extracted from episode description. Original recording/passage and supporting claim remain to be inspected.',
            })
            entry['mentions'].append({'episode_id': vid, 'locator': 'YouTube description', 'start_seconds': None})
        dest = ROOT / 'research/episodes' / f'{vid}.md'
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            contents = f'# {title}\n\n- Video: [{e["title_ar"]}]({e["url"]})\n- Date: {e["upload_date"]}\n- Role: {e["selection"]}\n- Duration: {timestamp(e["duration"])}\n- Arabic captions: `data/raw/subtitles/{vid}/{vid}.ar-orig.srt`\n- Readable transcript: `data/transcripts/{vid}/transcript.ar.md`\n- Reviewed transcript ranges: **none**\n- Owner: unclaimed\n\n## Work checklist\n\n- [ ] Read every transcript segment and log coverage.\n- [ ] Check article meaning, Arabic terms and named entities directly against the Arabic; English subtitles are not required.\n- [ ] Adapt into an article preserving this episode\'s section order.\n- [ ] Extract every Qur\'an verse, hadith, book, study, interview, anecdote and opinion.\n- [ ] Verify each source at its primary locator.\n- [ ] Check claims, tags, cross-links and footnote backlinks.\n- [ ] Record unresolved items, validation, and commit.\n\n## Publisher chapter outline\n\n'
            if e.get('chapters'):
                contents += '\n'.join(f'- [{timestamp(c["start_time"])}] {c["title"]}' for c in e['chapters']) + '\n'
            else:
                contents += 'No structured chapter metadata. Derive the outline from the complete transcript; do not invent it from the title.\n'
            contents += '\n## Links explicitly supplied in the description\n\n'
            contents += '\n'.join(f'- {url}' for url in links) if links else 'No non-promotional source links extracted. The spoken references still need to be collected.'
            contents += '\n\n## Translation and ASR questions\n\nPending complete reading.\n\n## Claim and source map\n\nPending complete reading.\n'
            dest.write_text(contents, encoding='utf-8')
    save_json(CATALOG / 'candidates.json', rows)
    save_json(CATALOG / 'episodes.json', index)
    # Preserve manually enriched entries when this script is run again.
    dest = ROOT / 'data/references/description-links.json'
    prior = {r['id']: r for r in read_json(dest)} if dest.exists() else {}
    save_json(dest, [prior.get(k, v) for k, v in source_links.items()])
    quality = [read_json(CATALOG / 'quality' / f'{e["id"]}.json') for e in selected]
    references = [r for p in sorted((ROOT / 'data/references').glob('*.json')) for r in read_json(p)]
    translations = [inspect_translation(p) for p in sorted((ROOT / 'data/translations').glob('*.json'))]
    summary = {
        'selected_videos': len(selected), 'core_videos': core_order,
        'total_duration_seconds': sum(e['duration'] for e in selected),
        'total_arabic_words': sum(q['word_count'] for q in quality),
        'total_cues': sum(q['raw_cues'] for q in quality),
        'captions_downloaded': sum(e['caption_status'] == 'downloaded' for e in selected),
        'transcripts_normalized': sum(e['transcript_status'] == 'normalized-unreviewed' for e in selected),
        'english_machine_drafts': sum(e.get('english_caption_status') == 'machine-draft-downloaded' for e in selected),
        'article_status_counts': dict(Counter(e['article_status'] for e in selected)),
        'description_source_links': len(source_links),
        'transcripts_with_reading_logged': sum(bool(e.get('reviewed_ranges')) for e in selected),
        'reference_records': len(references),
        'reference_status_counts': dict(Counter(r['verification_status'] for r in references)),
        'references_flagged_for_recheck': sum(r.get('audit_status') == 'needs-primary-recheck' for r in references),
        'authored_english_translation_files': len(translations),
        'authored_english_segments': sum(t['translated_segments'] for t in translations),
        'complete_english_translation_drafts': sum(t['complete_coverage'] for t in translations),
        'complete_reviewed_english_translations': sum(t['complete_coverage'] and bool(t['reviewed_at']) for t in translations),
    }
    save_json(CATALOG / 'summary.json', summary)
    report = '# Corpus inventory\n\nThe [channel-owned World of Jinn playlist](https://www.youtube.com/playlist?list=PLO7nbsS9Q8mGIU1XaSZXjaD5rBOn9OEma) establishes the main series. The requested inclusive window is May 26–August 24, 2026.\n\n'
    report += f'{core_order} main episodes; one related companion; one excerpt; seven unrelated uploads excluded. All {len(selected)} selected videos have original Arabic VTT, converted SRT and cleaned timestamped transcripts. Total: **{summary["total_arabic_words"]:,} Arabic words**, **{timestamp(summary["total_duration_seconds"])}** of video. Normalization is not translation or content review.\n\n'
    report += '| Order | English working title | Published | Duration | Role | Work package |\n| --- | --- | --- | --- | --- | --- |\n'
    for e in selected:
        report += f'| {e["core_order"] or "—"} | [{e["title_en"]}]({e["url"]}) | {e["upload_date"]} | {timestamp(e["duration"])} | {e["selection"]} | [{e["id"]}](../research/episodes/{e["id"]}.md) |\n'
    report += '\n## Exclusions\n\n'
    for e in rows:
        if e['selection'] == 'excluded':
            report += f'- `{e["id"]}` — {e["title_ar"]}. {e["selection_reason"]}\n'
    report += '\n## Scope limitations\n\nThe playlist extractor reported incomplete data after retries, but returned both boundary videos and all 21 in-window playlist members; these were cross-checked against the channel upload window. A private/unavailable older entry is outside the requested boundary. Shorts were not included as independent episodes. The older referenced videos `JTO_1Y8zYto` (2024-08-10) and `nQVlmmbV8A0` (2024-05-07) are background references, outside the requested main corpus.\n'
    (ROOT / 'docs/CORPUS.md').write_text(report, encoding='utf-8')
    print(summary)


if __name__ == '__main__':
    main()
