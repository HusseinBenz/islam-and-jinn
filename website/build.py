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

STAR='M11 0L7.78 3.22L7.78 7.78L3.22 7.78L0 11L-3.22 7.78L-7.78 7.78L-7.78 3.22L-11 0L-7.78 -3.22L-7.78 -7.78L-3.22 -7.78L0 -11L3.22 -7.78L7.78 -7.78L7.78 -3.22Z'
BOOK='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/></svg>'
ARROW='<svg class="sk-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>'
FONTS='https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Figtree:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500&family=Instrument+Serif:ital@0;1&family=Reem+Kufi:wght@400;500;600;700&display=swap'
THEME_INIT="(function(){var t;try{t=localStorage.getItem('sakina-theme')}catch(e){}if(t!=='light'&&t!=='dark'){t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}document.documentElement.setAttribute('data-theme',t)})();"
# Links are relative, so the site works at a domain root and under a project path (GitHub Pages).
ASSETS=['sakina.css','site.css','sakina.js','reading.js']

def href(article, root=''):
    return f'{root}articles/{article["slug"]}/'

def chapter_nav(articles, current=None, root=''):
    return ''.join(f'<a href="{href(a,root)}" data-slug="{a["slug"]}"'+(' aria-current="page"' if a['slug']==current else '')+f'><span class="chapter-number">{a["order"]:02}</span><span>{esc(a["title"])}</span></a>' for a in articles)

def shell(title, description, main, articles, preview, current=None, root=''):
    home=root or './'
    return f"""<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{esc(description,quote=True)}">
{'<meta name="robots" content="noindex,nofollow">' if preview else ''}
<meta name="theme-color" content="#F6F4EE">
<title>{esc(title)}{' — Jinn in Islam' if title!='Jinn in Islam' else ''}</title>
<script>{THEME_INIT}</script>
<link rel="icon" type="image/svg+xml" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/sakina.css"><link rel="stylesheet" href="{root}assets/site.css"></head>
<body class="sk-project-jinn"><a class="sk-skip" href="#main">Skip to content</a>
<div class="sk-pattern" aria-hidden="true"></div>
<div class="reading-progress" aria-hidden="true"><span></span></div>
<header class="sk-header"><div class="sk-container sk-header__inner">
<div class="masthead"><a class="sk-brand" href="{home}"><span class="sk-tile sk-tile--sm">{BOOK}</span><span class="sk-brand__text"><span class="sk-brand__name">Jinn in Islam</span><span class="sk-brand__sub" lang="ar">الجن في الإسلام</span></span></a>
<nav class="site-nav" aria-label="Main navigation"><a class="sk-btn sk-btn--ghost sk-btn--sm" href="{home}"{' aria-current="page"' if current=='home' else ''}>Encyclopedia</a><a class="sk-btn sk-btn--ghost sk-btn--sm" href="{root}about/"{' aria-current="page"' if current=='about' else ''}>About &amp; sources</a></nav></div>
<div class="sk-header__nav">{'<span class="sk-tag sk-tag--gold edition">Reading preview</span>' if preview else '<span class="sk-tag edition">English edition</span>'}
<a class="sk-btn sk-btn--line sk-btn--sm sk-projects" href="https://husseinbenz.github.io/islamic-projects/" aria-label="All Islamic projects"><span class="sk-constellation" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span><span class="sk-hide-sm">All projects</span></a>
<button class="sk-icon-btn sk-theme-btn" type="button" data-sk-theme-toggle aria-label="Switch to night theme"><svg class="sk-i-moon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg><svg class="sk-i-sun" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg></button></div>
</div></header>
{'' if current in ('home','about') else f'<details class="mobile-chapters sk-container"><summary>Browse the chapters</summary><nav aria-label="Chapters">{chapter_nav(articles,current,root)}</nav></details>'}
{main}
<footer class="sk-footer"><div class="sk-container sk-footer__inner"><p>An independent encyclopedia based on al-Sabeel. {'Drafts under editorial and reference review.' if preview else 'English edition.'} <a class="sk-link" href="{root}about/">Our approach to sources</a></p>
<a class="sk-footer__home" href="https://husseinbenz.github.io/islamic-projects/"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path style="fill:var(--primary)" d="M23 12L19.78 15.22L19.78 19.78L15.22 19.78L12 23L8.78 19.78L4.22 19.78L4.22 15.22L1 12L4.22 8.78L4.22 4.22L8.78 4.22L12 1L15.22 4.22L19.78 4.22L19.78 8.78Z"/><circle cx="12" cy="12" r="4.4" style="fill:var(--bg)"/></svg>Part of Islamic Projects</a></div></footer>
<script src="{root}assets/sakina.js"></script><script src="{root}assets/reading.js"></script>
</body></html>"""

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
    items=''.join(f"""<li><a class="chapter-row sk-card sk-lift" href="{href(a)}" data-slug="{a['slug']}"><span class="row-number sk-tile sk-tile--md">{a['order']:02}</span><div class="chapter-row__text"><span class="topic">{esc(a['tags'][0].replace('-',' '))}</span><h3>{esc(a['title'])}</h3><p>{esc(a['description'])}</p></div><span class="row-link">{ARROW}</span></a></li>""" for a in articles)
    first=f'<a class="sk-btn sk-btn--accent sk-btn--lg" href="{href(articles[0])}">Start reading {ARROW}</a>' if articles else ''
    main=f"""<main id="main" class="sk-container portal">
<section class="portal-hero"><div class="portal-hero__text"><span class="sk-eyebrow sk-rise">An encyclopedia of the unseen</span><h1 class="sk-display sk-rise sk-d1">{esc(lead)}</h1><p class="sk-lede sk-rise sk-d2">{esc(intro.strip())}</p><div class="portal-hero__actions sk-rise sk-d3">{first}<a class="sk-btn sk-btn--line sk-btn--lg" href="about/">About &amp; sources</a></div><a class="resume sk-card sk-lift" id="resume" href="./" hidden><span class="sk-eyebrow">Pick up where you left off</span><strong></strong>{ARROW}</a></div>
<figure class="portal-art sk-arch sk-rise sk-d2"><svg class="portal-art__star sk-slow-spin" width="26" height="26" viewBox="-12 -12 24 24" aria-hidden="true"><path d="{STAR}"/></svg><blockquote lang="ar" dir="rtl">وَخَلَقَ ٱلْجَآنَّ مِن مَّارِجٍ مِّن نَّارٍ</blockquote><figcaption>“And He created the jinn from a smokeless flame of fire.”<span>Ar-Raḥmān 55:15</span></figcaption></figure></section>
<section class="portal-body"><aside class="collection-note"><span class="sk-eyebrow">The collection</span><p class="large-number">{len(articles):02}<span>chapters available</span></p><p>Read in the order of the source series, from foundations to the questions that follow.</p>{'<p class="draft-note"><strong>A work in progress.</strong> These are condensed drafts. Source checks and editorial review continue.</p>' if preview else ''}<a class="sk-link" href="about/">About the project</a></aside><div class="chapter-list"><div class="list-title"><h2 class="sk-display">Explore the chapters</h2><span>English edition</span></div><ol>{items}</ol>{'<p>Reviewed articles are being prepared.</p>' if not articles else ''}</div></section></main>"""
    write('index.html',shell(home_meta['title'],home_meta['description'],main,articles,preview,'home'))
    for i,a in enumerate(articles):
        body,toc=render(a['body'])
        words=len(a['body'].split('\n## References')[0].split()); minutes=max(1,round(words/220))
        R='../../'
        prev=f'<a class="sk-card sk-lift" href="{href(articles[i-1],R)}"><span>Previous chapter</span>{esc(articles[i-1]["title"])}</a>' if i else f'<a class="sk-card sk-lift" href="{R}"><span>Return to</span>The encyclopedia</a>'
        nxt=f'<a class="sk-card sk-lift" href="{href(articles[i+1],R)}"><span>Next chapter</span>{esc(articles[i+1]["title"])}</a>' if i+1<len(articles) else f'<a class="sk-card sk-lift" href="{R}"><span>Continue exploring</span>All chapters</a>'
        next_card=f'<a class="next-card sk-card sk-lift" href="{href(articles[i+1],R)}"><span class="sk-eyebrow">Next chapter</span><strong class="sk-display">{articles[i+1]["order"]:02} · {esc(articles[i+1]["title"])}</strong><span class="next-card__go">Continue {ARROW}</span></a>' if i+1<len(articles) else ''
        main=f"""<main id="main" class="sk-container reading-layout">
<aside class="reading-chapters"><p class="sk-eyebrow">The collection</p><nav aria-label="Chapters">{chapter_nav(articles,a['slug'],R)}</nav></aside>
<article class="article" data-slug="{a['slug']}" data-title="{esc(a['title'],quote=True)}" data-minutes="{minutes}"><header class="article-header"><div class="article-meta"><span class="sk-tag sk-tag--accent">Chapter {a['order']:02}</span><span>{minutes} min read</span></div><h1 class="sk-display">{esc(a['title'])}</h1><p class="article-deck">{esc(a['description'])}</p><div class="tags">{''.join('<span class="sk-tag">'+esc(t.replace('-',' '))+'</span>' for t in a['tags'])}</div>{'<p class="review-notice"><strong>Draft for reading.</strong> Editorial and reference review is still in progress.</p>' if a['status']!='ready' else ''}</header><details class="mobile-toc"><summary>In this chapter</summary>{toc}</details><div class="prose">{body}</div><nav class="chapter-pagination" aria-label="Adjacent chapters">{prev}{nxt}</nav></article>
<aside class="reading-sidebar"><a class="back-link" href="{R}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>All chapters</a><p class="sk-eyebrow">In this chapter</p>{toc}<div class="progress-card sk-card" hidden><span class="progress-ring"><span>0%</span></span><span class="progress-card__text"><strong>{minutes} min read</strong><small>We'll keep your place</small></span></div>{next_card}</aside></main>"""
        write(f'articles/{a["slug"]}/index.html',shell(a['title'],a['description'],main,articles,preview,a['slug'],'../../'))
    meta,body=read_md(ROOT/'content/pages/about.md'); rendered,toc=render(body)
    main=f'<main id="main" class="sk-container about-page"><span class="sk-eyebrow">The project</span><h1 class="sk-display">{esc(meta["title"])}</h1><div class="prose">{rendered}</div></main>'
    write('about/index.html',shell(meta['title'],meta['description'],main,articles,preview,'about','../'))
    for asset in ASSETS:
        write(f'assets/{asset}',(ROOT/'website'/asset).read_text(encoding='utf-8'))
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
