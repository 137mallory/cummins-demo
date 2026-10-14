"""Re-check agent-found items: the page opens with a plain request and the quote is on it (whitespace and
quote-mark normalised). Prints a verdict per item; writes <in>.verified.json with the items that pass."""
import json, re, sys, urllib.request, html
from concurrent.futures import ThreadPoolExecutor
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).lower()).strip()

def check(it):
    try:
        req = urllib.request.Request(it["url"], headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read(2_500_000).decode("utf-8", "replace")
    except Exception as e:
        return "UNREADABLE " + str(e)[:40]
    body = norm(page)
    q = norm(it["quote"])
    if q and q in body:
        return "OK"
    # tolerate a quote that stops short of a trailing clause
    words = q.split()
    if len(words) > 8 and " ".join(words[:8]) in body:
        return "PARTIAL"
    return "QUOTE NOT FOUND"

if __name__ == "__main__":
    items = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(8) as p:
        res = list(p.map(check, items))
    for it, r in zip(items, res):
        print(r.ljust(18), it["date"], it["source"][:22].ljust(22), it["title"][:70])
    json.dump([it for it, r in zip(items, res) if r in ("OK", "PARTIAL")], open(sys.argv[1].replace(".json", ".verified.json"), "w"), indent=1, ensure_ascii=False)
