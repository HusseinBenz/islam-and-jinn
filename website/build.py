"""Build a static reading site from canonical Markdown; drafts require --preview.

Only content/pages, eligible content/articles and website assets enter dist.
Raw captions, research ledgers, credentials and repository history never enter it.
"""
from __future__ import annotations
import argparse
import html
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
esc = html.escape
FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230d2741'/%3E%3Cpath d='M8 8h16v16H8zM16 8v16' stroke='%23d2b779' stroke-width='2' fill='none'/%3E%3C/svg%3E"

def read_md(path):
    raw = path.read_text(encoding='utf-8')
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
    if not match:
        raise ValueError(f'Missing front matter: {path}')
    return yaml.safe_load(match[1]), match[2]

def order_footnotes(body):
    """Definition order avoids Markdown's table/paragraph traversal-order mismatch."""
    starts=list(re.finditer(r'^\[\^([\w-]+)\]:',body,re.M))
    if not starts: return body
    prose=body[:starts[0].start()]
    definitions={m[1]:body[m.start():starts[i+1].start() if i+1<len(starts) else len(body)].strip() for i,m in enumerate(starts)}
    order=list(dict.fromkeys(re.findall(r'\[\^([\w-]+)\]',prose)))
    if set(order)!=set(definitions): raise ValueError('Missing or unused footnote definition')
    return prose+'\n'+'\n'.join(definitions[k] for k in order)+'\n'

def render(body):
    # Heading is rendered in the shared page header. Definitions must number by use.
    body = re.sub(r'^# [^\n]+\n', '', body, count=1, flags=re.M)
    body = order_footnotes(body)
    md = markdown.Markdown(extensions=['footnotes', 'tables', 'toc', 'sane_lists'],
        extension_configs={'footnotes': {'USE_DEFINITION_ORDER': True,
            'SUPERSCRIPT_TEXT': '[{}]', 'BACKLINK_TITLE': 'Return to citation {}'},
            'toc': {'toc_depth': '2-3'}})
    result = md.convert(body)
    result = re.sub(r'<table>(.*?)</table>', r'<div class="table-scroll" tabindex="0" role="region" aria-label="Comparison table"><table>\1</table></div>', result, flags=re.S)
    return result, md.toc

def href(article):
    return f'/articles/{article["slug"]}/'

def chapter_nav(articles, current=None):
    return ''.join(f'<a href="{href(a)}"'+(' aria-current="page"' if a['slug']==current else '')+f'><span class="chapter-number">{a["order"]:02}</span><span>{esc(a["title"])}</span></a>' for a in articles)

def shell(title, description, main, articles, preview, current=None):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description,quote=True)}">
{'<meta name="robots" content="noindex,nofollow">' if preview else ''}
<title>{esc(title)}{' — Jinn in Islam' if title!='Jinn in Islam' else ''}</title>
<link rel="icon" type="image/svg+xml" href="{FAVICON}"><link rel="stylesheet" href="/assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="masthead"><a class="wordmark" href="/">Jinn <span>in</span> Islam</a>
<nav aria-label="Main navigation"><a href="/"{' aria-current="page"' if current=='home' else ''}>Encyclopedia</a><a href="/about/"{' aria-current="page"' if current=='about' else ''}>About & sources</a></nav>
{'<span class="edition">Reading preview</span>' if preview else '<span class="edition">English edition</span>'}</header>
<details class="mobile-chapters"><summary>Browse the chapters</summary><nav aria-label="Chapters">{chapter_nav(articles,current)}</nav></details>
{main}
<footer class="site-footer"><a class="wordmark" href="/">Jinn <span>in</span> Islam</a><p>An independent encyclopedia based on al-Sabeel.<br>{'Drafts under editorial and reference review.' if preview else 'English edition.'}</p><a href="/about/">Our approach to sources</a></footer>
</body></html>'''

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set(); self.links=[]; self.duplicates=[]; self.refs=[]; self.h1=0
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='h1': self.h1+=1
        if 'id' in attrs:
            if attrs['id'] in self.ids: self.duplicates.append(attrs['id'])
            self.ids.add(attrs['id'])
        for name in ('href','src'):
            if name in attrs: self.links.append(attrs[name])
        if attrs.get('class')=='footnote-ref': self.refs.append(attrs.get('href'))

def validate(output):
    pages={}
    for p in output.rglob('*.html'):
        parser=Links(); text=p.read_text(encoding='utf-8'); parser.feed(text)
        if parser.duplicates or parser.h1!=1 or re.search(r'\[\^[\w-]+\]',text):
            raise ValueError(f'Invalid headings/citation IDs in {p}: {parser.duplicates}')
        pages[p.resolve()]=parser
    for p, parser in pages.items():
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc: continue
            target=(output/unquote(u.path.lstrip('/'))) if u.path.startswith('/') else (p.parent/unquote(u.path)) if u.path else p
            if target.is_dir(): target/= 'index.html'
            target=target.resolve()
            if not target.is_relative_to(output.resolve()) or not target.exists(): raise ValueError(f'Broken local link {link} in {p}')
            if u.fragment and (target not in pages or unquote(u.fragment) not in pages[target].ids): raise ValueError(f'Broken anchor {link} in {p}')
        # Each citation must have its exact return target inside this article.
        for ref_id in parser.ids:
            if re.match(r'^fnref\d*:',ref_id) and '#'+ref_id not in parser.links:
                raise ValueError(f'Missing exact citation backlink {ref_id} in {p}')
    print(f'PASS: {len(pages)} static pages; local links, assets, headings and citation anchors.')

def build(output, preview):
    articles=[]
    for path in sorted((ROOT/'content/articles').glob('*.md')):
        meta, body=read_md(path)
        if meta['status']!='ready' and not preview: continue
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',meta['slug']): raise ValueError('Invalid article slug')
        articles.append(dict(meta,body=body))
    articles.sort(key=lambda a:a['order'])
    output.mkdir(parents=True,exist_ok=True)
    produced=[]
    def write(name,text):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8');produced.append(name)
    home_meta, home_body=read_md(ROOT/'content/pages/index.md')
    lead, intro=home_body.strip().split('\n\n',1)
    items=''.join(f'''<li><a class="chapter-row" href="{href(a)}"><span class="row-number">{a['order']:02}</span><div><span class="topic">{esc(a['tags'][0].replace('-',' '))}</span><h3>{esc(a['title'])}</h3><p>{esc(a['description'])}</p></div><span class="row-link" aria-hidden="true">↗</span></a></li>''' for a in articles)
    main=f'''<main id="main"><section class="portal-intro"><div class="intro-label"><span class="eyebrow">An encyclopedia of the unseen</span><span class="volume">I · JINN IN ISLAM</span></div><div><h1>{esc(lead)}</h1><p class="intro-text">{esc(intro.strip())}</p></div></section>
<section class="portal-body"><aside class="collection-note"><span class="eyebrow">The collection</span><p class="large-number">{len(articles):02}<span> chapters available</span></p><p>Read in the order of the source series, from foundations to the questions that follow.</p>{'<p class="draft-note"><strong>A work in progress</strong><br>These are condensed drafts. Source checks and editorial review continue.</p>' if preview else ''}<a href="/about/">About the project</a></aside><div class="chapter-list"><div class="list-title"><h2>Explore the chapters</h2><span>English edition</span></div><ol>{items}</ol>{'<p>Reviewed articles are being prepared.</p>' if not articles else ''}</div></section></main>'''
    write('index.html',shell(home_meta['title'],home_meta['description'],main,articles,preview,'home'))
    for i,a in enumerate(articles):
        body,toc=render(a['body'])
        words=len(a['body'].split('\n## References')[0].split()); minutes=max(1,round(words/220))
        prev=f'<a href="{href(articles[i-1])}"><span>Previous chapter</span>{esc(articles[i-1]["title"])}</a>' if i else '<a href="/"><span>Return to</span>The encyclopedia</a>'
        nxt=f'<a href="{href(articles[i+1])}"><span>Next chapter</span>{esc(articles[i+1]["title"])}</a>' if i+1<len(articles) else '<a href="/"><span>Continue exploring</span>All chapters</a>'
        main=f'''<main id="main" class="reading-layout"><aside class="reading-sidebar"><a class="back-link" href="/">All chapters</a><p class="eyebrow">In this chapter</p>{toc}<details class="desktop-chapters"><summary>The collection</summary><nav aria-label="Chapters">{chapter_nav(articles,a['slug'])}</nav></details></aside><article class="article"><header class="article-header"><div class="article-meta"><span>Chapter {a['order']:02}</span><span>{minutes} min read</span></div><h1>{esc(a['title'])}</h1><p class="article-deck">{esc(a['description'])}</p><div class="tags">{''.join('<span>'+esc(t.replace('-',' '))+'</span>' for t in a['tags'])}</div>{'<p class="review-notice"><strong>Draft for reading.</strong> Editorial and reference review is still in progress.</p>' if a['status']!='ready' else ''}</header><details class="mobile-toc"><summary>In this chapter</summary>{toc}</details><div class="prose">{body}</div><nav class="chapter-pagination" aria-label="Adjacent chapters">{prev}{nxt}</nav></article></main>'''
        write(f'articles/{a["slug"]}/index.html',shell(a['title'],a['description'],main,articles,preview,a['slug']))
    meta,body=read_md(ROOT/'content/pages/about.md'); rendered,toc=render(body)
    main=f'<main id="main" class="about-page"><span class="eyebrow">The project</span><h1>{esc(meta["title"])}</h1><div class="prose">{rendered}</div></main>'
    write('about/index.html',shell(meta['title'],meta['description'],main,articles,preview,'about'))
    write('assets/site.css',(ROOT/'website/site.css').read_text(encoding='utf-8'))
    write('robots.txt','User-agent: *\nDisallow: /\n' if preview else 'User-agent: *\nAllow: /\n')
    # Reject stale outputs: a ready-only rebuild must never retain earlier draft pages.
    allowed=set(produced)|{'build-manifest.json'}
    stale=[str(p.relative_to(output)).replace('\\','/') for p in output.rglob('*') if p.is_file() and str(p.relative_to(output)).replace('\\','/') not in allowed]
    if stale: raise ValueError(f'Output contains stale files; use a new empty output directory: {stale}')
    write('build-manifest.json',json.dumps({'mode':'private-draft-preview' if preview else 'reviewed-only','articles':[a['slug'] for a in articles],'files':produced.copy()},indent=2)+'\n')
    validate(output)
    print(f'Built {len(articles)} articles; mode={"private-draft-preview" if preview else "reviewed-only"}; output={output}')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args();build(args.output.resolve(),args.preview)
