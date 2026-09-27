"""Validate authored English segments and export local, explicitly labelled SRT drafts."""
from __future__ import annotations

import argparse
import hashlib
import re

from scripts.corpus import RAW, ROOT, TRANSCRIPTS, parse_srt, read_json, save_json


def validate_segments(draft, source):
    entries = draft['segments']
    indices = [entry['source_segment_index'] for entry in entries]
    if not entries or any(type(i) is not int for i in indices):
        raise ValueError('Translation must contain integer source indices')
    if indices != sorted(set(indices)):
        raise ValueError('Duplicate or unordered source indices')
    if indices[0] < 0 or indices[-1] >= len(source):
        raise ValueError('Source index outside transcript')
    if any(not isinstance(e['text'], str) or not e['text'].strip() or
           '\n\n' in e['text'].replace('\r\n', '\n') or '-->' in e['text']
           for e in entries):
        raise ValueError('Empty or invalid subtitle text')
    complete = indices == list(range(len(source)))
    if draft.get('complete') and not complete:
        raise ValueError('Complete claim has untranslated source segments')
    return complete


def srt_time(seconds):
    milliseconds = round(seconds * 1000)
    seconds, ms = divmod(milliseconds, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f'{hours:02}:{minute:02}:{sec:02},{ms:03}'


def prepare(draft, source_bytes, srt_bytes):
    import json
    if hashlib.sha256(source_bytes).hexdigest() != draft['source_segments_sha256']:
        raise ValueError('Normalized source hash changed; reconcile translation first')
    if hashlib.sha256(srt_bytes).hexdigest() != draft['source_srt_sha256']:
        raise ValueError('Original SRT hash changed; reconcile provenance first')
    source = json.loads(source_bytes)
    complete = validate_segments(draft, source)
    cues, mapping = [], []
    for number, entry in enumerate(draft['segments'], 1):
        original = source[entry['source_segment_index']]
        cues.append(f'{number}\n{srt_time(original["start"])} --> '
                    f'{srt_time(original["end"])}\n{entry["text"].strip()}\n')
        mapping.append({'english_cue': number, 'source_segment_index': entry['source_segment_index'],
                        'source_cue': original['cue'], 'start': original['start'],
                        'end': original['end'], 'review_notes': entry.get('review_notes')})
    output = '\n'.join(cues)
    if len(parse_srt(output)) != len(mapping):
        raise ValueError('Exported SRT cue count does not match translation')
    manifest = {'episode_id': draft['episode_id'], 'complete_coverage': complete,
                'reviewed_at': draft.get('reviewed_at'), 'source_segments': len(source),
                'translated_segments': len(mapping),
                'next_source_segment_index': next((i for i in range(len(source))
                    if i not in {e['source_segment_index'] for e in draft['segments']}), None),
                'source_segments_sha256': draft['source_segments_sha256'],
                'source_srt_sha256': draft['source_srt_sha256'], 'cue_map': mapping}
    return output, manifest


def process(path, export=False):
    draft = read_json(path)
    vid = draft['episode_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        raise ValueError('Invalid episode ID')
    output, manifest = prepare(draft, (TRANSCRIPTS / vid / 'segments.ar.json').read_bytes(),
                               (RAW / 'subtitles' / vid / f'{vid}.ar-orig.srt').read_bytes())
    if export:
        folder = ROOT / 'data/exports/translations'
        folder.mkdir(parents=True, exist_ok=True)
        label = 'complete' if manifest['complete_coverage'] else 'partial'
        stem = f'{vid}.en.{label}-draft'
        (folder / f'{stem}.srt').write_text(output, encoding='utf-8')
        save_json(folder / f'{stem}.provenance.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true', help='Write local SRT drafts and cue maps')
    args = parser.parse_args()
    for path in sorted((ROOT / 'data/translations').glob('*.json')):
        result = process(path, export=args.export)
        print(f'{result["episode_id"]}: {result["translated_segments"]}/{result["source_segments"]} '
              f'segments; complete={result["complete_coverage"]}; '
              f'next index={result["next_source_segment_index"]}; reviewed={result["reviewed_at"]}')


if __name__ == '__main__':
    main()
