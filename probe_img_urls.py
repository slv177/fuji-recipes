"""Probe image URL patterns to find the filter for real photos vs logos/banners."""
import os, re
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd

def all_images(slug):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    out = []
    for img in content.select('img'):
        src = img.get('src','') or img.get('data-src','') or img.get('data-lazy-src','')
        w = img.get('width','')
        h = img.get('height','')
        out.append({'src': src, 'w': w, 'h': h,
                    'alt': img.get('alt','')[:60]})
    return out

df = pd.read_csv('subclusters.csv')

# collect sample from 5 recipes
samples = []
for slug in df['slug'].head(5):
    imgs = all_images(slug)
    for im in imgs:
        samples.append(im)

print(f'total images in sample: {len(samples)}\n')

# show all unique URL patterns (domain + first path component)
patterns = Counter()
for im in samples:
    src = im['src']
    m = re.match(r'https?://([^/]+)/([^/]+)', src)
    if m:
        patterns[m.group(1) + '/' + m.group(2)] += 1

print('URL patterns:')
for p, n in patterns.most_common(20):
    print(f'  {n:3}  {p}')

print('\nSample URLs with dimensions:')
for im in samples[:40]:
    # extract resize param
    resize = re.search(r'resize=([^&"]+)', im['src'])
    w_param = re.search(r'[?&]w=(\d+)', im['src'])
    print(f"  w={im['w']:>5} h={im['h']:>5}  "
          f"resize={resize.group(1) if resize else '—':>15}  "
          f"w_param={w_param.group(1) if w_param else '—':>6}  "
          f"{im['src'][:80]}")
