"""선수 / 팀 이름 맞추기 (같은 게임 안에서만 비교해서 다른 게임 선수와 섞이지 않게 함)."""

import re
import unicodedata

TEAM_STOPWORDS = {"esports", "esport", "gaming", "team", "club", "clan", "gc", "academy", "the"}


def name_key(name):
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", text.lower())


def team_tokens(name):
    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii").lower()
    tokens = set(re.findall(r"[a-z0-9]+", text)) - TEAM_STOPWORDS
    return tokens or set(re.findall(r"[a-z0-9]+", text))


def same_team(a, b):
    if not a or not b:
        return False
    ka, kb = name_key(a), name_key(b)
    if ka and (ka == kb or ka in kb or kb in ka):
        return True
    return bool(team_tokens(a) & team_tokens(b))


class GearIndex:
    """출처 목록(선수 이름 + 팀)에서 로스터 선수를 찾음"""

    def __init__(self, rows):
        self.by_key = {}
        for row in rows:
            self.by_key.setdefault(name_key(row["player"]), []).append(row)

    def find(self, names, team_name):
        for name in names:
            candidates = self.by_key.get(name_key(name), [])
            if not candidates:
                continue
            if len(candidates) == 1:
                return candidates[0]
            for row in candidates:
                if same_team(row.get("team"), team_name):
                    return row
            return candidates[0]
        return None
