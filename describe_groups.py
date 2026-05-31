"""Generate a text description for each recipe sub-group using the Claude API.

For each group:
- collect all recipe texts
- find TF-IDF keywords to hint at distinctive themes
- ask Claude to write a 2-3 sentence description
"""
import json, os
from dotenv import load_dotenv
load_dotenv()
import anthropic
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

df = pd.read_csv('subclusters_with_text.csv')
df = df[df['subcluster_label'] != '']  # skip un-clustered

client = anthropic.Anthropic()


def top_keywords(group_texts, all_texts, n=12):
    """TF-IDF keywords distinctive to this group vs all others."""
    labels = ['group'] * len(group_texts) + ['other'] * len(all_texts)
    corpus = list(group_texts) + list(all_texts)
    vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2),
                          stop_words='english', min_df=1)
    try:
        X = vec.fit_transform(corpus)
    except ValueError:
        return []
    names = vec.get_feature_names_out()
    # mean TF-IDF score for group docs vs other docs
    gi = [i for i, l in enumerate(labels) if l == 'group']
    oi = [i for i, l in enumerate(labels) if l == 'other']
    g_mean = np.asarray(X[gi].mean(axis=0)).flatten()
    o_mean = np.asarray(X[oi].mean(axis=0)).flatten() if oi else np.zeros_like(g_mean)
    diff = g_mean - o_mean
    top_idx = diff.argsort()[::-1][:n]
    return [names[i] for i in top_idx if diff[i] > 0]


all_texts = df['text'].fillna('').tolist()
groups = df.groupby('subcluster_label')

results = []
for label, gdf in groups:
    film_sim = gdf['film_sim'].iloc[0]
    n = len(gdf)
    titles = gdf['title'].astype(str).tolist()
    group_texts = gdf['text'].fillna('').tolist()

    kws = top_keywords(
        [t for t in group_texts if t],
        [t for t in all_texts if t],
        n=12
    )

    # settings summary for the group
    feat_cols = ['highlight', 'shadow', 'color', 'sharpness', 'clarity',
                 'dynamic_range', 'grain_strength', 'wb_red', 'wb_blue']
    feat = pd.read_csv('features.csv')
    gfeat = feat[feat['slug'].isin(gdf['slug'])]
    setting_bits = []
    for c in feat_cols:
        v = gfeat[c].dropna()
        if len(v):
            setting_bits.append(f'{c}={v.mean():+.1f}')
    settings_str = ', '.join(setting_bits)

    prompt = f"""You are describing a group of Fujifilm film simulation recipes for photographers.

Group: {label}
Film simulation: {film_sim}
Number of recipes: {n}
Recipe names: {', '.join(titles[:10])}
Average settings: {settings_str}
Distinctive keywords from recipe descriptions: {', '.join(kws)}

Write 2–3 sentences describing what makes this group of recipes distinctive — their mood, look, typical use case, and what kind of photos they suit. Be specific and use photography language. Do not mention the group number or technical cluster names."""

    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=200,
        messages=[{'role': 'user', 'content': prompt}]
    )
    description = message.content[0].text.strip()

    results.append({
        'label': label,
        'film_sim': film_sim,
        'n': n,
        'titles': titles,
        'keywords': kws,
        'description': description,
    })
    print(f'{label} ({n}) -> done')

json.dump(results, open('group_descriptions.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f'\nSaved {len(results)} group descriptions.')
