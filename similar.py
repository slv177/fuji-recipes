"""Similarity search over recipes.

Builds a feature vector per recipe = standardized numeric settings + weighted
film-simulation one-hot, then finds nearest neighbours by Euclidean distance.
Usable as a CLI (`python similar.py <query> [n]`) or imported (find_similar()).
"""
import sys, json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

NUMERIC = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
           'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
           'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']

# how much the base film simulation matters relative to one numeric setting
FS_WEIGHT = 2.0


def build_space(features_csv='features.csv'):
    df = pd.read_csv(features_csv)

    Xnum = SimpleImputer(strategy='median').fit_transform(df[NUMERIC].to_numpy(float))
    Xnum = StandardScaler().fit_transform(Xnum)

    fam = df['film_sim'].fillna('Unknown')
    fs = pd.get_dummies(fam)
    fs_cols = fs.columns.tolist()
    fs = StandardScaler().fit_transform(fs.to_numpy(float)) * FS_WEIGHT

    X = np.hstack([Xnum, fs])
    return df, X


def find_similar(query, n=8, df=None, X=None):
    """query: slug substring or title substring (case-insensitive)."""
    if df is None or X is None:
        df, X = build_space()

    q = query.lower()
    mask = (df['slug'].str.lower().str.contains(q) |
            df['title'].astype(str).str.lower().str.contains(q))
    if not mask.any():
        return None, []
    qi = df.index[mask][0]

    nn = NearestNeighbors(n_neighbors=n + 1, metric='euclidean').fit(X)
    dist, idx = nn.kneighbors(X[qi:qi + 1])
    results = []
    for d, i in zip(dist[0], idx[0]):
        if i == qi:
            continue
        results.append({
            'title': df.loc[i, 'title'],
            'film_sim': df.loc[i, 'film_sim'],
            'distance': round(float(d), 3),
            'slug': df.loc[i, 'slug'],
        })
    return df.loc[qi, 'title'], results[:n]


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'mccurry'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    qtitle, res = find_similar(query, n)
    out = {'query': query, 'matched': qtitle, 'results': res}
    json.dump(out, open('similar_result.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f'query={query!r} matched={qtitle!r} -> {len(res)} results')
