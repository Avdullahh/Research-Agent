"""Fetch and extract candidate sources for a research run.

Reads .tmp/<run_id>/candidates.json, writes one JSON per source to
.tmp/<run_id>/fetched/. Deterministic execution only -- no judgment about
source quality happens here. That is the agent's job (see
workflows/research_report.md, stage 3).

Usage:
    python tools/fetch_sources.py --run-id 20260802-153000-eu-ai-act
    python tools/fetch_sources.py --run-id <id> --force        # re-fetch everything
    python tools/fetch_sources.py --run-id <id> --no-robots    # ignore robots.txt
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura
from dateutil import parser as date_parser

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 "
    "ResearchAssistant/1.0 (+respects robots.txt)"
)

TIMEOUT = 25
MAX_RETRIES = 2
PER_DOMAIN_DELAY = 1.5  # seconds between requests to the same domain
MAX_TEXT_CHARS = 200_000


def slug_for(url):
    """Stable, filesystem-safe filename for a URL."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    host = urlparse(url).netloc.replace(":", "_") or "unknown"
    return f"{host}-{digest}.json"


def normalize_date(value):
    """Best-effort ISO-8601 date string, or None. Never raises."""
    if not value:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return date_parser.parse(str(value), fuzzy=True).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        return None


class RobotsCache:
    """Per-domain robots.txt lookups. Failure to fetch robots.txt means allow."""

    def __init__(self, session, enabled=True):
        self.session = session
        self.enabled = enabled
        self._cache = {}

    def allows(self, url):
        if not self.enabled:
            return True
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._cache:
            parser = urllib.robotparser.RobotFileParser()
            try:
                resp = self.session.get(
                    f"{base}/robots.txt", timeout=10, headers={"User-Agent": USER_AGENT}
                )
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    parser.parse([])  # no robots.txt -> allow all
            except requests.RequestException:
                parser.parse([])  # unreachable robots.txt -> allow, don't block research
            self._cache[base] = parser
        try:
            return self._cache[base].can_fetch(USER_AGENT, url)
        except Exception:
            return True


class DomainThrottle:
    """Keeps at least PER_DOMAIN_DELAY seconds between hits on one domain."""

    def __init__(self, delay=PER_DOMAIN_DELAY):
        self.delay = delay
        self._last = {}

    def wait(self, url):
        host = urlparse(url).netloc
        last = self._last.get(host)
        if last is not None:
            elapsed = time.monotonic() - last
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last[host] = time.monotonic()


def blank_record(url, title, why_selected, tier_guess):
    return {
        "url": url,
        "candidate_title": title,
        "why_selected": why_selected,
        "proximity_tier_guess": tier_guess,
        "final_url": None,
        "status": "failed",
        "http_status": None,
        "title": None,
        "byline": None,
        "published_date": None,
        "modified_date": None,
        "publisher_domain": urlparse(url).netloc or None,
        "sitename": None,
        "description": None,
        "text": "",
        "word_count": 0,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }


def http_get(session, url, throttle):
    """GET with retry/backoff. Returns (response, error_string)."""
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        throttle.wait(url)
        try:
            resp = session.get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": USER_AGENT},
                allow_redirects=True,
            )
            # Retry transient server-side and rate-limit responses only.
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                last_error = f"HTTP {resp.status_code}"
                time.sleep(2 ** attempt * 2)
                continue
            return resp, None
        except requests.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt * 2)
    return None, last_error


def extract(record, html, url):
    """Populate record from HTML via trafilatura. Mutates and returns record."""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
        url=url,
    )
    if text:
        record["text"] = text[:MAX_TEXT_CHARS]
        record["word_count"] = len(text.split())

    try:
        meta = trafilatura.extract_metadata(html, default_url=url)
    except Exception:
        meta = None

    if meta is not None:
        as_dict = meta.as_dict() if hasattr(meta, "as_dict") else {}
        record["title"] = as_dict.get("title") or record["candidate_title"]
        author = as_dict.get("author")
        record["byline"] = author or None
        record["published_date"] = normalize_date(as_dict.get("date"))
        record["sitename"] = as_dict.get("sitename") or None
        record["description"] = as_dict.get("description") or None
        if as_dict.get("hostname"):
            record["publisher_domain"] = as_dict["hostname"]
    else:
        record["title"] = record["candidate_title"]

    return record


def fetch_one(session, candidate, robots, throttle):
    url = candidate.get("url", "")
    record = blank_record(
        url,
        candidate.get("title"),
        candidate.get("why_selected"),
        candidate.get("proximity_tier_guess"),
    )

    if not url or not urlparse(url).scheme in ("http", "https"):
        record["error"] = "invalid or missing URL"
        return record

    if not robots.allows(url):
        record["status"] = "blocked_by_robots"
        record["error"] = "disallowed by robots.txt"
        return record

    resp, error = http_get(session, url, throttle)
    if resp is None:
        record["error"] = error or "request failed"
        return record

    record["http_status"] = resp.status_code
    record["final_url"] = resp.url
    record["modified_date"] = normalize_date(resp.headers.get("Last-Modified"))

    if resp.status_code >= 400:
        record["error"] = f"HTTP {resp.status_code}"
        return record

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type.lower() and "xml" not in content_type.lower():
        record["status"] = "unsupported_content_type"
        record["error"] = f"Content-Type: {content_type or 'unknown'}"
        return record

    try:
        extract(record, resp.text, resp.url)
    except Exception as exc:  # extraction must never kill the run
        record["error"] = f"extraction failed: {type(exc).__name__}: {exc}"
        return record

    if record["word_count"] == 0:
        record["status"] = "empty"
        record["error"] = (
            "no main content extracted (JS-rendered, paywalled, or bot-walled) -- "
            "see workflows/research_report.md edge cases"
        )
    else:
        record["status"] = "ok"

    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-id", required=True, help="run directory under .tmp/")
    ap.add_argument("--force", action="store_true", help="re-fetch already-fetched URLs")
    ap.add_argument("--no-robots", action="store_true", help="skip robots.txt checks")
    args = ap.parse_args()

    run_dir = TMP_DIR / args.run_id
    candidates_path = run_dir / "candidates.json"
    out_dir = run_dir / "fetched"

    if not candidates_path.exists():
        sys.exit(f"ERROR: {candidates_path} not found. Stage 1 writes this file.")

    try:
        candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {candidates_path} is not valid JSON: {exc}")

    if not isinstance(candidates, list) or not candidates:
        sys.exit(f"ERROR: {candidates_path} must be a non-empty JSON array.")

    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    robots = RobotsCache(session, enabled=not args.no_robots)
    throttle = DomainThrottle()

    counts = {}
    skipped = 0

    for i, candidate in enumerate(candidates, 1):
        url = candidate.get("url", "")
        out_path = out_dir / slug_for(url)

        if out_path.exists() and not args.force:
            skipped += 1
            print(f"[{i}/{len(candidates)}] skip (cached)  {url}")
            continue

        record = fetch_one(session, candidate, robots, throttle)
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        status = record["status"]
        counts[status] = counts.get(status, 0) + 1
        detail = f" -- {record['error']}" if record["error"] else ""
        words = f" ({record['word_count']} words)" if status == "ok" else ""
        print(f"[{i}/{len(candidates)}] {status}{words}  {url}{detail}")

    print("\n--- summary ---")
    print(f"candidates: {len(candidates)}  |  skipped (cached): {skipped}")
    for status, n in sorted(counts.items()):
        print(f"  {status}: {n}")
    print(f"output: {out_dir}")

    ok = counts.get("ok", 0)
    if ok == 0 and skipped == 0:
        print("\nWARNING: nothing fetched successfully. Check connectivity before vetting.")


if __name__ == "__main__":
    main()
