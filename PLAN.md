# ProGear 기획서

> 프로 선수들이 쓰는 장비를 게임별, 시즌별로 정리해서 순위로 보여주는 웹사이트
> 작성자: 조용빈 (30718) · 원본: `3주차_3718_조용빈_서비스명_기획서.docx` · 정리일: 2026-10-19

---

## 1. 서비스 개요

| 항목 | 내용 |
| --- | --- |
| 서비스명 | **ProGear** (Pro Gear Ranking) |
| 종류 | 웹사이트 |
| 대상 사용자 | 게임용 장비를 사려는데 무엇을 살지 고민하는 사람 |
| 핵심 가치 | 1티어 리그나 세계대회에 나오는 프로 선수들이 실제로 쓰는 장비를 **종류별 사용 순위**로 보여줌 |
| 다루는 장비 (5종) | 마우스 · 키보드 · 모니터 · 헤드셋 · 마우스패드 |
| 다루는 게임 (5종) | League of Legends · VALORANT · PUBG: BATTLEGROUNDS · Counter-Strike 2 · Overwatch 2 |
| 다루는 시즌 | **2023 · 2024 · 2025 · 2026** (시즌이 시작한 연도 기준, Overwatch는 2024부터) |
| 기술 스택 | HTML · CSS · JavaScript (Vanilla) + 데이터 수집용 Node.js 스크립트 |

### 데이터 출처

| 용도 | 출처 | 채택 이유 |
| --- | --- | --- |
| 리그 / 대회, 팀, 로스터, 선수 정보 | [Liquipedia](https://liquipedia.net/) | 선수와 팀 정보를 가장 빠르고 정확하게 받아올 수 있음 |
| 선수 장비 정보 | [ProSettings.net](https://prosettings.net/), [EsportSettings](https://www.esportsettings.com/) | 프로 선수 장비 세팅을 정리해 둔 사이트 (Liquipedia에는 장비 정보가 없음) |
| 추가 장비 정보 (PUBG · Overwatch) | [EsportsMice](https://esportsmice.com/) | 위 두 사이트에 없는 선수의 **마우스**만 보충 (연도별 마우스 기록으로 과거 시즌도 채움) |

- 두 장비 사이트 정보가 서로 다르면 **페이지가 최근에 수정된 쪽**을 씁니다. (각 선수 페이지의 "Last updated" 같은 수정 날짜 기준. 날짜가 같거나 없으면 ProSettings.net을 먼저 씀) 두 출처는 모두 남깁니다.
- 두 사이트 모두 이용 약관과 `robots.txt`에서 수집이 허용된 것을 확인했습니다.
- 다른 게임 선수 정보가 섞이지 않도록 **게임 이름과 선수 ID를 함께 확인**해서 매칭합니다. (기획서 06번에서 발견한 문제)

### 게임별 대상 리그 / 대회

| 게임 | Liquipedia 위키 | 대상 | 시즌별 참고 |
| --- | --- | --- | --- |
| League of Legends | `leagueoflegends` | 1부 지역 리그: LCK, LPL, LEC, 북미 리그 | 북미는 2023~24 LCS, 2025 LTA, 2026 LCS |
| VALORANT | `valorant` | VCT 국제 리그: Americas / EMEA / Pacific / China | China 리그는 2024부터 |
| PUBG | `pubg` | **모든 세계대회**: PGC, PNC, PGS, 그 밖에 Liquipedia에서 국제 대회로 분류된 대회 참가 팀 | 시즌마다 열린 국제 대회를 모두 포함 |
| Counter-Strike 2 | `counterstrike` | **세계대회만**: Major 대회 참가 팀 | 2023 시즌은 **CS:GO 기준**으로 넣고 화면에 `CS:GO` 표시 |
| Overwatch 2 | `overwatch` | 1부 리그: OWCS | **2023 시즌은 제외** (2024~2026만) |

> **CS:GO 표시**: CS2 출시(2023년 9월) 전에 열린 대회는 대회 데이터에 `gameVersion: "csgo"`를 넣고, 시즌 선택과 순위 화면에 `CS:GO` 배지를 붙여서 CS2 시즌과 구분합니다. (예: 시즌 드롭다운 `2023 (CS:GO)`)

---

## 2. 기능 정의

### 기능 1 · 필수: 게임 탭과 장비 사용 순위
- 메인 화면에 게임 5개를 카드나 탭으로 보여줌
- 게임을 클릭하면 그 게임의 대상 선수들이 쓰는 장비 순위가 나옴
- **시즌 선택** (2023 / 2024 / 2025 / 2026, 기본값은 최신 시즌)
- 장비 종류 탭(마우스 / 키보드 / 모니터 / 헤드셋 / 마우스패드)으로 바꿔 볼 수 있음
- 순위 항목: 순위, 제품명(색상 없이 모델명만), 브랜드, 사용 선수 수, 사용률(%) 막대
- 항목을 클릭하면 오른쪽에 상세 패널이 열림 (제품명, 사용 선수 수, 사용률, 쓰는 선수 목록, 선수별 사용 색상)

### 기능 2 · 선택: 팀별 장비 보기
- 게임 → 시즌 → 리그 / 대회 → 팀을 고르면 그 팀 선수들의 장비를 한 화면에서 볼 수 있음
- 선수 한 명 = 한 행, 장비 5종 = 열로 된 표 (색상까지 표시)

### 기능 3 · 선택: 검색
- 선수 이름이나 팀 이름을 검색하면 해당 선수 / 팀의 장비가 나옴
- 선수 페이지에서는 시즌별로 장비가 어떻게 바뀌었는지 볼 수 있음
- **테스트 시나리오**: `Faker`를 검색했을 때 Faker의 장비 5종이 색상까지 나오는지 확인

### 사용 흐름
```
메인(게임 목록) → 게임 클릭 → 시즌 선택 → 장비 종류 탭 선택 → 순위표 확인 → 항목 클릭 → 상세 패널(사용 선수 목록)
                                                                          └→ 선수 클릭 → 선수 장비 페이지(색상 포함, 시즌별)
```

---

## 3. 제품 묶기 규칙

순위에서 같은 제품으로 셀지 다른 제품으로 셀지 정하는 규칙입니다.

| 차이 | 처리 | 예시 |
| --- | --- | --- |
| **색상** | 순위에서는 **하나로 묶음**, 선수 개인 정보에는 **색상까지 표시** | `G Pro X Superlight 2` **Black / White / Magenta** → 순위에서는 `G Pro X Superlight 2` 하나 |
| **버전** | **묶지 않고 따로 셈** | `G Pro X Superlight` ≠ `G Pro X Superlight 2` ≠ `G Pro X2 SUPERSTRIKE`<br>`DeathAdder V3` ≠ `DeathAdder V3 HyperSpeed` ≠ `DeathAdder V3 Pro` |
| **색상인지 버전인지 애매함** | **기본 제품**으로 처리 (기본 모델에 묶음) | 색상 이름인지 새 버전 이름인지 알 수 없는 꼬리말 → 떼고 기본 모델로 셈 |
| **한정판 / 콜라보 에디션** | 순위에서는 **기본 제품에 묶음**. 에디션 이름을 알 수 있으면 선수 개인 정보에 **에디션 배지로 표시**, 알 수 없으면 **기본 제품**으로만 표시 | `Viper V3 Pro Faker Edition` → 순위: `Viper V3 Pro`, 선수 정보: `Viper V3 Pro` + `Faker Edition` 배지 |

### 구현 방법
- 장비 하나를 `brand`(브랜드), `model`(색상과 에디션을 뺀 모델명, 버전은 포함), `color`(색상), `edition`(한정판 / 콜라보 이름) 네 칸으로 나눠서 저장
- 순위 집계 키 = `brand + model` → 색상이나 에디션만 다르면 자동으로 묶이고, 버전이 다르면 모델명이 달라서 따로 셈
- 수집할 때 원래 제품명을 나누는 데 `data/aliases.json`을 사용
  - `colors`: 알려진 색상 단어 목록 (`Black`, `White`, `Magenta`, `Pink`, `Lunar Eclipse` …)
  - `editions`: 알려진 한정판 / 콜라보 이름 목록 (`… Edition`, `x 팀이름`, 선수 시그니처 등)
  - `models`: 사이트마다 다르게 적은 이름을 표준 모델명으로 바꾸는 표 (`GPX2` → `G Pro X Superlight 2`)
- 나누는 순서: ① `models`로 표준 모델명 찾기 → ② 남은 부분이 `editions`에 있으면 `edition` → ③ `colors`에 있으면 `color` → ④ 그래도 애매하면 버리고 **기본 제품**으로 처리 (원래 이름은 `rawName`에 남겨서 나중에 확인)

---

## 4. 시즌 규칙

### 시즌 기준: **시즌이 시작한 연도**
- 리그 / 대회의 **시작일 연도**가 그 시즌의 연도가 됩니다.
- 예: 2025년 12월에 시작해서 2026년 1월에 끝난 대회 → **2025 시즌**
- 시작일은 Liquipedia의 리그 / 대회 페이지에 있는 날짜를 기준으로 합니다.

### 수집 대상 시즌: 2023 · 2024 · 2025 · 2026

| 시즌 | 상태 | 수집 방식 |
| --- | --- | --- |
| 2023, 2024, 2025 | 끝난 시즌 | 한 번 모은 뒤 고정 (오류를 고칠 때만 다시 수집) |
| 2026 | 진행 중 | **한 달에 한 번** 다시 수집해서 갱신 |

| 게임 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- |
| League of Legends | O | O | O | O |
| VALORANT | O | O | O | O |
| PUBG | O | O | O | O |
| Counter-Strike | O (`CS:GO`) | O | O | O |
| Overwatch 2 | **제외** | O | O | O |

### 시즌별 데이터의 의미
- **선수 명단**: 그 시즌 대상 리그 / 대회에 나온 팀의 로스터 (Liquipedia)
- **장비**: 그 시즌 동안 선수가 쓴 장비
- 한 시즌 안에 장비를 바꾼 선수는 **그 시즌에 마지막으로 사용한 장비**로 셉니다. 순위, 상세 패널, 선수 정보 모두 이 장비 하나만 보여주고 시즌 중간에 쓴 장비는 따로 표시하지 않습니다.
  - 진행 중인 2026 시즌은 월 1회 수집할 때마다 최신 장비로 바뀌고, 시즌이 끝나면 마지막 수집값으로 고정됩니다.
  - 과거 시즌은 그 시즌 기간 안에서 가장 늦은 날짜의 자료(스냅샷, 기사)를 기준으로 합니다.
- 한 시즌 안에 팀을 옮긴 선수는 **마지막 소속팀** 기준으로 한 번만 셉니다. (중복 집계 방지)

### 그 시즌 정보가 없는 선수
- 예: 2026년에도 뛰는 선수인데 장비 정보가 2023년 보관본에만 있음 → 2026 시즌에 2023 장비를 쓰고 `2023 시즌 정보`로 표시
- 앞 시즌(2025) → 2024 → 2023 순서로 ProSettings 보관본을 찾아 가장 최근 것을 씀 (`gearFromSeason`)
- 이 선수들도 순위에 포함되고, 순위 화면에 "그중 N명은 이전 시즌 정보"로 따로 표시

### 과거 시즌(2023~2025) 장비 찾는 방법
ProSettings.net과 EsportSettings는 기본적으로 **지금 쓰는 장비**만 보여주기 때문에, 과거 시즌은 아래 순서로 찾습니다. (데이터 수집 단계에서 Claude가 직접 찾아서 채움)

1. **장비 사이트의 변경 기록**: 선수 페이지에 예전 장비나 변경 이력이 있으면 그 시즌에 해당하는 것을 씀
2. **Wayback Machine 스냅샷**: [Wayback Machine](https://web.archive.org/)에 저장된 ProSettings.net / EsportSettings 선수 페이지 중 **그 시즌 기간에 가장 가까운(시즌 마지막에 가까운) 스냅샷**을 씀
3. **그 시즌 장비 기사 / 목록**: 장비 사이트가 그 시즌에 올린 "대회별 장비 통계"나 "팀 장비" 글
4. 위에서 찾지 못하면 `null`로 두고 집계에서 뺌 (추측해서 채우지 않음)

- 찾은 장비에는 `gearSources`(어디서 찾았는지 링크)와 `gearCheckedAt`(그 자료의 날짜)을 꼭 남깁니다.
- 출처끼리 정보가 다르면 이 시즌 기간 안에서 **가장 최근에 수정된 자료**를 씁니다.

---

## 5. 개발 범위와 진행 상황

| 구분 | 내용 |
| --- | --- |
| 이번에 먼저 | ① 게임 탭 분류 ② 게임별 장비 사용 순위 ③ 시즌 선택 |
| 나중에 | 검색 기능, 불러온 장비 정보가 정확한지 확인 |
| 지금 된 것 | **로드맵 1~9단계 완료, 10단계 대부분 완료 (2026-10-19)**: 화면 5개(메인, 순위, 팀, 선수, 검색), 19개 게임-시즌 실제 데이터, 월 1회 수집 스크립트, 표본 검증 |
| 아직 안 된 것 | 배포(GitHub Pages 등), PUBG · Overwatch 장비 확인 인원 늘리기(출처 한계, 아래 표) |

### 장비 확인 인원 (2026-10-19 수집 기준, 확인 인원 / 로스터)
| 게임 | 2023 | 2024 | 2025 | 2026 | 비고 |
| --- | --- | --- | --- | --- | --- |
| LoL | 63 / 276 | 62 / 267 | 92 / 251 | 90 / 255 | ProSettings 167명 + EsportSettings 128명뿐, LPL 선수가 특히 적음 |
| VALORANT | 132 / 150 | 202 / 257 | 230 / 301 | 206 / 274 | |
| PUBG | 44 / 214 | 31 / 178 | 30 / 233 | 24 / 198 | ProSettings PUBG 목록 전체가 64명, EsportSettings는 PUBG 없음, EsportsMice로 마우스만 5명 추가 |
| CS | 125 / 127 | 189 / 194 | 224 / 263 | 170 / 198 | 2026 PGL Singapore Major(11월)는 아직 로스터 없음 |
| Overwatch | - | 31 / 659 | 24 / 556 | 27 / 419 | ProSettings Overwatch 목록 전체가 36명, EsportSettings는 Overwatch 없음, EsportsMice로 마우스만 12명 추가 |

> 이전 시즌 정보로 채운 인원 포함 (예: Overwatch 2026의 27명 중 8명은 2023 · 2025 시즌 정보)

- 지금까지 받은 ProSettings PUBG 목록(현재 + 모든 보관본)을 다 합쳐도 2026 PUBG 로스터 중 한 번이라도 나온 선수는 26명
- 추가 출처 조사 (2026-10-19): EsportsMice(PUBG 61명, Overwatch 26명)는 대부분 ProSettings와 같은 선수라 새로 늘어난 인원이 적음. 마우스만 있음
  - 제외: sensconverter.app (OWL 시절 데이터, 날짜 없음), proaiming.com (Overwatch 선수 목록 없음), settings.gg (CS2 · VALORANT만)
  - 후보: Liquipedia Overwatch [List of player hardware](https://liquipedia.net/overwatch/List_of_player_hardware) (선수 문서의 장비 칸을 모은 표) → 조사한 날 Liquipedia 연결이 끊겨서 형식을 확인하지 못함. 연결되면 다음 출처로 추가
- 확인 인원이 로스터의 30% 미만이면 메인 게임 카드, 순위 화면, 팀 화면에 "일부 선수 기준" 안내가 표시됨 (기준값은 `js/ui.js`의 `LOW_COVERAGE`)
- 표본 검증: 게임 · 시즌마다 3명씩 고른 249개 장비 항목이 모두 출처 페이지에 그대로 있음 (`py scripts/verify_data.py`)
| 다음 할 일 | 검색 기능 (선수 / 팀이 많아지면 찾기 어렵기 때문) |

> **기획서에서 바뀐 점**
> - 게임: 4개(CS2, VALORANT, Overwatch, LoL) → **PUBG를 추가해서 5개**
> - PUBG, CS2: 1부 리그 기준이 애매해서 **세계대회만** 다룸 (PUBG는 모든 세계대회, CS 2023 시즌은 CS:GO로 표시)
> - 데이터: 선수 / 팀 = **Liquipedia**, 장비 = **ProSettings.net, EsportSettings**
> - **2023~2026 시즌 구분** 추가 (Overwatch는 2024부터)

---

## 6. 기획서 분석

### 잘된 점
- **대상과 목적이 분명함**: "장비 구매를 고민하는 사람"이라는 대상과 해결하려는 문제가 구체적입니다.
- **핵심 기능이 하나로 모여 있음**: 필수 기능(게임별 장비 순위)이 명확하고, 선택 기능이 자연스럽게 확장됩니다.
- **범위 조절이 현실적임**: 검색과 데이터 검증을 "나중에"로 미루고 핵심 화면부터 만든 순서가 좋습니다.
- **AI 답변을 그대로 쓰지 않음**: 다른 게임 정보가 섞이는 문제를 직접 찾아서 걸러낸 판단이 기획서에 잘 드러납니다.

### 보완이 필요한 점

| # | 문제 | 설명 | 해결 방법 |
| --- | --- | --- | --- |
| 1 | 데이터 출처 역할 | Liquipedia에는 장비 정보가 없음 | 선수 / 팀은 Liquipedia, 장비는 ProSettings / EsportSettings로 나눔 (1장) |
| 2 | "1티어" 기준 | CS2, PUBG는 고정 리그가 없음 | 두 게임은 세계대회만 다룸 (1장) |
| 3 | 표본 수가 적음 | 예시 화면은 "장비 확인 5명 기준"이라 모든 제품이 1명(20%)으로 같은 순위 | 집계 인원을 항상 표시하고, 같은 수는 같은 순위로 처리 |
| 4 | 제품명 표기가 제각각 | 색상이 다르면 다른 제품으로 셈 | 색상 / 에디션은 묶고 버전은 나눔, 애매하면 기본 제품 (3장) |
| 5 | 정확도와 최신성 | 선수 이적, 장비 교체가 잦음 | 시즌 구분 + 월 1회 수집, 데이터마다 수집일과 출처 저장 (4장) |
| 6 | 사용률 분모 | 무엇으로 나누는지 불분명 | "그 시즌에 장비가 확인된 선수 수"로 나누고 화면에 표시 |
| 7 | 과거 시즌 장비 | 장비 사이트는 지금 장비 위주로 보여줌 | Wayback Machine의 ProSettings 목록 보관본으로 채우고, 없으면 `null` (4장, 7장) |

---

## 7. 데이터 수집 계획

### 수집 구조: "미리 수집 → JSON 저장 → 사이트는 JSON만 읽기"

```
[수집 스크립트 (Python, 한 달에 한 번: py scripts/update_all.py)]
  ① fetch_liquipedia.py  Liquipedia API ──▶ 시즌별 대회 → 참가 팀 → 로스터  (scripts/work/rosters)
  ② fetch_gear.py        ProSettings / EsportSettings / Wayback ──▶ 선수별 장비  (scripts/work/gear)
  ②-1 fetch_extra_gear.py EsportsMice ──▶ PUBG · Overwatch 빈칸의 마우스 보충  (scripts/work/gear에 덧붙임)
  ③ build_data.py        제품명 정리(aliases.json) ──▶ data/{game}/{season}.json, data/index.json
  ④ upload_supabase.py   data/*.json ──▶ Supabase 테이블 season_data, site_index  (환경 변수가 있을 때만)
                                                         │
[웹사이트 (HTML/CSS/JS)]                                  ▼
  Supabase REST (season_data?game=eq.valorant&season=eq.2026) ──▶ 순위 계산 ──▶ 화면 표시
  (js/config.js에 Supabase 설정이 없거나 불러오지 못하면 data/valorant/2026.json 파일을 읽음)
```

### Supabase
| 테이블 | 열 | 내용 |
| --- | --- | --- |
| `season_data` | `game`, `season` (기본 키), `data` (jsonb), `updated_at` | `data/{game}/{season}.json` 하나 = 한 행 |
| `site_index` | `id` (`'main'`), `data` (jsonb), `updated_at` | `data/index.json` |

- 테이블 만들기: `scripts/supabase/schema.sql`. RLS를 켜고 **읽기만** 누구나 가능 (쓰기 정책 없음)
- 올리기: `scripts/upload_supabase.py`가 secret 키로 upsert. secret 키는 환경 변수로만 넘기고 코드에 넣지 않음
- 사이트: `js/data.js`가 publishable(anon) 키로 PostgREST를 직접 부름 (라이브러리 없이 `fetch`). 화면 코드는 그대로

> 수집 스크립트는 처음 계획한 Node.js 대신 **Python**으로 만들었습니다. 이 PC에 Node.js가 없고 Python 3.12가 설치돼 있기 때문입니다. 웹사이트 자체는 그대로 HTML / CSS / JS입니다.

### 실제 수집 방법
| 단계 | 출처 | 방법 |
| --- | --- | --- |
| 로스터 | Liquipedia | `scripts/sources/competitions.json`에 적은 대회 문서의 위키 원문을 `action=query`로 받아(50개씩 묶어서) `TeamCard` / `TeamParticipants` 틀에서 팀과 선수를 읽음. 대회 시작일(`sdate`) 연도로 시즌을 정하고, 시즌 마지막 대회의 소속팀을 기록 |
| 2026 장비 | ProSettings.net | 게임별 "Pro Settings & Gear List" 표. 페이지에는 100명만 있고 나머지는 사이트가 쓰는 `wp-json/pro/v1/pro-list`에서 50명씩 받음 |
| 2026 장비 | EsportSettings | 게임 페이지(`/game/{게임}/`)에서 선수를 찾고 선수 페이지(`/player/{id}/`)의 "Full gear loadout"을 읽음. LoL, VALORANT, CS만 있음 (PUBG, Overwatch 없음) |
| 추가 마우스 (PUBG · Overwatch) | EsportsMice | 게임 페이지(`/games/pubg`, `/games/overwatch-2`)의 선수 목록에서 찾고, 선수 페이지의 Game 칸이 같은 게임일 때만 사용. 2026은 현재 마우스, 과거 시즌은 "Mouse History" 기간 중 그 해를 포함하고 가장 늦게 시작한 마우스. 그 시즌 장비가 없는 선수만 새로 넣고, 이전 시즌 정보로 채운 선수에는 섞지 않음. `robots.txt`는 `Allow: /` |
| 출처가 다를 때 | 두 사이트 | ProSettings 선수 페이지의 `dateModified`와 EsportSettings 사이트 빌드 날짜를 비교해 **최근 것**을 씀. 한쪽에 없는 장비 종류는 다른 쪽으로 채움 |
| 2023~2025 장비 | Wayback Machine | ProSettings 목록의 보관본 중 시즌 마지막 대회가 끝난 날 이전 것을 최신순으로 최대 4개 보고, 선수마다 가장 최근 보관본의 장비를 씀 (CS 2023은 CS:GO 목록 `lists/cs-go/`, Overwatch 2024~2025는 `lists/overwatch-2/`) |
| 매칭 | - | 같은 게임 목록 안에서만 선수 이름으로 찾고, 이름이 겹치면 팀 이름으로 구분 → 다른 게임 선수와 섞이지 않음 |

- 모든 응답은 `scripts/.cache`에 25일 동안 저장 (끝난 시즌 보관본은 계속 재사용) → 같은 달에 다시 실행해도 요청이 거의 없음
- Liquipedia 요청은 2.1초, 장비 사이트 2초, Wayback 4초 간격

브라우저에서 방문할 때마다 외부 사이트를 직접 부르지 않는 이유:
- 브라우저 `fetch`로는 User-Agent를 바꿀 수 없음 (Liquipedia 필수 조건)
- CORS에 막힐 수 있음
- 방문자가 많아지면 요청 속도 제한을 바로 넘김

### 수집 주기
- **한 달에 한 번** (예: 매달 1일) `py scripts/update_all.py` 실행 → 진행 중인 시즌(2026)이 갱신됨
- 끝난 시즌(2023~2025)의 보관본은 처음 한 번만 받고 고정
- 자동으로 돌리려면 Windows 작업 스케줄러에 `scripts/update_monthly.bat`를 "매월 1일"로 등록 (12장 참고)

### Liquipedia 규칙 (중요)
[API 이용 약관](https://liquipedia.net/api-terms-of-use)을 어기면 IP가 차단될 수 있습니다.
- 일반 API 요청은 2초에 1번 이하, `action=parse`는 30초에 1번 이하
- User-Agent 필수: 프로젝트 이름과 연락처 → `PROGEAR_CONTACT` 환경 변수에 연락처를 넣으면 `ProGear/1.0 (연락처)`로 보냄
- gzip 압축 요청 (`Accept-Encoding: gzip`)
- 내용이 CC BY-SA 3.0이므로 사이트에 "Data from Liquipedia"와 출처 링크를 표시
- 공식 데이터 API(LiquipediaDB)는 API 키와 승인이 필요해서 쓰지 않음

### 장비 사이트 규칙
- ProSettings.net과 EsportSettings는 이용 약관과 `robots.txt`에서 수집이 허용된 것을 확인함
- 그래도 요청 사이에 간격을 두고, 한 달에 한 번만 수집해서 부담을 줄임
- 선수 페이지마다 **수정 날짜**를 함께 저장해서 두 사이트 중 무엇을 쓸지 정하는 데 사용 (`gearUpdatedAt`)
- 사이트 푸터와 선수 페이지에 장비 정보 출처(사이트 이름, 링크)를 표시

---

## 8. 데이터 구조 (초안)

`data/{game}/{season}.json` (예: `data/valorant/2025.json`)
```json
{
  "game": "valorant",
  "season": 2025,
  "updatedAt": "2026-10-01",
  "competitions": [
    {
      "id": "vct-2025-pacific",
      "name": "VCT 2025: Pacific",
      "startDate": "2025-01-18",
      "gameVersion": null,
      "liquipedia": "https://liquipedia.net/valorant/..."
    }
  ],
  "teams": [
    { "id": "team-a", "name": "Team A", "competitions": ["vct-2025-pacific"] }
  ],
  "players": [
    {
      "id": "player-a",
      "name": "PlayerA",
      "team": "team-a",
      "role": "Duelist",
      "liquipedia": "https://liquipedia.net/valorant/PlayerA",
      "gear": {
        "mouse":    { "brand": "Logitech", "model": "G Pro X Superlight 2", "color": "Magenta", "edition": null, "rawName": "Logitech G Pro X Superlight 2 Magenta" },
        "keyboard": { "brand": "Wooting",  "model": "60HE+", "color": "Black", "edition": null, "rawName": "Wooting 60HE+" },
        "monitor":  { "brand": "ZOWIE",    "model": "XL2566K", "color": null, "edition": null, "rawName": "ZOWIE XL2566K" },
        "headset":  null,
        "mousepad": { "brand": "Artisan",  "model": "Zero", "color": "Black", "edition": null, "rawName": "Artisan Zero Black" }
      },
      "gearSources": ["https://prosettings.net/...", "https://www.esportsettings.com/..."],
      "gearUpdatedAt": "2026-09-14",
      "gearCheckedAt": "2026-10-01"
    }
  ]
}
```
> 위 선수 / 팀 / 장비 값은 형식 예시일 뿐 실제 데이터가 아닙니다.
> - `season`: 시즌 시작 연도 (대회 `startDate`의 연도)
> - `gameVersion`: CS 2023 시즌 대회는 `"csgo"`, 나머지는 `null` → 화면에 `CS:GO` 배지 표시
> - `model`: 색상과 에디션은 빼고 버전은 포함한 이름 → 순위 집계 키
> - `color`: 선수 개인 정보에만 표시, 모르면 `null`
> - `edition`: 한정판 / 콜라보 이름, 알 수 있을 때만 넣고 모르면 `null` (기본 제품으로 표시)
> - `rawName`: 출처에 적힌 원래 제품명 (애매한 이름을 나중에 확인하는 용도)
> - `gearFromSeason`: 그 시즌 정보가 없어 이전 시즌 장비를 쓴 경우 그 시즌 연도, 아니면 `null`
> - `gearUpdatedAt`: 출처 페이지의 수정 날짜 → 두 사이트 중 최근 것을 고르는 기준
> - 장비 자체를 모르면 `null` → 집계에서 뺌

시즌 설정 (`js/config.js`에 들어 있음, 파일을 직접 열어도 동작하도록 JSON 대신 JS로 둠)
```json
{
  "seasons": [2023, 2024, 2025, 2026],
  "current": 2026,
  "games": {
    "lol":       [2023, 2024, 2025, 2026],
    "valorant":  [2023, 2024, 2025, 2026],
    "pubg":      [2023, 2024, 2025, 2026],
    "cs2":       [2023, 2024, 2025, 2026],
    "overwatch": [2024, 2025, 2026]
  },
  "labels": { "cs2": { "2023": "CS:GO" } }
}
```
> 시즌 드롭다운은 `games`에 있는 시즌만 보여줍니다. (Overwatch를 고르면 2023이 안 보임)

### 순위 계산 방식
1. 선택한 게임 + 시즌 파일을 불러옴
2. 선택한 장비 종류에서 `gear[종류]`가 `null`이 아닌 선수만 고름 → 이 인원이 **분모**
3. `brand + model`로 묶어서 선수 수를 셈 (색상 무시, 버전은 구분)
4. 선수 수 내림차순, 같으면 이름순으로 정렬 (같은 수는 같은 순위)
5. 사용률 = 사용 선수 수 ÷ 분모 × 100
6. 상세 패널에서는 같은 모델을 쓰는 선수들과 각자의 `color`, `edition`을 보여줌

---

## 9. 화면 구성

| 화면 | 주요 요소 |
| --- | --- |
| 메인 | 상단 내비(게임 / 장비 순위 / 선수 / 팀), **시즌 선택 드롭다운**, 히어로 문구, 게임 카드 5개 |
| 장비 순위 | 게임 이름, 시즌 선택(CS 2023은 `CS:GO` 배지), 장비 종류 탭 5개, 순위표, 상세 패널(선수별 색상 / 에디션), "장비 확인 N명 기준", 수집일 |
| 팀 (선택) | 시즌, 리그 / 대회 필터 → 팀 목록 → 팀 선수별 장비 표 (색상 / 에디션 포함) |
| 선수 (선택) | 선수 정보, 장비 5종(색상 / 에디션 배지 포함), 시즌별 장비 변화, 출처 링크와 수정 날짜 |
| 공통 | 검색창, 푸터에 출처 표기 (Liquipedia / ProSettings.net / EsportSettings) |

- 선택한 시즌은 주소에 남겨서 새로고침해도 유지: `ranking.html?game=valorant&season=2025`

### 폴더 구조
```
ProGear/
├─ index.html          # 메인 (게임 카드 5개, 시즌 선택)
├─ ranking.html        # 게임별 장비 순위 (?game=valorant&season=2026&gear=mouse)
├─ team.html           # 팀 목록 / 팀 선수별 장비 (?game=…&season=…&team=…)
├─ player.html         # 선수 장비 + 시즌별 변화 (?game=…&id=…)
├─ search.html         # 선수 · 팀 검색 (?q=Faker)
├─ css/style.css
├─ js/
│  ├─ config.js        # 게임 / 시즌 / 장비 종류 설정 (CS:GO 표시, Overwatch 2023 제외)
│  ├─ ui.js            # 공통 헤더 · 푸터 · 도우미
│  ├─ data.js          # JSON 불러오기
│  ├─ ranking.js       # 순위 계산 (brand + model로 묶기)
│  ├─ main.js · ranking-page.js · team.js · player.js · search.js   # 화면별 코드
├─ data/
│  ├─ aliases.json     # 브랜드 / 색상 / 에디션 / 애매한 꼬리말 / 버전 단어 / 제외할 이름
│  ├─ index.json       # 검색 · 팀 · 선수 화면용 요약
│  ├─ lol/ · valorant/ · pubg/   2023~2026.json
│  ├─ cs2/             2023.json(CS:GO) ~ 2026.json
│  └─ overwatch/       2024~2026.json
├─ scripts/            # 데이터 수집 (Python)
│  ├─ update_all.py         # 한 번에 실행 (월 1회)
│  ├─ update_monthly.bat    # 작업 스케줄러 등록용
│  ├─ fetch_liquipedia.py   # 시즌별 대회 / 팀 / 로스터
│  ├─ fetch_gear.py         # ProSettings / EsportSettings / Wayback 장비
│  ├─ fetch_extra_gear.py   # EsportsMice로 PUBG · Overwatch 마우스 보충
│  ├─ upload_supabase.py    # data/*.json → Supabase 테이블
│  ├─ supabase/schema.sql   # Supabase 테이블 · 읽기 정책
│  ├─ build_data.py         # 제품명 정리 → data/*.json
│  ├─ products.py · matching.py · liquipedia.py · wikitext.py · common.py
│  ├─ sources/competitions.json   # 게임 · 시즌별 대상 대회 목록
│  ├─ sources/gear_sources.json   # 게임별 장비 출처 주소
│  ├─ work/            # 중간 결과 (로스터, 장비)
│  └─ .cache/          # 받은 페이지 캐시
└─ PLAN.md
```

---

## 10. 개발 로드맵

| 단계 | 할 일 | 완료 기준 |
| --- | --- | --- |
| 1 ✅ | 화면 뼈대 (메인, 게임 카드 5개, 순위 화면, 시즌 선택) | 게임 카드와 시즌을 고르면 순위 화면으로 이동 |
| 2 ✅ | JSON 형식 확정 + 실제 데이터 | 5개 게임 모두 순위표가 나옴 |
| 3 ✅ | 순위 계산 + 제품 묶기 규칙 | 색상 / 에디션만 다른 제품은 묶이고, 버전이 다른 제품은 따로 나오고, 애매한 이름은 기본 제품으로 감 |
| 4 ✅ | Liquipedia 수집 스크립트 (시즌별 대회 / 팀 / 로스터) | 19개 게임-시즌(5게임 × 4시즌 − Overwatch 2023)의 팀과 선수가 채워짐, CS 2023은 `csgo` 표시 |
| 5 ✅ | 장비 수집 스크립트 (ProSettings / EsportSettings) | 2026 시즌 선수 장비가 채워짐, 수정 날짜가 최근인 출처가 쓰임, 다른 게임 선수와 섞이지 않음 |
| 6 ✅ | 과거 시즌(2023~2025) 장비 | Wayback Machine 보관본으로 출처와 함께 채우고, 못 찾으면 `null` |
| 7 ✅ | 장비 데이터 검증 | 표본 249개 항목 100% 출처와 일치 |
| 8 ✅ | 검색 기능 | `Faker` 검색 → 장비 5종(색상, 에디션 포함) 표시 |
| 9 ✅ | 팀별 보기 / 선수 시즌별 장비 변화 | 팀을 고르면 선수별 장비 표 표시 |
| 10 | 마무리 | 모바일 화면 대응 ✅, 출처 표기 ✅, 월 1회 수집 스크립트 ✅, 배포 (남음) |

---

## 11. 결정된 것 / 확인이 필요한 것

### 결정됨
- [x] 게임 5종: LoL, VALORANT, PUBG, CS2, Overwatch 2
- [x] PUBG, CS2는 세계대회만 다룸
- [x] 선수 / 팀 정보는 Liquipedia, 장비는 ProSettings.net + EsportSettings
- [x] 순위에서는 색상을 묶고, 선수 개인 정보에는 색상까지 표시
- [x] 버전 차이는 묶지 않고 따로 셈
- [x] 수집 주기: 한 달에 한 번
- [x] 시즌 기준: 시즌 시작 연도 (2025년 12월 시작 ~ 2026년 1월 종료 → 2025 시즌)
- [x] 대상 시즌: 2023, 2024, 2025, 2026
- [x] PUBG: 모든 세계대회 포함 (PGC, PNC, PGS 등)
- [x] CS 2023 시즌: CS:GO 기준으로 넣고 `CS:GO` 배지로 구분
- [x] Overwatch: 2023 시즌 제외 (2024~2026)
- [x] ProSettings.net / EsportSettings: 이용 약관과 `robots.txt`에서 수집 허용 확인
- [x] 과거 시즌 장비: Wayback Machine에 보관된 ProSettings 목록으로 채움 (ProSettings 선수 페이지에는 변경 기록이 없고, EsportSettings는 보관본이 없음)
- [x] 두 장비 사이트 정보가 다를 때: 최근에 수정된 날짜 기준
- [x] 색상인지 버전인지 애매하면: 기본 제품
- [x] 한정판 / 콜라보 에디션: 알 수 있으면 에디션 배지로 표시, 모르면 기본 제품 (순위에서는 기본 제품에 묶음)
- [x] 시즌 중 장비를 바꾼 경우: 그 시즌에 마지막으로 사용한 장비 기준 ("시즌 중 변경" 표시는 하지 않음)
- [x] 장비 출처: ProSettings.net, EsportSettings + PUBG · Overwatch는 다른 사이트도 사용 가능 (2026-10-19 변경). 지금은 EsportsMice로 빈칸의 마우스만 보충하고 기존 출처 값은 덮어쓰지 않음
- [x] 확인 인원이 로스터의 30% 미만이면 안내 표시: 메인 게임 카드, 순위 화면, 팀 화면
- [x] 그 시즌 장비 정보가 없는 선수: 앞 시즌부터 2023 시즌까지 거슬러 올라가 가장 최근에 확인된 장비를 쓰고 `○○○○ 시즌 정보`로 표시 (순위에도 포함, 순위 화면에 "그중 N명은 이전 시즌 정보" 표시)
- [x] 게임 총 랭킹: 시즌 선택의 "전체 시즌"에서 2023~2026 선수를 한 명씩, 각자 가장 최근 시즌 장비로 셈

### 확인 필요
- 없음 (모든 항목 결정됨)

---

## 12. 실행 방법

### 사이트 보기
JSON을 불러오기 때문에 파일을 더블클릭하지 말고 로컬 서버로 엽니다.
- VS Code의 **Live Server** 확장으로 `index.html` 열기, 또는
- ProGear 폴더에서 `py scripts/serve.py` 실행 후 `http://localhost:5500` 접속 (캐시를 쓰지 않는 개발 서버)

### Supabase 연결 (처음 한 번)
1. [Supabase](https://supabase.com/)에서 새 프로젝트 만들기
2. 대시보드 → **SQL Editor**에 `scripts/supabase/schema.sql` 내용을 붙여 넣고 실행 → `season_data`, `site_index` 테이블 생성
3. 대시보드 → **Project Settings → API Keys**에서 Project URL, publishable 키(또는 anon 키), secret 키(또는 service_role 키) 확인
4. 데이터 올리기 (PowerShell, ProGear 폴더에서)
   ```
   $env:SUPABASE_URL = "https://<프로젝트 id>.supabase.co"
   $env:SUPABASE_SECRET_KEY = "<secret 키>"
   py scripts/upload_supabase.py
   ```
   → 마지막 줄에 `시즌 파일 19개 올림, 테이블에 19개 있음`이 나오면 성공
5. `js/config.js`의 `SUPABASE_URL`, `SUPABASE_KEY`에 Project URL과 **publishable 키**를 넣기 (secret 키는 절대 넣지 않음)
6. 사이트를 열고 개발자 도구 → 네트워크에 `rest/v1/season_data` 요청이 보이면 Supabase에서 읽는 중

- 월 1회 `update_all.py`를 돌릴 때 `SUPABASE_URL`, `SUPABASE_SECRET_KEY` 환경 변수가 있으면 마지막에 자동으로 올림 (작업 스케줄러로 돌리면 `scripts/secrets.bat`에 `set SUPABASE_URL=…`, `set SUPABASE_SECRET_KEY=…` 두 줄을 적어 둠. 이 파일은 `.gitignore`에 있어서 GitHub에 올라가지 않음. `update_monthly.bat`에 직접 적으면 키가 저장소에 올라가므로 안 됨)
- 설정을 비워 두면 예전처럼 `data/` 폴더의 JSON을 읽음

### 데이터 갱신 (월 1회)
```
py scripts/update_all.py
```
- 처음 실행은 수십 분 걸리고(EsportSettings 선수 페이지, Wayback 보관본), 다음부터는 캐시 덕분에 바뀐 부분만 받음
- 연락처를 넣으려면 먼저 `$env:PROGEAR_CONTACT = "내 이메일"` (PowerShell)

### 자동 실행 (선택)
1. Windows 검색에서 "작업 스케줄러" 실행 → "기본 작업 만들기"
2. 트리거: **매월**, 1일
3. 동작: 프로그램 시작 → `ProGear\scripts\update_monthly.bat`
4. 실행 기록은 `scripts/work/update.log`에 남음

### 새 시즌 / 새 대회 추가
- 새 대회: `scripts/sources/competitions.json`의 해당 게임 · 시즌 목록에 Liquipedia 문서 제목 추가
- 새 시즌(예: 2027): `js/config.js`의 `SEASONS`, `CURRENT_SEASON`, 게임별 `seasons`와 `scripts/fetch_liquipedia.py`의 `GAME_SEASONS`, `scripts/fetch_gear.py`의 `CURRENT_SEASON`을 함께 바꿈
- CSS / JS를 고친 뒤에는 HTML 5개의 `?v=2026101902` 숫자를 더 큰 값(예: 날짜 + 번호)으로 바꿔야 배포된 사이트 방문자 브라우저가 예전 파일을 쓰지 않음
- 개발할 때는 `py scripts/serve.py`로 열면 캐시를 쓰지 않아서 고친 내용이 바로 보임 (`py -m http.server`는 예전 파일이 남을 수 있음)
- 제품명이 이상하게 묶이면: `data/aliases.json`의 `colors`(색상), `variantWords`(애매한 꼬리말), `models`(표준 이름)에 추가하고 `py scripts/build_data.py`만 다시 실행

---

## 13. 참고

- Liquipedia: https://liquipedia.net/
- Liquipedia API 이용 약관: https://liquipedia.net/api-terms-of-use
- ProSettings.net: https://prosettings.net/
- EsportSettings: https://www.esportsettings.com/
- Wayback Machine: https://web.archive.org/
