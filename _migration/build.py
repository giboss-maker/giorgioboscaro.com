"""Turn the raw WordPress mirror into a static site for GitHub Pages.

Usage: python3 -I build.py <mirror_dir> <fonts_pkg_dir> <site_dir>
"""
import json, os, re, shutil, sys
from datetime import date
from html import escape

MIRROR, FONTS, SITE = sys.argv[1:4]
OLD = r"https?://(?:www\.)?giorgioboscaro\.com"
NEW_ORIGIN = "https://www.giorgioboscaro.com"
GTM_ID = "GTM-5V3PT75"

# slugs looked up from the WordPress REST API
SPECIAL = {
    "p=48": "/we-appreciate-any-kind-of-feedback/",
    "page_id=47": "/blog/",
    "page_id=12": "/",
    "cat=5": "/category/video/",
    "author=1": "/author/giboss/",
}
PREFIX = {
    "portfolio": "/portfolio/{}/",
    "portfolio-category": "/portfolio-category/{}/",
    "tag": "/tag/{}/",
    "post_format": "/type/{}/",
}


def new_path(query):
    """Map a WordPress query string (without '?') to a static path."""
    query = query.replace("&#038;", "&").replace("&amp;", "&")
    if not query:
        return "/"
    if query in SPECIAL:
        return SPECIAL[query]
    k, _, v = query.partition("=")
    if k in PREFIX and v and "&" not in v:
        return PREFIX[k].format(v)
    return None


manifest = json.load(open(f"{MIRROR}/manifest.json"))
pages = {}  # new path -> raw html
aliases = {}  # shortlink query (p=87) -> canonical query (portfolio=fulmine)
for url, info in manifest["pages"].items():
    if info["status"] != 200:
        continue
    q = url.split("?", 1)[1] if "?" in url else ""
    raw = open(f"{MIRROR}/pages/{info['key']}.html", encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="[^"?]*\??([^"]*)"', raw)
    if m and m.group(1).replace("&#038;", "&") != q and not info.get("in_sitemap"):
        aliases[q] = m.group(1)
        continue
    p = new_path(q)
    if p is None:
        print("UNMAPPED page", url)
        continue
    pages[p] = open(f"{MIRROR}/pages/{info['key']}.html", encoding="utf-8").read()

# legacy redirect map for the JS shim (old query -> new path)
legacy = {}
for url in manifest["pages"]:
    q = url.split("?", 1)[1] if "?" in url else ""
    if q and new_path(q):
        legacy[q] = new_path(q)
legacy.update({k: v for k, v in SPECIAL.items()})
for short, canon in aliases.items():
    if new_path(canon):
        legacy[short] = new_path(canon)
SPECIAL.update({k: legacy[k] for k in aliases if k in legacy})  # rewrite shortlink hrefs too

REDIRECT_JS = """<script>
/* Legacy WordPress URLs (?p=, ?page_id=, ?portfolio=...) -> static paths */
(function(){var s=location.search;if(!s||s.length<2)return;var m=%s,q=s.slice(1),t=m[q];
if(!t){var a=q.split('&')[0].split('='),k=a[0],v=a[1],pre={'portfolio':'/portfolio/','portfolio-category':'/portfolio-category/','tag':'/tag/','post_format':'/type/'};
if(pre[k]&&v)t=pre[k]+v+'/';else if(/^(feed|page_id|p|cat|author|s|paged|attachment_id)=/.test(q))t='/';}
if(t&&t!==location.pathname)location.replace(t+location.hash);})();
</script>""" % json.dumps(legacy, separators=(",", ":"), sort_keys=True)

GTM_NOSCRIPT = (f'<!-- Google Tag Manager (noscript) -->\n<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"\n'
                'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n<!-- End Google Tag Manager (noscript) -->')

HEAD_REMOVE = [
    r'[ \t]*<link rel="pingback"[^>]*>\n?',
    r"[ \t]*<link rel='dns-prefetch'[^>]*>\n?",
    r'[ \t]*<link rel="alternate" type="application/rss\+xml"[^>]*>\n?',
    r'[ \t]*<script type="text/javascript">\s*window\._wpemojiSettings.*?</script>\s*<style type="text/css">\s*img\.wp-smiley.*?</style>\n?',
    r"[ \t]*<link rel='stylesheet' id='wp-block-library-css'[^>]*>\n?",
    r"[ \t]*<script type='text/javascript' src='[^']*comment-reply[^']*'[^>]*></script>\n?",
    r'<link rel="https://api\.w\.org/"[^>]*>',
    r'<link rel="alternate" type="application/json"[^>]*>',
    r'<link rel="EditURI"[^>]*>\n?',
    r'[ \t]*<link rel="wlwmanifest"[^>]*>\s*\n?',
    r'[ \t]*<meta name="generator"[^>]*>\n?',
    r"[ \t]*<link rel='shortlink'[^>]*>\n?",
    r'[ \t]*<link rel="alternate" type="(?:application/json|text/xml)\+oembed"[^>]*>\n?',
    r'[ \t]*<!--\[if lt IE 9\]>\s*<link href="[^"]*styles-ie8\.css"[^>]*>\s*<!\[endif\]-->\n?',
    r'[ \t]*<!--\[if lt IE 9\]><script src="https://html5shim[^>]*></script><!\[endif\]-->\n?',
    r"<script type='text/javascript' src='https://maps\.google\.com/[^']*'[^>]*></script>\n?",
    r"<script type='text/javascript' src='[^']*wp-embed\.min\.js[^']*'[^>]*></script>\n?",
]


def add_redirect(html):
    """Insert the legacy-URL shim right after <meta charset> / viewport (keeps charset in first 1024 bytes)."""
    return re.sub(r'(<meta name="viewport"[^>]*>)', lambda m: m.group(1) + "\n" + REDIRECT_JS, html, count=1)


def transform(path, html):
    for pat in HEAD_REMOVE:
        html = re.sub(pat, "", html, flags=re.S)

    # theme JS fix: jQuery 3 removed $.browser, which the bundled hashchange plugin reads,
    # so plugins.js crashed and isotope/fancybox never loaded (broken on the live site since WP 5.6)
    html = re.sub(r"(<script type='text/javascript' src='[^']*/modernizr\.js[^']*')",
                  lambda m: "<script type='text/javascript' src='/assets/js/jquery-browser-shim.js'></script>\n" + m.group(1),
                  html, count=1)

    # Google Fonts -> self-hosted
    html = re.sub(r"<link rel='stylesheet' id='font-css'\s+href='https://fonts\.googleapis\.com/[^']*'",
                  "<link rel='stylesheet' id='font-css'  href='/assets/fonts/open-sans.css'", html)

    # broken body attribute (GTM noscript pasted into class) -> clean class + real noscript
    def fix_body(m):
        cls = m.group(1).split("&quot;")[0].strip()
        return f'<body data-rsssl=1 class="{cls}">\n{GTM_NOSCRIPT}\n'
    html = re.sub(r'<body data-rsssl=1 class="([^"]*)">\s*', fix_body, html, count=1, flags=re.S)

    # injected spam: hidden footer link widget and link in post body
    html = re.sub(r'<div id="text-2" class="col1-3 clearfix widget_text">\s*<div class="textwidget">.*?</div>\s*</div>', "", html, flags=re.S)
    html = re.sub(r'\s*<a href="https?://cloneher\.com/[^"]*">[^<]*</a>', "", html)

    # comment form + its AJAX script cannot work on static hosting
    html = re.sub(r'<div class="full-comment-wrap">.*?//AJAXIFY COMMENTS.*?</script>', "", html, flags=re.S)

    # broken contact link, mixed-content video URL
    html = html.replace('href="giorgio.boscaro@gmail.com"', 'href="mailto:giorgio.boscaro@gmail.com"')
    html = html.replace("http://player.vimeo.com/", "https://player.vimeo.com/")

    # local assets: absolute -> root-relative, drop ?ver=
    html = re.sub(OLD + r"(/wp-(?:content|includes)/[^\"'\s?]+)\?ver=[^\"'\s]*", r"\1", html)
    html = re.sub(OLD + r"(/wp-(?:content|includes)/)", r"\1", html)

    # internal page links
    def link(m):
        q = m.group(2) or ""
        target = new_path(q.lstrip("?").replace("&#038;", "&"))
        if target is None:
            print(f"  [{path}] unmapped link {m.group(0)}")
            return m.group(0)
        return m.group(1) + target + (m.group(3) or "")
    html = re.sub(r"((?:href|action)=[\"'])" + OLD + r"/?(\?[^\"'#]*)?(#[^\"']*)?(?=[\"'])", link, html)
    html = re.sub(r"(href=[\"'])/(\?[^\"'#]+)(#[^\"']*)?(?=[\"'])", link, html)

    # canonical
    canon = f'<link rel="canonical" href="{NEW_ORIGIN}{path}" />'
    if re.search(r'<link rel="canonical"[^>]*>', html):
        html = re.sub(r'<link rel="canonical"[^>]*>', canon, html)
    else:
        html = html.replace("</head>", canon + "\n</head>", 1)

    if path == "/":
        html = add_redirect(html)
        html = clean_home_grid(html)
    return html


def clean_home_grid(html):
    """Home grid: drop empty <img src=""> placeholders (broken-image icons), the empty demo item
    "Quiet Village", and make the 2-column photos single-column so the masonry grid has no holes."""
    html = re.sub(r'<div class="images"><img src="" alt="[^"]*" /></div>\s*', "", html)
    html = re.sub(r'<div class="element clearfix col2-3 home  all home overflow load-content">'
                  r'(?:(?!<div class="element).)*?Quiet Village(?:(?!<div class="element).)*', "", html, flags=re.S)
    html = html.replace('class="element clearfix col2-3 ', 'class="element clearfix col1-3 ')
    html = re.sub(r'(<img[^>]*?)class="attachment-lscape-large size-lscape-large',
                  r'\1class="attachment-lscape-medium size-lscape-medium', html)
    return html


# ---- write site ----
if os.path.exists(SITE):
    for name in os.listdir(SITE):
        if name in (".git", "_migration", "README.md", ".gitignore"):
            continue
        p = os.path.join(SITE, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(SITE, exist_ok=True)

for path, html in pages.items():
    out = transform(path, html)
    leftovers = re.findall(OLD + r"[^\"'\s<]*", out)
    if leftovers:
        print(f"  [{path}] remaining old-domain refs: {sorted(set(leftovers))}")
    dest = os.path.join(SITE, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(out)

# assets (skip those only WordPress needed)
SKIP = re.compile(r"wp-includes/(js/wp-emoji|js/wp-embed|css/dist/block-library)|comment-reply")
for root, _, files in os.walk(f"{MIRROR}/files"):
    for f in files:
        src = os.path.join(root, f)
        rel = os.path.relpath(src, f"{MIRROR}/files")
        if SKIP.search(rel):
            continue
        dest = os.path.join(SITE, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)

# jQuery.browser shim (see transform)
os.makedirs(os.path.join(SITE, "assets/js"), exist_ok=True)
open(os.path.join(SITE, "assets/js/jquery-browser-shim.js"), "w").write(
    "/* Restores jQuery.browser (removed in jQuery 1.9) for the theme's hashchange plugin. */\n"
    "if (window.jQuery && !jQuery.browser) { jQuery.browser = { msie: false, version: '0' }; }\n"
    "/* The theme bundles the goMap plugin, which needs these two Google Maps classes at load time.\n"
    "   The site shows no maps, so the Maps API is not loaded; minimal placeholders keep plugins.js running. */\n"
    "if (!window.google) { window.google = {}; }\n"
    "if (!google.maps) { google.maps = { Geocoder: function () {}, OverlayView: function () {} }; }\n")

# fonts
fdir = os.path.join(SITE, "assets/fonts")
os.makedirs(fdir, exist_ok=True)
css = ["/* Open Sans, self-hosted (Fontsource 5.1.0, same files Google Fonts serves). */"]
RANGES = {
    "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF",
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
}
for style, weight in [("italic", 300), ("normal", 300), ("normal", 400), ("normal", 600), ("normal", 700), ("normal", 800)]:
    for sub in ("latin-ext", "latin"):
        fn = f"open-sans-{sub}-{weight}-{style}.woff2"
        shutil.copy2(f"{FONTS}/files/{fn}", os.path.join(fdir, fn))
        css.append(f"@font-face{{font-family:'Open Sans';font-style:{style};font-weight:{weight};font-display:swap;"
                   f"src:url(/assets/fonts/{fn}) format('woff2');unicode-range:{RANGES[sub]};}}")
open(os.path.join(fdir, "open-sans.css"), "w").write("\n".join(css) + "\n")
shutil.copy2(f"{FONTS}/LICENSE", os.path.join(fdir, "LICENSE-OFL.txt"))

# 404 page: reuse the blog listing template, with the legacy redirect shim
tpl = transform("/404.html", pages["/blog/"])
body404 = ('<div class="element clearfix col1-3 no-image">\n<h2>Page not found</h2>\n'
           '<p>The page you are looking for does not exist. <a href="/">Back to the home page &rarr;</a></p>\n</div>\n')
tpl = re.sub(r'(<div id="container" class="clearfix">).*?(</div></div><footer>)', lambda m: m.group(1) + "\n" + body404 + m.group(2), tpl, count=1, flags=re.S)
tpl = re.sub(r"<title>.*?</title>", "<title>Page not found | giorgio boscaro</title>", tpl, count=1, flags=re.S)
tpl = re.sub(r'<link rel="canonical"[^>]*>\n?', "", tpl)
tpl = tpl.replace("<meta name='robots' content='max-image-preview:large' />", "<meta name='robots' content='noindex' />")
tpl = add_redirect(tpl)
open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(tpl)

# sitemap.xml (same URL set as the WordPress sitemap, new locations)
today = date.today().isoformat()
order = sorted(pages, key=lambda p: (p != "/", p))
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for p in order:
    sm.append(f"  <url><loc>{escape(NEW_ORIGIN + p)}</loc><lastmod>{today}</lastmod></url>")
sm.append("</urlset>")
open(os.path.join(SITE, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(SITE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {NEW_ORIGIN}/sitemap.xml\n")
open(os.path.join(SITE, "CNAME"), "w").write("www.giorgioboscaro.com\n")
open(os.path.join(SITE, ".nojekyll"), "w").write("")
json.dump(legacy, open(os.path.join(MIRROR, "legacy-map.json"), "w"), indent=1, sort_keys=True)
print(f"built {len(pages)} pages")
