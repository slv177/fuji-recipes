import re, traceback
rep = []
try:
    import requests
    from bs4 import BeautifulSoup
    H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    URL = 'https://fujixweekly.com/fujifilm-x-trans-iv-recipes/'
    r = requests.get(URL, headers=H, timeout=30)
    open('index.html', 'w', encoding='utf-8').write(r.text)
    raw = r.text
    raw_dated = re.findall(r'https://fujixweekly\.com/20\d\d/\d\d/\d\d/[a-z0-9\-]+/?', raw)
    uniq_raw = sorted(set(raw_dated))
    soup = BeautifulSoup(raw, 'html.parser')
    anchors = soup.select('a[href]')
    a_dated = sorted({a['href'] for a in anchors
                      if re.search(r'fujixweekly\.com/20\d\d/\d\d/\d\d/', a['href'])})
    rep.append(f'status={r.status_code} len={len(raw)}')
    rep.append(f'total_anchors={len(anchors)}')
    rep.append(f'raw_dated_urls_unique={len(uniq_raw)}')
    rep.append(f'anchor_dated_urls_unique={len(a_dated)}')
    rep.append('--- first 40 raw dated urls ---')
    rep.extend(uniq_raw[:40])
except Exception:
    rep.append('ERROR:')
    rep.append(traceback.format_exc())
open('report1.txt', 'w', encoding='utf-8').write('\n'.join(rep))
