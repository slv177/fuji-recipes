"""Compact, clean summary of within-simulation sub-clusters."""
import warnings
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

warnings.filterwarnings('ignore')
df = pd.read_csv('features.csv')

NUMERIC = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
           'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
           'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']
# settings we describe in plain language (skip noise_reduction: almost always -4)
SHOW = ['highlight', 'shadow', 'color', 'sharpness', 'clarity',
        'dynamic_range', 'grain_strength', 'grain_size', 'wb_red', 'wb_blue']

sizes = df['film_sim'].value_counts()
big = [s for s in sizes.index if sizes[s] >= 10 and s != 'Unknown']

out = []
for sim in big:
    sub = df[df['film_sim'] == sim].copy()
    n = len(sub)
    X = StandardScaler().fit_transform(
        SimpleImputer(strategy='median').fit_transform(sub[NUMERIC].to_numpy(float)))
    best = (1, -1, None)
    for k in range(2, min(5, n - 1) + 1):
        lab = AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(X)
        s = silhouette_score(X, lab)
        if s > best[1]:
            best = (k, s, lab)
    k, sil, lab = best
    sub['c'] = lab
    out.append(f'### {sim}  (n={n})  ->  {k} sub-groups (silhouette {sil:.2f})')
    raw = sub[NUMERIC]
    simmean = raw.mean()
    for c in range(k):
        mem = sub[sub['c'] == c]
        m = mem[NUMERIC].mean()
        dev = (m - simmean)
        ranked = dev.reindex([x for x in dev.abs().sort_values(ascending=False).index
                              if x in SHOW]).head(4)
        bits = []
        for name in ranked.index:
            arrow = 'high' if dev[name] > 0 else 'low'
            bits.append(f'{name}={m[name]:+.1f}({arrow})')
        titles = ', '.join(mem['title'].head(3).astype(str).tolist())
        out.append(f'  group {c} (n={len(mem)}): ' + '; '.join(bits))
        out.append(f'      e.g.: {titles}')
    out.append('')

open('SUBCLUSTERS.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'lines')
