"""수집 스크립트 공통 도우미: HTTP 요청(속도 제한, gzip, 캐시), 경로, JSON 저장."""

import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
SOURCES_DIR = Path(__file__).resolve().parent / "sources"

# Liquipedia 약관: User-Agent에 프로젝트 이름과 연락처를 넣어야 함
# 연락처는 환경 변수 PROGEAR_CONTACT로 지정 (예: 이메일)
CONTACT = os.environ.get("PROGEAR_CONTACT", "school project")
USER_AGENT = f"ProGear/1.0 ({CONTACT})"

# 사이트별 최소 요청 간격(초)
MIN_INTERVAL = {
    "liquipedia.net": 2.1,
    "prosettings.net": 2.0,
    "www.esportsettings.com": 2.0,
    "esportsmice.com": 2.0,
    "web.archive.org": 4.0,
    "archive.org": 4.0,
}
_last_request = {}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def log(*args):
    print(*args, flush=True)


def _wait(host, interval=None):
    interval = interval if interval is not None else MIN_INTERVAL.get(host, 2.0)
    last = _last_request.get(host)
    if last is not None:
        delay = interval - (time.time() - last)
        if delay > 0:
            time.sleep(delay)
    _last_request[host] = time.time()


def _cache_path(url):
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()
    host = urllib.parse.urlparse(url).netloc.replace(":", "_")
    return CACHE_DIR / host / f"{key}.cache"


def fetch(url, max_age_days=25, retries=4, interval=None):
    """URL 내용을 문자열로 돌려줌. 캐시가 max_age_days 이내면 다시 요청하지 않음.
    없는 페이지(404)는 None."""
    path = _cache_path(url)
    if max_age_days is not None and path.exists():
        age = (time.time() - path.stat().st_mtime) / 86400
        if age <= max_age_days:
            text = path.read_text(encoding="utf-8")
            return None if text == "\0404" else text

    host = urllib.parse.urlparse(url).netloc
    backoff = 10
    for attempt in range(retries + 1):
        _wait(host, interval)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = res.read()
                if res.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                text = body.decode("utf-8", "replace")
                break
        except urllib.error.HTTPError as err:
            if err.code == 404:
                text = "\0404"
                break
            if err.code in (429, 500, 502, 503, 504) and attempt < retries:
                log(f"  {err.code} → {backoff}초 후 다시 시도: {url}")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt < retries:
                log(f"  연결 오류({err}) → {backoff}초 후 다시 시도")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None if text == "\0404" else text


def fetch_json(url, **kwargs):
    text = fetch(url, **kwargs)
    return json.loads(text) if text else None


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text):
    import re
    import unicodedata
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "unknown"
