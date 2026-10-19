"""7단계: 데이터 검증.

1) 표본 대조: 게임마다 장비가 있는 선수를 무작위로 골라, 저장된 장비 이름이
   실제 출처 페이지(ProSettings 선수 페이지 / EsportSettings 선수 페이지 / Wayback 보관본)에 있는지 확인
2) 제품명 점검: 같은 브랜드에서 이름이 비슷해 따로 세어지는 모델(묶어야 할 수도 있는 것) 목록
3) 확인 비율: 게임 · 시즌별 로스터 대비 장비 확인 인원

사용법: py scripts/verify_data.py [표본 수(기본 5)]
"""

import html
import random
import re
import sys
from collections import defaultdict

from common import DATA_DIR, fetch, log, read_json

GAMES = ["lol", "valorant", "pubg", "cs2", "overwatch"]


def page_text(url):
    if "web.archive.org/web/" in url:
        url = re.sub(r"/web/(\d+)/", r"/web/\1id_/", url)
    page = fetch(url, max_age_days=None) or ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page))).lower()


def sample_check(sample_size):
    rng = random.Random(42)
    total = ok = 0
    for game in GAMES:
        for path in sorted((DATA_DIR / game).glob("*.json")):
            data = read_json(path)
            players = [p for p in data["players"] if any(p["gear"].values()) and p["gearSources"]]
            for p in rng.sample(players, min(sample_size, len(players))):
                texts = [page_text(u) for u in p["gearSources"]]
                for cat, item in p["gear"].items():
                    if not item:
                        continue
                    total += 1
                    raw = re.sub(r"\s+", " ", item["rawName"]).lower()
                    if any(raw in t for t in texts):
                        ok += 1
                    else:
                        log(f"  [불일치?] {game} {data['season']} {p['name']} {cat}: '{item['rawName']}' 출처 {p['gearSources']}")
    log(f"표본 대조: {ok}/{total} 항목이 출처 페이지에 그대로 있음 ({ok / max(total, 1) * 100:.1f}%)")


def similar_models():
    models = defaultdict(lambda: defaultdict(int))
    for game in GAMES:
        for path in (DATA_DIR / game).glob("*.json"):
            for p in read_json(path)["players"]:
                for item in p["gear"].values():
                    if item:
                        models[item["brand"]][item["model"]] += 1
    log("이름이 겹치는 모델 (버전 차이인지 확인 필요):")
    shown = 0
    for brand, ms in sorted(models.items()):
        names = sorted(ms)
        for a in names:
            for b in names:
                if a != b and b.lower().startswith(a.lower() + " ") and shown < 60:
                    log(f"  {brand}: '{a}' ({ms[a]}) ↔ '{b}' ({ms[b]})")
                    shown += 1


def coverage():
    index = read_json(DATA_DIR / "index.json")
    log("장비 확인 비율:")
    for game, seasons in index["seasons"].items():
        row = ", ".join(f"{s}: {v['withGear']}/{v['players']}" for s, v in sorted(seasons.items()))
        log(f"  {game}: {row}")


if __name__ == "__main__":
    sample_check(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
    similar_models()
    coverage()
