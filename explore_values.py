import json
from collections import Counter, defaultdict

recs = json.load(open('recipes.json', encoding='utf-8'))

SYN = {'High ISO NR': 'Noise Reduction', 'Grain': 'Grain Effect'}

vals = defaultdict(Counter)
for r in recs:
    for k, v in r['settings'].items():
        k = SYN.get(k, k)
        vals[k][v] += 1

for k in ['Film Simulation', 'Dynamic Range', 'Color Chrome Effect',
          'Color Chrome FX Blue', 'Grain Effect', 'White Balance',
          'Highlight', 'Shadow', 'Color', 'Sharpness',
          'Noise Reduction', 'Clarity', 'ISO', 'Exposure Compensation', 'Toning']:
    c = vals[k]
    print(f'\n=== {k}  ({sum(c.values())} values, {len(c)} distinct) ===')
    for v, n in c.most_common(15):
        print(f'   {n:3}  {v!r}')
