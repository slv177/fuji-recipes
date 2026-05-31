"""Visual analysis of recipe group photos using Claude vision API.

For each group:
- collect candidate photo URLs (width >= 400px in img tag)
- send up to 20 to Claude vision
- get: subjects/moods analysis + list of 20 most representative indices
- save to group_visual_analysis.json
"""
import os, re, json
import anthropic
import pandas as pd
from bs4 import BeautifulSoup

client = anthropic.Anthropic()

def good_images(slug, max_imgs=30):
    """Return URLs of real photos (width >= 400) from a recipe page."""
    path = os.path.join('html_cache', slug + '.html')
    if not os.path.exists(path):
        return []
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
    content = soup.select_one('.entry-content') or soup
    out = []
    for img in content.select('img'):
        src = (img.get('src','') or img.get('data-src','') or
               img.get('data-lazy-src',''))
        if not src or not re.search(r'\.(jpg|jpeg|webp|png)', src, re.I):
            continue
        # use img width attribute as proxy for photo vs icon
        w = img.get('width', '0')
        try:
            w_int = int(str(w).split('.')[0])
        except ValueError:
            w_int = 0
        if w_int < 400:
            continue
        # also skip known non-photo patterns
        if re.search(r'(icon|logo|avatar|banner|button|pixel|gravatar|badge|paypal|patreon)',
                     src, re.I):
            continue
        out.append(src)
        if len(out) >= max_imgs:
            break
    return out


def collect_group_photos(slugs, target=20):
    """Collect up to target photos spread across slugs."""
    per = max(4, -(-target // max(len(slugs), 1)))
    photos = []
    for slug in slugs:
        photos.extend(good_images(slug, max_imgs=per))
        if len(photos) >= target:
            break
    return photos[:target]


def analyze_group(label, film_sim, slugs, titles):
    photos = collect_group_photos(slugs, target=20)
    if not photos:
        return None

    # build image content blocks for Claude
    image_blocks = []
    for i, url in enumerate(photos):
        image_blocks.append({
            "type": "text",
            "text": f"Фото {i+1}:"
        })
        image_blocks.append({
            "type": "image",
            "source": {"type": "url", "url": url}
        })

    image_blocks.append({
        "type": "text",
        "text": f"""Это примеры съёмки, сделанные с рецептом плёночной симуляции Fujifilm ({film_sim}).
Группа называется «{label}» и включает рецепты: {', '.join(titles[:8])}.

Проанализируй эти фотографии и ответь строго в формате JSON:
{{
  "subjects": ["сюжет1", "сюжет2", ...],
  "moods": ["настроение1", "настроение2", ...],
  "visual_notes": "2-3 предложения о визуальном характере этих фото — цвет, свет, тональность, типичные сцены",
  "best_indices": [список номеров (1-based) 20 наиболее характерных фото, без дублирующихся или нерезких]
}}

subjects — конкретные сюжеты (улица, портрет, природа, архитектура и т.д.)
moods — настроение и атмосфера (тёплое, меланхоличное, энергичное и т.д.)
visual_notes — на русском языке
best_indices — ровно столько, сколько фото есть (не больше {len(photos)})"""
    })

    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": image_blocks}]
    )
    raw = msg.content[0].text.strip()
    # extract JSON
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        return {"raw": raw, "photos": photos}
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError:
        return {"raw": raw, "photos": photos}

    # map best_indices back to URLs
    best = []
    for idx in data.get("best_indices", list(range(1, len(photos)+1))):
        if 1 <= idx <= len(photos):
            best.append(photos[idx - 1])
    if not best:
        best = photos

    return {
        "subjects": data.get("subjects", []),
        "moods": data.get("moods", []),
        "visual_notes": data.get("visual_notes", ""),
        "best_photos": best[:20],
        "all_photos": photos,
    }


# ── main ──────────────────────────────────────────────────────────────────────
df_sub  = pd.read_csv('subclusters.csv')
df_feat = pd.read_csv('features.csv')
desc    = json.load(open('group_descriptions_ru.json', encoding='utf-8'))

# build label -> slugs mapping (include small sims)
label_slugs = {}
for label, gdf in df_sub.groupby('subcluster_label'):
    label_slugs[label] = gdf['slug'].tolist()
# add small sims (no subcluster)
for sim in ['Velvia','Monochrome','Provia','Astia']:
    slugs = df_feat[df_feat['film_sim']==sim]['slug'].tolist()
    if slugs:
        label_slugs[sim] = slugs

results = {}
for g in desc:
    label = g['label']
    slugs = label_slugs.get(label, [])
    if not slugs:
        continue
    print(f'analyzing {label} ({len(slugs)} recipes)...', end=' ', flush=True)
    try:
        r = analyze_group(label, g['film_sim'], slugs, g['titles'])
        results[label] = r
        print('ok')
    except Exception as e:
        print(f'ERROR: {e}')
        results[label] = None

json.dump(results, open('group_visual_analysis.json', 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
print(f'\nDone. {sum(v is not None for v in results.values())}/{len(results)} groups analyzed.')
