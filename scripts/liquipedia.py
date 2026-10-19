"""Liquipedia MediaWiki API 도우미.

약관(https://liquipedia.net/api-terms-of-use) 준수:
- 요청은 2초에 1번 이하 (common.MIN_INTERVAL)
- User-Agent에 프로젝트 이름과 연락처
- gzip 요청
- action=parse는 쓰지 않고 action=query로 위키 원문(wikitext)만 받음
"""

import urllib.parse

from common import fetch_json

API = "https://liquipedia.net/{wiki}/api.php"


def api(wiki, max_age_days=25, **params):
    params = {"format": "json", "formatversion": "2", **params}
    url = API.format(wiki=wiki) + "?" + urllib.parse.urlencode(params)
    return fetch_json(url, max_age_days=max_age_days)


def allpages(wiki, prefix, max_age_days=25):
    """prefix로 시작하는 문서 제목 목록"""
    titles = []
    cont = {}
    while True:
        data = api(wiki, max_age_days=max_age_days, action="query", list="allpages",
                   apprefix=prefix, apnamespace=0, aplimit=500, apfilterredir="nonredirects", **cont)
        titles += [p["title"] for p in data["query"]["allpages"]]
        if "continue" not in data:
            return titles
        cont = {"apcontinue": data["continue"]["apcontinue"]}


def wikitexts(wiki, titles, max_age_days=25):
    """{제목: 위키 원문} — 한 번에 최대 50개씩 요청. 없는 문서는 빠짐. 넘겨주기(redirect)는 따라감."""
    result = {}
    titles = list(dict.fromkeys(titles))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        data = api(wiki, max_age_days=max_age_days, action="query", prop="revisions",
                   rvprop="content|timestamp", rvslots="main", redirects="1", titles="|".join(chunk))
        q = data.get("query", {})
        back = {}
        for r in q.get("normalized", []) + q.get("redirects", []):
            back[r["to"]] = back.get(r["from"], r["from"])
        for page in q.get("pages", []):
            if page.get("missing") or not page.get("revisions"):
                continue
            rev = page["revisions"][0]
            text = rev["slots"]["main"]["content"]
            original = back.get(page["title"], page["title"])
            result[original] = text
            result[page["title"]] = text
    return result
