"""Refine group names: ban words that appear in too many names (overused across groups)."""
import json, re
import math
import anthropic
from collections import Counter

client = anthropic.Anthropic()

desc   = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
visual = json.load(open('group_visual_analysis.json', encoding='utf-8'))
names  = json.load(open('group_names.json', encoding='utf-8'))

import pandas as pd
df = pd.read_csv('features.csv')

# ── find overused words across all current names ──────────────────────────────
def name_words(name):
    return [w.lower() for w in re.findall(r'[A-Za-z]+', name) if len(w) > 2]

word_freq = Counter()
for g in names:
    for w in name_words(g['name']):
        word_freq[w] += 1

OVERUSED_THRESHOLD = 2   # appears in more than 2 names → banned
overused = {w for w, c in word_freq.items() if c > OVERUSED_THRESHOLD}
print('Overused words:', sorted(overused))

# find which groups need a new name
needs_regen = [g for g in names if any(w in overused for w in name_words(g['name']))]
print(f'Groups to regenerate: {len(needs_regen)}')
for g in needs_regen:
    print(f'  {g["label"]:35} current: {g["name"]}')

# ── TF-IDF for title terms (same as before) ───────────────────────────────────
desc_by_label = {g['label']: g for g in desc}

STOP_TITLES = {'film','simulation','recipe','fujifilm','fuji','my','not','x100v',
               'x-t30','x-t3','x-e4','x-t4','x-pro3','x-trans','iv','a','the',
               'two','and','for','v2','v3','ii','iii','push','process','color',
               'colour','negative','positive','chrome','classic','pro','neg',
               'eterna','acros','velvia','provia','astia','monochrome','bleach',
               'bypass','style','inspired','using','create','ai','urban'}

def title_terms(titles):
    terms = []
    for t in titles:
        for w in re.findall(r"[A-Za-z][A-Za-z0-9'\-]+", t):
            w = w.lower().strip("'-")
            if len(w) >= 3 and w not in STOP_TITLES:
                terms.append(w)
    return terms

groups_terms = {g['label']: title_terms(g['titles']) for g in desc}
N = len(groups_terms)
df_count = Counter()
for terms in groups_terms.values():
    for t in set(terms):
        df_count[t] += 1

def idf(t): return math.log((N+1) / (df_count.get(t, 0)+1))

def top_terms(label, n=6):
    tf = Counter(groups_terms[label])
    total = sum(tf.values()) or 1
    scored = {t: (c/total)*idf(t) for t, c in tf.items()}
    return sorted(scored, key=scored.get, reverse=True)[:n]

# ── regenerate ────────────────────────────────────────────────────────────────
name_by_label = {g['label']: g['name'] for g in names}

for g in needs_regen:
    label    = g['label']
    gd       = desc_by_label[label]
    kw_terms = top_terms(label)
    v        = visual.get(label) or {}
    subjects = ', '.join(v.get('subjects', [])[:6])
    moods    = ', '.join(v.get('moods',    [])[:5])
    vis_notes= v.get('visual_notes','')[:300]
    sub      = df[df['film_sim'] == gd['film_sim']]
    s_bits   = [f'{c}={sub[c].dropna().mean():+.1f}'
                for c in ['highlight','shadow','color','sharpness','clarity']
                if sub[c].notna().any()]

    # collect all OTHER current names to avoid similarity
    other_names = [v for k, v in name_by_label.items() if k != label]

    prompt = f"""You are naming a group of Fujifilm film simulation recipes.

Film simulation: {gd['film_sim']}
Recipe titles: {', '.join(gd['titles'][:10])}
Key title terms (TF-IDF, higher = more distinctive to this group):
{', '.join(kw_terms) if kw_terms else '—'}
Visual character: {vis_notes}
Subjects: {subjects}
Mood: {moods}
Avg settings: {', '.join(s_bits[:5])}

Other groups already have these names (avoid duplication):
{', '.join(other_names)}

BANNED WORDS (appear in too many group names — do not use):
{', '.join(sorted(overused))}

Give this group a SHORT English name (2–4 words).
Rules:
- Must NOT contain any banned word
- Must be different from all other group names listed above
- Use the most distinctive film reference if it dominates this group
- Otherwise describe the visual character precisely
- No generic filler: no "style", "look", "recipe", "simulation", "film"

Reply with ONLY the name."""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=20,
        messages=[{'role': 'user', 'content': prompt}]
    )
    new_name = msg.content[0].text.strip().strip('"').strip("'")
    print(f'  {label:35} {g["name"]:30} → {new_name}')
    name_by_label[label] = new_name

# ── check if any overused words remain, iterate if needed ────────────────────
final = [{'label': g['label'], 'film_sim': g['film_sim'],
          'n': g['n'], 'name': name_by_label[g['label']]} for g in names]

word_freq2 = Counter()
for g in final:
    for w in name_words(g['name']):
        word_freq2[w] += 1
still_overused = {w for w, c in word_freq2.items() if c > OVERUSED_THRESHOLD}
if still_overused:
    print(f'\nStill overused after pass 2: {sorted(still_overused)}')
else:
    print('\nAll names are now distinct.')

print('\nFinal names:')
for g in final:
    print(f'  {g["label"]:35} {g["name"]}')

json.dump(final, open('group_names.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
