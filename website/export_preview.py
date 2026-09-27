"""Export an allowlisted private preview to an already registered Sites checkout."""
import argparse
import json
import shutil
from pathlib import Path
from website.build import ROOT, build

def export(destination):
    destination=destination.resolve()
    if destination==ROOT or destination.is_relative_to(ROOT):
        raise ValueError('Use a separate checkout outside the research repository')
    manifest=destination/'.openai/hosting.json'
    config=json.loads(manifest.read_text(encoding='utf-8-sig'))
    if not config.get('project_id') or config.get('static',{}).get('directory')!='dist':
        raise ValueError('Destination must already be registered as a static Site')
    build(ROOT/'dist',preview=True)
    generated=json.loads((ROOT/'dist/build-manifest.json').read_text(encoding='utf-8'))
    eligible=set(generated['articles'])
    files=[ROOT/'dist'/p for p in generated['files']]+[ROOT/'dist/build-manifest.json']
    from website.build import read_md
    files += [p for p in (ROOT/'content/articles').glob('*.md') if read_md(p)[0]['slug'] in eligible]
    files += list((ROOT/'content/pages').glob('*.md'))
    files += [ROOT/'website'/p for p in ['build.py','site.css','requirements.txt']]
    allowed={'.openai/hosting.json','.gitignore','README.md'}|{p.relative_to(ROOT).as_posix() for p in files}
    for p in destination.rglob('*'):
        relative=p.relative_to(destination)
        if p.is_file() and not any(part in ['.git','.sites-runtime','__pycache__'] for part in relative.parts) and relative.as_posix() not in allowed:
            raise ValueError(f'Unexpected/stale file in preview checkout: {relative}; inspect before removing')
    for source in files:
        target=destination/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    (destination/'.gitignore').write_text('.sites-runtime/\n__pycache__/\n.venv/\n.env*\n',encoding='utf-8')
    (destination/'README.md').write_text('# Jinn in Islam — private reading preview\n\nSanitized website export. Canonical editorial work remains in the separate Islam and Jinn research repository.\n\nInstall `website/requirements.txt`, then run `python website/build.py --preview` to regenerate these static assets from the included Markdown. Drafts require the explicit preview flag. Keep this Site owner-private while review is unfinished.\n\nRaw captions, reference registries, translation files and research Git history are deliberately absent.\n',encoding='utf-8')
    print(f'Exported {len(files)} allowlisted files to {destination}; no research history or raw downloads.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);export(parser.parse_args().destination)
