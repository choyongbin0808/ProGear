"""4단계: data/*.json → Supabase 테이블에 올리기 (build_data.py 다음에 실행).

먼저 scripts/supabase/schema.sql을 Supabase SQL Editor에서 한 번 실행해 테이블을 만들어 두어야 함.

필요한 환경 변수 (PowerShell 예시)
    $env:SUPABASE_URL = "https://<프로젝트 id>.supabase.co"
    $env:SUPABASE_SECRET_KEY = "<secret 키 또는 service_role 키>"   # 절대 사이트 코드나 저장소에 넣지 않음

사용법 (ProGear 폴더에서): py scripts/upload_supabase.py
"""

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import DATA_DIR, log

GAMES = ["lol", "valorant", "pubg", "cs2", "overwatch"]


def settings():
    # 복사할 때 딸려 온 공백 / 줄바꿈 / 따옴표 제거
    url = os.environ.get("SUPABASE_URL", "").strip().strip("\"'").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY", "").strip().strip("\"'")
    return (url, key) if url and key else (None, None)


def jwt_payload(key):
    try:
        part = key.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except (IndexError, ValueError):
        return None


def key_problem(url, key):
    """키 형식이 잘못됐으면 이유를 돌려줌 (키 값 자체는 화면에 보여 주지 않음)"""
    project = re.match(r"https://([a-z0-9]+)\.supabase\.co$", url)
    if not project:
        return f"SUPABASE_URL 형식이 이상해요: {url} (https://<프로젝트 id>.supabase.co 형식이어야 함)"
    if "<" in key or ">" in key or " " in key:
        return "SUPABASE_SECRET_KEY에 '<secret 키>' 같은 예시 글자나 공백이 남아 있어요. 실제 키로 바꿔 주세요"
    if "•" in key or "*" in key:
        return "가려진 키(••••)가 복사됐어요. 대시보드에서 Reveal을 누르거나 복사 버튼으로 다시 복사해 주세요"
    if key.startswith("sb_publishable_"):
        return "publishable 키를 넣었어요. 이 키는 읽기 전용이라 올릴 수 없어요. secret 키(sb_secret_…)를 넣어 주세요"
    if key.startswith("sb_"):
        return None if key.startswith("sb_secret_") else f"알 수 없는 키 형식이에요 ({key[:10]}…)"
    payload = jwt_payload(key)
    if payload is None:
        return f"키 형식이 아니에요 (길이 {len(key)}자). sb_secret_… 또는 eyJ…로 시작하는 키를 통째로 복사해 주세요"
    if payload.get("role") != "service_role":
        return f"'{payload.get('role')}' 키를 넣었어요. service_role 키(또는 sb_secret_…)를 넣어 주세요"
    if payload.get("ref") and payload["ref"] != project.group(1):
        return f"다른 프로젝트의 키예요 (키: {payload['ref']}, URL: {project.group(1)})"
    return None


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
    problem = key_problem(base, key)
    if problem:
        log(f"[Supabase] 올리지 않음: {problem}")
        return False
    # 올리기 전에 키 / 테이블을 한 번 확인 (실패 이유를 알기 쉽게)
    try:
        request(f"{base}/rest/v1/season_data?select=game&limit=1", key)
    except RuntimeError as err:
        text = str(err)
        if text.startswith("Supabase 401"):
            log(f"[Supabase] 키가 맞지 않아요 (형식: {key[:10]}…, 길이 {len(key)}자). 이 프로젝트의 secret 키를 "
                "대시보드 Project Settings → API Keys에서 복사 버튼으로 다시 복사해 주세요."
                " 키를 폐기(Revoke)했거나 다른 프로젝트 키일 수도 있어요")
        elif "season_data" in text and ("does not exist" in text or "404" in text or "PGRST205" in text):
            log("[Supabase] season_data 테이블이 없어요. scripts/supabase/schema.sql을 SQL Editor에서 먼저 실행해 주세요")
        else:
            log(f"[Supabase] 연결 확인 실패: {text}")
        return False
    now =datetime.now(timezone.utc).isoformat()
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
