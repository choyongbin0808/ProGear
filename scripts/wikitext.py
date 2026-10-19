"""아주 작은 위키 원문(wikitext) 파서: 틀(template) 찾기와 매개변수 나누기."""

import re


def find_templates(text, name):
    """{{name ...}} 틀을 모두 찾아 원문 문자열 목록으로 돌려줌 (중첩 괄호 처리)."""
    results = []
    pattern = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*(?=[|}\n])", re.IGNORECASE)
    for m in pattern.finditer(text):
        start = m.start()
        depth = 0
        i = start
        while i < len(text) - 1:
            pair = text[i:i + 2]
            if pair == "{{":
                depth += 1
                i += 2
                continue
            if pair == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    results.append(text[start:i])
                    break
                continue
            i += 1
    return results


def split_params(template):
    """틀 원문에서 최상위 매개변수를 나눔. (위치 인자 목록, 이름 인자 사전)"""
    body = template[2:-2]
    parts = []
    depth_t = depth_l = 0
    buf = []
    i = 0
    while i < len(body):
        pair = body[i:i + 2]
        if pair == "{{":
            depth_t += 1
            buf.append(pair)
            i += 2
            continue
        if pair == "}}":
            depth_t -= 1
            buf.append(pair)
            i += 2
            continue
        if pair == "[[":
            depth_l += 1
            buf.append(pair)
            i += 2
            continue
        if pair == "]]":
            depth_l -= 1
            buf.append(pair)
            i += 2
            continue
        ch = body[i]
        if ch == "|" and depth_t == 0 and depth_l == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    parts.append("".join(buf))

    positional = []
    named = {}
    for part in parts[1:]:  # parts[0]은 틀 이름
        if "=" in part and not part.lstrip().startswith("{{"):
            key, value = part.split("=", 1)
            named[key.strip()] = clean(value)
        else:
            positional.append(clean(part))
    return positional, named


def clean(value):
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", value, flags=re.S)
    return value.strip()


def plain(value):
    """[[링크|글자]] → 글자, 틀 제거 등 간단한 글자만 남김"""
    value = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", value)
    value = re.sub(r"\{\{[^{}]*\}\}", "", value)
    value = re.sub(r"'''?", "", value)
    return value.strip()
