import re
from bs4 import BeautifulSoup

f = "html_cache/mccurry-kodachrome-a-fujifilm-x-trans-iv-film-simulation-recipe.html"
soup = BeautifulSoup(open(f, encoding='utf-8').read(), 'html.parser')
content = soup.select_one('.entry-content') or soup

for tag in content.select('script, style, .sharedaddy, figcaption, .entry-footer'):
    tag.decompose()

# try all block-level text: p + div + li
blocks = []
STOP = re.compile(r'(leave a reply|related posts|you might also|share this|film simulation:|dynamic range:|grain effect:)', re.I)
for el in content.find_all(['p', 'li', 'h2', 'h3']):
    txt = el.get_text(' ', strip=True)
    if len(txt) < 30:
        continue
    if STOP.search(txt):
        continue
    blocks.append(txt)

print(f"blocks found: {len(blocks)}")
for b in blocks[:10]:
    print('>>>', b[:220])
    print()
