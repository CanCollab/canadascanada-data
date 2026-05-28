#!/usr/bin/env python3
"""
CanadaScanada RSS Pipeline v2 — parallel fetch with hard timeouts
"""

import json
import hashlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from datetime import datetime, timezone, timedelta
from pathlib import Path
from difflib import SequenceMatcher

try:
    import feedparser
    import requests
except ImportError:
    print("Install dependencies: pip install feedparser requests")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

FEED_TIMEOUT_SECONDS = 10    # per-feed HTTP timeout
GLOBAL_TIMEOUT_SECONDS = 180 # entire pipeline timeout (3 min)
MAX_ITEMS_PER_FEED = 20

ROOT = Path(__file__).parent
FEED_MAP_PATH     = ROOT / "feed-map.json"
KEYWORD_FILTER_PATH = ROOT / "keyword-filter.json"
REFS_INDEX_PATH   = ROOT / "references/index.json"
QUEUE_PATH        = ROOT / "submissions/rss-queue.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_known_urls():
    try:
        data = load_json(REFS_INDEX_PATH)
        return {r["url"].strip().rstrip("/") for r in data.get("references", []) if r.get("url")}
    except FileNotFoundError:
        return set()

def load_existing_queue():
    try:
        return load_json(QUEUE_PATH).get("items", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def normalize(text):
    return (text or "").lower()

def matches_any(text, terms):
    t = normalize(text)
    return any(normalize(term) in t for term in terms)

def is_relevant(title, description, kf):
    combined = f"{title} {description}"
    if matches_any(combined, kf["exclusions"]["terms"]):
        return False, None
    if not matches_any(combined, kf["actors_any"]["terms"]):
        return False, None
    cats = [cid for cid, cd in kf["categories"].items() if matches_any(combined, cd["terms"])]
    if not cats:
        return False, None
    return True, cats

def get_confidence(title, description, cats, kf):
    combined = f"{title} {description}"
    actors = sum(1 for t in kf["actors_any"]["terms"] if normalize(t) in normalize(combined))
    if actors >= 2 and len(cats) >= 2: return "high"
    if actors >= 1 and len(cats) >= 1: return "medium"
    return "low"

def url_key(url):
    u = url.strip().rstrip("/")
    for p in ["?utm_source", "&utm_", "?ref=", "#"]:
        if p in u:
            u = u[:u.index(p)]
    return u

def is_dupe(url, title, known_urls, seen):
    k = url_key(url)
    if k in known_urls: return True
    if any(url_key(q.get("url","")) == k for q in seen): return True
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    for q in seen:
        try:
            qt = datetime.fromisoformat(q.get("fetched_at",""))
            if qt.tzinfo is None: qt = qt.replace(tzinfo=timezone.utc)
            if qt < cutoff: continue
        except: continue
        if SequenceMatcher(None, normalize(title), normalize(q.get("title",""))).ratio() > 0.75:
            return True
    return False

# ── Fetch one feed (runs in thread) ──────────────────────────────────────────

def fetch_one(feed_config, kf, known_urls):
    fid = feed_config["feed_id"]
    url = feed_config["url"]
    results = []
    try:
        resp = requests.get(
            url, timeout=FEED_TIMEOUT_SECONDS,
            headers={"User-Agent": "CanadaScanada/1.0 (+https://canadascanada.ca)"},
            allow_redirects=True
        )
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        entries = parsed.get("entries", [])[:MAX_ITEMS_PER_FEED]
        status = f"✓ {len(entries)} entries"
    except requests.exceptions.Timeout:
        return fid, [], f"✗ TIMEOUT ({FEED_TIMEOUT_SECONDS}s)"
    except requests.exceptions.SSLError as e:
        return fid, [], f"✗ SSL ERROR: {e}"
    except Exception as e:
        return fid, [], f"✗ ERROR: {type(e).__name__}: {str(e)[:80]}"

    for entry in entries:
        title = entry.get("title", "").strip()
        link  = entry.get("link",  "").strip()
        if not title or not link: continue
        raw = entry.get("summary", entry.get("description", ""))
        summary = re.sub(r"<[^>]+>", " ", raw).strip()[:500]

        ok, cats = is_relevant(title, summary, kf)
        if not ok: continue

        pub = None
        if getattr(entry, "published_parsed", None):
            try: pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except: pass

        results.append({
            "queue_id": f"RSS-{hashlib.md5(link.encode()).hexdigest()[:8].upper()}",
            "feed_id": fid,
            "outlet_id": feed_config["outlet_id"],
            "outlet_name": feed_config["outlet_name"],
            "tier": feed_config["tier"],
            "dedup_group": feed_config.get("dedup_group", fid),
            "title": title,
            "url": link,
            "summary": summary or None,
            "publication_date": pub,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "matched_categories": cats,
            "confidence": get_confidence(title, summary, cats, kf),
            "outlet_stance_note": feed_config.get("notes"),
            "editorial_decision": "pending",
            "editorial_notes": None
        })

    return fid, results, status

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    print(f"CanadaScanada RSS Pipeline v2 — {ts}")
    print(f"Per-feed timeout: {FEED_TIMEOUT_SECONDS}s | Global timeout: {GLOBAL_TIMEOUT_SECONDS}s")
    print("=" * 60)

    kf         = load_json(KEYWORD_FILTER_PATH)
    feed_map   = load_json(FEED_MAP_PATH)
    known_urls = load_known_urls()
    existing   = load_existing_queue()

    active = [f for f in feed_map["feeds"] if f.get("active", True)]
    print(f"Active feeds: {len(active)} | Known URLs: {len(known_urls)} | Queue: {len(existing)}")
    print()

    all_new = []

    # Fetch all feeds in parallel — no single feed can block the others
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, fc, kf, known_urls): fc for fc in active}
        try:
            for future in as_completed(futures, timeout=GLOBAL_TIMEOUT_SECONDS):
                fc = futures[future]
                try:
                    fid, items, status_msg = future.result()
                    relevant = [i for i in items if not is_dupe(i["url"], i["title"], known_urls, existing + all_new)]
                    all_new.extend(relevant)
                    print(f"  [{fc.get('priority','?'):6}] {fid}: {status_msg}"
                          + (f" → {len(relevant)} new" if relevant else ""))
                except Exception as e:
                    print(f"  ✗ {fc['feed_id']}: thread error — {e}")
        except FuturesTimeout:
            print(f"\n⚠ Global timeout ({GLOBAL_TIMEOUT_SECONDS}s) reached — some feeds skipped")

    print()
    print(f"New items this run: {len(all_new)}")

    # Sort and write queue
    order = {"high": 0, "medium": 1, "low": 2}
    all_items = existing + all_new
    sorted_items = sorted(all_items, key=lambda x: (order.get(x.get("confidence"), 2),
                                                     x.get("publication_date") or ""), reverse=True)

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    queue = {
        "meta": {
            "schema_version": "2.0.0",
            "schema": "rss-queue",
            "project": "CanadaScanada",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "item_count": len(sorted_items),
            "new_this_run": len(all_new),
        },
        "items": sorted_items
    }
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    h = len([i for i in sorted_items if i.get("confidence") == "high"])
    m = len([i for i in sorted_items if i.get("confidence") == "medium"])
    l = len([i for i in sorted_items if i.get("confidence") == "low"])
    print(f"Queue: {len(sorted_items)} total (high={h} medium={m} low={l})")
    print("Done.")

if __name__ == "__main__":
    main()
