"""Translate content JSON files to a target language via Claude.

Usage: python translate_content.py <lang>

Translates VALUES only, preserving all JSON keys (keys are the schema).
Film/recipe proper names, setting names (Highlight, DR400, etc.), and the
table keys stay unchanged. Source language is Russian (the original content).

Outputs: group_descriptions_<lang>.json, film_sim_info_<lang>.json,
         group_visual_analysis_<lang>.json
"""
import json, sys, os
from dotenv import load_dotenv
load_dotenv()
import anthropic

client = anthropic.Anthropic()

LANG_FULL = {'en': 'English', 'de': 'German', 'es': 'Spanish', 'fr': 'French'}

if len(sys.argv) < 2 or sys.argv[1] not in LANG_FULL:
    print('usage: python translate_content.py <en|de|es|fr>')
    sys.exit(1)
lang = sys.argv[1]
target = LANG_FULL[lang]


def translate_texts(texts):
    """Translate a list of strings, return list of same length."""
    if not texts:
        return []
    numbered = '\n'.join(f'[{i}] {t}' for i, t in enumerate(texts))
    prompt = f"""Translate the following texts to {target}. These are descriptions of
Fujifilm film simulation recipes for photographers.

Rules:
- Keep film names, simulation names and camera models unchanged (Classic Chrome,
  Velvia, Kodachrome, X-Pro3, etc.)
- Keep camera setting names and values in their standard English form
  (Highlight, Shadow, Dynamic Range, DR400, Grain, WB, Clarity, +2, -4, etc.)
- Use natural photographer's language, not literal translation.
- Return EACH text on its own, prefixed with its [index] exactly as given.
- Do not add commentary.

Texts:
{numbered}"""
    msg = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=8000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    raw = msg.content[0].text
    # parse back by [index]
    import re
    out = [''] * len(texts)
    parts = re.split(r'\[(\d+)\]\s*', raw)
    # parts: ['', '0', 'text0', '1', 'text1', ...]
    for i in range(1, len(parts) - 1, 2):
        idx = int(parts[i])
        if 0 <= idx < len(texts):
            out[idx] = parts[i + 1].strip()
    # fallback: any empty stays as original
    for i, v in enumerate(out):
        if not v:
            out[i] = texts[i]
    return out


def translate_strings_in(obj, collect, assign):
    """Generic: collect translatable strings, then assign translations back."""
    pass  # we do explicit per-file handling below for clarity


# ── film_sim_info: translate inspired_by, description, best_for, table VALUES ──
def do_film_sim():
    src = json.load(open('film_sim_info_ru.json', encoding='utf-8'))
    texts, slots = [], []
    for sim, info in src.items():
        for field in ('inspired_by', 'description', 'best_for'):
            if info.get(field):
                slots.append((sim, field, None))
                texts.append(info[field])
        for k, v in info.get('table', {}).items():
            slots.append((sim, 'table', k))
            texts.append(v)
    tr = translate_texts(texts)
    for (sim, field, key), val in zip(slots, tr):
        if field == 'table':
            src[sim]['table'][key] = val
        else:
            src[sim][field] = val
    json.dump(src, open(f'film_sim_info_{lang}.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f'film_sim_info_{lang}.json: {len(texts)} strings')


# ── group_descriptions: translate description (keep keywords as-is) ───────────
def do_group_desc():
    src = json.load(open('group_descriptions_ru.json', encoding='utf-8'))
    texts = [g['description'] for g in src]
    tr = translate_texts(texts)
    for g, val in zip(src, tr):
        g['description'] = val
    json.dump(src, open(f'group_descriptions_{lang}.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f'group_descriptions_{lang}.json: {len(texts)} descriptions')


# ── visual analysis: translate visual_notes, subjects, moods ──────────────────
def do_visual():
    src = json.load(open('group_visual_analysis_ru.json', encoding='utf-8'))
    texts, slots = [], []
    for label, v in src.items():
        if not v:
            continue
        if v.get('visual_notes'):
            slots.append((label, 'visual_notes', None)); texts.append(v['visual_notes'])
        for i, s in enumerate(v.get('subjects', [])):
            slots.append((label, 'subjects', i)); texts.append(s)
        for i, m in enumerate(v.get('moods', [])):
            slots.append((label, 'moods', i)); texts.append(m)
    # batch in chunks of ~80 to keep prompts sane
    CHUNK = 80
    tr = []
    for i in range(0, len(texts), CHUNK):
        tr.extend(translate_texts(texts[i:i+CHUNK]))
        print(f'  visual {min(i+CHUNK, len(texts))}/{len(texts)}')
    for (label, field, idx), val in zip(slots, tr):
        if field == 'visual_notes':
            src[label]['visual_notes'] = val
        else:
            src[label][field][idx] = val
    json.dump(src, open(f'group_visual_analysis_{lang}.json', 'w', encoding='utf-8'),
              indent=2, ensure_ascii=False)
    print(f'group_visual_analysis_{lang}.json: {len(texts)} strings')


if __name__ == '__main__':
    do_film_sim()
    do_group_desc()
    do_visual()
    print('done')
