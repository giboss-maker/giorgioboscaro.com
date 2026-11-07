"""Polite mirror of giorgioboscaro.com (WordPress, plain permalinks).

Usage: python3 -I crawl.py <out_dir>
Saves pages to <out_dir>/pages/<key>.html and assets to <out_dir>/files/<path>.
Writes <out_dir>/manifest.json.
"""
import json, os, re, sys, time
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup

ORIGIN = "https://giorgioboscaro.com"
HOSTS = {"giorgioboscaro.com", "www.giorgioboscaro.com"}
DELAY = 2.0
OUT = sys.argv[1]
S = requests.Session()  # default client identity, no spoofing
last = [0.0]


def get(url):
    for attempt in range(5):
        wait = DELAY - (time.time() - last[0])
        if wait > 0:
            time.sleep(wait)
        last[0] = time.time()
        r = S.get(url, timeout=60)
        ctype = r.headers.get("content-type", "")
        challenge = "text/html" in ctype and b"One moment, please" in r.content[:3000]
        if r.status_code == 200 and not challenge:
            return r
        if r.status_code == 404:
            return r
        print(f"  retry {attempt+1} ({r.status_code}{' challenge' if challenge else ''}) {url}", flush=True)
        time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"failed: {url}")


def page_key(url):
    q = urlparse(url).query
    return "home" if not q else re.sub(r"[^A-Za-z0-9_-]+", "_", q)


def is_local(u):
    p = urlparse(u)
    return p.scheme in ("http", "https") and p.hostname in HOSTS


def asset_path(u):
    return unquote(urlparse(u).path).lstrip("/")


def css_refs(text, base):
    out = []
    for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", text):
        v = m.group(1)
        if not v.startswith("data:"):
            out.append(urljoin(base, v))
    for m in re.finditer(r"@import\s+['\"]([^'\"]+)['\"]", text):
        out.append(urljoin(base, m.group(1)))
    return out


def main():
    os.makedirs(f"{OUT}/pages", exist_ok=True)
    os.makedirs(f"{OUT}/files", exist_ok=True)
    # 1. sitemap
    idx = get(f"{ORIGIN}/?sitemap=index").text
    subs = [s.replace("&amp;", "&") for s in re.findall(r"<loc>([^<]+)</loc>", idx)]
    pages = [f"{ORIGIN}/"]
    for s in subs:
        for loc in re.findall(r"<loc>([^<]+)</loc>", get(s).text):
            loc = loc.replace("&amp;", "&")
            if loc not in pages:
                pages.append(loc)
    print(f"{len(pages)} pages in sitemap", flush=True)

    assets, seen_pages, manifest = set(), set(), {"pages": {}, "assets": {}, "external": set()}
    queue = list(pages)
    while queue:
        url = queue.pop(0)
        if url in seen_pages:
            continue
        seen_pages.add(url)
        r = get(url)
        key = page_key(url)
        print(f"page {r.status_code} {key}", flush=True)
        if r.status_code != 200:
            manifest["pages"][url] = {"key": key, "status": r.status_code}
            continue
        with open(f"{OUT}/pages/{key}.html", "wb") as f:
            f.write(r.content)
        manifest["pages"][url] = {"key": key, "status": 200, "in_sitemap": url in pages}
        soup = BeautifulSoup(r.content, "lxml")
        refs = []
        for tag in soup.find_all(True):
            for attr in ("src", "href", "data-src", "poster"):
                if tag.get(attr):
                    refs.append(urljoin(url, tag[attr]))
            if tag.get("srcset"):
                refs += [urljoin(url, c.strip().split()[0]) for c in tag["srcset"].split(",") if c.strip()]
            if tag.get("style"):
                refs += css_refs(tag["style"], url)
        for st in soup.find_all("style"):
            refs += css_refs(st.get_text(), url)
        for ref in refs:
            ref = ref.split("#")[0]
            if not ref:
                continue
            if not is_local(ref):
                manifest["external"].add(ref)
                continue
            p = urlparse(ref)
            if p.path.startswith(("/wp-content/", "/wp-includes/")):
                assets.add(ref.split("?")[0])
            elif p.path in ("", "/") and p.query and not re.search(r"feed=|rest_route|sitemap", p.query):
                # discover pages not listed in sitemap (pagination, attachments...)
                if p.query.split("=")[0] in ("p", "page_id", "portfolio", "cat", "tag", "post_format", "portfolio-category", "author", "paged", "attachment_id"):
                    queue.append(f"{ORIGIN}/?{p.query}")

    done = set()
    todo = sorted(assets)
    while todo:
        a = todo.pop(0)
        if a in done:
            continue
        done.add(a)
        r = get(a)
        path = asset_path(a)
        manifest["assets"][path] = r.status_code
        print(f"asset {r.status_code} {path}", flush=True)
        if r.status_code != 200:
            continue
        dest = f"{OUT}/files/{path}"
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(r.content)
        if path.endswith(".css"):
            for ref in css_refs(r.text, a):
                if is_local(ref):
                    todo.append(ref.split("?")[0].split("#")[0])
                else:
                    manifest["external"].add(ref)

    manifest["external"] = sorted(manifest["external"])
    with open(f"{OUT}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print("done", len(manifest["pages"]), "pages", len(manifest["assets"]), "assets")


if __name__ == "__main__":
    main()
