"""Re-parse all recipes from the HTML cache (no network) with the fixed parser."""
import json, os
from recipe_parser import parse_recipe

urls = json.load(open('recipe_urls.json', encoding='utf-8'))
CACHE = 'html_cache'
OUTDIR = 'recipes'
os.makedirs(OUTDIR, exist_ok=True)

all_recipes = []
for item in urls:
    url = item['url']
    slug = url.rstrip('/').split('/')[-1]
    path = os.path.join(CACHE, slug + '.html')
    if not os.path.exists(path):
        continue
    rec = parse_recipe(open(path, encoding='utf-8').read())
    rec['url'] = url
    rec['slug'] = slug
    rec['index_title'] = item.get('title')
    json.dump(rec, open(os.path.join(OUTDIR, slug + '.json'), 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    all_recipes.append(rec)

json.dump(all_recipes, open('recipes.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)

# coverage report
from collections import Counter
cov = Counter()
for r in all_recipes:
    for k in r['settings']:
        cov[k] += 1
lines = [f'reparsed {len(all_recipes)} recipes', 'coverage per key:']
for k, c in cov.most_common():
    lines.append(f'  {k:24} {c:4}/{len(all_recipes)}')
open('coverage.txt', 'w', encoding='utf-8').write('\n'.join(lines))
