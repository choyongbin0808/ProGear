"""4단계: Liquipedia에서 시즌별 대회 → 참가 팀 → 로스터를 모음.

출력: scripts/work/rosters/{game}.json
시즌 규칙: 대회 시작일(sdate) 연도 = 시즌 (2025년 12월 시작 → 2025 시즌)
한 시즌에 팀을 옮긴 선수는 시즌 마지막 대회의 소속팀 하나로만 기록
"""

import re
import sys
from datetime import date

from common import SOURCES_DIR, ROOT, log, read_json, slugify, write_json
from liquipedia import wikitexts
from wikitext import find_templates, plain, split_params

WORK_DIR = ROOT / "scripts" / "work" / "rosters"
GAME_SEASONS = {
    "lol": [2023, 2024, 2025, 2026],
    "valorant": [2023, 2024, 2025, 2026],
    "pubg": [2023, 2024, 2025, 2026],
    "cs2": [2023, 2024, 2025, 2026],
    "overwatch": [2024, 2025, 2026],
}
LOL_ROLES = ["Top", "Jungle", "Mid", "Bot", "Support"]
ROLE_NAMES = {
    "top": "Top", "jgl": "Jungle", "jg": "Jungle", "jungle": "Jungle", "mid": "Mid", "bot": "Bot", "adc": "Bot",
    "sup": "Support", "support": "Support", "dps": "DPS", "tank": "Tank",
}


def parse_date(value):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", value or "")
    if not m:
        m2 = re.search(r"(\d{4})-(\d{2})", value or "")
        if not m2:
            return None
        return f"{m2.group(1)}-{m2.group(2)}-01"
    y, mo, d = m.groups()
    mo = mo if mo != "00" else "01"
    d = d if d != "00" else "01"
    return f"{y}-{mo}-{d}"


def parse_infobox(text):
    boxes = find_templates(text, "Infobox league")
    if not boxes:
        return {}
    _, named = split_params(boxes[0])
    return {
        "name": plain(named.get("name", "")),
        "sdate": parse_date(named.get("sdate") or named.get("date")),
        "edate": parse_date(named.get("edate") or named.get("date")),
    }


def role_name(value):
    if not value:
        return None
    first = value.split(",")[0].strip().lower()
    return ROLE_NAMES.get(first)


def parse_teamcards(text, game):
    teams = []
    for card in find_templates(text, "TeamCard"):
        if card.lower().startswith(("{{teamcard columns", "{{teamcardtoggle")):
            continue
        _, named = split_params(card)
        team = plain(named.get("team", ""))
        if not team:
            continue
        players = []
        for n in range(1, 11):
            name = plain(named.get(f"p{n}", ""))
            if not name:
                continue
            link = plain(named.get(f"p{n}link", "")) or name
            role = role_name(named.get(f"pos{n}"))
            if game == "lol" and not role and n <= 5:
                role = LOL_ROLES[n - 1]
            players.append({"name": name, "link": link, "role": role})
        teams.append({"team": team, "players": players})
    return teams


def parse_team_participants(text, game):
    teams = []
    for block in find_templates(text, "TeamParticipants"):
        for opp in find_templates(block[2:], "Opponent"):
            positional, named = split_params(opp)
            team = plain(positional[0]) if positional else ""
            if not team:
                continue
            players = []
            for person in find_templates(named.get("players", ""), "Person"):
                pos, pnamed = split_params(person)
                if pnamed.get("type") == "staff" or pnamed.get("status") in ("former", "sub", "inactive"):
                    continue
                name = plain(pos[0]) if pos else ""
                if not name:
                    continue
                link = plain(pnamed.get("link", "")).replace("_", " ") or name
                players.append({"name": name, "link": link, "role": role_name(pnamed.get("role"))})
            teams.append({"team": team, "players": players})
    return teams


def collect_game(game, config):
    titles = [t for season_titles in config["competitions"].values() for t in season_titles]
    texts = wikitexts(config["wiki"], titles)
    seasons_allowed = GAME_SEASONS[game]

    competitions = []
    for listed_season, season_titles in config["competitions"].items():
        for title in season_titles:
            text = texts.get(title)
            if text is None:
                log(f"  [없음] {config['wiki']}: {title}")
                continue
            info = parse_infobox(text)
            teams = parse_teamcards(text, game) + parse_team_participants(text, game)
            sdate = info.get("sdate")
            season = int(sdate[:4]) if sdate else int(listed_season)
            competitions.append({
                "id": slugify(title),
                "title": title,
                "name": info.get("name") or title,
                "startDate": sdate,
                "endDate": info.get("edate"),
                "season": season,
                "liquipedia": f"https://liquipedia.net/{config['wiki']}/" + title.replace(" ", "_"),
                "teams": teams,
            })
            log(f"  {title}: {len(teams)}팀, {sum(len(t['players']) for t in teams)}명 (시작 {sdate}, {season} 시즌)")

    result = {"game": game, "wiki": config["wiki"], "collectedAt": date.today().isoformat(), "seasons": {}}
    for season in seasons_allowed:
        comps = sorted([c for c in competitions if c["season"] == season],
                       key=lambda c: (c["endDate"] or c["startDate"] or "", c["startDate"] or ""))
        teams = {}
        players = {}
        for comp in comps:
            for entry in comp["teams"]:
                team_id = slugify(entry["team"])
                teams.setdefault(team_id, {"id": team_id, "name": entry["team"], "competitions": []})
                if comp["id"] not in teams[team_id]["competitions"]:
                    teams[team_id]["competitions"].append(comp["id"])
                for p in entry["players"]:
                    pid = slugify(p["link"])
                    prev = players.get(pid, {})
                    players[pid] = {
                        "id": pid,
                        "name": p["name"],
                        "link": p["link"],
                        "team": team_id,  # 나중 대회가 덮어씀 → 시즌 마지막 소속팀
                        "role": p["role"] or prev.get("role"),
                        "liquipedia": f"https://liquipedia.net/{config['wiki']}/" + p["link"].replace(" ", "_"),
                        "lastCompetition": comp["id"],
                    }
        used_teams = {p["team"] for p in players.values()}
        result["seasons"][str(season)] = {
            "competitions": [{k: v for k, v in c.items() if k != "teams"} for c in comps],
            "teams": [t for t in teams.values() if t["id"] in used_teams],
            "players": sorted(players.values(), key=lambda p: p["name"].lower()),
        }
        log(f"  → {season} 시즌: 대회 {len(comps)}개, 팀 {len(used_teams)}개, 선수 {len(players)}명")
    return result


def main(games=None):
    config = read_json(SOURCES_DIR / "competitions.json")
    for game in games or GAME_SEASONS:
        log(f"[Liquipedia] {game}")
        result = collect_game(game, config[game])
        result["gameVersion"] = config[game].get("gameVersion", {})
        write_json(WORK_DIR / f"{game}.json", result)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
