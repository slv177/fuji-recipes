"""Generate a readable HTML report of all recipe groups and their descriptions."""
import json, re
import pandas as pd

data = json.load(open('group_descriptions.json', encoding='utf-8'))
df = pd.read_csv('features.csv')

# film sim order for grouping
FS_ORDER = ['Classic Chrome', 'Classic Negative', 'Eterna', 'Eterna Bleach Bypass',
            'PRO Neg', 'Acros', 'Velvia', 'Monochrome', 'Provia', 'Astia']

# index descriptions by label
desc_by_label = {g['label']: g for g in data}

# also add the small sims that weren't sub-clustered
small_sims = [s for s in FS_ORDER if s not in {g['film_sim'] for g in data}]

# palette per film sim
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

def sim_color(sim):
    return SIM_COLORS.get(sim, '#666')

def recipe_url(slug):
    return f'https://fujixweekly.com/search?q={slug.replace("-", "+")}'

def settings_table(slugs):
    cols = ['highlight', 'shadow', 'color', 'sharpness', 'clarity',
            'dynamic_range', 'grain_strength', 'wb_red', 'wb_blue']
    labels = {
        'highlight': 'Highlight', 'shadow': 'Shadow', 'color': 'Color',
        'sharpness': 'Sharpness', 'clarity': 'Clarity',
        'dynamic_range': 'Dyn. Range', 'grain_strength': 'Grain',
        'wb_red': 'WB Red', 'wb_blue': 'WB Blue',
    }
    sub = df[df['slug'].isin(slugs)]
    rows = ''
    for c in cols:
        v = sub[c].dropna()
        if len(v) == 0:
            continue
        val = f'{v.mean():+.1f}'
        bar_w = min(abs(v.mean()) / 4 * 50, 50)
        bar_color = '#e07b54' if v.mean() > 0 else '#5a8fcb'
        rows += f'''<tr>
            <td class="skey">{labels[c]}</td>
            <td class="sval">{val}</td>
            <td class="sbar"><span style="display:inline-block;width:{bar_w:.0f}px;height:8px;
                background:{bar_color};border-radius:2px;vertical-align:middle"></span></td>
        </tr>'''
    return f'<table class="stbl">{rows}</table>'

# group data by film_sim in order
from collections import defaultdict
by_sim = defaultdict(list)
for g in data:
    by_sim[g['film_sim']].append(g)

# build sections
sections_html = ''
for sim in FS_ORDER:
    groups = by_sim.get(sim, [])
    sim_total = df[df['film_sim'] == sim].shape[0] if sim in df['film_sim'].values else 0
    if sim_total == 0:
        continue
    color = sim_color(sim)

    cards_html = ''
    if groups:
        for g in sorted(groups, key=lambda x: int(x['label'].split('#')[1]) if '#' in x['label'] else 0):
            slugs = df[df['film_sim'] == sim]['slug'].tolist()
            # try to match recipes from features
            all_titles_for_sim = df[df['film_sim'] == sim]['title'].tolist()
            recipe_list = ''.join(
                f'<li>{t}</li>' for t in g['titles']
            )
            kw_badges = ''.join(
                f'<span class="badge">{k}</span>' for k in g['keywords'][:8]
            )
            stbl = settings_table(
                df[df['film_sim'] == sim]['slug'].tolist()[:g['n']]  # rough
            )
            sub_n = g['n']
            desc_clean = re.sub(r'^#+\s.*\n?', '', g['description']).strip()

            cards_html += f'''
            <div class="card">
                <div class="card-header">
                    <span class="card-title">{g["label"]}</span>
                    <span class="card-count">{sub_n} recipes</span>
                </div>
                <p class="card-desc">{desc_clean}</p>
                <div class="card-body">
                    <div class="col-recipes">
                        <div class="recipes-label">Recipes</div>
                        <ul class="recipe-list">{recipe_list}</ul>
                    </div>
                    <div class="col-settings">
                        <div class="recipes-label">Avg settings</div>
                        {stbl}
                    </div>
                </div>
                <div class="keywords">{kw_badges}</div>
            </div>'''
    else:
        # small sim, no sub-clustering
        titles = df[df['film_sim'] == sim]['title'].tolist()
        recipe_list = ''.join(f'<li>{t}</li>' for t in titles)
        cards_html = f'''
        <div class="card card-small">
            <div class="card-header">
                <span class="card-title">{sim}</span>
                <span class="card-count">{sim_total} recipes</span>
            </div>
            <ul class="recipe-list">{recipe_list}</ul>
        </div>'''

    sections_html += f'''
    <section class="sim-section">
        <div class="sim-header" style="border-left:6px solid {color}">
            <span class="sim-name">{sim}</span>
            <span class="sim-total">{sim_total} recipes</span>
        </div>
        <div class="cards-grid">{cards_html}</div>
    </section>'''

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fujifilm X-Trans IV Recipe Groups</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #f5f4f0; color: #222; line-height: 1.6; }}
  header {{ background: #1a1a1a; color: #fff; padding: 32px 40px; }}
  header h1 {{ font-size: 1.8rem; font-weight: 600; letter-spacing: -0.5px; }}
  header p  {{ color: #aaa; margin-top: 6px; font-size: 0.95rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px; }}

  .sim-section {{ margin-bottom: 48px; }}
  .sim-header {{ background: #fff; padding: 14px 20px; margin-bottom: 16px;
                 border-radius: 6px; display: flex; align-items: baseline;
                 gap: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .sim-name  {{ font-size: 1.2rem; font-weight: 700; }}
  .sim-total {{ font-size: 0.85rem; color: #888; }}

  .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px,1fr)); gap: 16px; }}

  .card {{ background: #fff; border-radius: 8px; padding: 20px;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); display: flex; flex-direction: column; gap: 12px; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .card-title  {{ font-weight: 700; font-size: 1rem; }}
  .card-count  {{ font-size: 0.8rem; color: #888; background: #f0f0f0;
                  padding: 2px 8px; border-radius: 12px; }}
  .card-desc   {{ font-size: 0.9rem; color: #444; line-height: 1.65; }}

  .card-body   {{ display: flex; gap: 16px; }}
  .col-recipes {{ flex: 1; min-width: 0; }}
  .col-settings{{ flex: 0 0 160px; }}
  .recipes-label {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: .06em;
                    color: #999; margin-bottom: 6px; }}
  .recipe-list {{ list-style: none; font-size: 0.82rem; color: #333; }}
  .recipe-list li {{ padding: 2px 0; border-bottom: 1px solid #f0f0f0; }}
  .recipe-list li:last-child {{ border-bottom: none; }}

  .stbl        {{ width: 100%; border-collapse: collapse; font-size: 0.78rem; }}
  .stbl .skey  {{ color: #777; padding: 1px 4px 1px 0; white-space: nowrap; }}
  .stbl .sval  {{ font-variant-numeric: tabular-nums; color: #333; width: 36px; text-align: right; padding-right: 6px; }}
  .stbl .sbar  {{ }}

  .keywords    {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  .badge       {{ background: #eef2ff; color: #4a6fa5; font-size: 0.72rem;
                  padding: 2px 8px; border-radius: 12px; }}

  .card-small  {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<header>
  <h1>Fujifilm X-Trans IV — Recipe Groups</h1>
  <p>184 recipes · 11 film simulations · 20 sub-groups · descriptions generated by Claude</p>
</header>
<main>
{sections_html}
</main>
</body>
</html>'''

open('recipe_groups.html', 'w', encoding='utf-8').write(HTML)
print('saved recipe_groups.html')
