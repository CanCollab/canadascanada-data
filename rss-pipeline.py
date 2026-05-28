#!/usr/bin/env python3
"""
CanadaScanada RSS Pipeline
==========================
Zero-LLM feed fetcher and relevance filter.
Reads feed-map.json and keyword-filter.json.
Writes filtered items to submissions/rss-queue.json.

Run manually:
    python3 rss-pipeline.py

Run via GitHub Actions (see rss-pipeline.yml):
    Triggered on cron schedule. Commits rss-queue.json if new items found.

No API keys required. No LLM calls. Pure HTTP + XML parsing.

Requirements:
    pip install feedparser requests

Output:
    submissions/rss-queue.json — items for human review
    Each item that passes the filter and is not a duplicate appears here.
    Review the queue, then paste approved URLs into a Claude conversation
    with the extraction skill loaded to generate EVT + R JSON files.
"""

import json
import hashlib
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from difflib import SequenceMatcher

try:
    import feedparser
    import requests
except ImportError:
    print("Install dependencies: pip install feedparser requests")
    sys.exit(1)

# ── Paths (adjust if running from a different working directory) ──────────────

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
    """Return set of all URLs already in the reference index."""
    try:
        data = load_json(refs_index_path)
        return {r["url"].strip().rstrip("/") for r in data.get("references", []) if r.get("url")}
    except FileNotFoundError:
        return set()

def load_existing_queue(queue_path):
    """Return existing queue items to avoid adding duplicates within the queue."""
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

    # Exclusion check first
    if matches_any(combined, keyword_filter["exclusions"]["terms"]):
        return False, None, "excluded"

    # Must match at least one actor term
    if not matches_any(combined, keyword_filter["actors_any"]["terms"]):
        return False, None, "no_actor_match"

    # Must match at least one category
    matched_categories = []
    for cat_id, cat_data in keyword_filter["categories"].items():
        if matches_any(combined, cat_data["terms"]):
            matched_categories.append(cat_id)

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
    """Normalize URL for dedup — strip tracking params, trailing slashes."""
    url = url.strip().rstrip("/")
    # Strip common tracking params
    for param in ["?utm_source", "&utm_", "?ref=", "#"]:
        if param in url:
            url = url[:url.index(param)]
    return url

def title_similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def is_duplicate(item_url, item_title, known_urls, existing_queue_items, dedup_group, dedup_window_hours=48):
    """
    Check three dedup levels:
    1. URL exact match against reference index (already in data)
    2. URL exact match against current queue (already queued)
    3. Title similarity within same dedup_group in last N hours (same story, different outlet)
    """
    norm_url = url_fingerprint(item_url)

    # Level 1: already in reference index
    if norm_url in known_urls:
        return True, "already_in_refs"

    # Level 2: already in current queue
    for q in existing_queue_items:
        if url_fingerprint(q.get("url", "")) == norm_url:
            return True, "already_in_queue"

    # Level 3: similar title in same dedup group, recent
    cutoff = datetime.now(timezone.utc) - timedelta(hours=dedup_window_hours)
    for q in existing_queue_items:
        if q.get("dedup_group") != dedup_group:
            continue
        q_time_str = q.get("fetched_at", "")
        try:
            q_time = datetime.fromisoformat(q_time_str)
            if q_time.tzinfo is None:
                q_time = q_time.replace(tzinfo=timezone.utc)
            if q_time < cutoff:
                continue
        except (ValueError, TypeError):
            continue
        if title_similarity(item_title, q.get("title", "")) > 0.75:
            return True, f"similar_title_in_group_{dedup_group}"

    return False, None

# ── Feed fetching ─────────────────────────────────────────────────────────────

def fetch_feed(feed_config, keyword_filter, known_urls, existing_queue):
    results = []
    url = feed_config["url"]
    feed_id = feed_config["feed_id"]

    try:
        # feedparser handles both RSS and Atom
        parsed = feedparser.parse(url, request_headers={"User-Agent": "CanadaScanada/1.0 (+https://canadascanada.ca)"})
        entries = parsed.get("entries", [])
    except Exception as e:
        print(f"  ✗ {feed_id}: fetch error — {e}")
        return results

    print(f"  {feed_id}: {len(entries)} entries fetched")

    for entry in entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        # Strip HTML tags from summary
        summary_clean = re.sub(r"<[^>]+>", " ", summary).strip()

        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass

        if not title or not link:
            continue

        # Relevance filter
        relevant, matched_cats, reason = is_relevant(title, summary_clean, keyword_filter)
        if not relevant:
            continue

        # Dedup check
        dupe, dupe_reason = is_duplicate(
            link, title, known_urls, existing_queue + results,
            feed_config.get("dedup_group", feed_id),
            dedup_window_hours=48
        )
        if dupe:
            continue

        item_confidence = confidence(title, summary_clean, matched_cats, keyword_filter)

        item = {
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
        }
        results.append(item)

    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"CanadaScanada RSS Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
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

    for feed_config in active_feeds:
        priority = feed_config.get("priority", "medium")
        print(f"Fetching [{priority}] {feed_config['feed_id']} ({feed_config['outlet_name']})")
        items = fetch_feed(feed_config, keyword_filter, known_urls, existing_queue + all_new_items)
        if items:
            print(f"  → {len(items)} new relevant items")
        all_new_items.extend(items)

    print()
    print(f"Total new items this run: {len(all_new_items)}")

    if not all_new_items:
        print("Queue unchanged.")
        return

    # Sort: high confidence first, then by publication date
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    all_items = existing_queue + all_new_items
    all_items.sort(key=lambda x: (
        confidence_order.get(x.get("confidence", "low"), 2),
        x.get("publication_date") or "",
    ), reverse=False)
    # Reverse so newest high-confidence items are first
    high_med = [i for i in all_items if i.get("confidence") in ("high", "medium")]
    low_conf = [i for i in all_items if i.get("confidence") == "low"]
    sorted_items = high_med + low_conf

    queue = {
        "meta": {
            "schema_version": "2.0.0",
            "schema": "rss-queue",
            "project": "CanadaScanada",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "item_count": len(sorted_items),
            "note": "Review this queue. For each item you want to add to the timeline: paste the URL into a Claude conversation with the extraction skill loaded. Set editorial_decision to 'approved' or 'rejected' to track your review. Approved items generate EVT + R JSON files via the extraction skill."
        },
        "items": sorted_items
    }

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Queue written to {QUEUE_PATH}")
    print(f"  High confidence: {len([i for i in sorted_items if i.get('confidence') == 'high'])}")
    print(f"  Medium confidence: {len([i for i in sorted_items if i.get('confidence') == 'medium'])}")
    print(f"  Low confidence: {len([i for i in sorted_items if i.get('confidence') == 'low'])}")

if __name__ == "__main__":
    main()
