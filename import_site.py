import json, re, html, ssl
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image

BASE = 'https://easy-language.com.ua'
ROOT = Path('/root/easy-language-static')
CTX = ssl._create_unverified_context()  # legacy site has expired cert; new Vercel will not
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36'

SEED = [
    '/', '/order.php', '/about.php', '/languages.php', '/english-corporate-lessons.php',
    '/repetitor-english-kiev.php', '/methods.php', '/guarantees.php', '/faq.php',
    '/english-courses.php', '/german-courses.php', '/french-courses.php', '/spanish-courses.php',
    '/online-english-lessons.php', '/english-lessons-for-children.php', '/english-lessons-for-beginners.php',
    '/italian-courses.php', '/arabic-courses.php', '/chinese-courses.php', '/turkish-courses.php'
]

NAV = [
    ('/', 'Главная'),
    ('/about/', 'О нас'),
    ('/languages/', 'Языки'),
    ('/english-corporate-lessons/', 'Корпоративное обучение'),
    ('/repetitor-english-kiev/', 'Индивидуальные занятия'),
    ('/methods/', 'Методика'),
    ('/guarantees/', 'Гарантии'),
    ('/faq/', 'FAQ'),
    ('/order/', 'Заявка'),
]

IMAGE_NAMES = {
    'a1': 'classroom-adults', 'a2': 'classroom-speaking',
    'b1': 'teacher-session', 'b2': 'student-notes',
    'c1': 'language-class', 'c2': 'conversation-practice',
    'sub1': 'english-course', 'sub2': 'german-course', 'sub3': 'french-course', 'sub4': 'spanish-course',
    'sub5': 'italian-course', 'sub6': 'arabic-course', 'sub7': 'chinese-course',
    'flag1': 'flag-english', 'flag2': 'flag-german', 'flag3': 'flag-french', 'flag4': 'flag-spanish',
    'flag5': 'flag-italian', 'flag6': 'flag-arabic', 'flag7': 'flag-chinese', 'flag8': 'flag-turkish',
    'h1': 'easy-language-logo', 'bg': 'background-pattern', 'nav': 'navigation-bg', 'phone': 'phone-icon',
    'zayavka': 'application-button', 'form': 'form-bg', 'f': 'footer-bg', 'f-bot': 'footer-bottom',
    'f-top': 'footer-top', 'bul': 'bullet', 'bul1': 'bullet-alt', 'faq': 'faq-icon', 'trionika': 'trionika',
    'easy': 'easy-logo', 'f-phone': 'footer-phone', 'f-mail': 'footer-mail', 'l': 'nav-left', 'r': 'nav-right',
    'none': 'placeholder', 'prep': 'teachers',
}

def fetch(url, binary=False):
    req = Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urlopen(req, timeout=40, context=CTX) as r:
        data = r.read()
    return data if binary else data.decode('utf-8', 'replace')

def textify(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or '')).strip())

def clean_name(url):
    stem = Path(urlparse(url).path).stem.lower().replace('_','-')
    mapped = IMAGE_NAMES.get(stem, stem)
    mapped = re.sub(r'[^a-z0-9-]+','-', mapped).strip('-') or 'image'
    return mapped + '.webp'

def unique(name, used):
    if name not in used:
        used.add(name); return name
    base, ext = name.rsplit('.',1); i=2
    while f'{base}-{i}.{ext}' in used: i+=1
    out=f'{base}-{i}.{ext}'; used.add(out); return out

def new_path(old_path):
    if old_path in ['', '/']: return '/'
    slug = old_path.strip('/').removesuffix('.php')
    return f'/{slug}/'

def extract_between(s, start_pat, end_pat):
    start = re.search(start_pat, s, re.I|re.S)
    if not start: return ''
    sub = s[start.end():]
    end = re.search(end_pat, sub, re.I|re.S)
    return sub[:end.start()] if end else sub

def strip_common(raw):
    # Prefer main content column from this old template.
    content = extract_between(raw, r'<!--BEGIN \.contetn-->|<div class="contetn[^>]*>|<div class="content[^>]*>', r'<!--END \.contetn-->|<div class="sidebar|<!--BEGIN \.footer-->|</body>')
    if not content:
        content = extract_between(raw, r'<div class="page"[^>]*>', r'<!--BEGIN \.footer-->|</body>')
    content = re.sub(r'<p class="bc">.*?</p>', '', content, flags=re.I|re.S)
    content = re.sub(r'<script.*?</script>', '', content, flags=re.I|re.S)
    content = re.sub(r'\s(?:class|style|width|height)="[^"]*"', lambda m: '' if 'style=' in m.group(0) or 'width=' in m.group(0) or 'height=' in m.group(0) else m.group(0), content, flags=re.I)
    return content.strip()

def description_from(content, title):
    t = textify(content)
    if t.startswith(title): t = t[len(title):].strip(' .—:-')
    return (t[:157].rsplit(' ',1)[0] + '...') if len(t) > 160 else t

# crawl pages + discover assets
raw_pages = []
asset_urls = set()
all_page_urls = set(BASE + p for p in SEED)
for path in SEED:
    url = BASE + path
    raw = fetch(url)
    final_path = urlparse(url).path or '/'
    title = textify((re.search(r'<title>(.*?)</title>', raw, re.I|re.S) or ['',''])[1])
    h1 = textify((re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.I|re.S) or ['',''])[1])
    content = strip_common(raw)
    # gather links/assets from full HTML
    for ref in re.findall(r'(?:href|src)=["\']([^"\']+)', raw, re.I):
        if ref.startswith('//'): ref = 'https:' + ref
        full = urljoin(url, ref)
        pu = urlparse(full)
        if pu.netloc.replace('www.','') == 'easy-language.com.ua':
            if re.search(r'\.(png|jpe?g|gif|svg|ico|css|js)$', pu.path, re.I) or '/img/' in pu.path:
                asset_urls.add(full)
            elif pu.path.endswith('.php') or pu.path in ['', '/']:
                all_page_urls.add(BASE + pu.path)
    raw_pages.append({'oldPath': final_path, 'path': new_path(final_path), 'title': title, 'h1': h1, 'raw': raw, 'contentHtml': content})

# CSS background assets
for css_path in ['/css/master.css','/css/base.css','/css/layout.css']:
    try:
        css = fetch(BASE + css_path)
        asset_urls.add(BASE + css_path)
        for ref in re.findall(r'url\(([^)]+)\)', css):
            ref = ref.strip('"\' ')
            if not ref.startswith('data:'):
                asset_urls.add(urljoin(BASE + css_path, ref))
    except Exception:
        pass

# Convert image assets to webp; ignore css/js as source assets
used=set(); image_map={}; manifest=[]
for url in sorted(asset_urls):
    if not re.search(r'\.(png|jpe?g|gif|ico|svg)$', urlparse(url).path, re.I):
        continue
    try:
        raw = fetch(url, binary=True)
        img = Image.open(BytesIO(raw)).convert('RGBA')
        name = unique(clean_name(url), used)
        out = ROOT / 'public/images' / name
        # Flatten transparent decorative images onto transparent webp where possible
        img.save(out, 'WEBP', quality=84, method=6)
        image_map[url] = '/images/' + name
        image_map[url.replace('https://www.', 'https://')] = '/images/' + name
        image_map[url.replace('https://', 'http://')] = '/images/' + name
        manifest.append({'old': url, 'new': '/images/'+name, 'width': img.width, 'height': img.height})
    except Exception as e:
        print('asset skip', url, e)

# rewrite content links/assets
old_to_new = {BASE + p: new_path(p) for p in SEED}
old_to_new.update({'https://www.easy-language.com.ua'+p: new_path(p) for p in SEED})
old_to_new[BASE + '/'] = '/'

def rewrite_html(s):
    out = s
    for old, new in sorted(image_map.items(), key=lambda kv:-len(kv[0])):
        out = out.replace(old, new)
        out = out.replace(urlparse(old).path.lstrip('/'), new.lstrip('/'))
        out = out.replace(urlparse(old).path, new)
    for old, new in sorted(old_to_new.items(), key=lambda kv:-len(kv[0])):
        out = out.replace(old, new)
    # relative php hrefs
    out = re.sub(r'href="/?([a-z0-9-]+)\.php"', lambda m: f'href="/{m.group(1)}/"', out, flags=re.I)
    out = re.sub(r'src="/?img/([^"\']+)"', lambda m: f'src="{image_map.get(BASE+"/img/"+m.group(1), "/images/"+clean_name(m.group(1)))}"', out, flags=re.I)
    out = out.replace('src="images/', 'src="/images/')
    out = re.sub(r'<img\b(?![^>]*loading=)', '<img loading="lazy" decoding="async"', out, flags=re.I)
    out = re.sub(r'\s+', ' ', out)
    return out.strip()

pages=[]
for p in raw_pages:
    content = rewrite_html(p['contentHtml'])
    title = p['title'] or p['h1'] or 'Easy Language'
    h1 = p['h1'] or title
    pages.append({
        'oldPath': p['oldPath'], 'path': p['path'], 'slug': '' if p['path']=='/' else p['path'].strip('/'),
        'title': title, 'h1': h1, 'description': description_from(content, h1),
        'canonical': BASE + (p['path'] if p['path'] != '/' else '/'),
        'contentHtml': content,
    })

# dedupe/order
seen=set(); ordered=[]
for seed in SEED:
    np = new_path(seed)
    for p in pages:
        if p['path']==np and np not in seen:
            ordered.append(p); seen.add(np)
pages = ordered

# write content
(ROOT/'src/content/pages.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2)+'\n')
(ROOT/'src/content/images.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')

# redirects: php + image originals to webp
redirects=[]
for p in pages:
    if p['oldPath'] != p['path']:
        redirects.append({'source': p['oldPath'], 'destination': p['path'], 'statusCode': 301})
for old, new in image_map.items():
    path = urlparse(old).path
    if path.startswith('/img/'):
        redirects.append({'source': path, 'destination': new, 'statusCode': 301})
uniq=[]; s=set()
for r in redirects:
    k=(r['source'],r['destination'])
    if k not in s: s.add(k); uniq.append(r)
(ROOT/'vercel.redirects.json').write_text(json.dumps(uniq, ensure_ascii=False, indent=2)+'\n')
(ROOT/'vercel.json').write_text(json.dumps({'trailingSlash': True, 'cleanUrls': True, 'redirects': uniq}, ensure_ascii=False, indent=2)+'\n')

# sitemap robots
sitemap=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p in pages:
    sitemap += ['  <url>', f'    <loc>{html.escape(p["canonical"])}</loc>', '    <changefreq>monthly</changefreq>', '    <priority>0.7</priority>', '  </url>']
sitemap.append('</urlset>')
(ROOT/'public/sitemap.xml').write_text('\n'.join(sitemap)+'\n')
(ROOT/'public/robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://easy-language.com.ua/sitemap.xml\n')

print(json.dumps({'pages':len(pages),'images':len(manifest),'redirects':len(uniq),'paths':[p['path'] for p in pages]}, ensure_ascii=False, indent=2))
