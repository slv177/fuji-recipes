"""Non-linear projection (UMAP, with t-SNE fallback) of recipe settings.

Adds the base Film Simulation as one-hot features (it is the dominant "character"
axis), standardizes everything, then projects to 2D and colors by film sim.
"""
import json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

df = pd.read_csv('features.csv')

NUMERIC = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
           'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
           'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']

# numeric block: impute (median) + standardize
Xnum = SimpleImputer(strategy='median').fit_transform(df[NUMERIC].to_numpy(float))
Xnum = StandardScaler().fit_transform(Xnum)

# film simulation one-hot (the main qualitative axis), weighted so it matters
fam = df['film_sim'].fillna('Unknown')
onehot = pd.get_dummies(fam).to_numpy(float)
FS_WEIGHT = 2.0
onehot = StandardScaler().fit_transform(onehot) * FS_WEIGHT

X = np.hstack([Xnum, onehot])

# ---- UMAP projection ----
import umap
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='euclidean',
                    random_state=42)
emb = reducer.fit_transform(X)
df['x'], df['y'] = emb[:, 0], emb[:, 1]
df[['slug', 'title', 'film_sim', 'x', 'y']].to_csv('coords_umap.csv', index=False)

# ---- plot ----
order = fam.value_counts().index.tolist()
cmap = plt.get_cmap('tab20')
colors = {name: cmap(i % 20) for i, name in enumerate(order)}

fig, ax = plt.subplots(figsize=(13, 9))
for name in order:
    sub = df[fam == name]
    ax.scatter(sub['x'], sub['y'], s=60, alpha=0.85, color=colors[name],
               label=f'{name} ({len(sub)})', edgecolors='white', linewidths=0.5)
ax.set_title('Fujifilm X-Trans IV recipes — UMAP of settings + film simulation')
ax.set_xlabel('UMAP-1'); ax.set_ylabel('UMAP-2')
ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8, frameon=False)
ax.grid(True, alpha=0.2)
fig.tight_layout()
fig.savefig('recipes_umap.png', dpi=130)
print('saved recipes_umap.png')
