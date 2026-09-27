"""Validate local corpus integrity and tracked article/reference links."""
from __future__ import annotations
import hashlib
import re
from scripts.corpus import CATALOG, CHANNEL, END, RAW, ROOT, START, parse_srt, read_json
from scripts.translations import process as validate_translation


def main():
    errors = []
    rows = read_json(CATALOG / 'candidates.json')
    selected = [e for e in rows if e['selection'] != 'excluded']
    core = [e for e in rows if e['selection'] == 'core']
    if core[0]['id'] != START or core[-1]['id'] != END:
        errors.append('Boundary/order mismatch')
    if len({e['id'] for e in rows}) != len(rows):
        errors.append('Duplicate candidate ID')
    if any(e['selection'] == 'pending' for e in rows):
        errors.append('Unclassified upload')
    for e in selected:
        vid = e['id']
        if e['channel_id'] != CHANNEL or not '20260526' <= e['upload_date'] <= '20260824':
            errors.append(f'{vid}: channel/date mismatch')
        if e['caption_status'] != 'downloaded':
            errors.append(f'{vid}: captions incomplete')
            continue
        q = read_json(CATALOG / 'quality' / f'{vid}.json')
        for ext in ('srt', 'vtt'):
            p = RAW / 'subtitles' / vid / f'{vid}.ar-orig.{ext}'
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != q[f'sha256_{ext}']:
                errors.append(f'{vid}: {ext} hash mismatch')
        try:
            cues = parse_srt((RAW / 'subtitles' / vid / f'{vid}.ar-orig.srt').read_text(encoding='utf-8-sig'))
            if len(cues) != q['raw_cues']:
                errors.append(f'{vid}: cue-count mismatch')
        except ValueError as exc:
            errors.append(f'{vid}: {exc}')
    registry = {}
    for p in (ROOT / 'data/references').glob('*.json'):
        for ref in read_json(p):
            if ref['id'] in registry:
                errors.append(f'Duplicate reference ID: {ref["id"]}')
            registry[ref['id']] = ref
            if ref['verification_status'] == 'verified' and not all(ref.get(k) for k in ['url', 'locator', 'checked_at', 'support']):
                errors.append(f'Incomplete verified reference: {ref["id"]}')
    for p in (ROOT / 'content/articles').glob('*.md'):
        text = p.read_text(encoding='utf-8')
        uses = set(re.findall(r'\[\^([\w-]+)\](?!:)', text))
        definitions = set(re.findall(r'^\[\^([\w-]+)\]:', text, re.M))
        if uses != definitions:
            errors.append(f'{p.name}: missing/unused footnote definitions {uses ^ definitions}')
        for rid in uses:
            if rid not in registry:
                errors.append(f'{p.name}: reference {rid} absent from registry')
            elif 'status: ready' in text and registry[rid]['verification_status'] != 'verified':
                errors.append(f'{p.name}: unverified citation in ready article: {rid}')
        for field in ['title', 'slug', 'description', 'order', 'tags', 'source_videos', 'status', 'reviewed_at']:
            if not re.search(rf'^{field}:', text, re.M):
                errors.append(f'{p.name}: missing metadata {field}')
    for p in (ROOT / 'data/translations').glob('*.json'):
        try:
            validate_translation(p)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors.append(f'{p.name}: {exc}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(rows)} classified uploads; {len(selected)} SRT/VTT pairs and hashes; {len(registry)} reference records; article citation integrity.')
    print('This checks structure and local data integrity; it does not certify ASR accuracy or unfinished editorial/source review.')


if __name__ == '__main__':
    main()
