"""2·3단계: 로스터 + 장비 → 사이트가 읽는 data/{game}/{season}.json 생성.

- 제품명 정리(products.py): brand / model / color / edition
- data/index.json: 검색, 팀, 선수 화면용 요약 (모든 게임 · 시즌의 선수 목록)
"""

from datetime import date

from common import DATA_DIR, ROOT, log, read_json, write_json
from products import ProductNormalizer

ROSTER_DIR = ROOT / "scripts" / "work" / "rosters"
GEAR_DIR = ROOT / "scripts" / "work" / "gear"
GAMES = ["lol", "valorant", "pubg", "cs2", "overwatch"]
CATEGORIES = ["mouse", "keyboard", "monitor", "headset", "mousepad"]


def build():
    normalizer = ProductNormalizer()
    today = date.today().isoformat()

    # 1) 모든 장비 이름을 먼저 정리 (기본 제품 묶기는 전체 데이터를 보고 판단)
    loaded = {}
    all_items = []
    for game in GAMES:
        rosters = read_json(ROSTER_DIR / f"{game}.json")
        gear = read_json(GEAR_DIR / f"{game}.json", {"seasons": {}})
        if not rosters:
            log(f"[빌드] {game}: 로스터 없음, 건너뜀")
            continue
        loaded[game] = (rosters, gear)
        for season_gear in gear["seasons"].values():
            for pg in season_gear["players"].values():
                for cat, item in pg["gear"].items():
                    item["norm"] = normalizer.normalize(item["raw"])
                    if item["norm"]:
                        item["norm"]["category"] = cat
                        all_items.append(item["norm"])
    normalizer.finalize(all_items)

    # 2) 게임 · 시즌별 파일
    index = {"updatedAt": today, "players": [], "teams": [], "seasons": {}}
    for game, (rosters, gear) in loaded.items():
        versions = rosters.get("gameVersion", {})
        for season_str, season in rosters["seasons"].items():
            sg = gear["seasons"].get(season_str, {"sources": [], "players": {}})
            team_names = {t["id"]: t["name"] for t in season["teams"]}
            players = []
            with_gear = 0
            for p in season["players"]:
                pg = sg["players"].get(p["id"])
                gear_out = {cat: None for cat in CATEGORIES}
                if pg:
                    for cat, item in pg["gear"].items():
                        n = item.get("norm")
                        if n:
                            gear_out[cat] = {"brand": n["brand"], "model": n["model"], "color": n["color"],
                                             "edition": n["edition"], "rawName": n["rawName"], "site": item["site"]}
                if any(gear_out.values()):
                    with_gear += 1
                players.append({
                    "id": p["id"],
                    "name": p["name"],
                    "team": p["team"],
                    "role": p.get("role"),
                    "liquipedia": p["liquipedia"],
                    "gear": gear_out,
                    "gearSources": pg["sources"] if pg else [],
                    "gearUpdatedAt": pg.get("updatedAt") if pg else None,
                    # 이 시즌 정보가 없어 이전 시즌 장비를 쓴 경우 그 시즌 연도 (없으면 null)
                    "gearFromSeason": pg.get("fromSeason") if pg else None,
                    "gearCheckedAt": (pg.get("updatedAt") if pg.get("fromSeason") or int(season_str) < 2026
                                      else gear.get("collectedAt")) if pg else None,
                })
                index["players"].append({
                    "id": p["id"], "name": p["name"], "game": game, "season": int(season_str),
                    "team": p["team"], "teamName": team_names.get(p["team"], p["team"]),
                    "hasGear": any(gear_out.values()),
                })

            competitions = [{
                "id": c["id"], "name": c["name"], "startDate": c["startDate"], "endDate": c["endDate"],
                "gameVersion": versions.get(season_str), "liquipedia": c["liquipedia"],
            } for c in season["competitions"]]

            out = {
                "game": game,
                "season": int(season_str),
                "gameVersion": versions.get(season_str),
                "updatedAt": today,
                "rosterSource": f"https://liquipedia.net/{rosters['wiki']}/",
                "gearSources": sg["sources"],
                "competitions": competitions,
                "teams": season["teams"],
                "players": players,
            }
            write_json(DATA_DIR / game / f"{season_str}.json", out)
            for t in season["teams"]:
                index["teams"].append({"id": t["id"], "name": t["name"], "game": game, "season": int(season_str)})
            index["seasons"].setdefault(game, {})[season_str] = {"players": len(players), "withGear": with_gear,
                                                                  "teams": len(season["teams"])}
            log(f"[빌드] {game} {season_str}: 선수 {len(players)}명 (장비 확인 {with_gear}명), 팀 {len(season['teams'])}개")

    write_json(DATA_DIR / "index.json", index)


if __name__ == "__main__":
    build()
