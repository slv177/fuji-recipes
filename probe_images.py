"""Probe image URLs in recipe HTML pages."""
from bs4 import BeautifulSoup
import re, os

def get_images(slug, max_imgs=10):
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    imgs = []
    for img in content.select('img'):
        src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
        if not src:
            continue
        # skip icons, logos, ads
        if re.search(r'(icon|logo|avatar|banner|button|pixel|gravatar|badge|paypal|patreon)',
                     src, re.I):
            continue
        # prefer large images
        if re.search(r'\.(jpg|jpeg|webp|png)', src, re.I):
            # get largest srcset if available
            srcset = img.get('srcset', '')
            if srcset:
                parts = [p.strip().split() for p in srcset.split(',') if p.strip()]
                # pick largest by width descriptor
                best = src
                best_w = 0
                for p in parts:
                    if len(p) >= 2 and p[1].endswith('w'):
                        w = int(p[1][:-1])
                        if w > best_w:
                            best_w = w
                            best = p[0]
                src = best
            imgs.append(src)
        if len(imgs) >= max_imgs:
            break
    return imgs

# test on a few recipes
import pandas as pd
df = pd.read_csv('subclusters.csv')

for slug in df['slug'].head(5):
    imgs = get_images(slug)
    title = df[df['slug']==slug]['title'].values[0]
    print(f'{title}: {len(imgs)} images')
    for url in imgs[:3]:
        print('  ', url[:100])
    print()
