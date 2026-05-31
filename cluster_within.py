"""Find hidden sub-groups WITHIN each large film simulation.

For every film simulation with enough recipes, cluster on the numeric settings
only (film sim is constant inside the group, so it carries no info here). Pick k
by silhouette, then describe each sub-cluster by the settings that make it stand
out from the rest of that simulation.
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

warnings.filterwarnings('ignore')

df = pd.read_csv('features.csv')

NUMERIC = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
           'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
           'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']

MIN_SIZE = 10           # only sims with at least this many recipes
report = []
df['subcluster'] = -1   # global label: "<film_sim>#<k>"
df['subcluster_label'] = ''

# coords for plotting (reuse UMAP if present)
try:
    coords = pd.read_csv('coords_umap.csv')[['slug', 'x', 'y']]
    df = df.merge(coords, on='slug', how='left')
    have_umap = df['x'].notna().any()
except FileNotFoundError:
    have_umap = False

sizes = df['film_sim'].value_counts()
big_sims = [s for s in sizes.index if sizes[s] >= MIN_SIZE and s != 'Unknown']

# global medians, to describe sub-clusters relative to the whole dataset
global_med = df[NUMERIC].median()

for sim in big_sims:
    sub = df[df['film_sim'] == sim].copy()
    idx = sub.index

    # impute within this sim, standardize
    imp = SimpleImputer(strategy='median')
    Xraw = imp.fit_transform(sub[NUMERIC].to_numpy(float))
    X = StandardScaler().fit_transform(Xraw)

    # choose k by silhouette (2..min(6, n-1))
    n = len(sub)
    best_k, best_s, best_labels = 1, -1, np.zeros(n, dtype=int)
    for k in range(2, min(6, n - 1) + 1):
        labels = AgglomerativeClustering(n_clusters=k, linkage='ward').fit_predict(X)
        s = silhouette_score(X, labels)
        if s > best_s:
            best_k, best_s, best_labels = k, s, labels

    df.loc[idx, 'subcluster'] = best_labels
    df.loc[idx, 'subcluster_label'] = [f'{sim}#{c}' for c in best_labels]

    report.append(f'\n========== {sim}  (n={n}) ==========')
    report.append(f'best k = {best_k} (silhouette {best_s:.3f})')

    # describe each sub-cluster: mean of each setting, and which deviate most
    Xback = pd.DataFrame(Xraw, columns=NUMERIC, index=idx)
    for c in range(best_k):
        members = idx[best_labels == c]
        report.append(f'\n  -- {sim}#{c}  (n={len(members)})')
        means = Xback.loc[members].mean()
        # rank settings by absolute deviation from the global median
        dev = (means - global_med)
        ranked = dev.reindex(dev.abs().sort_values(ascending=False).index)
        top = ranked.head(5)
        desc = ', '.join(f'{name} {means[name]:+.1f}' for name in top.index)
        report.append(f'     defining settings: {desc}')
        # show a couple example recipe titles
        ex = df.loc[members, 'title'].head(3).tolist()
        report.append(f'     e.g.: {ex}')

# ---- plot: per-sim small multiples on the UMAP, colored by subcluster ----
if have_umap:
    ncol = 3
    nrow = int(np.ceil(len(big_sims) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(16, 5 * nrow))
    axes = np.array(axes).reshape(-1)
    for ax, sim in zip(axes, big_sims):
        sub = df[df['film_sim'] == sim]
        # faint background of everything
        ax.scatter(df['x'], df['y'], s=12, color='#dddddd', zorder=1)
        cmap = plt.get_cmap('tab10')
        for c in sorted(sub['subcluster'].unique()):
            m = sub[sub['subcluster'] == c]
            ax.scatter(m['x'], m['y'], s=55, color=cmap(c % 10), zorder=3,
                       edgecolors='white', linewidths=0.5,
                       label=f'#{c} ({len(m)})')
        ax.set_title(f'{sim} (n={len(sub)})')
        ax.legend(fontsize=7, frameon=False)
        ax.set_xticks([]); ax.set_yticks([])
    for ax in axes[len(big_sims):]:
        ax.axis('off')
    fig.suptitle('Hidden sub-clusters within each film simulation (numeric settings)',
                 fontsize=14)
    fig.tight_layout()
    fig.savefig('subclusters_umap.png', dpi=120)
    plt.close(fig)

# save labeled data
out_cols = ['slug', 'title', 'film_sim', 'subcluster', 'subcluster_label']
df[out_cols].to_csv('subclusters.csv', index=False)
open('subcluster_report.txt', 'w', encoding='utf-8').write('\n'.join(report))
print('done; sims processed:', big_sims)
