"""4단계: data/*.json → Supabase 테이블에 올리기 (build_data.py 다음에 실행).

먼저 scripts/supabase/schema.sql을 Supabase SQL Editor에서 한 번 실행해 테이블을 만들어 두어야 함.

필요한 환경 변수 (PowerShell 예시)
    $env:SUPABASE_URL = "https://<프로젝트 id>.supabase.co"
    $env:SUPABASE_SECRET_KEY = "<secret 키 또는 service_role 키>"   # 절대 사이트 코드나 저장소에 넣지 않음

사용법 (ProGear 폴더에서): py scripts/upload_supabase.py
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import DATA_DIR, log

GAMES = ["lol", "valorant", "pubg", "cs2", "overwatch"]


def settings():
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    return (url, key) if url and key else (None, None)


def request(url, key, method="GET", body=None, prefer=None):
    headers = {"apikey": key, "Content-Type": "application/json"}
    # 예전 형식 키(JWT)는 Authorization에도 넣음. 새 형식(sb_secret_…)은 apikey만 씀
    if not key.startswith("sb_"):
        headers["Authorization"] = f"Bearer {key}"
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            text = res.read().decode("utf-8")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"Supabase {err.code}: {err.read().decode('utf-8', 'replace')[:500]}") from None


def upsert(base, key, table, row, conflict):
    request(f"{base}/rest/v1/{table}?on_conflict={conflict}", key, "POST", [row],
            prefer="resolution=merge-duplicates,return=minimal")


def main():
    base, key = settings()
    if not base:
        log("[Supabase] SUPABASE_URL / SUPABASE_SECRET_KEY 환경 변수가 없어서 건너뜀")
        return False
    now = datetime.now(timezone.utc).isoformat()
    count = 0
    for game in GAMES:
        for path in sorted((DATA_DIR / game).glob("*.json")):
            season = int(path.stem)
            data = json.loads(path.read_text(encoding="utf-8"))
            upsert(base, key, "season_data", {"game": game, "season": season, "data": data,
                                              "updated_at": now}, "game,season")
            count += 1
            log(f"[Supabase] season_data {game} {season} 올림")
    index = json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8"))
    upsert(base, key, "site_index", {"id": "main", "data": index, "updated_at": now}, "id")
    log("[Supabase] site_index 올림")

    # 올라간 행 수 확인
    rows = request(f"{base}/rest/v1/season_data?select=game,season", key) or []
    log(f"[Supabase] 완료: 시즌 파일 {count}개 올림, 테이블에 {len(rows)}개 있음")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
