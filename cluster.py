"""Agglomerative (Ward) clustering of the recipes, in two variants:
   (A) settings only, (B) settings + film simulation one-hot.
Picks k by silhouette, draws dendrograms, colors the UMAP embedding by cluster,
and cross-tabs clusters against film simulation.
"""
import json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster

warnings.filterwarnings('ignore')

df = pd.read_csv('features.csv')

NUMERIC = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
           'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
           'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']

# numeric block: median-impute + standardize
Xnum = SimpleImputer(strategy='median').fit_transform(df[NUMERIC].to_numpy(float))
Xnum = StandardScaler().fit_transform(Xnum)

# film simulation one-hot, standardized and weighted
fam = df['film_sim'].fillna('Unknown')
fs = StandardScaler().fit_transform(pd.get_dummies(fam).to_numpy(float)) * 2.0

VARIANTS = {
    'settings_only': Xnum,
    'with_filmsim': np.hstack([Xnum, fs]),
}

report = []
for vname, X in VARIANTS.items():
    # ---- pick k by silhouette ----
    scores = {}
    for k in range(2, 13):
        labels = AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(X)
        scores[k] = silhouette_score(X, labels)
    best_k = max(scores, key=scores.get)
    labels = AgglomerativeClustering(n_clusters=best_k, linkage='ward').fit_predict(X)
    df[f'cluster_{vname}'] = labels

    report.append(f'=== {vname} ===')
    report.append('silhouette by k: ' +
                  ', '.join(f'{k}:{s:.3f}' for k, s in scores.items()))
    report.append(f'best k = {best_k} (silhouette {scores[best_k]:.3f})')

    # ---- cross-tab cluster vs film simulation ----
    ct = pd.crosstab(df[f'cluster_{vname}'], fam)
    report.append('cluster x film_sim:')
    report.append(ct.to_string())
    # dominant film sim per cluster
    report.append('dominant film sim per cluster:')
    for c in sorted(df[f'cluster_{vname}'].unique()):
        row = ct.loc[c]
        report.append(f'  cluster {c} (n={row.sum()}): '
                      f'{row.idxmax()} {row.max()}/{row.sum()}')
    report.append('')

    # ---- dendrogram ----
    Z = linkage(X, method='ward')
    fig, ax = plt.subplots(figsize=(15, 6))
    dendrogram(Z, ax=ax, color_threshold=Z[-(best_k - 1), 2],
               no_labels=True)
    ax.set_title(f'Ward dendrogram — {vname} (cut into {best_k} clusters)')
    ax.set_ylabel('distance')
    fig.tight_layout()
    fig.savefig(f'dendrogram_{vname}.png', dpi=120)
    plt.close(fig)

# ---- color the existing UMAP embedding by cluster (both variants) ----
try:
    coords = pd.read_csv('coords_umap.csv')
    df = df.merge(coords[['slug', 'x', 'y']], on='slug', how='left')
    have_umap = df['x'].notna().any()
except FileNotFoundError:
    have_umap = False

if have_umap:
    for vname in VARIANTS:
        fig, ax = plt.subplots(figsize=(12, 9))
        labels = df[f'cluster_{vname}']
        cmap = plt.get_cmap('tab10')
        for c in sorted(labels.unique()):
            sub = df[labels == c]
            ax.scatter(sub['x'], sub['y'], s=60, alpha=0.85,
                       color=cmap(c % 10), label=f'cluster {c} ({len(sub)})',
                       edgecolors='white', linewidths=0.5)
        ax.set_title(f'UMAP colored by Agglomerative clusters — {vname}')
        ax.set_xlabel('UMAP-1'); ax.set_ylabel('UMAP-2')
        ax.legend(loc='best', fontsize=8, frameon=False)
        ax.grid(True, alpha=0.2)
        fig.tight_layout()
        fig.savefig(f'clusters_umap_{vname}.png', dpi=130)
        plt.close(fig)

# ---- save labeled data ----
cols = ['slug', 'title', 'film_sim'] + [f'cluster_{v}' for v in VARIANTS]
df[cols].to_csv('clusters.csv', index=False)

open('cluster_report.txt', 'w', encoding='utf-8').write('\n'.join(report))
print('done, best_k per variant saved to cluster_report.txt')
