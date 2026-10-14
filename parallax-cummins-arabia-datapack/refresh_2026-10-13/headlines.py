"""Use each article's own headline (og:title / <title>, site name stripped) as the row title where the page can be read.
A headline we wrote ourselves stays only where the page is blocked. Source labels are already the link's host."""
import json, re, html, subprocess, sys, concurrent.futures as cf
from urllib.parse import urlparse
P = "news_refresh.json"
nr = json.load(open(P))
UA = "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"
SEP = re.compile(r"\s+[\|–—-]\s+|\s*\|\s*")

def page_title(url):
    b = subprocess.run(["curl", "-sL", "-m", "20", "-A", UA, url], capture_output=True).stdout.decode("utf-8", "ignore")
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', b) or \
        re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title', b) or re.search(r"<title[^>]*>([^<]+)", b)
    return html.unescape(m.group(1)).strip() if m else None

def clean(t, host):
    base = re.sub(r"[^a-z0-9]", "", host.split(".")[-2] if host.count(".") else host)
    parts = [p.strip() for p in SEP.split(t) if p.strip()]
    keep = [p for p in parts if not (re.sub(r"[^a-z0-9]", "", p.lower()) and (re.sub(r"[^a-z0-9]", "", p.lower()) in base or base in re.sub(r"[^a-z0-9]", "", p.lower())) and len(p) <= 40)]
    out = (keep[0] if keep else parts[0]) if len(keep) <= 1 or True else t
    return re.sub(r"\s+", " ", out).strip()

BLOCK = re.compile(r"just a moment|access denied|attention required|your request originates|human verification|403|forbidden|404|not found|^\s*$", re.I)
items = nr["items"]
with cf.ThreadPoolExecutor(8) as ex:
    titles = list(ex.map(lambda it: page_title(it["url"]), items))
changed = []
for it, t in zip(items, titles):
    if not t or BLOCK.search(t): continue
    host = urlparse(it["url"]).netloc.replace("www.", "")
    new = clean(t, host)
    if len(new) < 18 or BLOCK.search(new): continue
    if new != it["title"]:
        changed.append((it["company_id"], it["title"], new))
        if "--apply" in sys.argv:
            it["title_ours"] = it["title"]; it["title"] = new[:200]
print(len(items), "items;", len(changed), "headlines differ from the article's own")
for c in changed: print(f"  [{c[0]}]\n     ours : {c[1][:110]}\n     page : {c[2][:110]}")
if "--apply" in sys.argv:
    json.dump(nr, open(P, "w"), indent=1, ensure_ascii=False); print("applied")
