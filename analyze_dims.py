import json, re
from collections import Counter, defaultdict

recs = json.load(open('recipes.json', encoding='utf-8'))

key_counts = Counter()
val_examples = defaultdict(set)
for r in recs:
    for k, v in r['settings'].items():
        key_counts[k] += 1
        if len(val_examples[k]) < 6:
            val_examples[k].add(v)

print(f'recipes: {len(recs)}')
print(f'distinct setting keys: {len(key_counts)}\n')
print('key, present_in_N_recipes, sample_values')
for k, c in key_counts.most_common():
    samples = list(val_examples[k])[:4]
    print(f'  {k:24} {c:4}/{len(recs)}   e.g. {samples}')
