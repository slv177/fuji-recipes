"""Build long-form articles from articles/*.md into static pages.

Source files are named `<order>-<slug>-<lang>.md`, e.g. `01-eval-harness-ru.md`.
The first `# ` heading becomes the page title and is dropped from the body.

Output (served straight from the repo root by nginx):

    article/<slug>/index.html          default language (en)
    <lang>/article/<slug>/index.html   other languages
    article/index.html                 article index per language
    <lang>/article/index.html

Usage:
    python make_articles.py            build every visible language
    python make_articles.py ru         build one language
"""
import os
import re
import sys
import html
import markdown

from i18n import VISIBLE_LANGS, DEFAULT_LANG, t

SRC_DIR = 'articles'
FNAME_RE = re.compile(r'^(\d+)-(.+)-([a-z]{2})\.md$')

MD_EXTENSIONS = ['tables', 'fenced_code', 'sane_lists', 'attr_list']


# ── discovery ─────────────────────────────────────────────────────────────────
def discover():
    """Return [{'order', 'slug', 'files': {lang: path}}] sorted by order."""
    found = {}
    for name in sorted(os.listdir(SRC_DIR)):
        m = FNAME_RE.match(name)
        if not m:
            continue
        order, slug, lang = int(m.group(1)), m.group(2), m.group(3)
        art = found.setdefault(slug, {'order': order, 'slug': slug, 'files': {}})
        art['files'][lang] = os.path.join(SRC_DIR, name)
    return sorted(found.values(), key=lambda a: a['order'])


# ── markdown → html ───────────────────────────────────────────────────────────
def split_title(text):
    """Pull the leading `# Title` out of the markdown source."""
    lines = text.splitlines()
    title = ''
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line[2:].strip()
            lines = lines[i + 1:]
            break
    return title, '\n'.join(lines).lstrip('\n')


def render_md(text):
    body = markdown.markdown(text, extensions=MD_EXTENSIONS)
    # mermaid fences must reach the browser as <pre class="mermaid">; the entities
    # markdown escaped (--&gt;) are decoded by the DOM before mermaid reads them
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                  r'<pre class="mermaid">\1</pre>', body, flags=re.S)
    # wide tables scroll inside their own box instead of stretching the page
    body = re.sub(r'<table>.*?</table>',
                  lambda m: f'<div class="art-tw">{m.group(0)}</div>', body, flags=re.S)
    return body


# ── page shell ────────────────────────────────────────────────────────────────
def url_for(lang, slug=None):
    """Absolute URL of an article (or of the article index when slug is None)."""
    prefix = '' if lang == DEFAULT_LANG else f'/{lang}'
    return f'{prefix}/article/' + (f'{slug}/' if slug else '')


def lang_switcher(cur_lang, langs, slug=None):
    links = []
    for lg in langs:
        cls = 'lang-cur' if lg == cur_lang else ''
        links.append(f'<a class="{cls}" href="{url_for(lg, slug)}">{lg.upper()}</a>')
    return '<nav class="lang-switch">' + ''.join(links) + '</nav>'


def page(lang, title, sub, switcher, body, back_href, back_label):
    return PAGE.format(
        lang=lang, title=html.escape(title), h1=html.escape(title),
        sub=f'<p>{sub}</p>' if sub else '',
        switcher=switcher, body=body,
        back_href=back_href, back_label=back_label,
        css=CSS, mermaid=MERMAID if 'class="mermaid"' in body else '')


# ── build ─────────────────────────────────────────────────────────────────────
def build_article(art, lang):
    """Write one article page. Falls back to the default language if untranslated."""
    src_lang = lang if lang in art['files'] else DEFAULT_LANG
    if src_lang not in art['files']:
        return None
    text = open(art['files'][src_lang], encoding='utf-8').read()
    title, md_body = split_title(text)
    body = render_md(md_body)
    if src_lang != lang:
        body = f'<p class="art-na">{t(lang, "lang_na")}</p>' + body

    # the switcher lists the languages this article actually exists in
    langs = [lg for lg in VISIBLE_LANGS if lg in art['files']]
    switcher = lang_switcher(src_lang, langs, art['slug'])

    out = os.path.join(*(([] if lang == DEFAULT_LANG else [lang])
                         + ['article', art['slug'], 'index.html']))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page(
        lang, title, '', switcher, f'<article class="art-body">{body}</article>',
        url_for(lang), t(lang, 'back_to_articles')))
    print(f'saved {out}')
    return {'slug': art['slug'], 'title': title, 'langs': langs, 'src_lang': src_lang}


def build_index(lang, entries):
    items = []
    for e in entries:
        langs = ' · '.join(lg.upper() for lg in e['langs'])
        items.append(
            f'<li><a href="{url_for(lang, e["slug"])}">{html.escape(e["title"])}</a>'
            f'<div class="art-meta">{langs}</div></li>')
    body = f'<ul class="art-list">{"".join(items)}</ul>'
    out = os.path.join(*(([] if lang == DEFAULT_LANG else [lang])
                         + ['article', 'index.html']))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page(
        lang, t(lang, 'articles_title'), t(lang, 'articles_sub'),
        lang_switcher(lang, VISIBLE_LANGS), body,
        '/' if lang == DEFAULT_LANG else f'/{lang}/', t(lang, 'back_to_catalog')))
    print(f'saved {out}')


def build(lang, articles):
    entries = [e for e in (build_article(a, lang) for a in articles) if e]
    build_index(lang, entries)


CSS = ''.join(open(f, encoding='utf-8').read()
              for f in ('catalog.css', 'article.css') if os.path.exists(f))

MERMAID = ('<script type="module">'
           'import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
           'mermaid.initialize({startOnLoad:true,theme:"neutral",'
           'fontFamily:"-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"});'
           '</script>')

PAGE = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script defer src="https://stats.ss.zone/script.js" data-website-id="58d1f8c5-a3e9-4cc3-805a-1f0802b2f5b3"></script>
<style>{css}</style>
</head>
<body>
<header>
  {switcher}
  <h1>{h1}</h1>
  {sub}
</header>
<main class="art-main">
<a class="art-back" href="{back_href}">{back_label}</a>
{body}
</main>
{mermaid}
</body>
</html>'''


if __name__ == '__main__':
    arts = discover()
    if not arts:
        sys.exit(f'no articles found in {SRC_DIR}/')
    targets = [sys.argv[1]] if len(sys.argv) > 1 else VISIBLE_LANGS
    for lg in targets:
        build(lg, arts)
