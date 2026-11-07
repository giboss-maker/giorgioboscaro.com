# giorgioboscaro.com

Static copy of the former WordPress site (WordPress 5.7, theme "mf"), served by GitHub Pages at
<https://www.giorgioboscaro.com/>. The design and content are unchanged.

## Structure

| Path | What |
|---|---|
| `index.html` | Home (portfolio grid, About, Contact) |
| `portfolio/<slug>/` | 25 portfolio items |
| `blog/`, `we-appreciate-any-kind-of-feedback/` | Blog listing + its single post |
| `category/`, `tag/`, `type/`, `portfolio-category/`, `author/` | Archive pages |
| `wp-content/`, `wp-includes/` | Theme CSS/JS, images and jQuery, at their original paths |
| `assets/fonts/` | Self-hosted Open Sans (replaces Google Fonts) |
| `404.html`, `sitemap.xml`, `robots.txt`, `CNAME`, `.nojekyll` | GitHub Pages files |
| `_migration/` | Scripts used for the migration (crawl, build, test) |

## Old URLs

WordPress used query-string URLs (`/?portfolio=fulmine`, `/?p=48`, `/?page_id=47`...), which GitHub
Pages cannot serve as separate pages. Pages now live at clean paths with trailing slashes
(`/portfolio/fulmine/`). A small script at the top of `index.html` and `404.html` sends old links to
the new address (map in `_migration/legacy-map.json`). Canonical tags point at the new URLs.

## Removed during migration

- Injected spam: a hidden link in the footer widget and a link inside the blog post.
- Comment form (needs a server); RSS feeds, REST API, oEmbed, XML-RPC, emoji script, wp-embed,
  block-library CSS, Google Maps script (unused), IE8 shims.

## Theme JavaScript fix

Since WordPress 5.6 (jQuery 3) the theme's `plugins.js` crashed on `$.browser.msie`, so the masonry
grid, category filters, About/Contact menu and photo lightbox stopped working on the old site.
`assets/js/jquery-browser-shim.js` restores `jQuery.browser` and adds placeholders for the two Google
Maps classes the bundled (unused) goMap plugin touches at load time. No theme file was edited.

## Local preview

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.
