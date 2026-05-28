#!/usr/bin/env python3
"""
CanadaScanada RSS Pipeline
==========================
Zero-LLM feed fetcher and relevance filter.
Reads feed-map.json and keyword-filter.json.
Writes filtered items to submissions/rss-queue.json.

Requirements:
    pip install feedparser requests

Output:
    submissions/rss-queue.json — items for human review
"""

import json
import hashlib
import re
import sys
import socket
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

FEED_TIMEOUT_SECONDS = 15   # kill any feed that takes longer than this
MAX_ITEMS_PER_FEED = 30     # cap items per feed to avoid huge runs

ROOT = Path(__file__).parent
FEED_MAP_PATH = ROOT / "feed-map.json"
KEYWORD_FILTER_PATH = ROOT / "keyword-filter.json"
REFS_INDEX_PATH = ROOT / "references/index.json"
QUEUE_PATH = ROOT / "submissions/rss-queue.json"

# ── Load config ───────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_known_urls(refs_index_path):
    try:
        data = load_json(refs_index_path)
        return {r["url"].strip().rstrip("/") for r in data.get("references", []) if r.get("url")}
    except FileNotFoundError:
        return set()

def load_existing_queue(queue_path):
    try:
        data = load_json(queue_path)
        return data.get("items", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# ── Filtering ─────────────────────────────────────────────────────────────────

def normalize(text):
    return (text or "").lower()

def matches_any(text, terms):
    t = normalize(text)
    return any(normalize(term) in t for term in terms)

def is_relevant(title, description, keyword_filter):
    combined = f"{title} {description}"
    if matches_any(combined, keyword_filter["exclusions"]["terms"]):
        return False, None, "excluded"
    if not matches_any(combined, keyword_filter["actors_any"]["terms"]):
        return False, None, "no_actor_match"
    matched_categories = [
        cat_id for cat_id, cat_data in keyword_filter["categories"].items()
        if matches_any(combined, cat_data["terms"])
    ]
    if not matched_categories:
        return False, None, "no_category_match"
    return True, matched_categories, "pass"

def confidence(title, description, matched_categories, keyword_filter):
    combined = f"{title} {description}"
    actor_matches = sum(
        1 for t in keyword_filter["actors_any"]["terms"]
        if normalize(t) in normalize(combined)
    )
    if actor_matches >= 2 and len(matched_categories) >= 2:
        return "high"
    elif actor_matches >= 1 and len(matched_categories) >= 1:
        return "medium"
    return "low"

# ── Deduplication ─────────────────────────────────────────────────────────────

def url_fingerprint(url):
    url = url.strip().rstrip("/")
    for param in ["?utm_source", "&utm_", "?ref=", "#"]:
        if param in url:
            url = url[:url.index(param)]
    return url

def title_similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def is_duplicate(item_url, item_title, known_urls, existing_queue_items, dedup_group, dedup_window_hours=48):
    norm_url = url_fingerprint(item_url)
    if norm_url in known_urls:
        return True, "already_in_refs"
    for q in existing_queue_items:
        if url_fingerprint(q.get("url", "")) == norm_url:
            return True, "already_in_queue"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=dedup_window_hours)
    for q in existing_queue_items:
        if q.get("dedup_group") != dedup_group:
            continue
        try:
            q_time = datetime.fromisoformat(q.get("fetched_at", ""))
            if q_time.tzinfo is None:
                q_time = q_time.replace(tzinfo=timezone.utc)
            if q_time < cutoff:
                continue
        except (ValueError, TypeError):
            continue
        if title_similarity(item_title, q.get("title", "")) > 0.75:
            return True, f"similar_title_in_group_{dedup_group}"
    return False, None

# ── Feed fetching — with timeout ──────────────────────────────────────────────

def fetch_with_timeout(url, timeout=FEED_TIMEOUT_SECONDS):
    """
    Use requests to fetch the feed content with a hard timeout,
    then pass the content to feedparser. This avoids feedparser's
    default of waiting forever on a slow connection.
    """
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "CanadaScanada/1.0 (+https://canadascanada.ca)"},
            allow_redirects=True
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Feed timed out after {timeout}s")
    except requests.exceptions.SSLError as e:
        raise ConnectionError(f"SSL error: {e}")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Connection failed: {e}")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"HTTP {resp.status_code}: {e}")

def fetch_feed(feed_config, keyword_filter, known_urls, existing_queue):
    results = []
    url = feed_config["url"]
    feed_id = feed_config["feed_id"]

    try:
        parsed = fetch_with_timeout(url, timeout=FEED_TIMEOUT_SECONDS)
        entries = parsed.get("entries", [])
    except TimeoutError as e:
        print(f"  ✗ {feed_id}: TIMEOUT — {e} (skipping)")
        return results
    except ConnectionError as e:
        print(f"  ✗ {feed_id}: CONNECTION ERROR — {e} (skipping)")
        return results
    except Exception as e:
        print(f"  ✗ {feed_id}: ERROR — {e} (skipping)")
        return results

    # Cap items per feed to avoid huge runs
    entries = entries[:MAX_ITEMS_PER_FEED]
    print(f"  {feed_id}: {len(entries)} entries fetched")

    for entry in entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        summary_clean = re.sub(r"<[^>]+>", " ", summary).strip()

        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass

        if not title or not link:
            continue

        relevant, matched_cats, reason = is_relevant(title, summary_clean, keyword_filter)
        if not relevant:
            continue

        dupe, _ = is_duplicate(
            link, title, known_urls, existing_queue + results,
            feed_config.get("dedup_group", feed_id)
        )
        if dupe:
            continue

        item_confidence = confidence(title, summary_clean, matched_cats, keyword_filter)

        results.append({
            "queue_id": f"RSS-{hashlib.md5(link.encode()).hexdigest()[:8].upper()}",
            "feed_id": feed_id,
            "outlet_id": feed_config["outlet_id"],
            "outlet_name": feed_config["outlet_name"],
            "tier": feed_config["tier"],
            "dedup_group": feed_config.get("dedup_group", feed_id),
            "title": title,
            "url": link,
            "summary": summary_clean[:500] if summary_clean else None,
            "publication_date": pub_date,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "matched_categories": matched_cats,
            "confidence": item_confidence,
            "outlet_stance_note": feed_config.get("notes"),
            "editorial_decision": "pending",
            "editorial_notes": None
        })

    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"CanadaScanada RSS Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Feed timeout: {FEED_TIMEOUT_SECONDS}s per feed")
    print("=" * 60)

    feed_map = load_json(FEED_MAP_PATH)
    keyword_filter = load_json(KEYWORD_FILTER_PATH)
    known_urls = load_known_urls(REFS_INDEX_PATH)
    existing_queue = load_existing_queue(QUEUE_PATH)

    print(f"Known URLs in reference index: {len(known_urls)}")
    print(f"Items currently in queue: {len(existing_queue)}")
    print()

    all_new_items = []
    active_feeds = [f for f in feed_map["feeds"] if f.get("active", True)]
    print(f"Active feeds: {len(active_feeds)}")
    print()

    for i, feed_config in enumerate(active_feeds, 1):
        priority = feed_config.get("priority", "medium")
        print(f"[{i}/{len(active_feeds)}] [{priority}] {feed_config['feed_id']}")
        items = fetch_feed(feed_config, keyword_filter, known_urls, existing_queue + all_new_items)
        if items:
            print(f"  → {len(items)} new relevant items")
        all_new_items.extend(items)

    print()
    print(f"Total new items this run: {len(all_new_items)}")

    if not all_new_items and not existing_queue:
        # Write empty queue so the file exists
        QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        queue = {
            "meta": {
                "schema_version": "2.0.0",
                "schema": "rss-queue",
                "project": "CanadaScanada",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "item_count": 0,
            },
            "items": []
        }
        with open(QUEUE_PATH, "w") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("No new items. Empty queue written.")
        return

    # Sort: high confidence first
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    all_items = existing_queue + all_new_items
    high_med = sorted(
        [i for i in all_items if i.get("confidence") in ("high", "medium")],
        key=lambda x: (confidence_order.get(x.get("confidence"), 2), x.get("publication_date") or ""),
        reverse=True
    )
    low_conf = [i for i in all_items if i.get("confidence") == "low"]
    sorted_items = high_med + low_conf

    queue = {
        "meta": {
            "schema_version": "2.0.0",
            "schema": "rss-queue",
            "project": "CanadaScanada",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "item_count": len(sorted_items),
            "new_this_run": len(all_new_items),
            "note": "Review queue. Paste approved URLs into Claude with extraction skill loaded to generate EVT + R JSON files."
        },
        "items": sorted_items
    }

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Queue written: {len(sorted_items)} total items")
    print(f"  High: {len([i for i in sorted_items if i.get('confidence') == 'high'])}")
    print(f"  Medium: {len([i for i in sorted_items if i.get('confidence') == 'medium'])}")
    print(f"  Low: {len([i for i in sorted_items if i.get('confidence') == 'low'])}")

if __name__ == "__main__":
    main()
