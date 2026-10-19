"""5·6단계: 장비 수집.

- 진행 중인 시즌(2026): ProSettings 목록(현재) + EsportSettings 선수 페이지
  두 출처가 다르면 '최근에 수정된 쪽'을 씀
  (ProSettings 선수 페이지의 dateModified ↔ EsportSettings 사이트 빌드 날짜)
  현재 목록에 없는 선수는 올해 Wayback 보관본에서 가장 최근 장비로 채움
- 끝난 시즌(2023~2025): Wayback Machine에 저장된 ProSettings 목록
  시즌 마지막 대회가 끝난 날 이전 스냅샷을 최신순으로(한 달에 하나, 최대 12개) 보고,
  선수마다 가장 최근 스냅샷의 장비를 씀 → 시즌 마지막으로 사용한 장비
  (그 전 스냅샷이 없으면 같은 해의 그 이후 스냅샷)

입력: scripts/work/rosters/{game}.json
출력: scripts/work/gear/{game}.json
"""

import html
import json
import re
import sys
import urllib.parse
from datetime import date

from common import ROOT, SOURCES_DIR, fetch, log, read_json, write_json
from matching import GearIndex, name_key

ROSTER_DIR = ROOT / "scripts" / "work" / "rosters"
GEAR_DIR = ROOT / "scripts" / "work" / "gear"
CURRENT_SEASON = 2026
FIRST_SEASON = 2023  # 이전 시즌 정보로 채울 때 여기까지 거슬러 올라감
MAX_SNAPSHOTS = 12  # 시즌마다 합쳐 볼 스냅샷 수 (최신 것부터, 한 달에 하나)
CATEGORIES = ["mouse", "keyboard", "monitor", "headset", "mousepad"]
PS_COLUMNS = {"mouse": "mouse", "keyboard": "keyboard", "monitor": "monitor", "headset": "headset", "mousepad": "mousepad"}
ES_ICONS = {"🖱️": "mouse", "🖱": "mouse", "⌨️": "keyboard", "⌨": "keyboard", "🎧": "headset", "🖥️": "monitor", "🖥": "monitor", "🟫": "mousepad"}


def text_of(fragment):
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


# ---------------- ProSettings ----------------

def parse_prosettings_list(page, extra_rows=()):
    """ProSettings 'Pro Settings & Gear List' 표 → [{player, slug, team, gear{}}]
    extra_rows: 페이지가 나중에 불러오는 나머지 행(셀 HTML 목록)"""
    m = re.search(r'<table[^>]*id="pro-list-table"[^>]*>(.*?)</table>', page, re.S)
    if not m:
        m = re.search(r"<table[^>]*>(.*?)</table>", page, re.S)
    if not m:
        return []
    table = m.group(1)
    head = re.search(r"<thead>(.*?)</thead>", table, re.S)
    headers = [text_of(h).lower() for h in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1) if head else table, re.S)]
    body = re.search(r"<tbody>(.*?)</tbody>", table, re.S)
    cell_rows = [re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                 for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1) if body else table, re.S)]
    cell_rows += list(extra_rows)
    rows = []
    for cells in cell_rows:
        if len(cells) < len(headers):
            continue
        record = dict(zip(headers, cells))
        player_cell = record.get("player", "")
        name_m = re.search(r'class="name"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', player_cell, re.S) \
            or re.search(r'<a[^>]*href="([^"]*players/[^"]*)"[^>]*>(.*?)</a>', player_cell, re.S)
        player = text_of(name_m.group(2)) if name_m else text_of(player_cell)
        if not player:
            continue
        href = name_m.group(1) if name_m else ""
        slug_m = re.search(r"/players/([^/]+)/?", href)
        gear = {}
        for col, cat in PS_COLUMNS.items():
            value = text_of(record.get(col, ""))
            if value and value not in ("-", "N/A"):
                gear[cat] = value
        rows.append({
            "player": player,
            "slug": slug_m.group(1) if slug_m else None,
            "team": text_of(record.get("team", "")),
            "gear": gear,
        })
    return rows


def fetch_prosettings_current(url):
    """현재 목록 전체: 페이지에는 처음 100명만 있고 나머지는 pro-list API로 50명씩 불러옴"""
    page = fetch(url, max_age_days=25) or ""
    m = re.search(r"var prosettingsProList = (\{.*?\});", page, re.S)
    extra = []
    if m:
        cfg = json.loads(m.group(1))
        total = int(cfg.get("recordsTotal") or 0)
        start = int(cfg.get("loaded") or 0)
        size = int(cfg.get("pageSize") or 50)
        while start < total:
            q = urllib.parse.urlencode({"game": cfg["game"], "start": start, "length": size})
            data = json.loads(fetch(f"{cfg['endpoint']}?{q}", max_age_days=25) or "{}")
            rows = data.get("data") or []
            if not rows:
                break
            extra += rows
            start += len(rows)
    return parse_prosettings_list(page, extra)


def prosettings_player_date(slug):
    if not slug:
        return None
    page = fetch(f"https://prosettings.net/players/{slug}/", max_age_days=25)
    if not page:
        return None
    m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', page)
    return m.group(1) if m else None


# ---------------- Wayback Machine ----------------

def wayback_snapshots(url, year):
    q = "http://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({
        "url": url.replace("https://", ""), "from": str(year), "to": str(year),
        "output": "json", "filter": "statuscode:200", "fl": "timestamp,original",
    })
    text = fetch(q, max_age_days=None if year < CURRENT_SEASON else 25)
    rows = json.loads(text)[1:] if text and text.strip() else []
    return [(r[0], r[1]) for r in rows]


def pick_snapshots(sources, season, end_date):
    """우선순위 순서의 스냅샷 목록: end_date 이전 것을 최신순으로, 그다음 end_date 이후(그 해) 것을 오래된 순으로."""
    end = (end_date or f"{season}-12-31").replace("-", "")
    candidates = []
    for src in sources:
        for ts, original in wayback_snapshots(src["url"], season):
            day = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
            if src.get("from") and day < src["from"]:
                continue
            if src.get("until") and day > src["until"]:
                continue
            candidates.append((ts, original))
    candidates = sorted(set(candidates))
    before = [c for c in candidates if c[0][:8] <= end]
    after = [c for c in candidates if c[0][:8] > end]
    # 같은 달에 여러 개면 하나만 (요청 수 줄이기)
    picked, months = [], set()
    for c in list(reversed(before)) + after:
        if c[0][:6] not in months:
            months.add(c[0][:6])
            picked.append(c)
    return picked


# ---------------- EsportSettings ----------------

def es_build_date(page):
    m = re.search(r"es-build:[a-z\-]*?(\d{4})(\d{2})(\d{2})", page or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def parse_es_game(page):
    rows = []
    for m in re.finditer(r'<div class="pro-card" data-id="([^"]+)"(.*?)(?=<div class="pro-card" |</main>)', page, re.S):
        pid, block = m.group(1), m.group(2)
        name_m = re.search(r'class="pc-name"[^>]*>(.*?)</a>', block, re.S)
        team_m = re.search(r"🏆 Team</span><span class=\"v\">(.*?)</span>", block, re.S)
        rows.append({"id": pid, "player": text_of(name_m.group(1)) if name_m else pid,
                     "team": text_of(team_m.group(1)) if team_m else ""})
    return rows


def parse_es_player(page):
    gear = {}
    for block in re.findall(r'<div class="gear-load">(.*?)</a>\s*</div>', page, re.S):
        icon_m = re.search(r'<span class="gl-ico">(.*?)</span>', block, re.S)
        name_m = re.search(r'<span class="gl-name">(.*?)</span>', block, re.S)
        if not icon_m or not name_m:
            continue
        cat = ES_ICONS.get(text_of(icon_m.group(1)))
        if cat and cat not in gear:
            gear[cat] = text_of(name_m.group(1))
    return gear


# ---------------- 수집 ----------------

def roster_names(player):
    return [player["name"], player["link"].split(" (")[0]]


def team_name(season_data, team_id):
    for t in season_data["teams"]:
        if t["id"] == team_id:
            return t["name"]
    return ""


def fill_from_snapshots(season_data, snaps, players, sources, max_age_days=None, from_season=None):
    """아직 장비가 없는 로스터 선수를 스냅샷 목록(우선순위 순)에서 채움. 선수마다 처음 찾은(가장 최근) 스냅샷을 씀.
    from_season: 이전 시즌 보관본에서 가져온 경우 그 시즌 연도 (화면에 'OOOO 시즌 정보'로 표시)"""
    remaining = [p for p in season_data["players"] if p["id"] not in players]
    for ts, original in snaps:
        if not remaining:
            break
        page = fetch(f"https://web.archive.org/web/{ts}id_/{original}", max_age_days=max_age_days)
        rows = parse_prosettings_list(page or "")
        index = GearIndex(rows)
        snap_date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
        snap_url = f"https://web.archive.org/web/{ts}/{original}"
        found = 0
        still = []
        for p in remaining:
            row = index.find(roster_names(p), team_name(season_data, p["team"]))
            if row and row["gear"]:
                players[p["id"]] = {
                    "gear": {cat: {"raw": raw, "site": "prosettings"} for cat, raw in row["gear"].items()},
                    "sources": [snap_url],
                    "updatedAt": snap_date,
                    "fromSeason": from_season,
                }
                found += 1
            else:
                still.append(p)
        remaining = still
        if found:
            label = "ProSettings.net (Wayback Machine" + (f", {from_season} 시즌 정보)" if from_season else ")")
            sources.append({"site": label, "url": snap_url, "date": snap_date, "fromSeason": from_season})
        log(f"    스냅샷 {snap_date}: 목록 {len(rows)}명, 새로 확인 {found}명")


def collect_past(game, cfg, season, season_data):
    end_date = max([c["endDate"] or c["startDate"] or "" for c in season_data["competitions"]] or [""]) or None
    snaps = pick_snapshots(cfg["prosettings"], season, end_date)[:MAX_SNAPSHOTS]
    players, sources = {}, []
    if snaps:
        fill_from_snapshots(season_data, snaps, players, sources)
    log(f"  {season}: 시즌 종료 {end_date}, 스냅샷 {len(snaps)}개 → 장비 확인 {len(players)}/{len(season_data['players'])}명")
    return {"sources": sources, "players": players}


def collect_current(game, cfg, season_data):
    ps_url = cfg["prosettings"][-1]["url"]
    ps_rows = fetch_prosettings_current(ps_url)
    ps_index = GearIndex(ps_rows)
    today = date.today().isoformat()
    sources = [{"site": "ProSettings.net", "url": ps_url, "date": today}]

    es_index = None
    es_date = None
    es_game = cfg.get("esportsettings")
    if es_game:
        es_url = f"https://www.esportsettings.com/game/{es_game}/"
        es_page = fetch(es_url, max_age_days=25) or ""
        es_date = es_build_date(es_page)
        es_index = GearIndex(parse_es_game(es_page))
        sources.append({"site": "EsportSettings", "url": es_url, "date": es_date or today})

    players = {}
    conflicts = 0
    for p in season_data["players"]:
        team = team_name(season_data, p["team"])
        ps_row = ps_index.find(roster_names(p), team)
        es_row = es_index.find(roster_names(p), team) if es_index else None

        ps_gear = ps_row["gear"] if ps_row else {}
        es_gear = {}
        if es_row:
            es_page = fetch(f"https://www.esportsettings.com/player/{es_row['id']}/", max_age_days=25)
            es_gear = parse_es_player(es_page or "")
        if not ps_gear and not es_gear:
            continue

        ps_date = None
        primary, secondary = ("prosettings", "esportsettings")
        differs = any(ps_gear.get(c) and es_gear.get(c) and name_key(ps_gear[c]) != name_key(es_gear[c]) for c in CATEGORIES)
        if ps_gear and es_gear and differs:
            conflicts += 1
            ps_date = prosettings_player_date(ps_row.get("slug"))
            # 최근에 수정된 쪽 우선 (날짜가 같거나 모르면 ProSettings)
            if es_date and (not ps_date or es_date > ps_date):
                primary, secondary = ("esportsettings", "prosettings")
        elif es_gear and not ps_gear:
            primary, secondary = ("esportsettings", "prosettings")

        by_site = {"prosettings": ps_gear, "esportsettings": es_gear}
        gear = {}
        for cat in CATEGORIES:
            for site in (primary, secondary):
                if by_site[site].get(cat):
                    gear[cat] = {"raw": by_site[site][cat], "site": site}
                    break
        src = []
        if ps_row and ps_row.get("slug"):
            src.append(f"https://prosettings.net/players/{ps_row['slug']}/")
        if es_row:
            src.append(f"https://www.esportsettings.com/player/{es_row['id']}/")
        players[p["id"]] = {
            "gear": gear,
            "sources": src,
            "updatedAt": (es_date if primary == "esportsettings" else ps_date) or None,
        }
    live = len(players)
    # 올해 목록에 있다가 빠진 선수(무소속 전환 등)는 올해 Wayback 보관본에서 가장 최근 장비로 채움
    snaps = pick_snapshots(cfg["prosettings"], CURRENT_SEASON, None)[:MAX_SNAPSHOTS]
    fill_from_snapshots(season_data, snaps, players, sources, max_age_days=25)
    log(f"  {CURRENT_SEASON}: ProSettings {len(ps_rows)}명" + (", EsportSettings 사용" if es_index else "")
        + f" → 현재 목록 {live}명 + 올해 보관본 {len(players) - live}명 = 장비 확인 {len(players)}/{len(season_data['players'])}명"
        + f" (출처끼리 다름 {conflicts}명)")
    return {"sources": sources, "players": players}


def fill_previous_seasons(cfg, season, season_data, result):
    """이 시즌에 장비를 못 찾은 선수 → 바로 앞 시즌부터 FIRST_SEASON까지 거슬러 올라가며 가장 최근 장비로 채움
    (예: 2026 로스터 선수인데 2023 정보밖에 없으면 2023 장비, fromSeason=2023)"""
    before = len(result["players"])
    for year in range(season - 1, FIRST_SEASON - 1, -1):
        if len(result["players"]) >= len(season_data["players"]):
            break
        snaps = pick_snapshots(cfg["prosettings"], year, None)[:MAX_SNAPSHOTS]
        if snaps:
            fill_from_snapshots(season_data, snaps, result["players"], result["sources"], from_season=year)
    added = len(result["players"]) - before
    if added:
        log(f"  {season}: 이전 시즌 정보로 {added}명 추가 → 장비 확인 {len(result['players'])}/{len(season_data['players'])}명")


def main(games=None):
    cfg_all = read_json(SOURCES_DIR / "gear_sources.json")
    for game in games or [g for g in cfg_all if not g.startswith("_")]:
        rosters = read_json(ROSTER_DIR / f"{game}.json")
        if not rosters:
            log(f"[장비] {game}: 로스터 없음 → fetch_liquipedia.py 먼저 실행")
            continue
        log(f"[장비] {game}")
        out = {"game": game, "collectedAt": date.today().isoformat(), "seasons": {}}
        for season_str, season_data in rosters["seasons"].items():
            season = int(season_str)
            if season >= CURRENT_SEASON:
                result = collect_current(game, cfg_all[game], season_data)
            else:
                result = collect_past(game, cfg_all[game], season, season_data)
            fill_previous_seasons(cfg_all[game], season, season_data, result)
            out["seasons"][season_str] = result
        write_json(GEAR_DIR / f"{game}.json", out)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
