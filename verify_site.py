import json, re, sys
from pathlib import Path
from html.parser import HTMLParser
import html as htmlmod

ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
pages=json.loads((ROOT/'src/content/pages.json').read_text())
redirects=json.loads((ROOT/'vercel.redirects.json').read_text())
errors=[]
class P(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.imgs=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'): self.links.append(d['href'])
        if tag=='img' and d.get('src'): self.imgs.append(d['src'])
def file_for(path):
    return DIST/'index.html' if path=='/' else DIST/path.strip('/')/'index.html'
for page in pages:
    f=file_for(page['path'])
    if not f.exists(): errors.append(f'missing page {page["path"]}'); continue
    raw=f.read_text(); dec=htmlmod.unescape(raw)
    if f'<title>{page["title"]}</title>' not in dec: errors.append(f'title mismatch {page["path"]}')
    if page['description'] and page['description'] not in dec: errors.append(f'description missing {page["path"]}')
    if page['canonical'] not in dec: errors.append(f'canonical missing {page["path"]}')
    if '.php' in raw: errors.append(f'php reference left {page["path"]}')
    if '/img/' in raw: errors.append(f'old img path left {page["path"]}')
    p=P(); p.feed(raw)
    for href in p.links:
        if href.startswith('/') and not href.startswith('//') and not href.startswith('/images/'):
            if not file_for(href).exists(): errors.append(f'broken link {href} from {page["path"]}')
    for src in p.imgs:
        if src.startswith('/images/'):
            img=DIST/src.lstrip('/')
            if not img.exists(): errors.append(f'missing image {src}')
            if img.suffix!='.webp': errors.append(f'non-webp {src}')
        elif src.startswith('/'): errors.append(f'unexpected local image {src}')
for p in pages:
    if p['canonical'] not in (DIST/'sitemap.xml').read_text(): errors.append(f'sitemap missing {p["canonical"]}')
for old in ['/about.php','/languages.php','/english-courses.php','/order.php']:
    if not any(r['source']==old and r['statusCode']==301 for r in redirects): errors.append(f'missing redirect {old}')
imgs=sorted((DIST/'images').glob('*'))
if len(imgs) < 20: errors.append(f'too few images {len(imgs)}')
for img in imgs:
    if img.suffix!='.webp': errors.append(f'non-webp file {img.name}')
    if re.search(r'\.(jpg|jpeg|png|gif)$|flag\d|sub\d|^[abc]\d', img.name, re.I): errors.append(f'unclean image name {img.name}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(json.dumps({'pages_checked':len(pages),'images_checked':len(imgs),'redirects':len(redirects)},indent=2,ensure_ascii=False))
