"""The picture that belongs to each news article, read from the article itself.

    python db/article_images.py <dataset.json> <pack>/article_images.json [--refresh]

For every url the dataset cites (news rows, signal cards, details, dossier entities) the page is
read once and its picture candidates are collected in this order:
    og:image / twitter:image, JSON-LD image, <link rel=image_src>, then the images in the article body
Body images skip anything a reader cannot see (hidden attribute, aria-hidden, display:none,
visibility:hidden, zero size, sr-only) and anything that is page furniture (nav, header, footer,
aside, forms, share bars, related lists, ads, author avatars, logos, icons).
A candidate is kept only if it really loads (HTTP 200, image content type) and is a real picture:
at least 300 x 150 px, not a thin strip, not a logo by name, and not one that two or more different
articles declare (a site's default share picture). The first candidate that passes is the answer;
a page that cannot be read (403, login, timeout) or has no passing picture stays empty.
A picture a person has looked at and refused (a logo, a stock illustration the publisher puts on every
story) is listed in <pack>/article_images_deny.json as {"match": url fragment, "reason": why}.
Nothing here gets around a block: a page that refuses a plain request is left without an image.

Result: {article url: {"image": url | null, "how": "og"|"twitter"|"jsonld"|"link"|"body"|"none"|"unreadable",
                       "w": int, "h": int}}
"""
import json
import os
import re
import struct
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124 Safari/537.36")
OG_RX = [("og", re.compile(r'<meta[^>]+property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)', re.I)),
         ("og", re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::url)?["\']', re.I)),
         ("twitter", re.compile(r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)', re.I)),
         ("twitter", re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', re.I)),
         ("link", re.compile(r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)', re.I)),
         ("link", re.compile(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']image_src["\']', re.I))]
LD_RX = re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.I | re.S)
BAD_NAME = re.compile(r"logo|favicon|sprite|placeholder|default[-_]?(share|og|image)|og[-_]default|share[-_]image"
                      r"|ogp_sns|metaimage|social_image|byline|author|avatar|gravatar|icon|pixel|spacer|blank"
                      r"|1x1|loader|spinner|badge|emoji|flag[-_]|/ads?/|banner|\.gif(\?|$)|\.svg(\?|$)"
                      r"|fallback|og[-_]?image|shutterstock|istock|gettyimages|depositphotos|adobestock|dreamstime|alamy", re.I)
FURNITURE_TAG = {"nav", "header", "footer", "aside", "form", "noscript", "svg", "template", "script", "style", "button", "select"}
FURNITURE_CLASS = re.compile(r"(^|[\s_-])(nav|menu|footer|sidebar|related|comment|share|social|advert|ad|ads|banner|promo|"
                             r"cookie|modal|popup|newsletter|author|byline|avatar|logo|widget|subscribe|trending|recommended)"
                             r"([\s_-]|$)", re.I)
HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(\.0+)?\s*(;|$)|"
                          r"(^|;)\s*(width|height)\s*:\s*0(px)?\s*(;|$)", re.I)
HIDDEN_CLASS = re.compile(r"(^|\s)(hidden|d-none|sr-only|visually-hidden|screen-reader-text|is-hidden)(\s|$)", re.I)
VOID = {"img", "br", "hr", "meta", "link", "input", "source", "area", "base", "col", "embed", "param", "track", "wbr"}
MIN_W, MIN_H = 300, 150
AD_SIZES = {(300, 250), (300, 300), (336, 280), (300, 600), (728, 90), (970, 250), (970, 90), (160, 600), (320, 50), (320, 100), (468, 60)}
DENY = []      # picture url fragments a person has looked at and refused (article_images_deny.json)


PROXY_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36")      # what backend/app.py /api/img sends: a picture must load for that


def get(url, accept, limit):
    req = urllib.request.Request(url, headers={"User-Agent": PROXY_UA if accept.startswith("image/") else UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, (r.headers.get("Content-Type") or "").lower(), r.read(limit)


def dims(b):
    """(w, h) from the first bytes of a png / jpeg / gif / webp, else None."""
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", b[16:24])
        if b[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", b[6:10])
        if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
            k = b[12:16]
            if k == b"VP8 ":
                return struct.unpack("<HH", b[26:30])[0] & 0x3FFF, struct.unpack("<HH", b[26:30])[1] & 0x3FFF
            if k == b"VP8L":
                v = struct.unpack("<I", b[21:25])[0]
                return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
            if k == b"VP8X":
                return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
        if b[:2] == b"\xff\xd8":
            i = 2
            while i < len(b) - 9:
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    i += 2
                    continue
                n = struct.unpack(">H", b[i + 2:i + 4])[0]
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    return struct.unpack(">HH", b[i + 5:i + 9])[::-1]
                i += 2 + n
    except Exception:
        pass
    return None


class Body(HTMLParser):
    """Images a reader can see, in document order; `in_article` marks those inside <article>/<main>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.out = [], []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        cls = f"{a.get('class', '')} {a.get('id', '')}"
        hidden = ("hidden" in a or a.get("aria-hidden", "").lower() == "true" or bool(HIDDEN_STYLE.search(a.get("style", "")))
                  or bool(HIDDEN_CLASS.search(a.get("class", ""))) or a.get("type", "").lower() == "hidden")
        furn = tag in FURNITURE_TAG or bool(FURNITURE_CLASS.search(cls))
        if tag == "img":
            self.img(a, hidden or any(s[1] for s in self.stack), furn or any(s[2] for s in self.stack))
            return
        if tag not in VOID:
            self.stack.append((tag, hidden, furn, tag in ("article", "main")))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def img(self, a, hidden, furniture):
        if hidden or furniture or a.get("loading") == "lazy-hidden":
            return
        for k in ("width", "height"):
            m = re.match(r"\d+", a.get(k, ""))
            if m and int(m.group()) < 150:
                return
        src = ""
        ss = a.get("srcset") or a.get("data-srcset") or ""
        if ss:
            best = 0
            for part in ss.split(","):
                bits = part.strip().split()
                if bits and bits[0]:
                    w = int(re.sub(r"\D", "", bits[1]) or 0) if len(bits) > 1 else 0
                    if w >= best:
                        best, src = w, bits[0]
        src = src or a.get("data-src") or a.get("data-lazy-src") or a.get("data-original") or a.get("src") or ""
        if src and not src.startswith("data:"):
            self.out.append((src, any(s[3] for s in self.stack)))


def candidates(url):
    """[(how, absolute image url)] for one article page, or None when the page cannot be read."""
    if not url.startswith("http") or url.lower().endswith(".pdf"):
        return None
    try:
        status, ctype, raw = get(url, "text/html,*/*", 1_500_000)
    except Exception:
        return None
    if status != 200 or "html" not in ctype:
        return None
    page = raw.decode("utf-8", "replace")
    out = []
    for how, rx in OG_RX:
        for m in rx.finditer(page):
            out.append((how, m.group(1)))
    for blob in LD_RX.findall(page):
        try:
            node = json.loads(blob.strip())
        except Exception:
            continue
        stack = [node]
        while stack:
            n = stack.pop()
            if isinstance(n, list):
                stack += n
            elif isinstance(n, dict):
                for k in ("image", "thumbnailUrl", "contentUrl"):
                    v = n.get(k)
                    if isinstance(v, str):
                        out.append(("jsonld", v))
                    elif isinstance(v, (list, dict)):
                        stack.append(v)
                if n.get("@type") == "ImageObject" and isinstance(n.get("url"), str):
                    out.append(("jsonld", n["url"]))
                stack += [v for k, v in n.items() if k in ("@graph", "mainEntity", "mainEntityOfPage") and isinstance(v, (dict, list))]
    p = Body()
    try:
        p.feed(page)
    except Exception:
        pass
    body = sorted(p.out, key=lambda t: not t[1])        # inside <article>/<main> first, stable otherwise
    out += [("body", s) for s, _ in body[:8]]
    seen, res = set(), []
    for how, s in out:
        s = unescape(s.strip())
        if not s:
            continue
        s = urljoin(url, s)
        if s not in seen and urlparse(s).scheme in ("http", "https") and urlparse(s).path not in ("", "/"):
            seen.add(s)
            res.append((how, s))
    return res


def check(img):
    """(w, h) when the picture loads and is big enough, else None."""
    if BAD_NAME.search(unquote(img.split("//", 1)[-1])) or any(m in img for m in DENY):
        return None
    try:
        status, ctype, raw = get(img, "image/*,*/*", 6 * 1024 * 1024 + 1)
    except Exception:
        return None
    if status != 200 or not ctype.startswith("image/") or not 6000 <= len(raw) <= 6 * 1024 * 1024:   # the app's /api/img proxy refuses over 6 MB
        return None
    d = dims(raw)
    if d and tuple(d) in AD_SIZES:
        return None        # an advertising slot size, not a story picture
    if not d or d[0] < MIN_W or d[1] < MIN_H or not 0.45 <= d[0] / d[1] <= 3.6:
        return None
    return d


def urls_of(data):
    rows = [n for lst in (data.get("competitorNews") or {}).values() for n in lst]
    cards = [c for lane in ("competitiveCards", "marketCards", "techCards") for c in data.get(lane) or []]
    dets = list((data.get("details") or {}).values())
    profs = [c.get("profile") or {} for c in (data.get("competitors") or {}).values()]
    dossier = [x for pr in profs for key in ("entities", "refs") for x in pr.get(key) or []]
    link = lambda x: x.get("url") or x.get("source_url")
    return sorted({link(x) for x in rows + cards + dets + dossier if link(x)})


def run(data, path, refresh=False):
    cache = {} if refresh or not os.path.exists(path) else json.load(open(path, encoding="utf-8"))
    deny = os.path.join(os.path.dirname(path), "article_images_deny.json")
    DENY[:] = [d["match"] for d in json.load(open(deny, encoding="utf-8"))] if os.path.exists(deny) else []
    todo = [u for u in urls_of(data) if u not in cache]
    with ThreadPoolExecutor(12) as pool:
        cands = dict(zip(todo, pool.map(candidates, todo)))
    # a picture two different articles both name is the site's default, not the story's
    uses = {}
    for u, c in cands.items():
        for _, img in c or []:
            uses.setdefault(img, set()).add(u)
    for u, c in cache.items():
        if c.get("image"):
            uses.setdefault(c["image"], set()).add(u)
    default = {img for img, us in uses.items() if len(us) >= 2}

    def pick(u):
        c = cands[u]
        if c is None:
            return {"image": None, "how": "unreadable"}
        for how, img in c:
            if img in default:
                continue
            d = check(img)
            if d:
                return {"image": img, "how": how, "w": d[0], "h": d[1]}
        return {"image": None, "how": "none"}
    with ThreadPoolExecutor(12) as pool:
        for u, r in zip(todo, pool.map(pick, todo)):
            cache[u] = r
    # the same story on another public page (a person found it, looked at the picture, kept it in
    # <pack>/article_images_alt.json); used only where the article itself gave nothing, and it must still pass check()
    alt = os.path.join(os.path.dirname(path), "article_images_alt.json")
    for a in json.load(open(alt, encoding="utf-8")) if os.path.exists(alt) else []:
        r = cache.get(a["url"])
        if r is not None and not r.get("image") and a["url"] in urls_of(data):
            d = check(a["image"])
            if d:
                cache[a["url"]] = {"image": a["image"], "how": "alt", "alt_url": a["alt_url"], "w": d[0], "h": d[1]}
    json.dump(cache, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return cache


def apply(data, cache):
    """Set `image` on every record from its article's picture; a record whose article has none is cleared."""
    rows = [n for lst in (data.get("competitorNews") or {}).values() for n in lst]
    cards = [c for lane in ("competitiveCards", "marketCards", "techCards") for c in data.get(lane) or []]
    dets = list((data.get("details") or {}).values())
    profs = [c.get("profile") or {} for c in (data.get("competitors") or {}).values()]
    dossier = [x for pr in profs for key in ("entities", "refs") for x in pr.get(key) or []]
    n = cleared = 0
    verified = {r["image"] for r in cache.values() if r.get("image")}
    for x in rows + cards + dets + dossier:
        r = cache.get(x.get("url") or x.get("source_url") or "")
        if r is None:
            r = {"image": x.get("image") if x.get("image") in verified else None}   # a picture from anywhere else is unverified
        if r.get("image"):
            n += x.get("image") != r["image"]
            x["image"] = r["image"]
        elif x.get("image"):
            del x["image"]
            cleared += 1
    return n, cleared


def demo():
    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 800, 450)
    assert dims(png) == (800, 450)
    jpg = b"\xff\xd8\xff\xe0" + struct.pack(">H", 16) + b"JFIF" + bytes(11) + b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 450, 800) + bytes(12)
    assert dims(jpg) == (800, 450), dims(jpg)
    p = Body()
    p.feed('<nav><img src="/n.jpg"></nav><div hidden><img src="/h.jpg"></div><div style="display:none"><img src="/h2.jpg"></div>'
           '<article><img src="/small.jpg" width="40"><img src="/a.jpg" width="900"><div class="share"><img src="/s.jpg"></div></article>'
           '<img src="/outside.jpg">')
    assert p.out == [("/a.jpg", True), ("/outside.jpg", False)], p.out
    print("demo ok")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        a = [x for x in sys.argv[1:] if not x.startswith("--")]
        res = run(json.load(open(a[0], encoding="utf-8")), a[1], "--refresh" in sys.argv)
        import collections
        print(collections.Counter(r["how"] for r in res.values()))
