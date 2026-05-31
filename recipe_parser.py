"""Parser for a single fujixweekly recipe page: extracts the settings block."""
import re
from bs4 import BeautifulSoup

# Canonical setting keys found in fujixweekly recipes (lowercased -> canonical).
KNOWN_KEYS = {
    'film simulation': 'Film Simulation',
    'dynamic range': 'Dynamic Range',
    'd range priority': 'D Range Priority',
    'priority': 'Priority',
    'grain effect': 'Grain Effect',
    'grain': 'Grain',
    'color chrome effect': 'Color Chrome Effect',
    'color chrome fx blue': 'Color Chrome FX Blue',
    'color chrome effect blue': 'Color Chrome FX Blue',
    'white balance': 'White Balance',
    'wb': 'White Balance',
    'white balance shift': 'White Balance Shift',
    'highlight': 'Highlight',
    'highlight tone': 'Highlight',
    'shadow': 'Shadow',
    'shadow tone': 'Shadow',
    'color': 'Color',
    'saturation': 'Color',
    'sharpness': 'Sharpness',
    'sharpening': 'Sharpness',
    'noise reduction': 'Noise Reduction',
    'high iso nr': 'High ISO NR',
    'clarity': 'Clarity',
    'iso': 'ISO',
    'exposure compensation': 'Exposure Compensation',
    'exposure comp': 'Exposure Compensation',
    'toning': 'Toning',
    'bw toning': 'Toning',
    'color temperature': 'Color Temperature',
    'monochromatic color': 'Monochromatic Color',
    'tone curve': 'Tone Curve',
}

# regex: "Key: value" at line start
LINE_RE = re.compile(r'^\s*([A-Za-z][A-Za-z0-9 /&()\-\.]{2,40}?)\s*[:–—]\s*(.+?)\s*$')


def _normalize_key(k):
    k = k.strip().lower().rstrip(':').strip()
    k = re.sub(r'\s+', ' ', k)
    return k


# Base film simulation families, longest-substring-first so "Eterna Bleach Bypass"
# wins over "Eterna" and "Classic Negative" over "Negative".
_FS_FAMILIES = [
    'classic chrome', 'classic negative', 'pro neg. hi', 'pro neg. std',
    'pro neg', 'eterna bleach bypass', 'eterna', 'acros', 'monochrome',
    'velvia', 'astia', 'provia', 'nostalgic neg', 'sepia',
]


def _film_sim_from_heading(lines, first_key_idx):
    """Look at the line(s) right before the settings block for a bare film-sim name."""
    for j in (first_key_idx - 1, first_key_idx - 2):
        if j < 0:
            continue
        cand = lines[j].strip()
        if not cand or len(cand) > 45 or ':' in cand:
            continue
        low = cand.lower()
        for fam in _FS_FAMILIES:
            if fam in low:
                return cand
    return None


def parse_recipe(html):
    soup = BeautifulSoup(html, 'html.parser')

    # title
    title = None
    h1 = soup.select_one('h1.entry-title') or soup.select_one('h1')
    if h1:
        title = h1.get_text(strip=True)
    elif soup.title:
        title = soup.title.string

    content = soup.select_one('.entry-content') or soup.select_one('article') or soup

    # Build text lines by breaking ONLY on block-level boundaries (<br>, </p>,
    # </li>, etc.). Inline tags like <strong> must stay joined, otherwise a
    # "<strong>Film Simulation</strong>: Acros" gets split into two lines and the
    # "Key: value" pattern no longer matches.
    frag = str(content)
    frag = re.sub(r'(?i)<br\s*/?>', '\n', frag)
    frag = re.sub(r'(?i)</(p|li|div|h[1-6]|tr|ul|ol|blockquote)>', '\n', frag)
    text = BeautifulSoup(frag, 'html.parser').get_text()  # no separator -> inline joined
    lines = [l.strip() for l in text.split('\n')]

    settings = {}
    block_lines = []
    first_key_idx = None
    for idx, line in enumerate(lines):
        m = LINE_RE.match(line)
        if not m:
            continue
        rawkey, val = m.group(1), m.group(2)
        nk = _normalize_key(rawkey)
        if nk in KNOWN_KEYS:
            canon = KNOWN_KEYS[nk]
            if canon not in settings:           # keep first occurrence
                settings[canon] = val.strip()
                block_lines.append(f'{canon}: {val.strip()}')
                if first_key_idx is None:
                    first_key_idx = idx

    # Older recipes name the base film simulation as a standalone heading line
    # right before the block (e.g. "Classic Chrome" then "Dynamic Range: ..."),
    # without a "Film Simulation:" prefix. Recover it from the preceding line.
    if 'Film Simulation' not in settings and first_key_idx is not None:
        fam = _film_sim_from_heading(lines, first_key_idx)
        if fam:
            settings['Film Simulation'] = fam
            block_lines.insert(0, f'Film Simulation: {fam}')

    return {
        'title': title,
        'settings': settings,
        'raw_block': '\n'.join(block_lines),
        'num_fields': len(settings),
    }


if __name__ == '__main__':
    import sys, json, requests
    url = sys.argv[1] if len(sys.argv) > 1 else \
        'https://fujixweekly.com/2024/01/25/mccurry-kodachrome-a-fujifilm-x-trans-iv-film-simulation-recipe/'
    H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    html = requests.get(url, headers=H, timeout=30).text
    res = parse_recipe(html)
    res['url'] = url
    json.dump(res, open('test_parse.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    print('parsed fields:', res['num_fields'])
