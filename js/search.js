// 검색 화면: 선수 / 팀 이름으로 찾기 (data/index.json)

mountHeader('players');
mountFooter();

const form = document.getElementById('search-form');
const input = document.getElementById('q');
const filterEl = document.getElementById('game-filter');
const resultsEl = document.getElementById('results');

const params = getParams();
let query = params.get('q') || '';
let gameFilter = getGame(params.get('game')) ? params.get('game') : 'all';
let index = null;

input.value = query;

function key(text) {
  return String(text || '').toLowerCase().normalize('NFKD').replace(/[^a-z0-9가-힣]/g, '');
}

// 정확히 같으면 0, 앞부분이 같으면 1, 포함하면 2, 아니면 -1
function matchScore(name, q) {
  const k = key(name);
  if (!q || !k.includes(q)) return -1;
  if (k === q) return 0;
  return k.startsWith(q) ? 1 : 2;
}

function renderFilter() {
  const options = [{ id: 'all', name: '전체' }, ...GAMES];
  filterEl.innerHTML = options.map((g) => `<button type="button" data-game="${g.id}" class="chip-btn${g.id === gameFilter ? ' active' : ''}" aria-pressed="${g.id === gameFilter}">${esc(g.name)}</button>`).join('');
}

// 같은 선수(게임 + id)의 여러 시즌 기록을 하나로 묶음
function groupPlayers(q) {
  const groups = new Map();
  index.players.forEach((p) => {
    if (gameFilter !== 'all' && p.game !== gameFilter) return;
    const score = matchScore(p.name, q);
    if (score < 0) return;
    const k = `${p.game}:${p.id}`;
    const g = groups.get(k) || { ...p, seasons: [], score, hasGearAny: false };
    g.seasons.push(p.season);
    g.hasGearAny = g.hasGearAny || p.hasGear;
    if (p.season >= Math.max(...g.seasons)) Object.assign(g, { teamName: p.teamName, team: p.team, season: p.season });
    groups.set(k, g);
  });
  return [...groups.values()].sort((a, b) => a.score - b.score || b.hasGearAny - a.hasGearAny || b.season - a.season || a.name.localeCompare(b.name));
}

function groupTeams(q) {
  const groups = new Map();
  index.teams.forEach((t) => {
    if (gameFilter !== 'all' && t.game !== gameFilter) return;
    const score = matchScore(t.name, q);
    if (score < 0) return;
    const k = `${t.game}:${t.id}`;
    const g = groups.get(k) || { ...t, seasons: [], score };
    g.seasons.push(t.season);
    g.season = Math.max(...g.seasons);
    groups.set(k, g);
  });
  return [...groups.values()].sort((a, b) => a.score - b.score || b.season - a.season || a.name.localeCompare(b.name));
}

function seasonRange(seasons) {
  const s = [...new Set(seasons)].sort();
  return s.length > 1 ? `${s[0]}–${s[s.length - 1]}` : `${s[0]}`;
}

function render() {
  renderFilter();
  if (!index) return;
  const q = key(query);
  if (!q) {
    resultsEl.innerHTML = `
      <div class="hint-box">
        <p>선수 이름(예: <a href="search.html?q=Faker">Faker</a>, <a href="search.html?q=TenZ">TenZ</a>, <a href="search.html?q=ZywOo">ZywOo</a>)이나
        팀 이름(예: <a href="search.html?q=T1">T1</a>)을 입력해 보세요.</p>
        <p class="muted">${index.players.length.toLocaleString()}개의 선수 · 시즌 기록에서 찾아요.</p>
      </div>`;
    return;
  }

  const players = groupPlayers(q);
  const teams = groupTeams(q);
  if (!players.length && !teams.length) {
    resultsEl.innerHTML = emptyState(`"${query}" 검색 결과가 없어요`, '철자를 확인하거나 다른 게임 필터를 골라 보세요.');
    return;
  }

  const playerCards = players.slice(0, 60).map((p) => {
    const game = getGame(p.game);
    return `
      <a class="result-card" href="${playerUrl(p.game, p.id)}">
        <span class="result-dot" style="--from:${game.theme.from}"></span>
        <span class="result-main">
          <b>${esc(p.name)}</b>
          <small>${esc(game.name)} · ${esc(p.teamName)}</small>
        </span>
        <span class="result-side">
          <small>${seasonRange(p.seasons)} 시즌</small>
          ${p.hasGearAny ? '<span class="badge">장비 정보</span>' : '<span class="muted small">장비 미확인</span>'}
        </span>
      </a>`;
  }).join('');

  const teamCards = teams.slice(0, 30).map((t) => {
    const game = getGame(t.game);
    return `
      <a class="result-card" href="${teamUrl(t.game, t.season, t.id)}">
        <span class="result-dot" style="--from:${game.theme.from}"></span>
        <span class="result-main"><b>${esc(t.name)}</b><small>${esc(game.name)} · 팀</small></span>
        <span class="result-side"><small>${seasonRange(t.seasons)} 시즌</small></span>
      </a>`;
  }).join('');

  resultsEl.innerHTML = `
    ${players.length ? `<section><h2 class="result-h">선수 <span class="muted">${players.length}</span></h2><div class="result-list">${playerCards}</div></section>` : ''}
    ${teams.length ? `<section><h2 class="result-h">팀 <span class="muted">${teams.length}</span></h2><div class="result-list">${teamCards}</div></section>` : ''}`;
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  query = input.value.trim();
  updateParams({ q: query, game: gameFilter === 'all' ? null : gameFilter });
  const headerInput = document.getElementById('header-search');
  if (headerInput) headerInput.value = query;
  render();
});

input.addEventListener('input', () => {
  query = input.value.trim();
  render();
});

filterEl.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-game]');
  if (!btn) return;
  gameFilter = btn.dataset.game;
  updateParams({ q: query, game: gameFilter === 'all' ? null : gameFilter });
  render();
});

renderFilter();
resultsEl.innerHTML = '<p class="muted">불러오는 중…</p>';
loadIndex().then((data) => {
  index = data;
  if (!index) {
    resultsEl.innerHTML = emptyState('검색 데이터를 불러오지 못했어요', dataErrorText());
    return;
  }
  render();
  if (!query) input.focus();
});
