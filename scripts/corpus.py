"""Resumable al-Sabeel corpus acquisition. Run with the research virtualenv."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data/catalog'
RAW = ROOT / 'data/raw'
LOGS = ROOT / 'data/logs'
TRANSCRIPTS = ROOT / 'data/transcripts'
CHANNEL = 'UCyvk_lo0codsbB8oWL6xUBA'
START, END = 'GZRckyIXMBc', 'Gv8vBol0EAU'
ASSETS = Path(os.environ.get('YTDLP_ASSETS', r'C:\Users\Hamza\Desktop\yt-dlp_win_x86\yt-dlp-gui+required_assets'))


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def run_ytdlp(args, label):
    LOGS.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-progress',
               '--socket-timeout', '30', '--retries', '2', '--extractor-retries', '2']
    if (ASSETS / 'deno.exe').is_file():
        command += ['--js-runtimes', f'deno:{ASSETS / "deno.exe"}']
    command += args
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                            encoding='utf-8', errors='replace', timeout=240)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    (LOGS / f'{stamp}-{label}.log').write_text(
        f'Command: {json.dumps(command)}\nExit: {result.returncode}\n' + result.stdout + result.stderr,
        encoding='utf-8')
    if result.returncode:
        print(result.stderr[-1400:], flush=True)
    return result


def discover(args):
    target = RAW / 'channel/videos.json'
    if not target.exists() or args.refresh:
        result = run_ytdlp(['--flat-playlist', '--skip-download', '--playlist-end', '250',
                           '--dump-single-json', 'https://www.youtube.com/@al-sabeel/videos'], 'inventory')
        if result.returncode:
            raise SystemExit('Channel inventory failed; see data/logs.')
        save_json(target, json.loads(result.stdout))
    entries = read_json(target)['entries']
    positions = {e['id']: i for i, e in enumerate(entries)}
    if START not in positions or END not in positions:
        raise SystemExit('Boundary absent: expand inventory before proceeding.')
    lo, hi = sorted([positions[START], positions[END]])
    candidates = list(reversed(entries[lo:hi + 1]))
    old = {e['id']: e for e in read_json(CATALOG / 'candidates.json')} if (CATALOG / 'candidates.json').exists() else {}
    rows = []
    for order, entry in enumerate(candidates, 1):
        rows.append(old.get(entry['id'], {
            'id': entry['id'], 'window_order': order, 'title_inventory': entry['title'],
            'duration_inventory': entry.get('duration'), 'url': f'https://www.youtube.com/watch?v={entry["id"]}',
            'selection': 'pending', 'selection_reason': '', 'metadata_status': 'pending',
            'caption_status': 'pending', 'transcript_status': 'pending',
            'article_status': 'pending', 'reference_status': 'pending',
            'translation_status': 'pending', 'reviewed_ranges': [],
        }))
    save_json(CATALOG / 'candidates.json', rows)
    save_json(CATALOG / 'scope.json', {
        'channel_id': CHANNEL, 'channel_url': 'https://www.youtube.com/@al-sabeel',
        'first_video': START, 'last_video': END, 'captured_at': now(),
        'inventory_count': len(entries), 'window_count': len(rows),
        'method': 'Inclusive upload-position window in the channel Videos tab, oldest first. Metadata dates checked separately.',
        'limits': 'Videos-tab snapshot only; deleted/private uploads and live-only recordings cannot be inferred. Shorts are not enumerated.',
    })
    print(f'{len(rows)} candidates, both boundaries present.', flush=True)


def metadata(args):
    rows = read_json(CATALOG / 'candidates.json')
    for row in rows:
        if args.ids and row['id'] not in args.ids:
            continue
        vid = row['id']
        target = RAW / 'metadata' / f'{vid}.info.json'
        existing = RAW / 'boundaries' / f'{vid}.info.json'
        if not target.exists() and existing.exists():
            save_json(target, read_json(existing))
        if not target.exists() or args.refresh:
            result = run_ytdlp(['--skip-download', '--no-playlist', '--write-info-json', '--write-description',
                               '--paths', str(RAW / 'metadata'), '-o', '%(id)s.%(ext)s', row['url']], f'metadata-{vid}')
            row['last_metadata_attempt'] = now()
            if result.returncode or not target.exists():
                row['metadata_status'] = 'blocked'
                save_json(CATALOG / 'candidates.json', rows)
                continue
            time.sleep(args.delay)
        d = read_json(target)
        if d.get('channel_id') != CHANNEL:
            raise SystemExit(f'Unexpected channel for {vid}; investigate before acquisition.')
        row.update({
            'title_ar': d['title'], 'upload_date': d.get('upload_date'), 'duration': d.get('duration'),
            'channel_id': d['channel_id'], 'chapters': d.get('chapters') or [],
            'metadata_status': 'downloaded',
            'available_arabic_auto_tracks': [k for k in d.get('automatic_captions', {}) if k.startswith('ar')],
            'description_video_links': list(dict.fromkeys(re.findall(
                r'(?:youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})', d.get('description', '')))),
        })
        # Preserve only a short topic description; full raw metadata stays local.
        row['description_intro'] = d.get('description', '').split('إعداد وتقديم')[0].strip()
        save_json(CATALOG / 'candidates.json', rows)
        print(f'Metadata {vid} {row["upload_date"]}: {d["title"]}', flush=True)


def download(args):
    rows = read_json(CATALOG / 'candidates.json')
    for row in rows:
        if row['selection'] not in ('core', 'companion', 'compilation', 'excerpt'):
            continue
        if args.ids and row['id'] not in args.ids:
            continue
        vid = row['id']
        folder = RAW / 'subtitles' / vid
        srt = folder / f'{vid}.ar-orig.srt'
        vtt = folder / f'{vid}.ar-orig.vtt'
        english = folder / f'{vid}.en.srt'
        # Keep optional machine translation separate: an unavailable en track must
        # never prevent original-caption conversion or trigger repeated downloads.
        if vtt.exists() and vtt.stat().st_size and not srt.exists():
            converted = subprocess.run([str(ASSETS / 'ffmpeg.exe'), '-nostdin', '-y', '-i', str(vtt), str(srt)], capture_output=True)
            if converted.returncode:
                print(f'Existing VTT conversion failed: {vid}', flush=True)
        if not (srt.exists() and vtt.exists()) or args.refresh:
            if 'ar-orig' not in row.get('available_arabic_auto_tracks', []):
                row['caption_status'] = 'blocked-no-original-arabic-track'
                save_json(CATALOG / 'candidates.json', rows)
                continue
            result = run_ytdlp([
                '--skip-download', '--no-playlist', '--write-auto-subs', '--sub-langs', 'ar-orig',
                '--sub-format', 'vtt', '--convert-subs', 'srt', '--keep-video',
                '--ffmpeg-location', str(ASSETS), '--sleep-subtitles', str(args.delay),
                '--paths', str(RAW / 'subtitles'), '-o', '%(id)s/%(id)s.%(ext)s', row['url'],
            ], f'captions-{vid}')
            row['last_caption_attempt'] = now()
            row['caption_exit_code'] = result.returncode
        row['caption_status'] = 'downloaded' if srt.exists() and srt.stat().st_size and vtt.exists() else 'blocked'
        row['english_caption_status'] = 'machine-draft-downloaded' if english.exists() and english.stat().st_size else 'unavailable'
        save_json(CATALOG / 'candidates.json', rows)
        print(f'Captions {vid}: {row["caption_status"]}', flush=True)


def stamp_seconds(stamp):
    h, m, s = stamp.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_srt(text):
    cues = []
    for block in re.split(r'\n\s*\n(?=\d+\n\d{2,}:)', text.replace('\r\n', '\n').strip()):
        lines = block.splitlines()
        timeline = next((i for i, line in enumerate(lines) if '-->' in line), None)
        if timeline is None:
            raise ValueError('Subtitle block has no timing line')
        match = re.fullmatch(r'(\d{2,}:\d{2}:\d{2},\d{3}) --> (\d{2,}:\d{2}:\d{2},\d{3})', lines[timeline].strip())
        if not match:
            raise ValueError(f'Invalid timing: {lines[timeline]}')
        start, end = map(stamp_seconds, match.groups())
        body = html.unescape(re.sub(r'<[^>]+>', '', '\n'.join(lines[timeline + 1:])))
        if end <= start:
            raise ValueError('Cue has non-positive duration')
        if cues and start < cues[-1]['start']:
            raise ValueError('Cue starts are not monotonic')
        cues.append({'cue': len(cues) + 1, 'start': start, 'end': end, 'text': body})
    if not cues or not any(c['text'].strip() for c in cues):
        raise ValueError('Empty subtitle file')
    return cues


def normalize_cues(cues):
    """Remove rolling *line* carryover only on overlapping/near-adjacent cues.

    Keep repetition within a line and after a time gap. Never deduplicate globally.
    Each output segment retains its originating raw cue for audit.
    """
    result = []
    previous_lines = []
    previous_end = -100.0
    for cue in cues:
        lines = [re.sub(r'\s+', ' ', line).strip() for line in cue['text'].splitlines() if line.strip()]
        overlap = 0
        if cue['start'] <= previous_end + 0.08:
            for count in range(min(len(previous_lines), len(lines)), 0, -1):
                if previous_lines[-count:] == lines[:count]:
                    overlap = count
                    break
        fresh = lines[overlap:]
        if fresh:
            result.append({**cue, 'text': ' '.join(fresh)})
        previous_lines, previous_end = lines, cue['end']
    return result


def timestamp(seconds):
    whole = int(seconds)
    return f'{whole // 3600:02}:{whole // 60 % 60:02}:{whole % 60:02}'


def normalize(args):
    rows = read_json(CATALOG / 'candidates.json')
    for row in rows:
        if row['caption_status'] != 'downloaded' or (args.ids and row['id'] not in args.ids):
            continue
        vid = row['id']
        source = RAW / 'subtitles' / vid / f'{vid}.ar-orig.srt'
        cues = parse_srt(source.read_text(encoding='utf-8-sig'))
        segments = normalize_cues(cues)
        dest = TRANSCRIPTS / vid
        save_json(dest / 'segments.ar.json', segments)
        text = f'# {row.get("title_ar", row["title_inventory"])}\n\nAutomatic Arabic captions; NOT manually corrected. Timestamped research copy.\n\n'
        text += '\n\n'.join(f'[{timestamp(s["start"])}] {s["text"]}' for s in segments) + '\n'
        (dest / 'transcript.ar.md').write_text(text, encoding='utf-8')
        duration = row.get('duration')
        covered = 0.0
        last_end = 0.0
        gaps = []
        for cue in cues:
            if cue['start'] > last_end:
                gaps.append({'start': last_end, 'end': cue['start'], 'seconds': round(cue['start'] - last_end, 3)})
            covered += max(0.0, cue['end'] - max(last_end, cue['start']))
            last_end = max(last_end, cue['end'])
        report = {
            'video_id': vid, 'normalized_at': now(), 'raw_cues': len(cues), 'segments': len(segments),
            'word_count': sum(len(s['text'].split()) for s in segments),
            'first_cue_seconds': cues[0]['start'], 'last_cue_seconds': cues[-1]['end'],
            'video_duration_seconds': duration,
            'tail_gap_seconds': round(duration - cues[-1]['end'], 3) if duration else None,
            'timed_caption_coverage_fraction': round(covered / duration, 5) if duration else None,
            'internal_gaps_over_20_seconds': [g for g in gaps if g['seconds'] > 20],
            'sha256_srt': hashlib.sha256(source.read_bytes()).hexdigest(),
            'sha256_vtt': hashlib.sha256(source.with_suffix('.vtt').read_bytes()).hexdigest(),
            'sha256_segments': hashlib.sha256((dest / 'segments.ar.json').read_bytes()).hexdigest(),
            'caption_language': 'ar-orig', 'caption_kind': 'automatic',
            'speech_recognition_review': 'pending', 'content_review': 'pending',
            'normalization': 'Adjacent rolling line carryover only; preserve raw files for audit.',
        }
        save_json(CATALOG / 'quality' / f'{vid}.json', report)
        row['transcript_status'] = 'normalized-unreviewed'
        english = source.with_name(f'{vid}.en.srt')
        if english.exists():
            en_cues = parse_srt(english.read_text(encoding='utf-8-sig'))
            en_segments = normalize_cues(en_cues)
            save_json(dest / 'segments.en.draft.json', en_segments)
            en_text = f'# {row.get("title_en", row["title_inventory"])}\n\nYouTube automatic English translation. UNREVIEWED machine draft; verify against Arabic.\n\n'
            en_text += '\n\n'.join(f'[{timestamp(s["start"])}] {s["text"]}' for s in en_segments) + '\n'
            (dest / 'transcript.en.draft.md').write_text(en_text, encoding='utf-8')
            row['translation_status'] = 'machine-draft-unreviewed'
        save_json(CATALOG / 'candidates.json', rows)
        print(f'Normalized {vid}: {len(cues)} cues, {report["word_count"]} words', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['discover', 'metadata', 'download', 'normalize'])
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--ids', nargs='+')
    parser.add_argument('--delay', type=float, default=3)
    args = parser.parse_args()
    globals()[args.command](args)


if __name__ == '__main__':
    main()
