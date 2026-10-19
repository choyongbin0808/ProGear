"""5-1단계: 추가 장비 출처로 빈칸 채우기 (fetch_gear.py 다음에 실행).

ProSettings / EsportSettings에 없는 선수가 많은 게임(PUBG, Overwatch)을 보충함.
- EsportsMice (esportsmice.com): 게임별 선수 목록 → 선수 페이지의 현재 마우스와 연도별 마우스 기록
  마우스만 있음. robots.txt에서 수집 허용(Allow: /) 확인함
- 기존 출처를 덮어쓰지 않음: 그 시즌 장비가 아예 없는 선수는 새로 넣고,
  그 시즌 장비가 있는데 마우스만 빠진 선수는 마우스만 채움
- 진행 중인 시즌은 현재 마우스, 끝난 시즌은 기록에서 그 해를 포함하는 기간 중 가장 늦게 시작한 마우스
  (시즌에 마지막으로 쓴 장비) → 기록이 없으면 채우지 않음

입력·출력: scripts/work/gear/{game}.json (fetch_gear.py 결과에 덧붙임)
"""

import re
import sys
from datetime import date

from common import ROOT, fetch, log, read_json, write_json
from fetch_gear import CURRENT_SEASON, roster_names, team_name, text_of
from matching import GearIndex

ROSTER_DIR = ROOT / "scripts" / "work" / "rosters"
GEAR_DIR = ROOT / "scripts" / "work" / "gear"
SITE = "esportsmice"
BASE = "https://esportsmice.com"
# 게임 id → (EsportsMice 게임 주소, 선수 페이지의 Game 칸 이름)
EM_GAMES = {"pubg": ("pubg", "PUBG"), "overwatch": ("overwatch-2", "Overwatch 2")}


def parse_em_game(page):
    """게임 페이지의 'All … Pro Players' 표 → [{slug, player, team}]"""
    rows = []
    for slug, name, team in re.findall(
            r'<tr><td><a href="/players/([^"]+)">([^<]+)</a></td><td>([^<]*)</td>', page):
        rows.append({"slug": slug, "player": text_of(name), "team": text_of(team)})
    return rows


def parse_em_player(page):
    """선수 페이지 → {game, mouse, history[(mouse, 시작 연도, 끝 연도)]}"""
    def table_value(label):
        m = re.search(rf"<tr><th>{label}</th><td>(.*?)</td></tr>", page, re.S)
        return text_of(m.group(1)) if m else ""

    history = []
    hist = re.search(r"<caption>Complete mouse history for.*?<tbody>(.*?)</tbody>", page, re.S)
    for mouse, period in re.findall(r"<tr><td>(.*?)</td><td>(.*?)</td>", hist.group(1) if hist else "", re.S):
        years = re.findall(r"\d{4}|Present", text_of(period))
        if not years:
            continue
        start = int(years[0]) if years[0] != "Present" else CURRENT_SEASON
        end = CURRENT_SEASON if years[-1] == "Present" else int(years[-1])
        history.append((text_of(mouse), start, end))
    mouse = table_value("Mouse")
    return {"game": table_value("Game"), "mouse": "" if mouse in ("-", "—") else mouse, "history": history}


def mouse_for_season(info, season):
    if season >= CURRENT_SEASON:
        return info["mouse"]
    covering = [h for h in info["history"] if h[1] <= season <= h[2]]
    return max(covering, key=lambda h: h[1])[0] if covering else ""


def add_source(result, url, season):
    if not any(s["url"] == url for s in result["sources"]):
        result["sources"].append({"site": "EsportsMice", "url": url,
                                  "date": date.today().isoformat() if season >= CURRENT_SEASON else None})


def main(games=None):
    for game in games or list(EM_GAMES):
        if game not in EM_GAMES:
            continue
        rosters = read_json(ROSTER_DIR / f"{game}.json")
        gear = read_json(GEAR_DIR / f"{game}.json")
        if not rosters or not gear:
            log(f"[추가 장비] {game}: 로스터 / 장비 결과 없음 → fetch_liquipedia.py, fetch_gear.py 먼저 실행")
            continue
        em_slug, em_game = EM_GAMES[game]
        list_url = f"{BASE}/games/{em_slug}"
        index = GearIndex(parse_em_game(fetch(list_url, max_age_days=25) or ""))
        log(f"[추가 장비] {game}: EsportsMice")
        for season_str, season_data in rosters["seasons"].items():
            season = int(season_str)
            result = gear["seasons"].setdefault(season_str, {"sources": [], "players": {}})
            added = filled = 0
            for p in season_data["players"]:
                current = result["players"].get(p["id"])
                if current and (current["gear"].get("mouse") or current.get("fromSeason")):
                    continue  # 이미 마우스가 있거나, 이전 시즌 장비로 채운 선수 (시즌을 섞지 않음)
                row = index.find(roster_names(p), team_name(season_data, p["team"]))
                if not row:
                    continue
                url = f"{BASE}/players/{row['slug']}"
                info = parse_em_player(fetch(url, max_age_days=25) or "")
                if info["game"] != em_game:
                    continue  # 다른 게임 선수 페이지 (이름만 같음)
                mouse = mouse_for_season(info, season)
                if not mouse:
                    continue
                item = {"raw": mouse, "site": SITE}
                if current:
                    current["gear"]["mouse"] = item
                    current["sources"].append(url)
                    filled += 1
                else:
                    result["players"][p["id"]] = {"gear": {"mouse": item}, "sources": [url],
                                                  "updatedAt": None, "fromSeason": None}
                    added += 1
                add_source(result, list_url, season)
            log(f"  {season}: 새 선수 {added}명, 마우스 보충 {filled}명"
                f" → 장비 확인 {len(result['players'])}/{len(season_data['players'])}명")
        write_json(GEAR_DIR / f"{game}.json", gear)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
