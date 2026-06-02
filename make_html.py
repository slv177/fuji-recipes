"""Build the multilingual HTML catalog.

Usage:  python make_html.py [LANG]   (LANG in en|ru|de|es|fr; default: all)

English is the canonical content language. Per-language content files:
  group_descriptions_<lang>.json, film_sim_info_<lang>.json,
  group_visual_analysis_<lang>.json
Missing content files fall back to Russian (the original), then to whatever exists.
Output: index.html (for DEFAULT_LANG) and <lang>/index.html for the rest.
"""
import json, re, os, sys
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict

from i18n import UI, LANGS, LANG_NAMES, DEFAULT_LANG, t, plural_recipes, plural_groups
from i18n_blocks import blocks

# ── language-independent data ─────────────────────────────────────────────────
names    = {g['label']: g['name'] for g in json.load(open('group_names.json', encoding='utf-8'))}
official_photos = json.load(open('official_photos.json', encoding='utf-8'))
df_feat  = pd.read_csv('features.csv')
df_sub   = pd.read_csv('subclusters.csv')
slug_url = {r['slug']: r['url'] for r in json.load(open('recipes.json', encoding='utf-8'))}


def load_lang_json(stem, lang):
    """Load <stem>_<lang>.json, fall back to _ru then _en."""
    for suffix in (lang, 'ru', 'en'):
        path = f'{stem}_{suffix}.json'
        if os.path.exists(path):
            return json.load(open(path, encoding='utf-8'))
    raise FileNotFoundError(f'no {stem}_*.json found')


SIM_COLORS = {
    'Classic Chrome': '#4a6fa5', 'Classic Negative': '#7a9e7e', 'Eterna': '#c17c3a',
    'Eterna Bleach Bypass': '#7a6a8a', 'PRO Neg': '#b05a5a', 'Acros': '#555555',
    'Velvia': '#c44b2b', 'Monochrome': '#888888', 'Provia': '#4a8aa5', 'Astia': '#a57a4a',
}
FS_ORDER = ['Classic Chrome','Classic Negative','Eterna','Eterna Bleach Bypass',
            'PRO Neg','Acros','Velvia','Monochrome','Provia','Astia']
BW_SIMS = {'Acros', 'Monochrome'}

# numeric settings shown in card "Settings" table (labels are film terms, kept as-is)
FEAT_LABELS = {
    'highlight': 'Highlight', 'shadow': 'Shadow', 'color': 'Color',
    'sharpness': 'Sharpness', 'clarity': 'Clarity', 'dynamic_range': 'Dynamic Range',
    'grain_strength': 'Grain Effect', 'wb_red': 'WB Red', 'wb_blue': 'WB Blue',
}
MODE_FIELDS = {'dynamic_range', 'grain_strength', 'grain_size', 'color_chrome', 'color_chrome_blue'}
DR_MAP = {100.0: 'DR100', 200.0: 'DR200', 400.0: 'DR400', 250.0: 'DR-Auto'}
LEVEL_MAP = {0.0: 'Off', 1.0: 'Weak', 1.5: 'Medium', 2.0: 'Strong'}

# comparison table column order in film_sim_info table dict (Russian keys, the
# original data language). We map UI labels onto these fixed keys.
CMP_KEYS = ['Контраст', 'Насыщенность', 'Цветовой сдвиг', 'Светa', 'Тени']
# map the (Russian) film_sim_info table keys → UI translation keys
TBL_KEY_UI = {
    'Контраст': 'cmp_contrast', 'Насыщенность': 'cmp_saturation',
    'Цветовой сдвиг': 'cmp_colorcast', 'Светa': 'cmp_highlights',
    'Тени': 'cmp_shadows', 'Зерно': 'cmp_grain',
}
NUMERIC_HOM = {
    'highlight': 'Highlight', 'shadow': 'Shadow', 'color': 'Color',
    'sharpness': 'Sharpness', 'clarity': 'Clarity', 'dynamic_range': 'Dyn. Range',
    'grain_strength': 'Grain', 'wb_red': 'WB Red', 'wb_blue': 'WB Blue', 'wb_kelvin': 'WB Kelvin',
}
DR_DECODE = {100.0:'DR100', 200.0:'DR200', 400.0:'DR400', 250.0:'DR-Auto'}
GRAIN_DECODE = {0.0:'Off', 1.0:'Weak', 2.0:'Strong'}


# ── image helpers ─────────────────────────────────────────────────────────────
def get_images(slug, max_imgs=20):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    imgs = []
    for img in content.select('img'):
        src = (img.get('src','') or img.get('data-src','') or img.get('data-lazy-src',''))
        if not src or not re.search(r'\.(jpg|jpeg|webp|png)', src, re.I):
            continue
        if re.search(r'(icon|logo|avatar|banner|button|pixel|gravatar|badge|paypal|patreon)', src, re.I):
            continue
        srcset = img.get('srcset','')
        if srcset:
            parts = [p.strip().split() for p in srcset.split(',') if p.strip()]
            best, best_w = src, 0
            for p in parts:
                if len(p) >= 2 and p[1].endswith('w'):
                    w = int(p[1][:-1])
                    if w > best_w:
                        best_w, best = w, p[0]
            src = best
        imgs.append(src)
        if len(imgs) >= max_imgs:
            break
    return imgs


def group_photo_list(label, slugs, visual):
    v = visual.get(label)
    if v and v.get('best_photos'):
        return v['best_photos']
    per = max(4, -(-20 // max(len(slugs), 1)))
    photos = []
    for slug in slugs:
        photos.extend(get_images(slug, max_imgs=per))
        if len(photos) >= 20:
            break
    return photos[:20]


def fmt_mode(col, val):
    if col == 'dynamic_range':
        return DR_MAP.get(val, str(int(val)))
    if col in ('grain_strength', 'color_chrome', 'color_chrome_blue'):
        return LEVEL_MAP.get(val, str(val))
    return str(val)


def settings_rows(slugs):
    sub = df_feat[df_feat['slug'].isin(slugs)]
    rows = ''
    for c, lbl in FEAT_LABELS.items():
        v = sub[c].dropna()
        if not len(v):
            continue
        if c in MODE_FIELDS:
            rows += (f'<tr><td class="sk">{lbl}</td>'
                     f'<td class="sv mode-val">{fmt_mode(c, v.mode().iloc[0])}</td></tr>')
        else:
            rows += (f'<tr><td class="sk">{lbl}</td>'
                     f'<td class="sv">{v.mean():+.1f}</td></tr>')
    return f'<table class="stbl">{rows}</table>' if rows else ''


def group_homogeneity(slugs):
    sub = df_feat[df_feat['slug'].isin(slugs)]
    if len(sub) < 2:
        return [], []
    stable, variable = [], []
    for col, lbl in NUMERIC_HOM.items():
        v = sub[col].dropna()
        if len(v) < 2:
            continue
        std, mean = v.std(), v.mean()
        if col == 'wb_kelvin':
            if std < 400: stable.append(f'{lbl} ≈ {mean:.0f}K')
            elif std > 1200: variable.append(lbl)
        elif col == 'dynamic_range':
            if std < 50: stable.append(f'{lbl}: {DR_DECODE.get(v.mode().iloc[0], str(int(v.mode().iloc[0])))}')
            elif std > 100: variable.append(lbl)
        elif col == 'grain_strength':
            if std < 0.4: stable.append(f'{lbl}: {GRAIN_DECODE.get(v.mode().iloc[0], str(v.mode().iloc[0]))}')
        else:
            if std < 0.5: stable.append(f'{lbl}: {mean:+.0f}')
            elif std > 1.5: variable.append(lbl)
    return stable, variable


def homogeneity_html(slugs, lang):
    stable, variable = group_homogeneity(slugs)
    if not stable and not variable:
        return ''
    parts = []
    if stable:
        items = ' · '.join(f'<span class="hom-val">{s}</span>' for s in stable)
        parts.append(f'<span class="hom-lbl">{t(lang,"same")}</span> {items}')
    if variable:
        items = ' · '.join(f'<span class="hom-var">{v}</span>' for v in variable)
        parts.append(f'<span class="hom-lbl">{t(lang,"varies")}</span> {items}')
    return f'<div class="hom-block">{" &nbsp;|&nbsp; ".join(parts)}</div>'


# ── per-language build ─────────────────────────────────────────────────────────
def lang_switcher(cur):
    links = []
    for lg in LANGS:
        href = './' if lg == DEFAULT_LANG else f'/{lg}/'
        # from a sub-page, root is '../' ; keep absolute paths for simplicity
        href = '/' if lg == DEFAULT_LANG else f'/{lg}/'
        cls = 'lang-cur' if lg == cur else ''
        links.append(f'<a class="{cls}" href="{href}">{lg.upper()}</a>')
    return '<nav class="lang-switch">' + ''.join(links) + '</nav>'


def build(lang):
    data    = load_lang_json('group_descriptions', lang)
    visual  = load_lang_json('group_visual_analysis', lang)
    sim_info = load_lang_json('film_sim_info', lang)
    desc_by_label = {g['label']: g for g in data}

    group_photos = {}
    for label, gdf in df_sub.groupby('subcluster_label'):
        group_photos[label] = group_photo_list(label, gdf['slug'].tolist(), visual)
    for _sim in ['Velvia', 'Monochrome', 'Provia', 'Astia']:
        _slugs = df_feat[df_feat['film_sim'] == _sim]['slug'].tolist()
        if _slugs:
            group_photos[_sim] = group_photo_list(_sim, _slugs, visual)

    # comparison table
    def make_row(sim):
        si = sim_info.get(sim)
        if not si:
            return None
        color = SIM_COLORS.get(sim, '#999')
        tt = si.get('table', {})
        cells = ''.join(f'<td>{tt.get(k, "—")}</td>' for k in CMP_KEYS)
        cells += f'<td>{si.get("best_for","—")}</td>'
        anchor = sim.lower().replace(' ', '-').replace('/', '-')
        rank = si.get('contrast_rank', 2)
        return (rank,
                f'<tr class="cmp-link" onclick="location.href=\'#sim-{anchor}\'">'
                f'<td><span class="sim-dot" style="background:{color}"></span>'
                f'<strong>{sim}</strong></td>{cells}</tr>')

    color_sims = sorted([r for s in FS_ORDER if s not in BW_SIMS and (r := make_row(s))],
                        key=lambda x: x[0], reverse=True)
    bw_sims = sorted([r for s in FS_ORDER if s in BW_SIMS and (r := make_row(s))],
                     key=lambda x: x[0], reverse=True)
    cmp_rows = ''.join(r for _, r in color_sims)
    cmp_rows_bw = ''.join(r for _, r in bw_sims)

    cmp_cols = [t(lang,'cmp_contrast'), t(lang,'cmp_saturation'), t(lang,'cmp_colorcast'),
                t(lang,'cmp_highlights'), t(lang,'cmp_shadows'), t(lang,'cmp_bestfor')]
    cmp_headers = ''.join(f'<th>{c}</th>' for c in cmp_cols)

    comparison_table = f'''{blocks(lang)}
<div class="cmp-section">
  <h2>{t(lang,'comparison_title')}</h2>
  <table class="cmp-tbl">
    <thead><tr><th>{t(lang,'col_sim')}</th>{cmp_headers}</tr></thead>
    <tbody>{cmp_rows}<tr class="bw-sep"><td colspan="7">{t(lang,'bw_films')}</td></tr>{cmp_rows_bw}</tbody>
  </table>
</div>'''

    # sections
    by_sim = defaultdict(list)
    for g in data:
        by_sim[g['film_sim']].append(g)
    slug_title = df_feat.set_index('slug')['title'].to_dict()

    def recipe_li(s):
        title = slug_title.get(s, s)
        mark = ' <span class="ext-mark">*</span>' if s.startswith('ext-') else ''
        return f'<li><a href="{slug_url.get(s,"#")}" target="_blank">{title}</a>{mark}</li>'

    def vision_block(v):
        if v and (v.get('subjects') or v.get('visual_notes')):
            notes = v.get('visual_notes', '')
            return (f'<div class="vision-block"><div class="col-lbl">'
                    f'{t(lang,"visual_analysis")}</div>'
                    f'<p class="vision-notes">{notes}</p></div>')
        return ''

    def card_html(group_name, n_label, hom, desc, photo_html, vblock, stbl, recipe_items, badges):
        desc_p = f'<p class="desc">{desc}</p>' if desc else ''
        tags = f'<div class="tags">{badges}</div>' if badges else ''
        return f'''
<div class="card">
  <div class="card-head">
    <span class="card-name">{group_name}</span>
    <span class="pill">{n_label}</span>
  </div>
  {hom}
  {desc_p}
  <div class="gallery">{photo_html}</div>
  {vblock}
  <div class="bottom-row">
    <div class="col-settings"><div class="col-lbl">{t(lang,'settings')}</div>{stbl}</div>
    <div class="col-recipes"><div class="col-lbl">{t(lang,'recipes')}</div>
      <ul class="rlist">{recipe_items}</ul></div>
  </div>
  {tags}
</div>'''

    sections = ''
    for sim in FS_ORDER:
        sim_total = df_feat[df_feat['film_sim'] == sim].shape[0]
        if sim_total == 0:
            continue
        color = SIM_COLORS.get(sim, '#666')
        groups = by_sim.get(sim, [])

        cards = ''
        if groups:
            for g in sorted(groups, key=lambda x: int(x['label'].split('#')[1]) if '#' in x['label'] else 0):
                photos = group_photos.get(g['label'], [])
                photo_html = ''.join(f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">' for u in photos)
                if '#' in g['label']:
                    slugs = df_sub[df_sub['subcluster_label'] == g['label']]['slug'].tolist()
                else:
                    slugs = df_feat[df_feat['film_sim'] == g['label']]['slug'].tolist()
                recipe_items = ''.join(recipe_li(s) for s in slugs)
                badges = ''.join(f'<span class="badge">{k}</span>' for k in g.get('keywords', [])[:7])
                cards += card_html(
                    names.get(g['label'], g['label']),
                    plural_recipes(lang, len(slugs)),
                    homogeneity_html(slugs, lang),
                    re.sub(r'^#+\s.*\n?', '', g['description']).strip(),
                    photo_html, vision_block(visual.get(g['label'])),
                    settings_rows(slugs), recipe_items, badges)
        else:
            g = desc_by_label.get(sim)
            slugs_sim = df_feat[df_feat['film_sim'] == sim]['slug'].tolist()
            photos = group_photo_list(sim, slugs_sim, visual)
            photo_html = ''.join(f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">' for u in photos)
            recipe_items = ''.join(recipe_li(s) for s in slugs_sim)
            desc = re.sub(r'^#+\s.*\n?', '', g['description']).strip() if g else ''
            cards = card_html(
                names.get(sim, sim), plural_recipes(lang, sim_total),
                homogeneity_html(slugs_sim, lang), desc,
                photo_html, vision_block(visual.get(sim)),
                settings_rows(slugs_sim), recipe_items, '')

        si = sim_info.get(sim, {})
        tbl_rows = ''.join(
            f'<tr><td class="ti-k">{t(lang, TBL_KEY_UI.get(k)) if k in TBL_KEY_UI else k}</td>'
            f'<td class="ti-v">{v}</td></tr>'
            for k, v in si.get('table', {}).items()) if si else ''
        op = official_photos.get(sim, {})
        official_gallery = ''
        if op.get('photos'):
            imgs = ''.join(f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">' for u in op['photos'])
            src_link = f'<a href="{op["url"]}" target="_blank">fujifilm-x.com</a>'
            official_gallery = (f'<div class="official-gallery"><div class="og-photos">{imgs}</div>'
                                f'<div class="og-credit">{t(lang,"official_credit")} · {src_link}</div></div>')
        si_block = ''
        if si:
            si_block = f'''
    <div class="si-body">
      <div class="si-inspired"><span class="si-lbl">{t(lang,'basis')}</span> {si.get("inspired_by","")}</div>
      <p class="si-desc">{si.get("description","")}</p>
      <div class="si-row">
        <table class="si-tbl">{tbl_rows}</table>
        <div class="si-bestfor"><span class="si-lbl">{t(lang,'best_for_label')}</span><br>{si.get("best_for","")}</div>
      </div>
      {official_gallery}
    </div>'''

        sim_id = sim.lower().replace(' ', '-').replace('/', '-')
        n_groups = len(groups) if groups else 1
        meta = f'{plural_groups(lang, n_groups)} · {plural_recipes(lang, sim_total)}'
        sections += f'''
<section class="sim-sec" id="sim-{sim_id}" style="border-top:4px solid {color}">
  <div class="sim-hdr">
    <span class="sim-title">{sim}</span>
    <span class="sim-n">{meta}</span>
  </div>
  {si_block}
  <div class="sim-cards-area"><div class="grid">{cards}</div></div>
</section>'''

    html = PAGE.format(lang=lang, title=t(lang,'page_title'), h1=t(lang,'header_h1'),
                       sub=t(lang,'header_sub'), switcher=lang_switcher(lang),
                       body=comparison_table + '\n' + sections, css=CSS)

    out = 'index.html' if lang == DEFAULT_LANG else f'{lang}/index.html'
    os.makedirs(os.path.dirname(out), exist_ok=True) if os.path.dirname(out) else None
    open(out, 'w', encoding='utf-8').write(html)
    print(f'saved {out}  ({lang})')


# CSS and page shell are defined after build() to keep build() readable.
CSS = open('catalog.css', encoding='utf-8').read() if os.path.exists('catalog.css') else ''

PAGE = '''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<header>
  {switcher}
  <h1>{h1}</h1>
  <p>{sub}</p>
</header>
<main>{body}</main>
</body>
</html>'''


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    targets = [arg] if arg else LANGS
    # only build languages that actually have UI strings defined
    for lg in targets:
        if lg not in UI:
            print(f'skip {lg}: no UI strings yet')
            continue
        build(lg)
