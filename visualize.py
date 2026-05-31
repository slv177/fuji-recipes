"""First-pass visualization: PCA of recipe settings, colored by film simulation."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

df = pd.read_csv('features.csv')

FEATURES = ['highlight', 'shadow', 'color', 'sharpness', 'noise_reduction',
            'clarity', 'dynamic_range', 'color_chrome', 'color_chrome_blue',
            'grain_strength', 'grain_size', 'wb_red', 'wb_blue', 'wb_kelvin']

X = df[FEATURES].to_numpy(dtype=float)
X = SimpleImputer(strategy='median').fit_transform(X)
Xs = StandardScaler().fit_transform(X)

pca = PCA(n_components=2, random_state=0)
coords = pca.fit_transform(Xs)
df['pc1'], df['pc2'] = coords[:, 0], coords[:, 1]

# save 2D coordinates for downstream use
df[['slug', 'title', 'film_sim', 'pc1', 'pc2']].to_csv('coords_pca.csv', index=False)

# plot, colored by film simulation (top families get distinct colors)
fams = df['film_sim'].fillna('Unknown')
top = fams.value_counts().index.tolist()
cmap = plt.get_cmap('tab20')
color_map = {name: cmap(i % 20) for i, name in enumerate(top)}

fig, ax = plt.subplots(figsize=(13, 9))
for name in top:
    sub = df[fams == name]
    ax.scatter(sub['pc1'], sub['pc2'], s=55, alpha=0.8,
               color=color_map[name], label=f'{name} ({len(sub)})',
               edgecolors='white', linewidths=0.5)

var = pca.explained_variance_ratio_ * 100
ax.set_xlabel(f'PC1 ({var[0]:.0f}% variance)')
ax.set_ylabel(f'PC2 ({var[1]:.0f}% variance)')
ax.set_title('Fujifilm X-Trans IV recipes — PCA of settings (colored by film simulation)')
ax.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8, frameon=False)
ax.grid(True, alpha=0.2)
fig.tight_layout()
fig.savefig('recipes_pca.png', dpi=130)

# component loadings (what each PC axis means)
load = pd.DataFrame(pca.components_.T, index=FEATURES, columns=['PC1', 'PC2'])
rep = [f'explained variance: PC1={var[0]:.1f}%  PC2={var[1]:.1f}%  (sum {var.sum():.1f}%)',
       '', 'loadings (feature contribution to each axis):',
       load.round(2).to_string()]
open('pca_report.txt', 'w', encoding='utf-8').write('\n'.join(rep))
print('saved recipes_pca.png')
