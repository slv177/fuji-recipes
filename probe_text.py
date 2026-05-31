import re
from bs4 import BeautifulSoup

f = "html_cache/mccurry-kodachrome-a-fujifilm-x-trans-iv-film-simulation-recipe.html"
soup = BeautifulSoup(open(f, encoding='utf-8').read(), 'html.parser')
content = soup.select_one('.entry-content') or soup

# remove scripts, styles, captions, share buttons
for tag in content.select('script, style, .sharedaddy, .wp-caption, figcaption, .entry-footer'):
    tag.decompose()

# get paragraphs
paras = [p.get_text(' ', strip=True) for p in content.select('p') if len(p.get_text(strip=True)) > 40]

# stop before comments / related posts
STOP = re.compile(r'(leave a reply|related posts|you might also|share this)', re.I)
clean = []
for p in paras:
    if STOP.search(p):
        break
    clean.append(p)

print(f"paragraphs: {len(clean)}")
print()
for i, p in enumerate(clean[:6]):
    print(f"[{i}] {p[:200]}")
    print()
