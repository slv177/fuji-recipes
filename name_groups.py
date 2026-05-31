"""Generate short evocative English names for each recipe sub-group.

Film names from recipe titles get TF-IDF weighting across groups:
a name that appears in many groups gets down-weighted so it doesn't dominate.
"""
import json, re
import math
import anthropic
import pandas as pd
from collections import Counter

client = anthropic.Anthropic()

desc   = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
visual = json.load(open('group_visual_analysis.json', encoding='utf-8'))
df     = pd.read_csv('features.csv')

# ── extract film/brand terms from recipe titles ───────────────────────────────
STOP = {'film','simulation','recipe','fujifilm','fuji','my','not','x100v',
        'x-t30','x-t3','x-e4','x-t4','x-pro3','x-trans','iv','a','the',
        'two','and','for','v2','v3','ii','iii','push','process','color',
        'colour','negative','positive','chrome','classic','pro','neg',
        'eterna','acros','velvia','provia','astia','monochrome','bleach',
        'bypass','style','inspired','using','create','ai','urban'}

def title_terms(titles):
    terms = []
    for t in titles:
        words = re.findall(r"[A-Za-z][A-Za-z0-9'\-]+", t)
        for w in words:
            w = w.lower().strip("'-")
            if len(w) >= 3 and w not in STOP:
                terms.append(w)
    return terms

# build per-group term lists
groups_terms = {}
for g in desc:
    groups_terms[g['label']] = title_terms(g['titles'])

# IDF: how many groups contain each term
all_labels = list(groups_terms.keys())
N = len(all_labels)
df_count = Counter()
for terms in groups_terms.values():
    for t in set(terms):
        df_count[t] += 1

def idf(term):
    return math.log((N + 1) / (df_count.get(term, 0) + 1))

def top_terms(label, n=6):
    tf = Counter(groups_terms[label])
    total = sum(tf.values()) or 1
    scored = {t: (c / total) * idf(t) for t, c in tf.items()}
    return sorted(scored, key=scored.get, reverse=True)[:n]

# ── generate names via Claude ─────────────────────────────────────────────────
results = []
for g in desc:
    label     = g['label']
    film_sim  = g['film_sim']
    titles    = g['titles']
    n_recipes = g['n']
    kw_terms  = top_terms(label)

    v = visual.get(label) or {}
    subjects  = ', '.join(v.get('subjects', [])[:6])
    moods     = ', '.join(v.get('moods',    [])[:5])
    vis_notes = v.get('visual_notes', '')[:300]

    # settings summary
    slugs = df[df['film_sim'] == film_sim]['slug'].tolist()  # rough
    feat_cols = ['highlight','shadow','color','sharpness','clarity','dynamic_range']
    sub = df[df['slug'].isin(slugs)]
    s_bits = [f'{c}={sub[c].dropna().mean():+.1f}' for c in feat_cols if sub[c].notna().any()]

    prompt = f"""You are naming a group of Fujifilm film simulation recipes for a photo reference guide.

Film simulation: {film_sim}
Number of recipes: {n_recipes}
Recipe titles: {', '.join(titles[:10])}

Key title terms (TF-IDF weighted — rarer across groups = higher weight):
{', '.join(kw_terms) if kw_terms else '—'}

Visual character: {vis_notes}
Subjects: {subjects}
Mood: {moods}
Avg settings: {', '.join(s_bits[:5])}

Give this group a SHORT English name (2–4 words max).
Rules:
- Captures the visual mood or dominant film reference
- If a strong film name dominates (e.g. "Kodachrome") use it, but only if it's distinctive to THIS group
- Otherwise lead with mood/character (e.g. "Warm Analog", "Cool Fade", "Cinematic Lift")
- No generic words like "style", "look", "recipe", "simulation"
- No numbers or group indices

Reply with ONLY the name, nothing else."""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=20,
        messages=[{'role': 'user', 'content': prompt}]
    )
    name = msg.content[0].text.strip().strip('"').strip("'")
    results.append({'label': label, 'film_sim': film_sim,
                    'n': n_recipes, 'name': name,
                    'top_terms': kw_terms})
    print(f'{label:35} → {name}')

json.dump(results, open('group_names.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f'\nSaved {len(results)} group names.')
