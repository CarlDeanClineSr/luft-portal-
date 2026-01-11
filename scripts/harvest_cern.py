#!/usr/bin/env python3
"""
LUFT Portal — CERN/Physics Paper Harvester (resilient)

Purpose:
- Harvest physics papers relevant to LUFT topics from multiple sources:
  1) CERN Document Server (RSS and JSON 'recjson' endpoints)
  2) CERN Open Data (Invenio REST API)
  3) arXiv (Atom API) as a fallback if CERN blocks automated requests

Features:
- Polite headers (User-Agent, From), configurable via env HARVEST_CONTACT
- Backoff/retry on 403/429/503
- Keyword-based relevance filtering
- Deduplication across sources
- Timestamped output + latest.json for easy consumption

Outputs:
- data/papers/cern/cern_harvest_YYYYMMDD_HHMMSS.json
- data/papers/cern/latest.json
"""

import os
import time
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import requests
import feedparser


# -----------------------------
# Configuration
# -----------------------------
CONTACT_EMAIL = os.getenv("HARVEST_CONTACT", "contact@luft-portal.local")
USER_AGENT = "LUFT-Portal/2026 (+https://github.com/CarlDeanClineSr/luft-portal-)"

# Queries to run (override via HARVEST_QUERIES env as CSV)
DEFAULT_QUERIES = [
    "plasma physics",
    "space physics",
    "magnetohydrodynamics",
    "cosmology",
    "gravitational waves",
    "unified field theory",
]

ENV_QUERIES = os.getenv("HARVEST_QUERIES", "")
QUERIES = (
    [q.strip() for q in ENV_QUERIES.split(",") if q.strip()]
    if ENV_QUERIES
    else DEFAULT_QUERIES
)

# LUFT-relevant keywords
LUFT_KEYWORDS = [
    "plasma",
    "magnetohydrodynamic",
    "mhd",
    "solar wind",
    "cosmic ray",
    "magnetic field",
    "coherence",
    "oscillation",
    "cosmology",
    "dark energy",
    "gravitational wave",
    "unified field",
    "field theory",
    "plasma instability",
    "coronal mass ejection",
    "cme",
    "space weather",
    "heliosphere",
    "particle physics",
    "high energy physics",
]

# Output locations
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "papers" / "cern"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Helper functions
# -----------------------------
def safe_string(value: Any) -> str:
    """Extract string from a value that may be a dict with 'value'/'summary' key or a string."""
    if value is None:
        return ""
    if isinstance(value, dict):
        # CERN APIs may return nested dicts like {"value": "text", "language": "en"}
        return str(value.get("value", "") or value.get("summary", "") or "")
    return str(value) if value else ""


# -----------------------------
# HTTP helpers
# -----------------------------
def polite_get(
    url: str,
    params: Dict[str, Any] | None = None,
    accept: str = "*/*",
    tries: int = 3,
    backoff_seconds: int = 2,
    timeout: int = 25,
) -> requests.Response | None:
    """HTTP GET with polite headers and exponential backoff."""
    for i in range(tries):
        try:
            headers = {
                "User-Agent": USER_AGENT,
                "From": CONTACT_EMAIL,
                "Accept": accept,
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close",
            }
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (403, 429, 503):
                # backoff and retry
                sleep_for = backoff_seconds * (i + 1)
                time.sleep(sleep_for)
                continue
            # other codes: return None
            return None
        except requests.RequestException:
            time.sleep(backoff_seconds * (i + 1))
    return None


# -----------------------------
# Harvesters
# -----------------------------
def harvest_cds_rss(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Harvest from CERN Document Server RSS (more likely to allow bots)."""
    url = "https://cds.cern.ch/rss"
    params = {"ln": "en", "p": query, "rg": min(max_results, 100)}
    resp = polite_get(url, params=params, accept="application/rss+xml")
    if not resp:
        return []
    feed = feedparser.parse(resp.text)
    results: List[Dict[str, Any]] = []
    for e in feed.entries:
        results.append(
            {
                "source": "CDS_RSS",
                "id": (e.get("id") or "").split("/")[-1],
                "title": (e.get("title") or "").replace("\n", " ").strip(),
                "authors": [a.get("name") for a in e.get("authors", [])] if hasattr(e, "authors") else [],
                "summary": (e.get("summary") or "").replace("\n", " ").strip(),
                "published": e.get("published") or e.get("updated"),
                "categories": [t.get("term") for t in e.get("tags", [])] if hasattr(e, "tags") else [],
                "link": e.get("link"),
                "query": query,
            }
        )
    return results


def harvest_cds_json(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Harvest from CERN Document Server JSON 'recjson' endpoint."""
    url = "https://cds.cern.ch/search"
    params = {"ln": "en", "p": query, "rg": min(max_results, 100), "of": "recjson"}
    resp = polite_get(url, params=params, accept="application/json")
    if not resp:
        return []
    results: List[Dict[str, Any]] = []
    try:
        data = resp.json()
    except Exception:
        return results
    items = data if isinstance(data, list) else data.get("records", [])
    for r in items:
        title = r.get("title")
        if isinstance(title, dict):
            title = title.get("title")
        recid = r.get("recid") or r.get("record_id")
        results.append(
            {
                "source": "CDS_JSON",
                "id": str(recid) if recid else "",
                "title": (title or "").replace("\n", " ").strip(),
                "authors": [],
                "summary": safe_string(r.get("abstract") or r.get("summary")).replace("\n", " ").strip(),
                "published": r.get("publication_date") or r.get("date"),
                "categories": [],
                "link": f"https://cds.cern.ch/record/{recid}" if recid else None,
                "query": query,
            }
        )
    return results


def harvest_cern_opendata(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Harvest from CERN Open Data API."""
    url = "https://opendata.cern.ch/api/records/"
    params = {"q": query, "size": min(max_results, 50)}
    resp = polite_get(url, params=params, accept="application/json")
    if not resp:
        return []
    results: List[Dict[str, Any]] = []
    try:
        data = resp.json()
    except Exception:
        return results
    hits = data.get("hits", {}).get("hits", [])
    for h in hits:
        md = h.get("metadata", {}) or {}
        rid = h.get("id")
        results.append(
            {
                "source": "CERN_OPEN_DATA",
                "id": str(rid or ""),
                "title": safe_string(md.get("title")).replace("\n", " ").strip(),
                "authors": md.get("authors") or [],
                "summary": safe_string(md.get("abstract") or md.get("description")).replace("\n", " ").strip(),
                "published": md.get("publication_date") or md.get("date"),
                "categories": md.get("keywords") or [],
                "link": md.get("url") or md.get("doi") or (f"https://opendata.cern.ch/record/{rid}" if rid else None),
                "query": query,
            }
        )
    return results


def harvest_arxiv(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Harvest from arXiv Atom API as a fallback."""
    url = "http://export.arxiv.org/api/query"
    params = {"search_query": f"all:{query}", "start": 0, "max_results": min(max_results, 50)}
    resp = polite_get(url, params=params, accept="application/atom+xml")
    if not resp:
        return []
    feed = feedparser.parse(resp.text)
    results: List[Dict[str, Any]] = []
    for e in feed.entries:
        results.append(
            {
                "source": "arXiv",
                "id": e.get("id") or "",
                "title": (e.get("title") or "").replace("\n", " ").strip(),
                "authors": [a.get("name") for a in e.get("authors", [])],
                "summary": (e.get("summary") or "").replace("\n", " ").strip(),
                "published": e.get("published") or e.get("updated"),
                "categories": [t.get("term") for t in e.get("tags", [])] if hasattr(e, "tags") else [],
                "link": e.get("id"),
                "query": query,
            }
        )
    return results


# -----------------------------
# Relevance & saving
# -----------------------------
def is_luft_relevant(paper: Dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("summary", "")),
            " ".join([str(c) for c in paper.get("categories", [])]),
        ]
    ).lower()
    return any(k.lower() in text for k in LUFT_KEYWORDS)


def dedup(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by normalized (title + link) or id if present."""
    seen: Dict[str, Dict[str, Any]] = {}
    for r in items:
        key = (r.get("id") or "") + "|" + (r.get("title") or "") + "|" + (r.get("link") or "")
        key = key.strip().lower()
        if key and key not in seen:
            seen[key] = r
    return list(seen.values())


def save_results(papers: List[Dict[str, Any]]) -> Path:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    payload = {
        "timestamp": ts,
        "harvest_date": now.isoformat(),
        "total_papers": len(papers),
        "papers": papers,
        "queries": QUERIES,
    }
    out_file = OUT_DIR / f"cern_harvest_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    latest = OUT_DIR / "latest.json"
    with open(latest, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(papers)} papers to {out_file}")
    print(f"Updated {latest}")
    return out_file


# -----------------------------
# Main
# -----------------------------
def main() -> int:
    print("=" * 60)
    print("LUFT Portal — CERN/Physics Paper Harvester (resilient)")
    print("=" * 60)
    print(f"Contact: {CONTACT_EMAIL}")
    print(f"Queries: {', '.join(QUERIES)}")
    print("Note: CERN endpoints may block bots; using polite headers and fallbacks.\n")

    all_results: List[Dict[str, Any]] = []
    for q in QUERIES:
        print(f"Query: {q}")
        # Try CDS RSS first
        rss = harvest_cds_rss(q)
        print(f"  CDS_RSS: {len(rss)}")
        all_results.extend(rss)

        # Then CDS JSON
        recjson = harvest_cds_json(q)
        print(f"  CDS_JSON: {len(recjson)}")
        all_results.extend(recjson)

        # CERN Open Data
        cod = harvest_cern_opendata(q)
        print(f"  CERN_OPEN_DATA: {len(cod)}")
        all_results.extend(cod)

        # arXiv fallback
        ax = harvest_arxiv(q)
        print(f"  arXiv: {len(ax)}")
        all_results.extend(ax)

        time.sleep(2)  # politeness gap between queries

    print(f"\nRaw total results: {len(all_results)}")
    deduped = dedup(all_results)
    print(f"Deduped total: {len(deduped)}")

    relevant = [p for p in deduped if is_luft_relevant(p)]
    print(f"LUFT-relevant: {len(relevant)}")

    out_file = save_results(relevant)

    # Print sample
    for i, p in enumerate(relevant[:5], 1):
        print(f"\n[{i}] {p.get('title', 'No title')}")
        auth = p.get("authors") or []
        if isinstance(auth, list):
            auth = ", ".join(auth[:4])
        print(f"    Authors: {auth or '--'}")
        print(f"    Source: {p.get('source')}")
        print(f"    Link:   {p.get('link', '--')}")

    print("\n✅ Harvest complete.")
    print(f"📄 Output: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
