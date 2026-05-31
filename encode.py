"""Turn parsed recipe settings into a clean numeric feature matrix."""
import json, re
import numpy as np
import pandas as pd

recs = json.load(open('recipes.json', encoding='utf-8'))

SYN = {'High ISO NR': 'Noise Reduction', 'Grain': 'Grain Effect'}


def get(r, key):
    s = r['settings']
    for k, v in s.items():
        if SYN.get(k, k) == key:
            return v
    return None


def num(val):
    """Parse a signed number like '+2', '-1.5', '0', '-0', '1' -> float or NaN."""
    if val is None:
        return np.nan
    m = re.search(r'[+-]?\d+(?:\.\d+)?', str(val).replace('–', '-'))
    return float(m.group()) if m else np.nan


def dynamic_range(val):
    if val is None:
        return np.nan
    m = re.search(r'(100|200|400)', str(val))
    if m:
        return float(m.group())
    if 'auto' in str(val).lower():
        return 250.0          # between 200 and 400
    if 'strong' in str(val).lower():
        return 400.0
    return np.nan


LEVEL = {'off': 0, 'weak': 1, 'medium': 1.5, 'strong': 2}


def level(val):
    if val is None:
        return np.nan
    s = str(val).lower()
    for word, n in LEVEL.items():
        if word in s:
            return float(n)
    return np.nan


def grain_strength(val):
    return level(val)


def grain_size(val):
    if val is None:
        return np.nan
    s = str(val).lower()
    if 'large' in s:
        return 1.0
    if 'small' in s:
        return 0.0
    if 'off' in s:
        return 0.0
    return np.nan          # strength given but size unspecified (older cameras)


def wb_shift(val):
    """Return (red_shift, blue_shift) parsed from '... +3 Red & -5 Blue'."""
    if val is None:
        return np.nan, np.nan
    s = str(val).replace('–', '-')
    r = re.search(r'([+-]?\d+)\s*Red', s)
    b = re.search(r'([+-]?\d+)\s*Blue', s)
    return (float(r.group(1)) if r else np.nan,
            float(b.group(1)) if b else np.nan)


def wb_kelvin(val):
    """Approximate WB warmth as a Kelvin number; named presets mapped roughly."""
    if val is None:
        return np.nan
    s = str(val).lower()
    m = re.search(r'(\d{4})\s*k', s)
    if m:
        return float(m.group(1))
    if 'daylight' in s:
        return 5500.0
    if 'auto' in s:
        return np.nan
    if 'shade' in s:
        return 7500.0
    if 'cloud' in s:
        return 6500.0
    if 'incandesc' in s or 'tungsten' in s:
        return 3200.0
    if 'fluorescent' in s:
        return 4000.0
    return np.nan


def film_sim(val):
    """Normalize to a base film simulation family."""
    if val is None:
        return None
    s = str(val).strip()
    s = re.split(r'[(,]| or ', s)[0].strip()      # drop "(or Acros+Y...)" etc.
    s = s.rstrip('+').strip()
    base = s.lower()
    families = {
        'classic chrome': 'Classic Chrome',
        'classic neg': 'Classic Negative',
        'pro neg': 'PRO Neg',
        'eterna bleach': 'Eterna Bleach Bypass',
        'eterna': 'Eterna',
        'acros': 'Acros',
        'monochrome': 'Monochrome',
        'velvia': 'Velvia',
        'astia': 'Astia',
        'provia': 'Provia',
        'nostalg': 'Nostalgic Neg',
    }
    for kk, vv in families.items():
        if base.startswith(kk):
            return vv
    return s.title() if s else None


rows = []
for r in recs:
    red, blue = wb_shift(get(r, 'White Balance'))
    rows.append({
        'slug': r['slug'],
        'title': r.get('index_title') or r.get('title'),
        'film_sim': film_sim(get(r, 'Film Simulation')),
        'highlight': num(get(r, 'Highlight')),
        'shadow': num(get(r, 'Shadow')),
        'color': num(get(r, 'Color')),
        'sharpness': num(get(r, 'Sharpness')),
        'noise_reduction': num(get(r, 'Noise Reduction')),
        'clarity': num(get(r, 'Clarity')),
        'dynamic_range': dynamic_range(get(r, 'Dynamic Range')),
        'color_chrome': level(get(r, 'Color Chrome Effect')),
        'color_chrome_blue': level(get(r, 'Color Chrome FX Blue')),
        'grain_strength': grain_strength(get(r, 'Grain Effect')),
        'grain_size': grain_size(get(r, 'Grain Effect')),
        'wb_red': red,
        'wb_blue': blue,
        'wb_kelvin': wb_kelvin(get(r, 'White Balance')),
    })

df = pd.DataFrame(rows)
df.to_csv('features.csv', index=False)

# coverage / NaN report
rep = [f'rows: {len(df)}', '', 'non-null per column:']
for c in df.columns:
    rep.append(f'  {c:18} {df[c].notna().sum():4}/{len(df)}')
rep.append('')
rep.append('film_sim distribution:')
for name, n in df['film_sim'].value_counts(dropna=False).items():
    rep.append(f'  {str(name):22} {n}')
open('encode_report.txt', 'w', encoding='utf-8').write('\n'.join(rep))
