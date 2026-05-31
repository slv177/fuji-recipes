"""Add external recipes (non-fujixweekly) to the catalog.

Adds to recipes.json, recipe_urls.json, features.csv, subclusters.csv.
Assigns each new recipe to the nearest existing subcluster.
"""
import json, re
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# ── define new recipes ────────────────────────────────────────────────────────
SOURCE_URL = 'https://www.josephdagostinophotography.com/joedagostino-photo-blog/2021/1/27/r7ydnsoxgcgdi4uasfztt70yyuty1t'
SOURCE_AUTHOR = 'Joseph D\'Agostino'

NEW_RECIPES = [
    {
        'slug': 'ext-dagostino-classic-negative',
        'title': 'Classic Negative (D\'Agostino)',
        'index_title': 'Classic Negative',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Classic Negative',
            'Grain Effect': 'Weak, Small',
            'Color Chrome Effect': 'Strong',
            'Color Chrome FX Blue': 'Strong',
            'White Balance': '6000K, 0 Red & 0 Blue',
            'D Range Priority': 'Auto',
            'Color': '+2',
            'Sharpness': '+3',
            'Noise Reduction': '-4',
            'Clarity': '+1',
            'Exposure Compensation': '0 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-kodachrome64-minus',
        'title': 'Kodachrome 64 - (D\'Agostino)',
        'index_title': 'Kodachrome 64 -',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Classic Chrome',
            'Grain Effect': 'Weak, Small',
            'Color Chrome Effect': 'Strong',
            'Color Chrome FX Blue': 'Weak',
            'White Balance': 'Auto, +2 Red & -4 Blue',
            'Dynamic Range': 'DR400',
            'Highlight': '+4',
            'Shadow': '-2',
            'Color': '+4',
            'Sharpness': '-1',
            'Noise Reduction': '-4',
            'Clarity': '+1',
            'Exposure Compensation': '-1/3 to -1 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-kodachrome64-plus',
        'title': 'Kodachrome 64 + (D\'Agostino)',
        'index_title': 'Kodachrome 64 +',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Classic Chrome',
            'Grain Effect': 'Weak, Small',
            'Color Chrome Effect': 'Strong',
            'Color Chrome FX Blue': 'Weak',
            'White Balance': 'Daylight, +2 Red & -5 Blue',
            'Dynamic Range': 'DR200',
            'Highlight': '0',
            'Shadow': '0',
            'Color': '+2',
            'Sharpness': '+1',
            'Noise Reduction': '-4',
            'Clarity': '+3',
            'Exposure Compensation': '+1/3 to +2/3 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-kodak-portra',
        'title': 'Kodak Portra (D\'Agostino)',
        'index_title': 'Kodak Portra',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Classic Chrome',
            'Grain Effect': 'Weak, Small',
            'Color Chrome Effect': 'Strong',
            'Color Chrome FX Blue': 'Weak',
            'White Balance': '5200K, +1 Red & -6 Blue',
            'Dynamic Range': 'DR400',
            'Highlight': '-2',
            'Shadow': '+2',
            'Color': '+2',
            'Sharpness': '-1',
            'Noise Reduction': '-4',
            'Clarity': '-2',
            'Exposure Compensation': '+1/3 to +1 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-summer',
        'title': 'Summer (D\'Agostino)',
        'index_title': 'Summer',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Classic Chrome',
            'Grain Effect': 'Off',
            'Color Chrome Effect': 'Strong',
            'Color Chrome FX Blue': 'Off',
            'White Balance': '7100K, -3 Red & -2 Blue',
            'Dynamic Range': 'DR400',
            'Highlight': '-2',
            'Shadow': '-2',
            'Color': '+4',
            'Sharpness': '0',
            'Noise Reduction': '-4',
            'Clarity': '-5',
            'Exposure Compensation': '+1 to +2 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-monochrome',
        'title': 'Monochrome (D\'Agostino)',
        'index_title': 'Monochrome',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Monochrome',
            'Grain Effect': 'Strong, Small',
            'Color Chrome Effect': 'Off',
            'Color Chrome FX Blue': 'Strong',
            'White Balance': 'Auto, 0 Red & 0 Blue',
            'Dynamic Range': 'DR100',
            'Highlight': '0',
            'Shadow': '+3',
            'Color': '0',
            'Sharpness': '+1',
            'Noise Reduction': '0',
            'Clarity': '+1',
            'Exposure Compensation': '0 to +2/3 (typically)',
        }
    },
    {
        'slug': 'ext-dagostino-noir',
        'title': 'Noir (D\'Agostino)',
        'index_title': 'Noir',
        'url': SOURCE_URL,
        'source': SOURCE_AUTHOR,
        'settings': {
            'Film Simulation': 'Acros',
            'Grain Effect': 'Strong, Large',
            'Color Chrome Effect': 'Off',
            'Color Chrome FX Blue': 'Off',
            'White Balance': 'Auto, 0 Red & 0 Blue',
            'Dynamic Range': 'DR100',
            'Highlight': '+4',
            'Shadow': '+4',
            'Color': '0',
            'Sharpness': '+4',
            'Noise Reduction': '-4',
            'Clarity': '+1',
            'Exposure Compensation': '0 (typically)',
        }
    },
]

# ── 1. add to recipes.json ────────────────────────────────────────────────────
recipes = json.load(open('recipes.json', encoding='utf-8'))
existing_slugs = {r['slug'] for r in recipes}

added = 0
for r in NEW_RECIPES:
    if r['slug'] in existing_slugs:
        print(f'skip (exists): {r["slug"]}')
        continue
    r['num_fields'] = len(r['settings'])
    r['raw_block'] = '\n'.join(f'{k}: {v}' for k, v in r['settings'].items())
    recipes.append(r)
    added += 1

json.dump(recipes, open('recipes.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'recipes.json: added {added} recipes, total {len(recipes)}')

# ── 2. add to recipe_urls.json ───────────────────────────────────────────────
urls = json.load(open('recipe_urls.json', encoding='utf-8'))
url_slugs = {u['url'].rstrip('/').split('/')[-1] for u in urls}
for r in NEW_RECIPES:
    if r['slug'] not in url_slugs:
        urls.append({'url': r['url'], 'title': r['index_title']})
json.dump(urls, open('recipe_urls.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

# ── 3. rebuild features.csv ──────────────────────────────────────────────────
import subprocess, sys
result = subprocess.run([sys.executable, 'encode.py'], capture_output=True, text=True)
if result.returncode != 0:
    print('encode.py error:', result.stderr[:300])
else:
    print('features.csv rebuilt')

# ── 4. assign new recipes to nearest subcluster ──────────────────────────────
df_feat = pd.read_csv('features.csv')
df_sub  = pd.read_csv('subclusters.csv')

NUMERIC = ['highlight','shadow','color','sharpness','noise_reduction',
           'clarity','dynamic_range','color_chrome','color_chrome_blue',
           'grain_strength','grain_size','wb_red','wb_blue','wb_kelvin']

all_slugs = df_sub['slug'].tolist()
new_slugs = [r['slug'] for r in NEW_RECIPES]

# fit space on existing recipes only
existing_feat = df_feat[df_feat['slug'].isin(all_slugs)]
Xe = SimpleImputer(strategy='median').fit_transform(existing_feat[NUMERIC].to_numpy(float))
imp = SimpleImputer(strategy='median').fit(existing_feat[NUMERIC].to_numpy(float))

fam = df_feat[df_feat['slug'].isin(all_slugs)]['film_sim'].fillna('Unknown')
fs  = pd.get_dummies(fam).reindex(columns=pd.get_dummies(
    df_feat['film_sim'].fillna('Unknown')).columns, fill_value=0).to_numpy(float)
fs_std = StandardScaler().fit(fs)

X_exist = np.hstack([StandardScaler().fit_transform(Xe), fs_std.transform(fs) * 2.0])
nn = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(X_exist)

new_rows = []
for slug in new_slugs:
    row = df_feat[df_feat['slug'] == slug]
    if row.empty:
        print(f'  not found in features: {slug}')
        continue
    title = row['title'].values[0]
    film_sim = row['film_sim'].values[0]

    xn = imp.transform(row[NUMERIC].to_numpy(float))
    fam_n = pd.get_dummies(pd.Series([film_sim])).reindex(
        columns=pd.get_dummies(df_feat['film_sim'].fillna('Unknown')).columns,
        fill_value=0).to_numpy(float)
    fam_n_std = fs_std.transform(fam_n) * 2.0
    xn_full = np.hstack([StandardScaler().fit_transform(Xe)[:1] * 0 +
                         StandardScaler().fit(Xe).transform(xn), fam_n_std])

    dist, idx = nn.kneighbors(xn_full)
    nearest_slug = existing_feat.iloc[idx[0][0]]['slug']
    subcluster = df_sub[df_sub['slug'] == nearest_slug]['subcluster_label'].values
    subcluster_label = subcluster[0] if len(subcluster) else film_sim
    subcluster_num   = df_sub[df_sub['slug'] == nearest_slug]['subcluster'].values
    subcluster_n     = int(subcluster_num[0]) if len(subcluster_num) else -1

    new_rows.append({
        'slug': slug, 'title': title, 'film_sim': film_sim,
        'subcluster': subcluster_n, 'subcluster_label': subcluster_label,
    })
    print(f'  {slug} → {subcluster_label} (nearest: {nearest_slug})')

df_sub_new = pd.concat([df_sub, pd.DataFrame(new_rows)], ignore_index=True)
df_sub_new.to_csv('subclusters.csv', index=False)
print(f'subclusters.csv: {len(df_sub)} → {len(df_sub_new)} rows')
