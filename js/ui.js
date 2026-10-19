// 여러 화면에서 같이 쓰는 화면 도우미

function esc(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getParams() {
  return new URLSearchParams(location.search);
}

// 새로고침해도 선택이 유지되도록 주소에 기록
function updateParams(values) {
  const params = getParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') params.delete(key);
    else params.set(key, value);
  });
  history.replaceState(null, '', `${location.pathname}?${params}`);
}

function seasonText(season, label) {
  return label ? `${season} 시즌 (${label})` : `${season} 시즌`;
}

// <select>에 시즌 목록을 채움. labels: { 2023: 'CS:GO' }
function fillSeasonSelect(select, seasons, current, labels = {}) {
  select.innerHTML = [...seasons]
    .sort((a, b) => b - a)
    .map((s) => `<option value="${s}"${s === current ? ' selected' : ''}>${esc(seasonText(s, labels[s]))}</option>`)
    .join('');
}

function rankingUrl(gameId, season, gear) {
  const params = new URLSearchParams({ game: gameId, season });
  if (gear) params.set('gear', gear);
  return `ranking.html?${params}`;
}

function teamUrl(gameId, season, teamId) {
  const params = new URLSearchParams({ game: gameId, season });
  if (teamId) params.set('team', teamId);
  return `team.html?${params}`;
}

function playerUrl(gameId, playerId) {
  return `player.html?${new URLSearchParams({ game: gameId, id: playerId })}`;
}

// 장비 한 개를 "브랜드 모델" + 색상 / 에디션 배지로 표시
function gearLabel(item, { withColor = true, fromSeason = null } = {}) {
  if (!item) return '<span class="muted">미확인</span>';
  const extras = [];
  if (withColor && item.color) extras.push(`<span class="tag-color">${esc(item.color)}</span>`);
  if (item.edition) extras.push(`<span class="tag-edition">${esc(item.edition)}</span>`);
  if (fromSeason) extras.push(fromSeasonTag(fromSeason));
  return `<span class="gear-name">${esc(item.brand)} ${esc(item.model)}</span>${extras.length ? ` ${extras.join(' ')}` : ''}`;
}

// 이 시즌 정보가 없어 이전 시즌 장비를 보여줄 때 붙이는 표시
function fromSeasonTag(season) {
  return `<span class="tag-old" title="이 시즌 장비 정보가 없어 ${season} 시즌에 확인된 장비를 표시해요">${season} 시즌 정보</span>`;
}

// ----- 공통 헤더 / 푸터 -----
const NAV_ITEMS = [
  { id: 'games', label: '게임', href: 'index.html' },
  { id: 'ranking', label: '장비 순위', href: 'ranking.html' },
  { id: 'players', label: '선수', href: 'search.html' },
  { id: 'teams', label: '팀', href: 'team.html' },
];

function mountHeader(active, { season = false } = {}) {
  const header = document.getElementById('site-header');
  const q = active === 'players' ? getParams().get('q') || '' : '';
  header.className = 'site-header';
  header.innerHTML = `
    <div class="container">
      <a class="logo" href="index.html" aria-label="ProGear 홈">
        <span class="logo-mark">P</span>
        <span class="logo-text"><strong>PRO GEAR</strong><span>RANKING</span></span>
      </a>
      <nav class="nav" aria-label="주요 메뉴">
        ${NAV_ITEMS.map((n) => `<a href="${n.href}" data-nav="${n.id}"${n.id === active ? ' class="active" aria-current="page"' : ''}>${n.label}</a>`).join('')}
      </nav>
      <div class="header-right">
        <form class="search-form" action="search.html" method="get" role="search">
          <label class="visually-hidden" for="header-search">선수 · 팀 검색</label>
          <input id="header-search" name="q" type="search" placeholder="선수 · 팀 검색" value="${esc(q)}" autocomplete="off">
        </form>
        ${season ? '<label class="visually-hidden" for="season-select">시즌 선택</label><select id="season-select" class="select"></select>' : ''}
      </div>
    </div>`;
}

function mountFooter() {
  const footer = document.getElementById('site-footer');
  footer.className = 'site-footer';
  footer.innerHTML = `
    <div class="container">
      선수 / 팀 정보: <a href="https://liquipedia.net/" target="_blank" rel="noopener">Liquipedia</a> (CC BY-SA 3.0) ·
      장비 정보: <a href="https://prosettings.net/" target="_blank" rel="noopener">ProSettings.net</a>,
      <a href="https://www.esportsettings.com/" target="_blank" rel="noopener">EsportSettings</a>,
      <a href="https://esportsmice.com/" target="_blank" rel="noopener">EsportsMice</a>(PUBG · Overwatch 마우스),
      과거 시즌은 <a href="https://web.archive.org/" target="_blank" rel="noopener">Wayback Machine</a> 보관본
    </div>`;
}

// 헤더의 메뉴 링크에 현재 게임 / 시즌을 이어 붙임
function setNavContext(gameId, season) {
  const map = {
    games: `index.html?season=${season}`,
    ranking: rankingUrl(gameId, season),
    teams: teamUrl(gameId, season),
  };
  Object.entries(map).forEach(([id, href]) => {
    const a = document.querySelector(`[data-nav="${id}"]`);
    if (a) a.href = href;
  });
}

const GEAR_ICONS = {
  mouse: '<rect x="7" y="3" width="10" height="18" rx="5"/><line x1="12" y1="3" x2="12" y2="9"/>',
  keyboard: '<rect x="2" y="6" width="20" height="12" rx="2"/><line x1="6" y1="10" x2="6" y2="10"/><line x1="10" y1="10" x2="10" y2="10"/><line x1="14" y1="10" x2="14" y2="10"/><line x1="18" y1="10" x2="18" y2="10"/><line x1="7" y1="14" x2="17" y2="14"/>',
  monitor: '<rect x="2" y="4" width="20" height="13" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
  headset: '<path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="2" y="14" width="5" height="7" rx="2"/><rect x="17" y="14" width="5" height="7" rx="2"/>',
  mousepad: '<rect x="3" y="5" width="18" height="14" rx="3"/><rect x="13" y="8" width="5" height="8" rx="2.5"/>',
};

function gearIcon(type) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${GEAR_ICONS[type]}</svg>`;
}

// 장비 확인 인원이 로스터의 30% 미만이면 "일부 선수 기준" 안내를 보여줌
const LOW_COVERAGE = 0.3;

function isLowCoverage(withGear, roster) {
  return roster > 0 && withGear / roster < LOW_COVERAGE;
}

function coverageWarning(withGear, roster) {
  if (!isLowCoverage(withGear, roster)) return '';
  return `<span class="coverage-warn">장비 출처에 등록된 선수가 로스터의 ${Math.round((withGear / roster) * 100)}%뿐이라, 이 순위는 일부 선수 기준이에요.</span>`;
}

function emptyState(title, text, icon = 'mouse') {
  return `<div class="empty"><div class="empty-icon">${gearIcon(icon)}</div><h3>${esc(title)}</h3><p>${text}</p></div>`;
}
