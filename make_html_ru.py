"""Build Russian HTML report with photos."""
import json, re, os
import pandas as pd
from bs4 import BeautifulSoup

data     = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
visual   = json.load(open('group_visual_analysis.json', encoding='utf-8'))
names    = {g['label']: g['name'] for g in json.load(open('group_names.json', encoding='utf-8'))}
sim_info     = json.load(open('film_sim_info.json', encoding='utf-8'))
official_photos = json.load(open('official_photos.json', encoding='utf-8'))
df_feat  = pd.read_csv('features.csv')
df_sub   = pd.read_csv('subclusters.csv')
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

# ── Comparison table ──────────────────────────────────────────────────────────
CMP_COLS = ['Контраст', 'Насыщенность', 'Цветовой сдвиг', 'Светa', 'Тени', 'Лучше всего для']
BW_SIMS = {'Acros', 'Monochrome'}

CONTRAST_ORDER = {
    'экстремальный': 5, 'extreme': 5,
    'очень высокий': 4,
    'высокий': 3,
    'средний': 2, 'medium': 2,
    'средний (std) / средний (hi)': 2,
    'низкий (std) / средний (hi)': 1.5,
    'низкий': 1,
    'очень низкий': 0,
}

def contrast_rank(si):
    v = si.get('table', {}).get('Контраст', '').lower()
    for key, rank in CONTRAST_ORDER.items():
        if key in v:
            return rank
    return 2  # default

def make_row(sim):
    si = sim_info.get(sim)
    if not si:
        return None
    color = SIM_COLORS.get(sim, '#999')
    t = si.get('table', {})
    cells = ''.join(f'<td>{t.get(c, "—")}</td>' for c in CMP_COLS[:-1])
    cells += f'<td>{si.get("best_for","—")}</td>'
    anchor = sim.lower().replace(' ', '-').replace('/', '-')
    return (contrast_rank(si),
            f'<tr class="cmp-link" onclick="location.href=\'#sim-{anchor}\'">'
            f'<td><span class="sim-dot" style="background:{color}"></span>'
            f'<strong>{sim}</strong></td>{cells}</tr>')

color_sims = sorted(
    [r for s in FS_ORDER if s not in BW_SIMS and (r := make_row(s))],
    key=lambda x: x[0], reverse=True)
bw_sims = sorted(
    [r for s in FS_ORDER if s in BW_SIMS and (r := make_row(s))],
    key=lambda x: x[0], reverse=True)

cmp_rows    = ''.join(r for _, r in color_sims)
cmp_rows_bw = ''.join(r for _, r in bw_sims)

cmp_headers = ''.join(f'<th>{c}</th>' for c in CMP_COLS)

INTRO_BLOCK = '''
<div class="intro-block">
  <h2>О каталоге</h2>
  <p>Каталог построен на основе двух источников. Основной массив — <strong>184 рецепта</strong>
  с сайта <a href="https://fujixweekly.com/fujifilm-x-trans-iv-recipes/" target="_blank">Fuji X Weekly</a>
  (Ritchie Roesch), крупнейшей коллекции рецептов для X-Trans IV. Дополнительно добавлены
  <strong>7 рецептов</strong> Джозефа Д'Агостино
  (<a href="https://www.josephdagostinophotography.com/joedagostino-photo-blog/2021/1/27/r7ydnsoxgcgdi4uasfztt70yyuty1t" target="_blank">josephdagostinophotography.com</a>).
  Итого: <strong>191 рецепт</strong>.</p>

  <p>Каждый рецепт представлен как точка в многомерном пространстве настроек. Мы сгруппировали
  рецепты методом иерархической кластеризации (Ward) сначала по типу плёночной симуляции, затем
  нашли скрытые подгруппы внутри каждой симуляции — по балансу белого, динамическому диапазону
  и чёткости. Для каждой группы Claude Opus проанализировал примеры фотографий и сформулировал
  визуальный характер. Названия групп сгенерированы с TF-IDF-взвешиванием названий плёнок.</p>

  <h3>Что объединяет рецепты внутри группы, а что различает</h3>
  <p>Анализ разброса параметров внутри каждой группы показал устойчивую закономерность:
  <strong>баланс белого</strong> — самый вариативный параметр почти везде. Авторы приходят к
  похожему визуальному результату разными путями: кто-то через тёплый Kelvin, кто-то через сдвиги
  Red/Blue. <strong>Grain</strong>, напротив, обычно стабилен — внутри группы авторы сходятся на
  одном характере зернистости.</p>
  <p>Самая неоднородная группа — <strong>Kodak Contrast Classics</strong> (Acros): варьируется
  буквально всё, включая WB ±1375K. Это скорее «сборная всего разного в Acros», чем плотный
  кластер. Наоборот, <strong>Cinematic Teal Glow</strong> (Eterna) — единственная группа, где
  стабильна и Clarity = −5, и WB ≈ 4275K: оба автора пришли к практически одинаковому
  специфическому профилю независимо.</p>
  <p><strong>Kodachrome Warm Earth</strong> (Classic Chrome, 26 рецептов) — самая большая группа,
  и при этом ни один параметр не зафиксирован: это «размытый центр» симуляции, куда попало всё,
  что не вписалось в более специфичные подгруппы. Использовать как ориентир, но не как образец.</p>

  <h3>Рецепты Д'Агостино: насколько они уникальны?</h3>
  <p>Сравнение с ближайшими соседями в пространстве настроек показало следующее:</p>
  <ul>
    <li><strong>Kodachrome 64 +</strong> и <strong>Summer</strong> — практически идентичны уже
    существующим рецептам (расстояние 0.00 и 0.26). Независимые переоткрытия одних и тех же настроек.</li>
    <li><strong>Classic Negative</strong>, <strong>Kodachrome 64 −</strong>, <strong>Kodak Portra</strong> —
    вписываются в свои группы, но с личным акцентом: повышенная резкость, экстремально поднятые
    света, сильный тёплый сдвиг WB.</li>
    <li><strong>Noir</strong> (Acros) — выбивается из группы: Sharpness +4, Highlight +4, DR100.
    Намеренный максимализм контраста.</li>
    <li><strong>Monochrome</strong> — самый далёкий от любого соседа (расстояние 6.23), занимает
    собственную нишу в малочисленной группе.</li>
  </ul>
  <p class="intro-note">Рецепты Д'Агостино отмечены звёздочкой <span class="ext-mark">*</span>
  в списках групп.</p>
</div>'''

comparison_table = f'''{INTRO_BLOCK}
<div class="cmp-section">
  <h2>Сравнение плёнок</h2>
  <table class="cmp-tbl">
    <thead><tr><th>Симуляция</th>{cmp_headers}</tr></thead>
    <tbody>{cmp_rows}<tr class="bw-sep"><td colspan="7">Монохромные плёнки</td></tr>{cmp_rows_bw}</tbody>
  </table>
</div>'''

# ── Group homogeneity analysis ────────────────────────────────────────────────
NUMERIC_LABELS = {
    'highlight': 'Highlight', 'shadow': 'Shadow', 'color': 'Color',
    'sharpness': 'Sharpness', 'clarity': 'Clarity', 'dynamic_range': 'Dyn. Range',
    'grain_strength': 'Grain', 'wb_red': 'WB Red', 'wb_blue': 'WB Blue',
    'wb_kelvin': 'WB Kelvin',
}
DR_DECODE = {100.0:'DR100', 200.0:'DR200', 400.0:'DR400', 250.0:'DR-Auto'}
GRAIN_DECODE = {0.0:'Off', 1.0:'Weak', 2.0:'Strong'}


def group_homogeneity(slugs):
    """Return (stable_items, variable_items) for a list of recipe slugs."""
    sub = df_feat[df_feat['slug'].isin(slugs)]
    if len(sub) < 2:
        return [], []
    stable, variable = [], []
    for col, lbl in NUMERIC_LABELS.items():
        v = sub[col].dropna()
        if len(v) < 2:
            continue
        std = v.std()
        mean = v.mean()
        if col == 'wb_kelvin':
            if std < 400:
                stable.append(f'{lbl} ≈ {mean:.0f}K')
            elif std > 1200:
                variable.append(lbl)
        elif col == 'dynamic_range':
            if std < 50:
                stable.append(f'{lbl}: {DR_DECODE.get(v.mode().iloc[0], str(int(v.mode().iloc[0])))}')
            elif std > 100:
                variable.append(lbl)
        elif col == 'grain_strength':
            if std < 0.4:
                stable.append(f'{lbl}: {GRAIN_DECODE.get(v.mode().iloc[0], str(v.mode().iloc[0]))}')
        else:
            if std < 0.5:
                stable.append(f'{lbl}: {mean:+.0f}')
            elif std > 1.5:
                variable.append(lbl)
    return stable, variable


def homogeneity_html(slugs):
    stable, variable = group_homogeneity(slugs)
    if not stable and not variable:
        return ''
    parts = []
    if stable:
        items = ' · '.join(f'<span class="hom-val">{s}</span>' for s in stable)
        parts.append(f'<span class="hom-lbl">Одинаково:</span> {items}')
    if variable:
        items = ' · '.join(f'<span class="hom-var">{v}</span>' for v in variable)
        parts.append(f'<span class="hom-lbl">Варьируется:</span> {items}')
    return f'<div class="hom-block">{" &nbsp;|&nbsp; ".join(parts)}</div>'


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

            if '#' in g['label']:
                # proper subcluster — use df_sub
                slugs = df_sub[df_sub['subcluster_label'] == g['label']]['slug'].tolist()
            else:
                # whole-sim label (small sims like Monochrome, Velvia…) — use df_feat
                slugs = df_feat[df_feat['film_sim'] == g['label']]['slug'].tolist()
            # build title map from df_feat (covers new external recipes too)
            slug_title = df_feat.set_index('slug')['title'].to_dict()
            def recipe_li(s):
                title = slug_title.get(s, s)
                mark = ' <span class="ext-mark">*</span>' if s.startswith('ext-') else ''
                return (f'<li><a href="{slug_url.get(s,"#")}" target="_blank">'
                        f'{title}</a>{mark}</li>')
            recipe_items = ''.join(recipe_li(s) for s in slugs)
            badges = ''.join(f'<span class="badge">{k}</span>' for k in g['keywords'][:7])
            stbl = settings_rows(slugs)

            sub_n_label = f'{len(slugs)} рецепт{"а" if 2<=len(slugs)<=4 else ("ов" if len(slugs)>=5 else "")}'
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

            hom_html = homogeneity_html(slugs)
            cards += f'''
<div class="card">
  <div class="card-head">
    <span class="card-name">{group_name}</span>
    <span class="pill">{sub_n_label}</span>
  </div>
  {hom_html}
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
            f'<li><a href="{slug_url.get(row.slug,"#")}" target="_blank">{row.title}</a>'
            f'{"<span class=\"ext-mark\"> *</span>" if row.slug.startswith("ext-") else ""}</li>'
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
        hom_html = homogeneity_html(slugs_sim)
        cards = f'''
<div class="card">
  <div class="card-head">
    <span class="card-name">{group_name}</span>
    <span class="pill">{n_label}</span>
  </div>
  {hom_html}
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

    si = sim_info.get(sim, {})
    tbl_rows = ''.join(
        f'<tr><td class="ti-k">{k}</td><td class="ti-v">{v}</td></tr>'
        for k, v in si.get('table', {}).items()
    ) if si else ''
    op = official_photos.get(sim, {})
    official_gallery = ''
    if op.get('photos'):
        imgs = ''.join(
            f'<img src="{u}" loading="lazy" onerror="this.style.display=\'none\'">'
            for u in op['photos']
        )
        src_link = f'<a href="{op["url"]}" target="_blank">fujifilm-x.com</a>'
        official_gallery = f'''
      <div class="official-gallery">
        <div class="og-photos">{imgs}</div>
        <div class="og-credit">© Fujifilm X · {src_link}</div>
      </div>'''

    si_block = f'''
    <div class="si-body">
      <div class="si-inspired"><span class="si-lbl">Основа:</span> {si.get("inspired_by","")}</div>
      <p class="si-desc">{si.get("description","")}</p>
      <div class="si-row">
        <table class="si-tbl">{tbl_rows}</table>
        <div class="si-bestfor"><span class="si-lbl">Лучше всего для:</span><br>{si.get("best_for","")}</div>
      </div>
      {official_gallery}
    </div>''' if si else ''

    sim_id = sim.lower().replace(' ', '-').replace('/', '-')
    n_groups = len(groups) if groups else 1
    groups_str = f'{n_groups} групп{"а" if n_groups==1 else ("ы" if 2<=n_groups<=4 else "")}'
    sections += f'''
<section class="sim-sec" id="sim-{sim_id}" style="border-top:4px solid {color}">
  <div class="sim-hdr">
    <span class="sim-title">{SIM_NAMES_RU.get(sim, sim)}</span>
    <span class="sim-n">{groups_str} · {sim_total} рецептов</span>
  </div>
  {si_block}
  <div class="sim-cards-area">
    <div class="grid">{cards}</div>
  </div>
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

/* ── outer film-simulation container ── */
.sim-sec{{background:#fff;border-radius:12px;margin-bottom:48px;
          box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden}}
.sim-hdr{{padding:20px 28px;display:flex;align-items:baseline;gap:14px;
          border-bottom:1px solid #f0eeea}}
.sim-title{{font-size:1.3rem;font-weight:800}}
.sim-n{{font-size:.82rem;color:#aaa}}

/* film sim description inside the container */
.si-body{{padding:20px 28px;border-bottom:1px solid #f0eeea;
          display:flex;flex-direction:column;gap:10px}}

/* nested recipe-group cards area */
.sim-cards-area{{background:#f7f6f2;padding:20px 28px;
                 display:flex;flex-direction:column;gap:0}}

.grid{{display:flex;flex-direction:column;gap:16px}}

/* inner card — slightly inset look */
.card{{background:#fff;border-radius:8px;padding:24px 28px;
       box-shadow:0 1px 3px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:16px;
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
.ext-mark{{color:#c17c3a;font-weight:700;font-size:.85em}}
.hom-block{{font-size:.78rem;color:#666;background:#f7f6f2;border-radius:4px;
            padding:6px 12px;display:flex;flex-wrap:wrap;gap:6px 16px}}
.hom-lbl{{color:#aaa;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-right:2px}}
.hom-val{{color:#4a7a5a;font-weight:500}}
.hom-var{{color:#b05a5a}}

.tags{{display:flex;flex-wrap:wrap;gap:5px}}
.badge{{background:#eef2ff;color:#4a6fa5;font-size:.7rem;
        padding:2px 8px;border-radius:12px}}

.vision-block{{background:#f9f8f5;border-radius:6px;padding:14px 18px;
               display:flex;flex-direction:column;gap:8px;flex:1}}
.vision-notes{{font-size:.88rem;color:#444;line-height:1.7}}
.vision-rows{{display:flex;gap:24px;font-size:.82rem;flex-wrap:wrap}}
.vtag-lbl{{color:#aaa;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-right:4px}}
.vtags{{color:#555}}

/* film simulation description (inside outer container) */
.si-inspired{{font-size:.83rem;color:#aaa}}
.si-lbl{{font-weight:600;color:#666;margin-right:5px}}
.si-desc{{font-size:.92rem;color:#333;line-height:1.75;max-width:900px}}
.si-row{{display:flex;gap:32px;align-items:flex-start;flex-wrap:wrap;margin-top:4px}}
.si-tbl{{border-collapse:collapse;font-size:.82rem}}
.si-tbl td{{padding:3px 16px 3px 0;vertical-align:top}}
.ti-k{{color:#888;white-space:nowrap}}
.ti-v{{color:#333;font-weight:500}}
.si-bestfor{{font-size:.88rem;color:#555;max-width:300px}}

/* official gallery */
.official-gallery{{margin-top:4px}}
.og-photos{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px;border-radius:6px;overflow:hidden}}
.og-photos img{{width:100%;aspect-ratio:3/2;object-fit:cover;display:block;transition:opacity .2s}}
.og-photos img:hover{{opacity:.9}}
.og-credit{{font-size:.72rem;color:#bbb;margin-top:5px;text-align:right}}
.og-credit a{{color:#bbb;text-decoration:none}}
.og-credit a:hover{{color:#4a6fa5}}

/* comparison table */
.cmp-section{{background:#fff;border-radius:8px;padding:28px 32px;margin-bottom:48px;
              box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.cmp-section h2{{font-size:1.1rem;font-weight:700;margin-bottom:16px;color:#1a1a1a}}
.cmp-tbl{{width:100%;border-collapse:collapse;font-size:.82rem}}
.cmp-tbl th{{background:#f4f3ef;padding:8px 12px;text-align:left;font-weight:600;
             color:#555;border-bottom:2px solid #e0ddd8;white-space:nowrap}}
.cmp-tbl td{{padding:7px 12px;border-bottom:1px solid #f0eeea;vertical-align:top}}
.cmp-tbl tr:last-child td{{border-bottom:none}}
.cmp-tbl tr:hover td{{background:#faf9f6}}
.cmp-link{{cursor:pointer}}
.cmp-link:hover td{{background:#eef2ff}}
.bw-sep td{{background:#f4f3ef;color:#999;font-size:.72rem;text-transform:uppercase;
            letter-spacing:.08em;padding:6px 12px;border-top:2px solid #e0ddd8}}

/* intro block */
.intro-block{{background:#fff;border-radius:8px;padding:28px 32px;margin-bottom:24px;
              box-shadow:0 1px 4px rgba(0,0,0,.07);display:flex;flex-direction:column;gap:14px}}
.intro-block h2{{font-size:1.1rem;font-weight:700}}
.intro-block h3{{font-size:.95rem;font-weight:700;color:#555;margin-top:4px}}
.intro-block p{{font-size:.9rem;color:#444;line-height:1.75;max-width:900px}}
.intro-block ul{{font-size:.9rem;color:#444;line-height:1.75;max-width:900px;
                 padding-left:20px;display:flex;flex-direction:column;gap:4px}}
.intro-block a{{color:#4a6fa5}}
.intro-note{{color:#888 !important;font-size:.82rem !important}}
.sim-dot{{display:inline-block;width:10px;height:10px;border-radius:50%;
          margin-right:7px;vertical-align:middle}}

/* ── tablet ── */
@media (max-width: 900px) {{
  main{{padding:24px 18px}}
  .gallery{{grid-template-columns:repeat(5,1fr)}}
  .og-photos{{grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}}
}}

/* ── phone ── */
@media (max-width: 600px) {{
  header{{padding:24px 18px}}
  header h1{{font-size:1.3rem}}
  header p{{font-size:.8rem}}
  main{{padding:16px 12px}}

  .sim-sec{{margin-bottom:28px;border-radius:8px}}
  .sim-hdr{{padding:14px 16px;flex-wrap:wrap;gap:4px 12px}}
  .sim-title{{font-size:1.1rem}}
  .si-body{{padding:16px}}
  .si-row{{flex-direction:column;gap:16px}}
  .si-desc,.si-bestfor{{max-width:100%}}
  .sim-cards-area{{padding:14px}}

  .card{{padding:18px 16px;gap:14px}}
  .card-name{{font-size:1rem}}
  .desc{{font-size:.88rem;max-width:100%}}

  /* galleries: 3 columns on phone */
  .gallery{{grid-template-columns:repeat(3,1fr);gap:3px}}
  .og-photos{{grid-template-columns:repeat(2,1fr)}}
  .og-photos img{{aspect-ratio:3/2}}

  /* recipes single column */
  .rlist{{columns:1}}

  /* homogeneity wraps */
  .hom-block{{flex-direction:column;gap:4px}}

  /* comparison table — horizontal scroll */
  .cmp-section{{padding:18px 14px}}
  .cmp-section .cmp-tbl{{display:block;overflow-x:auto;white-space:nowrap;font-size:.75rem}}

  .intro-block{{padding:18px 16px}}
  .intro-block p,.intro-block ul{{font-size:.86rem;max-width:100%}}
}}
</style>
</head>
<body>
<header>
  <h1>Fujifilm X-Trans IV — группы рецептов</h1>
  <p>184 рецепта · 11 плёночных симуляций · 20 подгрупп · описания и фотографии из оригинальных статей</p>
</header>
<main>{comparison_table}
{sections}</main>
</body>
</html>'''

open('index.html', 'w', encoding='utf-8').write(HTML)
print('saved index.html')
