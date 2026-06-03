"""Compare metrics on NUMERIC SETTINGS ONLY (no film-sim one-hot).

This reveals the true character of each metric, since no single dominant
feature flattens the differences. Cross-simulation neighbours become possible.
"""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# settings only — drop noise_reduction (almost constant -4) for cleaner signal
NUMERIC = ['highlight','shadow','color','sharpness','clarity',
           'dynamic_range','color_chrome','color_chrome_blue','grain_strength',
           'grain_size','wb_red','wb_blue','wb_kelvin']

df = pd.read_csv('features.csv')
X = SimpleImputer(strategy='median').fit_transform(df[NUMERIC].to_numpy(float))
X = StandardScaler().fit_transform(X)

titles = df['title'].tolist()
sims   = df['film_sim'].fillna('?').tolist()

def neighbours(qi, metric, n=6):
    nn = NearestNeighbors(n_neighbors=n+1, metric=metric).fit(X)
    d, idx = nn.kneighbors(X[qi:qi+1])
    return [(titles[i], sims[i], dd) for dd, i in zip(d[0], idx[0]) if i != qi][:n]

def show(query):
    qi = next(i for i,t in enumerate(titles) if query.lower() in t.lower())
    print(f'\n===== query: {titles[qi]}  ({sims[qi]}) =====')
    for metric in ['euclidean','manhattan','cosine']:
        print(f'\n-- {metric} --')
        for t, s, d in neighbours(qi, metric):
            print(f'   {d:6.3f}  [{s[:18]:18}] {t}')

for q in ['mccurry', 'rockwell', 'tri-x']:
    show(q)

# how often does each metric pull a DIFFERENT simulation into top-5?
def cross_sim_frac(metric, n=5):
    nn = NearestNeighbors(n_neighbors=n+1, metric=metric).fit(X)
    cross = 0
    for qi in range(len(df)):
        _, idx = nn.kneighbors(X[qi:qi+1])
        qs = sims[qi]
        cross += sum(1 for i in idx[0][1:n+1] if sims[i] != qs)
    return cross / (len(df) * n)

print('\n\n=== fraction of top-5 neighbours from a DIFFERENT simulation ===')
for metric in ['euclidean','manhattan','cosine']:
    print(f'{metric:11}: {cross_sim_frac(metric):.0%}')

# top-5 overlap between metrics
def topset(qi, metric, n=5):
    nn = NearestNeighbors(n_neighbors=n+1, metric=metric).fit(X)
    _, idx = nn.kneighbors(X[qi:qi+1])
    return set(idx[0][1:n+1])
em, ec, mc = [], [], []
for qi in range(len(df)):
    e, m, c = topset(qi,'euclidean'), topset(qi,'manhattan'), topset(qi,'cosine')
    em.append(len(e & m)/5); ec.append(len(e & c)/5); mc.append(len(m & c)/5)
print('\n=== avg top-5 overlap (settings only) ===')
print(f'Euclid ∩ Manhattan: {np.mean(em):.0%}')
print(f'Euclid ∩ Cosine:    {np.mean(ec):.0%}')
print(f'Manhat ∩ Cosine:    {np.mean(mc):.0%}')
