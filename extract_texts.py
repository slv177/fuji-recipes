"""Extract clean text description from each recipe's cached HTML."""
import os, json, re
from bs4 import BeautifulSoup

STOP_RE = re.compile(
    r'(leave a reply|related posts|you might also|share this|find this film|'
    r'become a patron|fuji x weekly app|support fuji|patreon)',
    re.I)

SETTINGS_RE = re.compile(
    r'^(film simulation|dynamic range|grain|color chrome|white balance|'
    r'highlight|shadow|color:|sharpness|noise|clarity|iso|exposure comp)',
    re.I)


def extract_text(slug):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return ''
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    for tag in content.select('script, style, .sharedaddy, figcaption, .entry-footer, figure'):
        tag.decompose()
    blocks = []
    for el in content.find_all(['p', 'li', 'h2', 'h3']):
        txt = el.get_text(' ', strip=True)
        if len(txt) < 30:
            continue
        if STOP_RE.search(txt):
            break
        if SETTINGS_RE.match(txt):
            continue
        blocks.append(txt)
    return ' '.join(blocks)


import pandas as pd
df = pd.read_csv('subclusters.csv')

texts = {}
for _, row in df.iterrows():
    t = extract_text(row['slug'])
    texts[row['slug']] = t

df['text'] = df['slug'].map(texts)
df['text_len'] = df['text'].str.len()

df.to_csv('subclusters_with_text.csv', index=False)

# quick coverage check
filled = (df['text_len'] > 100).sum()
print(f'recipes with text: {filled}/{len(df)}')
print(f'avg text length: {df["text_len"].mean():.0f} chars')
print('\nsample (McCurry):')
row = df[df['slug'].str.contains('mccurry')].iloc[0]
print(row['text'][:400])
