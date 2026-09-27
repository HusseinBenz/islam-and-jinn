"""Package local research files in the confirmed reading order. Not a web asset."""
import zipfile
from scripts.corpus import CATALOG, RAW, ROOT, TRANSCRIPTS, read_json


def main():
    episodes = read_json(CATALOG / 'episodes.json')
    dest = ROOT / 'data/exports/al-sabeel-jinn-arabic-corpus.zip'
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(CATALOG / 'episodes.json', 'episodes.json')
        bundle.write(ROOT / 'docs/CORPUS.md', 'CORPUS.md')
        bundle.write(ROOT / 'docs/PERMISSIONS.md', 'PERMISSIONS.md')
        for e in episodes:
            vid = e['id']
            prefix = f'{e["core_order"]:02}' if e['core_order'] else e['selection']
            folder = f'{prefix}-{vid}'
            for ext in ('srt', 'vtt'):
                bundle.write(RAW / 'subtitles' / vid / f'{vid}.ar-orig.{ext}', f'{folder}/original.ar.{ext}')
            bundle.write(TRANSCRIPTS / vid / 'transcript.ar.md', f'{folder}/transcript.ar.md')
            bundle.write(TRANSCRIPTS / vid / 'segments.ar.json', f'{folder}/segments.ar.json')
            bundle.write(CATALOG / 'quality' / f'{vid}.json', f'{folder}/quality.json')
    with zipfile.ZipFile(dest) as bundle:
        if bundle.testzip() is not None:
            raise SystemExit('Archive failed CRC check.')
        assert sum(n.endswith('original.ar.srt') for n in bundle.namelist()) == len(episodes)
    print(f'{dest} ({dest.stat().st_size:,} bytes; {len(episodes)} subtitle sets; CRC verified)')


if __name__ == '__main__':
    main()
