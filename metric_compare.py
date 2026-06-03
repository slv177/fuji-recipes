"""Compare Euclidean vs Manhattan vs Cosine nearest neighbours on our feature space."""
import json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

NUMERIC = ['highlight','shadow','color','sharpness','noise_reduction','clarity',
           'dynamic_range','color_chrome','color_chrome_blue','grain_strength',
           'grain_size','wb_red','wb_blue','wb_kelvin']
FS_WEIGHT = 2.0

df = pd.read_csv('features.csv')
Xnum = SimpleImputer(strategy='median').fit_transform(df[NUMERIC].to_numpy(float))
Xnum = StandardScaler().fit_transform(Xnum)
fs = StandardScaler().fit_transform(pd.get_dummies(df['film_sim'].fillna('Unknown')).to_numpy(float)) * FS_WEIGHT
X = np.hstack([Xnum, fs])

titles = df['title'].tolist()
sims   = df['film_sim'].fillna('?').tolist()

def neighbours(qi, metric, n=6):
    nn = NearestNeighbors(n_neighbors=n+1, metric=metric).fit(X)
    d, idx = nn.kneighbors(X[qi:qi+1])
    return [(titles[i], sims[i], d) for d, i in zip(d[0], idx[0]) if i != qi][:n]

def show(query):
    qi = next(i for i,t in enumerate(titles) if query.lower() in t.lower())
    print(f'\n===== query: {titles[qi]}  ({sims[qi]}) =====')
    for metric in ['euclidean','manhattan','cosine']:
        print(f'\n-- {metric} --')
        for t, s, d in neighbours(qi, metric):
            print(f'   {d:6.3f}  [{s[:16]:16}] {t}')

for q in ['mccurry', 'rockwell', 'tri-x']:
    show(q)

# overlap statistic: how often do the three metrics agree on the top-5 set?
def topset(qi, metric, n=5):
    nn = NearestNeighbors(n_neighbors=n+1, metric=metric).fit(X)
    _, idx = nn.kneighbors(X[qi:qi+1])
    return set(idx[0][1:n+1])

agree_em, agree_ec, agree_mc = [], [], []
for qi in range(len(df)):
    e, m, c = topset(qi,'euclidean'), topset(qi,'manhattan'), topset(qi,'cosine')
    agree_em.append(len(e & m)/5)
    agree_ec.append(len(e & c)/5)
    agree_mc.append(len(m & c)/5)
print('\n\n=== avg top-5 overlap across all 191 recipes ===')
print(f'Euclid ∩ Manhattan: {np.mean(agree_em):.0%}')
print(f'Euclid ∩ Cosine:    {np.mean(agree_ec):.0%}')
print(f'Manhat ∩ Cosine:    {np.mean(agree_mc):.0%}')
