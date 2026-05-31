"""Final naming pass: force distinctiveness by showing sibling groups explicitly."""
import json, re, math
import anthropic
from collections import Counter

client = anthropic.Anthropic()

desc   = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
visual = json.load(open('group_visual_analysis.json', encoding='utf-8'))
names  = json.load(open('group_names.json', encoding='utf-8'))

import pandas as pd
df_feat = pd.read_csv('features.csv')

desc_by_label = {g['label']: g for g in desc}

# ── title term TF-IDF ─────────────────────────────────────────────────────────
STOP_T = {'film','simulation','recipe','fujifilm','fuji','my','not','x100v',
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
            if len(w) >= 3 and w not in STOP_T:
                terms.append(w)
    return terms

groups_terms = {g['label']: title_terms(g['titles']) for g in desc}
N = len(groups_terms)
df_count = Counter()
for terms in groups_terms.values():
    for t in set(terms):
        df_count[t] += 1

def idf(t): return math.log((N+1)/(df_count.get(t,0)+1))

def top_terms(label, n=5):
    tf = Counter(groups_terms[label])
    total = sum(tf.values()) or 1
    scored = {t:(c/total)*idf(t) for t,c in tf.items()}
    return sorted(scored, key=scored.get, reverse=True)[:n]

# ── compute global overused words from current names ─────────────────────────
def name_words(name):
    return [w.lower() for w in re.findall(r'[A-Za-z]+', name) if len(w) > 2]

word_freq = Counter()
for g in names:
    for w in name_words(g['name']):
        word_freq[w] += 1

BANNED = {w for w, c in word_freq.items() if c > 2}
print('Banned words:', sorted(BANNED))

# ── group by film sim to show siblings ───────────────────────────────────────
from collections import defaultdict
by_sim = defaultdict(list)
name_by_label = {g['label']: g['name'] for g in names}
for g in names:
    by_sim[g['film_sim']].append(g['label'])

needs = [g for g in names if any(w in BANNED for w in name_words(g['name']))]
print(f'Regenerating {len(needs)} names\n')

for g in needs:
    label    = g['label']
    film_sim = g['film_sim']
    gd       = desc_by_label[label]
    kw       = top_terms(label)
    v        = visual.get(label) or {}
    vis      = v.get('visual_notes','')[:250]
    subjects = ', '.join(v.get('subjects',[])[:5])
    moods    = ', '.join(v.get('moods',[])[:4])

    # sibling groups in same film sim with their current names
    siblings = [(lb, name_by_label[lb]) for lb in by_sim[film_sim] if lb != label]
    sib_str  = '\n'.join(f'  - {lb}: "{nm}"' for lb, nm in siblings) or '  (none)'

    # avg settings for this group specifically
    slugs = df_feat[df_feat['slug'].isin(
        pd.read_csv('subclusters.csv').query('subcluster_label == @label')['slug']
    )]['slug'] if label in pd.read_csv('subclusters.csv')['subcluster_label'].values else []

    prompt = f"""You are naming one group in a Fujifilm recipe guide.

Film simulation: {film_sim}
Recipe titles in THIS group: {', '.join(gd['titles'][:8])}
Distinctive title terms (TF-IDF): {', '.join(kw) if kw else '—'}
Visual: {vis}
Subjects: {subjects}   Mood: {moods}

OTHER groups of the same simulation already named:
{sib_str}

ALL other group names in the guide (no repeats allowed):
{', '.join(v for k,v in name_by_label.items() if k != label)}

BANNED WORDS (used too often — absolutely forbidden):
{', '.join(sorted(BANNED))}

Task: give THIS group a unique 2–4 word English name that:
1. Contains NONE of the banned words
2. Is different from every other name listed
3. Picks the most specific distinguishing feature of this group vs its siblings
4. Uses a concrete noun or reference rather than a generic adjective when possible
5. No "style", "look", "recipe", "film", "simulation"

Reply with ONLY the name."""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=20,
        messages=[{'role':'user','content':prompt}]
    )
    new_name = msg.content[0].text.strip().strip('"\'')
    print(f'  {label:35} "{g["name"]:30}" → "{new_name}"')
    name_by_label[label] = new_name

# final check
final = [{'label':g['label'],'film_sim':g['film_sim'],
          'n':g['n'],'name':name_by_label[g['label']]} for g in names]

wf = Counter()
for g in final:
    for w in name_words(g['name']): wf[w] += 1
still = {w for w,c in wf.items() if c > 2}
print(f'\nStill overused: {sorted(still) or "none"}')
print('\nFinal names:')
for g in final:
    print(f'  {g["label"]:35} {g["name"]}')

json.dump(final, open('group_names.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
