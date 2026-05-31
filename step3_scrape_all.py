"""Fetch every recipe URL, parse the settings block, save JSON output."""
import json, os, re, time, traceback
import requests
from recipe_parser import parse_recipe

H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
OUTDIR = 'recipes'
CACHE = 'html_cache'
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

urls = json.load(open('recipe_urls.json', encoding='utf-8'))


def slug_of(url):
    return url.rstrip('/').split('/')[-1]


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code == 200:
                return r.text
            last = f'HTTP {r.status_code}'
        except Exception as e:
            last = str(e)
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(last)


all_recipes = []
failures = []
for i, item in enumerate(urls, 1):
    url = item['url']
    slug = slug_of(url)
    cache_path = os.path.join(CACHE, slug + '.html')
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            html = open(cache_path, encoding='utf-8').read()
        else:
            html = fetch(url)
            open(cache_path, 'w', encoding='utf-8').write(html)
            time.sleep(0.4)
        rec = parse_recipe(html)
        rec['url'] = url
        rec['slug'] = slug
        rec['index_title'] = item.get('title')
        json.dump(rec, open(os.path.join(OUTDIR, slug + '.json'), 'w', encoding='utf-8'),
                  indent=2, ensure_ascii=False)
        all_recipes.append(rec)
    except Exception:
        failures.append({'url': url, 'error': traceback.format_exc().splitlines()[-1]})
    # checkpoint every 25
    if i % 25 == 0:
        json.dump(all_recipes, open('recipes.json', 'w', encoding='utf-8'),
                  indent=2, ensure_ascii=False)

json.dump(all_recipes, open('recipes.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)

# summary
hist = {}
for r in all_recipes:
    hist[r['num_fields']] = hist.get(r['num_fields'], 0) + 1
summary = {
    'total_urls': len(urls),
    'parsed': len(all_recipes),
    'failed': len(failures),
    'low_field_recipes': [r['slug'] for r in all_recipes if r['num_fields'] < 5],
    'field_count_histogram': dict(sorted(hist.items())),
    'failures': failures,
}
json.dump(summary, open('scrape_summary.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print('DONE parsed', len(all_recipes), 'failed', len(failures))
