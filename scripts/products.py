"""제품명 정리: 원래 이름 → brand / model / color / edition.

규칙 (PLAN.md 3장)
- 색상: 순위에서는 묶고(model에서 뺌) 선수 정보에만 표시(color)
- 버전: model에 남겨서 따로 셈
- 한정판 / 콜라보: 알아낼 수 있으면 edition으로 표시, 순위는 기본 제품에 묶음
- 색상인지 버전인지 애매한 꼬리말: 버리고 기본 제품으로 처리 (원래 이름은 rawName에 남김)
"""

import re
from collections import Counter, defaultdict

from common import DATA_DIR, read_json


class ProductNormalizer:
    def __init__(self, aliases=None):
        a = aliases or read_json(DATA_DIR / "aliases.json", {})
        self.brands = sorted(a.get("brands", {}).items(), key=lambda kv: -len(kv[0]))
        self.colors = sorted(a.get("colors", []), key=lambda c: -len(c))
        self.edition_patterns = [re.compile(p) for p in a.get("editionPatterns", [])]
        self.variant_words = {w.lower() for w in a.get("variantWords", [])}
        self.version_re = re.compile(r"^(?:" + "|".join(a.get("versionWords", [])) + r")$", re.IGNORECASE)
        self.models = {k.lower(): v for k, v in a.get("models", {}).items()}
        self.ignore = {w.lower() for w in a.get("ignoreNames", [])}

    def split_brand(self, raw):
        low = raw.lower()
        for prefix, brand in self.brands:
            p = prefix.lower()
            if low == p or low.startswith(p + " "):
                return brand, raw[len(prefix):].strip()
        parts = raw.split(" ", 1)
        return parts[0], (parts[1] if len(parts) > 1 else "")

    def strip_colors(self, text):
        found = []
        changed = True
        while changed and text:
            changed = False
            paren = re.search(r"\s*\(([^)]*)\)$", text)
            if paren:
                inner = paren.group(1).strip()
                if self.is_color(inner):
                    found.insert(0, inner)
                text = text[:paren.start()].strip()  # 괄호 꼬리말: 색상이 아니면 애매 → 버림
                changed = True
                continue
            for color in self.colors:
                if re.search(r"(?:^|\s|/)" + re.escape(color) + r"$", text, re.IGNORECASE) and len(text) > len(color):
                    found.insert(0, text[-len(color):])
                    text = text[:-len(color)].rstrip(" /-")
                    changed = True
                    break
        return text, (" ".join(found) or None)

    def is_color(self, text):
        words = text
        for color in self.colors:
            words = re.sub(r"\b" + re.escape(color) + r"\b", "", words, flags=re.IGNORECASE)
        return text.strip() != "" and words.strip(" /-&") == ""

    def strip_variant_words(self, text):
        while " " in text:
            head, tail = text.rsplit(" ", 1)
            if tail.lower() in self.variant_words:
                text = head
            else:
                break
        return text

    def normalize(self, raw):
        raw = re.sub(r"\s+", " ", (raw or "").replace(" ", " ")).strip()
        if not raw or raw.lower() in self.ignore:
            return None  # 실제 제품명이 아닌 값(Custom, Unknown 등)은 미확인으로 처리
        brand, rest = self.split_brand(raw)
        rest = re.sub(r"^(G)\s+G\s+", r"\1 ", rest)  # "Logitech G G Pro" 같은 중복 정리
        tokens = rest.split(" ")
        if len(tokens) > 2 and tokens[1].lower() == brand.lower():  # "ASUS ROG ASUS TUF …" → "TUF …"
            rest = " ".join(tokens[2:])
        elif tokens and tokens[0].lower() == brand.lower() and len(tokens) > 1:  # "ZOWIE ZOWIE XL…"
            rest = " ".join(tokens[1:])

        rest, color = self.strip_colors(rest)  # "… Faker Edition White" → 색상을 먼저 떼어냄
        edition = None
        for pattern in self.edition_patterns:
            m = pattern.search(rest)
            if m and m.start() > 0:
                words = m.group(1).split()
                model_part = rest[:m.start()].strip()
                # "Ace HFX ZywOo Edition" → 버전 단어(Ace, HFX)는 모델로 돌려보내고 "ZywOo Edition"만 에디션
                while len(words) > 1 and words[0] not in ("x", "×") and self.version_re.match(words[0]):
                    model_part += " " + words.pop(0)
                edition = " ".join(words)
                rest = model_part
                break

        rest, color2 = self.strip_colors(rest)
        color = " ".join(c for c in (color2, color) if c) or None
        rest = self.strip_variant_words(rest)

        model = self.models.get(f"{brand} {rest}".lower()) or rest or raw
        return {"brand": brand, "model": model, "color": color, "edition": edition, "rawName": raw}

    # ----- 전체 데이터 정리 (기본 제품 묶기 + 표기 통일) -----

    def finalize(self, items):
        """items: normalize() 결과 목록 (제자리에서 수정)
        1) 'B 꼬리말' 모델에서 꼬리말이 버전 단어로 시작하지 않으면 기본 제품 B로 묶음
        2) 대소문자만 다른 표기는 가장 많이 쓰인 표기로 통일"""
        by_brand = defaultdict(set)
        for it in items:
            by_brand[it["brand"].lower()].add(it["model"].lower())

        def base_of(brand, model):
            low = model.lower()
            best = None
            for other in by_brand[brand.lower()]:
                if other != low and low.startswith(other + " "):
                    tail = model[len(other):].strip()
                    first = tail.split(" ")[0]
                    if not self.version_re.match(first) and (best is None or len(other) > len(best)):
                        best = other
            return best

        for it in items:
            base = base_of(it["brand"], it["model"])
            if base:
                tail = it["model"][len(base):].strip()
                if self.is_color(tail):
                    it["color"] = it["color"] or tail
                it["model"] = it["model"][:len(base)]

        spellings = defaultdict(Counter)
        brand_spellings = defaultdict(Counter)
        for it in items:
            spellings[(it["brand"].lower(), it["model"].lower())][it["model"]] += 1
            brand_spellings[it["brand"].lower()][it["brand"]] += 1
        for it in items:
            key = (it["brand"].lower(), it["model"].lower())
            it["model"] = spellings[key].most_common(1)[0][0]
            it["brand"] = brand_spellings[it["brand"].lower()].most_common(1)[0][0]
        return items
