"""Extract recipe URLs from the saved X-Trans IV index page."""
import re, json
from bs4 import BeautifulSoup

soup = BeautifulSoup(open('index.html', encoding='utf-8').read(), 'html.parser')

# Prefer links inside the article body if identifiable, else whole page.
container = (soup.select_one('.entry-content') or soup.select_one('article') or soup)

urls = []
seen = set()
for a in container.select('a[href]'):
    href = a['href'].split('#')[0].rstrip('/')
    if not re.search(r'https://fujixweekly\.com/20\d\d/\d\d/\d\d/[a-z0-9\-]+$', href):
        continue
    # keep recipe-like posts only
    if not re.search(r'(recipe|film-simulation|setting)', href):
        continue
    if href in seen:
        continue
    seen.add(href)
    urls.append({'url': href + '/', 'title': a.get_text(strip=True)})

json.dump(urls, open('recipe_urls.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'extracted {len(urls)} recipe urls')
