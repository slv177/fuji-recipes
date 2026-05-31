"""Regenerate group descriptions in Russian."""
import json, os
import anthropic
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

df_sub = pd.read_csv('subclusters_with_text.csv')
df_sub = df_sub[df_sub['subcluster_label'] != '']
df_feat = pd.read_csv('features.csv')

client = anthropic.Anthropic()

def top_keywords(group_texts, all_texts, n=12):
    corpus = list(group_texts) + list(all_texts)
    labels = ['g'] * len(group_texts) + ['o'] * len(all_texts)
    vec = TfidfVectorizer(max_features=2000, ngram_range=(1,2),
                          stop_words='english', min_df=1)
    try:
        X = vec.fit_transform(corpus)
    except ValueError:
        return []
    names = vec.get_feature_names_out()
    gi = [i for i,l in enumerate(labels) if l=='g']
    oi = [i for i,l in enumerate(labels) if l=='o']
    gm = np.asarray(X[gi].mean(axis=0)).flatten()
    om = np.asarray(X[oi].mean(axis=0)).flatten() if oi else np.zeros_like(gm)
    diff = gm - om
    top = diff.argsort()[::-1][:n]
    return [names[i] for i in top if diff[i] > 0]

all_texts = df_sub['text'].fillna('').tolist()
groups = df_sub.groupby('subcluster_label')

results = []
for label, gdf in groups:
    film_sim = gdf['film_sim'].iloc[0]
    n = len(gdf)
    titles = gdf['title'].astype(str).tolist()
    group_texts = gdf['text'].fillna('').tolist()
    kws = top_keywords([t for t in group_texts if t],
                       [t for t in all_texts if t], n=12)

    feat_cols = ['highlight','shadow','color','sharpness','clarity',
                 'dynamic_range','grain_strength','wb_red','wb_blue']
    gfeat = df_feat[df_feat['slug'].isin(gdf['slug'])]
    setting_bits = []
    for c in feat_cols:
        v = gfeat[c].dropna()
        if len(v):
            setting_bits.append(f'{c}={v.mean():+.1f}')

    prompt = f"""Ты описываешь группу пресетов плёночной симуляции для камер Fujifilm.

Группа: {label}
Симуляция: {film_sim}
Количество рецептов: {n}
Названия рецептов: {', '.join(titles[:10])}
Средние настройки: {', '.join(setting_bits)}
Ключевые слова из описаний: {', '.join(kws)}

Напиши 2–3 предложения на русском языке, описывающие эту группу рецептов: их настроение, визуальный характер, для каких сюжетов и условий съёмки они подходят. Используй язык фотографа. Не упоминай номер группы и технические названия кластеров."""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )
    description = msg.content[0].text.strip()
    results.append({
        'label': label,
        'film_sim': film_sim,
        'n': n,
        'titles': titles,
        'keywords': kws,
        'description': description,
    })
    print(f'{label} ({n}) -> done')

json.dump(results, open('group_descriptions_ru.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f'Saved {len(results)} descriptions.')
