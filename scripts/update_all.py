"""한 달에 한 번 실행: 로스터 수집 → 장비 수집 → data/*.json 빌드.

사용법 (ProGear 폴더에서):
    py scripts/update_all.py            # 모든 게임
    py scripts/update_all.py valorant   # 한 게임만

- Liquipedia / 장비 사이트 응답은 scripts/.cache에 25일 동안 저장돼서
  같은 달에 다시 실행하면 거의 요청을 보내지 않아요.
- 끝난 시즌(2023~2025)의 Wayback Machine 보관본은 한 번 받으면 계속 재사용해요.
- Liquipedia 약관에 따라 User-Agent에 연락처를 넣으려면 실행 전에
  PROGEAR_CONTACT 환경 변수를 지정하세요. (PowerShell: $env:PROGEAR_CONTACT = "내 이메일")
"""

import sys
import time

import build_data
import fetch_extra_gear
import fetch_gear
import fetch_liquipedia
import upload_supabase
from common import log


def main():
    games = sys.argv[1:] or None
    started = time.time()
    log("== 1/3 Liquipedia 로스터 ==")
    fetch_liquipedia.main(games)
    log("== 2/3 장비 (ProSettings · EsportSettings · Wayback Machine) ==")
    fetch_gear.main(games)
    log("== 2-1 추가 장비 (EsportsMice: PUBG · Overwatch 마우스) ==")
    fetch_extra_gear.main(games)
    log("== 3/3 data/*.json 빌드 ==")
    build_data.build()
    log("== 4 Supabase 올리기 (환경 변수가 있을 때만) ==")
    upload_supabase.main()
    log(f"완료 ({(time.time() - started) / 60:.1f}분)")


if __name__ == "__main__":
    main()
