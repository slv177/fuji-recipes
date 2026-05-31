"""Build Russian HTML report with photos."""
import json, re, os
import pandas as pd
from bs4 import BeautifulSoup

data    = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
visual  = json.load(open('group_visual_analysis.json', encoding='utf-8'))
names   = {g['label']: g['name'] for g in json.load(open('group_names.json', encoding='utf-8'))}
df_feat = pd.read_csv('features.csv')
df_sub  = pd.read_csv('subclusters.csv')
# slug → url mapping
slug_url = {r['slug']: r['url'] for r in json.load(open('recipes.json', encoding='utf-8'))}

# ── image extraction ──────────────────────────────────────────────────────────
def get_images(slug, max_imgs=20):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    imgs = []
    for img in content.select('img'):
        src = (img.get('src','') or img.get('data-src','') or
               img.get('data-lazy-src',''))
        if not src:
            continue
        if re.search(r'(icon|logo|avatar|banner|button|pixel|gravatar|badge|paypal|patreon)',
                     src, re.I):
            continue
        if not re.search(r'\.(jpg|jpeg|webp|png)', src, re.I):
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

desc_by_label = {g['label']: g for g in data}

# use Claude-selected best_photos when available, fallback to raw extraction
def group_photo_list(label, slugs):
    v = visual.get(label)
    if v and v.get('best_photos'):
        return v['best_photos']
    per_recipe = max(4, -(-20 // max(len(slugs), 1)))
    photos = []
    for slug in slugs:
        photos.extend(get_images(slug, max_imgs=per_recipe))
        if len(photos) >= 20:
            break
    return photos[:20]

group_photos = {}
for label, gdf in df_sub.groupby('subcluster_label'):
    group_photos[label] = group_photo_list(label, gdf['slug'].tolist())

# add small sims that were never sub-clustered
for _sim in ['Velvia', 'Monochrome', 'Provia', 'Astia']:
    _slugs = df_feat[df_feat['film_sim'] == _sim]['slug'].tolist()
    if _slugs:
        group_photos[_sim] = group_photo_list(_sim, _slugs)

# slug lookup per whole-sim label (for recipe links in if-groups branch)
sim_slugs = {
    _sim: df_feat[df_feat['film_sim'] == _sim]['slug'].tolist()
    for _sim in ['Velvia', 'Monochrome', 'Provia', 'Astia']
}

# ── palette ───────────────────────────────────────────────────────────────────
SIM_COLORS = {
    'Classic Chrome':       '#4a6fa5',
    'Classic Negative':     '#7a9e7e',
    'Eterna':               '#c17c3a',
    'Eterna Bleach Bypass': '#7a6a8a',
    'PRO Neg':              '#b05a5a',
    'Acros':                '#555555',
    'Velvia':               '#c44b2b',
    'Monochrome':           '#888888',
    'Provia':               '#4a8aa5',
    'Astia':                '#a57a4a',
}

SIM_NAMES_RU = {
    'Classic Chrome':       'Classic Chrome',
    'Classic Negative':     'Classic Negative',
    'Eterna':               'Eterna',
    'Eterna Bleach Bypass': 'Eterna Bleach Bypass',
    'PRO Neg':              'PRO Neg',
    'Acros':                'Acros',
    'Velvia':               'Velvia',
    'Monochrome':           'Monochrome',
    'Provia':               'Provia',
    'Astia':                'Astia',
}

FS_ORDER = ['Classic Chrome','Classic Negative','Eterna','Eterna Bleach Bypass',
            'PRO Neg','Acros','Velvia','Monochrome','Provia','Astia']

FEAT_LABELS_RU = {
    'highlight':      'Highlight',
    'shadow':         'Shadow',
    'color':          'Color',
    'sharpness':      'Sharpness',
    'clarity':        'Clarity',
    'dynamic_range':  'Dynamic Range',
    'grain_strength': 'Grain Effect',
    'wb_red':         'WB Red',
    'wb_blue':        'WB Blue',
}

# поля, где показываем моду (дискретные значения)
MODE_FIELDS = {'dynamic_range', 'grain_strength', 'grain_size',
               'color_chrome', 'color_chrome_blue'}

# как декодировать моду обратно в читаемый вид
DR_MAP = {100.0: 'DR100', 200.0: 'DR200', 400.0: 'DR400', 250.0: 'DR-Auto'}
LEVEL_MAP = {0.0: 'Off', 1.0: 'Weak', 1.5: 'Medium', 2.0: 'Strong'}


def fmt_mode(col, val):
    if col == 'dynamic_range':
        return DR_MAP.get(val, str(int(val)))
    if col in ('grain_strength', 'color_chrome', 'color_chrome_blue'):
        return LEVEL_MAP.get(val, str(val))
    return str(val)


def settings_rows(slugs):
    sub = df_feat[df_feat['slug'].isin(slugs)]
    rows = ''
    for c, lbl in FEAT_LABELS_RU.items():
        v = sub[c].dropna()
        if not len(v):
            continue
        if c in MODE_FIELDS:
            mode_val = v.mode().iloc[0]
            display = fmt_mode(c, mode_val)
            rows += (f'<tr><td class="sk">{lbl}</td>'
                     f'<td class="sv mode-val">{display}</td></tr>')
        else:
            mean = v.mean()
            rows += (f'<tr><td class="sk">{lbl}</td>'
                     f'<td class="sv">{mean:+.1f}</td></tr>')
    return f'<table class="stbl">{rows}</table>' if rows else ''

# ── HTML builder ──────────────────────────────────────────────────────────────
from collections import defaultdict
by_sim = defaultdict(list)
for g in data:
    by_sim[g['film_sim']].append(g)

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
            photo_html = ''.join(
                f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">'
                for u in photos)

            slugs = (df_sub[df_sub['subcluster_label'] == g['label']]['slug'].tolist()
                     or sim_slugs.get(g['label'], []))
            recipe_items = ''.join(
                f'<li><a href="{slug_url.get(s, "#")}" target="_blank">{t}</a></li>'
                for s, t in zip(slugs, g['titles'])
            )
            badges = ''.join(f'<span class="badge">{k}</span>' for k in g['keywords'][:7])
            stbl = settings_rows(slugs)

            sub_n_label = f'{g["n"]} рецепт{"а" if 2<=g["n"]<=4 else ("ов" if g["n"]>=5 else "")}'
            group_name  = names.get(g['label'], g['label'])
            desc = re.sub(r'^#+\s.*\n?', '', g['description']).strip()

            # visual analysis block
            v = visual.get(g['label'])
            vision_html = ''
            if v and (v.get('subjects') or v.get('visual_notes')):
                subj = ', '.join(v.get('subjects', [])[:8])
                moods = ', '.join(v.get('moods', [])[:6])
                notes = v.get('visual_notes', '')
                vision_html = f'''
  <div class="vision-block">
    <div class="col-lbl">Визуальный анализ</div>
    <p class="vision-notes">{notes}</p>
  </div>'''

            cards += f'''
<div class="card">
  <div class="card-head">
    <span class="card-name">{group_name}</span>
    <span class="pill">{sub_n_label}</span>
  </div>
  <p class="desc">{desc}</p>
  <div class="gallery">{photo_html}</div>
  {vision_html}
  <div class="bottom-row">
    <div class="col-settings">
      <div class="col-lbl">Настройки</div>
      {stbl}
    </div>
    <div class="col-recipes">
      <div class="col-lbl">Рецепты</div>
      <ul class="rlist">{recipe_items}</ul>
    </div>
  </div>
  <div class="tags">{badges}</div>
</div>'''
    else:
        # small sim: single card using the whole-sim description if available
        g = desc_by_label.get(sim)
        slugs_sim = df_feat[df_feat['film_sim'] == sim]['slug'].tolist()
        photos = group_photo_list(sim, slugs_sim)
        photo_html = ''.join(
            f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">'
            for u in photos)
        sim_rows = df_feat[df_feat['film_sim'] == sim][['slug','title']]
        recipe_items = ''.join(
            f'<li><a href="{slug_url.get(row.slug, "#")}" target="_blank">{row.title}</a></li>'
            for row in sim_rows.itertuples()
        )
        stbl = settings_rows(slugs_sim)
        desc = re.sub(r'^#+\s.*\n?', '', g['description']).strip() if g else ''
        n_label    = f'{sim_total} рецепт{"а" if 2<=sim_total<=4 else ("ов" if sim_total>=5 else "")}'
        group_name = names.get(sim, sim)
        v = visual.get(sim)
        vision_html = ''
        if v and (v.get('subjects') or v.get('visual_notes')):
            subj  = ', '.join(v.get('subjects', [])[:8])
            moods = ', '.join(v.get('moods', [])[:6])
            notes = v.get('visual_notes', '')
            vision_html = f'''
  <div class="vision-block">
    <div class="col-lbl">Визуальный анализ</div>
    <p class="vision-notes">{notes}</p>
  </div>'''
        cards = f'''
<div class="card">
  <div class="card-head">
    <span class="card-name">{group_name}</span>
    <span class="pill">{n_label}</span>
  </div>
  {"<p class='desc'>" + desc + "</p>" if desc else ""}
  <div class="gallery">{photo_html}</div>
  {vision_html}
  <div class="bottom-row">
    <div class="col-settings">
      <div class="col-lbl">Настройки</div>
      {stbl}
    </div>
    <div class="col-recipes">
      <div class="col-lbl">Рецепты</div>
      <ul class="rlist">{recipe_items}</ul>
    </div>
  </div>
</div>'''

    sections += f'''
<section class="sim-sec">
  <div class="sim-hdr" style="border-left:5px solid {color}">
    <span class="sim-title">{SIM_NAMES_RU.get(sim, sim)}</span>
    <span class="sim-n">{sim_total} рецептов</span>
  </div>
  <div class="grid">{cards}</div>
</section>'''

HTML = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Рецепты Fujifilm X-Trans IV — группы</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background:#f4f3ef;color:#1a1a1a;line-height:1.6}}
header{{background:#111;color:#fff;padding:36px 44px}}
header h1{{font-size:1.75rem;font-weight:700;letter-spacing:-.4px}}
header p{{color:#999;margin-top:8px;font-size:.9rem}}
main{{max-width:100%;padding:36px 40px}}

.sim-sec{{margin-bottom:60px}}
.sim-hdr{{background:#fff;padding:14px 20px;margin-bottom:18px;border-radius:6px;
          display:flex;align-items:baseline;gap:14px;
          box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.sim-title{{font-size:1.25rem;font-weight:800}}
.sim-n{{font-size:.82rem;color:#999}}

.grid{{display:flex;flex-direction:column;gap:24px}}

.card{{background:#fff;border-radius:10px;padding:28px 32px;
       box-shadow:0 1px 5px rgba(0,0,0,.08);display:flex;flex-direction:column;gap:16px;
       width:100%}}
.card-head{{display:flex;justify-content:space-between;align-items:center}}
.card-name{{font-weight:700;font-size:1.05rem}}
.pill{{background:#f0f0f0;color:#666;font-size:.75rem;padding:3px 10px;border-radius:20px}}

.desc{{font-size:.92rem;color:#444;line-height:1.75;max-width:900px}}

.gallery{{display:grid;grid-template-columns:repeat(10,1fr);gap:4px;
          border-radius:6px;overflow:hidden}}
.gallery img{{width:100%;aspect-ratio:1;object-fit:cover;display:block;
              transition:opacity .2s;cursor:pointer}}
.gallery img:hover{{opacity:.85}}
.gallery:empty{{display:none}}

.bottom-row{{display:flex;flex-direction:column;gap:20px}}
.col-recipes{{width:100%}}
.col-settings{{width:100%}}
.stbl{{border-collapse:collapse;font-size:.78rem}}
.sk{{color:#888;padding:2px 12px 2px 0;white-space:nowrap}}
.sv{{font-variant-numeric:tabular-nums;color:#333;text-align:right}}
.mode-val{{color:#555}}
.col-lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;color:#aaa;margin-bottom:6px}}

.rlist{{list-style:none;font-size:.82rem;color:#333;columns:2;column-gap:24px}}
.rlist li{{padding:2px 0;border-bottom:1px solid #f2f2f2;break-inside:avoid}}
.rlist li:last-child{{border-bottom:none}}
.rlist a{{color:#333;text-decoration:none}}
.rlist a:hover{{color:#4a6fa5;text-decoration:underline}}

.tags{{display:flex;flex-wrap:wrap;gap:5px}}
.badge{{background:#eef2ff;color:#4a6fa5;font-size:.7rem;
        padding:2px 8px;border-radius:12px}}

.vision-block{{background:#f9f8f5;border-radius:6px;padding:14px 18px;
               display:flex;flex-direction:column;gap:8px;flex:1}}
.vision-notes{{font-size:.88rem;color:#444;line-height:1.7}}
.vision-rows{{display:flex;gap:24px;font-size:.82rem;flex-wrap:wrap}}
.vtag-lbl{{color:#aaa;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-right:4px}}
.vtags{{color:#555}}
</style>
</head>
<body>
<header>
  <h1>Fujifilm X-Trans IV — группы рецептов</h1>
  <p>184 рецепта · 11 плёночных симуляций · 20 подгрупп · описания и фотографии из оригинальных статей</p>
</header>
<main>{sections}</main>
</body>
</html>'''

open('recipe_groups_ru.html', 'w', encoding='utf-8').write(HTML)
print('saved recipe_groups_ru.html')
