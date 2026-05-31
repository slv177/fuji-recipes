"""Generate Russian descriptions for small film simulations (not sub-clustered)."""
import json, os
from dotenv import load_dotenv
load_dotenv()
import anthropic
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from bs4 import BeautifulSoup
import re

client = anthropic.Anthropic()

df_feat = pd.read_csv('features.csv')

STOP_RE = re.compile(
    r'(leave a reply|related posts|you might also|share this|find this film|'
    r'become a patron|fuji x weekly app|support fuji|patreon)', re.I)
SETTINGS_RE = re.compile(
    r'^(film simulation|dynamic range|grain|color chrome|white balance|'
    r'highlight|shadow|color:|sharpness|noise|clarity|iso|exposure comp)', re.I)

def extract_text(slug):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return ''
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    for tag in content.select('script,style,.sharedaddy,figcaption,.entry-footer,figure'):
        tag.decompose()
    blocks = []
    for el in content.find_all(['p', 'li']):
        txt = el.get_text(' ', strip=True)
        if len(txt) < 30: continue
        if STOP_RE.search(txt): break
        if SETTINGS_RE.match(txt): continue
        blocks.append(txt)
    return ' '.join(blocks)

SMALL_SIMS = ['Velvia', 'Monochrome', 'Provia', 'Astia']

existing = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
existing_labels = {g['label'] for g in existing}

new_groups = []
for sim in SMALL_SIMS:
    sub = df_feat[df_feat['film_sim'] == sim]
    if len(sub) == 0:
        continue
    titles = sub['title'].tolist()
    slugs = sub['slug'].tolist()
    texts = [t for s in slugs if (t := extract_text(s))]

    feat_cols = ['highlight','shadow','color','sharpness','clarity',
                 'dynamic_range','grain_strength','wb_red','wb_blue']
    setting_bits = []
    for c in feat_cols:
        v = sub[c].dropna()
        if len(v):
            setting_bits.append(f'{c}={v.mean():+.1f}')

    prompt = f"""Ты описываешь группу пресетов плёночной симуляции для камер Fujifilm.

Симуляция: {sim}
Количество рецептов: {len(sub)}
Названия рецептов: {', '.join(titles)}
Средние настройки: {', '.join(setting_bits)}

Напиши 2–3 предложения на русском языке, описывающие эту группу рецептов: их настроение, визуальный характер, для каких сюжетов и условий съёмки они подходят. Используй язык фотографа."""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )
    description = msg.content[0].text.strip()
    new_groups.append({
        'label': sim,
        'film_sim': sim,
        'n': len(sub),
        'titles': titles,
        'keywords': [],
        'description': description,
    })
    print(f'{sim} ({len(sub)}) -> done')

all_groups = existing + new_groups
json.dump(all_groups, open('group_descriptions_ru.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f'Total: {len(all_groups)} groups saved.')
