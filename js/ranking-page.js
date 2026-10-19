// 순위 화면: 게임 탭 + 시즌 선택(전체 시즌 포함) + 장비 탭 + 순위표 + 상세 패널

mountHeader('ranking', { season: true });
mountFooter();

const ALL = 'all'; // 전체 시즌 총 랭킹

const els = {
  seasonSelect: document.getElementById('season-select'),
  gameTabs: document.getElementById('game-tabs'),
  gearTabs: document.getElementById('gear-tabs'),
  title: document.getElementById('page-title'),
  listTitle: document.getElementById('list-title'),
  listTotal: document.getElementById('list-total'),
  listMeta: document.getElementById('list-meta'),
  rankBody: document.getElementById('rank-body'),
  detail: document.getElementById('detail'),
};

// ----- 상태 -----
const params = getParams();
const state = {
  game: getGame(params.get('game')) || GAMES[0],
  season: null, // 숫자 또는 'all'
  gear: getGearType(params.get('gear')) ? params.get('gear') : GEAR_TYPES[0].id,
  data: null,
  ranking: null,
  selectedKey: null,
  loadId: 0,
};
state.season = params.get('season') === ALL ? ALL : normalizeSeason(state.game, params.get('season') ?? CURRENT_SEASON);

function seasonFor(game, season) {
  return season === ALL ? ALL : normalizeSeason(game, season);
}

function allSeasonsText(game = state.game) {
  return `전체 시즌 (${Math.min(...game.seasons)}~${Math.max(...game.seasons)})`;
}

function currentSeasonText() {
  return state.season === ALL ? allSeasonsText() : seasonText(state.season, state.game.seasonLabels[state.season]);
}

// ----- 화면 그리기 -----
function renderGameTabs() {
  els.gameTabs.innerHTML = GAMES.map((g) => {
    const active = g.id === state.game.id;
    return `<a class="game-tab${active ? ' active' : ''}" href="${rankingUrl(g.id, seasonFor(g, state.season), state.gear)}" data-game="${g.id}"
      style="--from:${g.theme.from}"${active ? ' aria-current="page"' : ''}><span class="dot"></span>${esc(g.name)}</a>`;
  }).join('');
}

function renderGearTabs() {
  els.gearTabs.innerHTML = GEAR_TYPES.map((t) => {
    const active = t.id === state.gear;
    return `<button type="button" role="tab" data-gear="${t.id}" class="${active ? 'active' : ''}" aria-selected="${active}">${esc(t.name)}</button>`;
  }).join('');
}

function renderHeader() {
  const label = state.season === ALL ? null : state.game.seasonLabels[state.season];
  els.title.innerHTML = `${esc(state.game.name)}${label ? ` <span class="badge badge-dark">${esc(label)}</span>` : ''}${state.season === ALL ? ' <span class="badge">총 랭킹</span>' : ''}`;
  document.title = `${state.game.name} ${state.season === ALL ? '전체 시즌 총' : `${state.season} 시즌`} 장비 순위 · ProGear`;
  fillSeasonSelect(els.seasonSelect, state.game.seasons, state.season, state.game.seasonLabels);
  els.seasonSelect.insertAdjacentHTML('afterbegin', `<option value="${ALL}"${state.season === ALL ? ' selected' : ''}>${esc(allSeasonsText())}</option>`);
  setNavContext(state.game.id, state.season === ALL ? Math.max(...state.game.seasons) : state.season);
  renderGameTabs();
  renderGearTabs();
}

function listTitleText() {
  const gearName = getGearType(state.gear).name;
  return `${state.game.name} ${currentSeasonText()} · 프로 선수들의 ${gearName} 사용 순위`;
}

function emptyDetail() {
  els.detail.innerHTML = `
    <p class="eyebrow">Product Detail</p>
    <div class="empty"><p>순위에서 장비를 고르면<br>자세한 정보가 여기에 나와요.</p></div>`;
}

function renderLoading() {
  els.listTitle.textContent = '불러오는 중…';
  els.listTotal.textContent = '';
  els.listMeta.hidden = true;
  els.rankBody.innerHTML = '';
  els.detail.innerHTML = '';
}

function renderEmpty() {
  els.listTitle.textContent = listTitleText();
  els.listTotal.textContent = '데이터 없음';
  els.listMeta.hidden = true;
  els.rankBody.innerHTML = emptyState('데이터를 불러오지 못했어요',
    location.protocol === 'file:' ? dataErrorText()
      : `<code>data/${esc(state.game.id)}/</code> 데이터 파일이 없어요. <code>py scripts/update_all.py</code>로 데이터를 만들어 주세요.`,
    state.gear);
  emptyDetail();
}

function renderList() {
  const { total, items } = state.ranking;
  const gearName = getGearType(state.gear).name;

  els.listTitle.textContent = listTitleText();
  els.listTotal.textContent = `장비 확인 ${total}명 기준`;

  const roster = state.data.players.length;
  const old = state.data.players.filter((p) => p.gear[state.gear] && p.gearFromSeason).length;
  const meta = [state.season === ALL
    ? `${allSeasonsText()} 선수 ${roster}명 중 ${total}명 확인 (선수마다 가장 최근 시즌 장비로 한 번씩 셈)`
    : `로스터 ${roster}명 중 ${total}명 확인`];
  if (old) meta.push(`그중 ${old}명은 이전 시즌 정보`);
  const sources = state.data.gearSources || [];
  const siteNames = [...new Set(sources.map((s) => s.site.replace(/ \(.*\)$/, '')))];
  if (siteNames.length) meta.push(`출처 ${siteNames.join(', ')}`);
  els.listMeta.innerHTML = `${esc(meta.join(' · '))}${coverageWarning(total, roster)}`;
  els.listMeta.hidden = false;

  if (!items.length) {
    els.rankBody.innerHTML = emptyState(`확인된 ${gearName} 정보가 없어요`,
      `이 시즌 선수들의 ${esc(gearName)} 정보를 출처에서 찾지 못했어요.`, state.gear);
    return;
  }

  els.rankBody.innerHTML = `<ol class="rank-list">${items.map((item, i) => `
    <li>
      <button type="button" class="rank-item${item.key === state.selectedKey ? ' active' : ''}${i >= 3 ? ' dim' : ''}" data-key="${esc(item.key)}">
        <span class="rank-no">${String(item.rank).padStart(2, '0')}</span>
        <span>
          <span class="rank-name">${esc(item.brand)} ${esc(item.model)}</span>
          <span class="rank-brand">${esc(item.brand)}</span>
        </span>
        <span class="rank-usage">
          <span class="rank-count">${item.count}명</span>
          <span class="bar" aria-hidden="true"><span style="width:${item.rate.toFixed(1)}%"></span></span>
        </span>
      </button>
    </li>`).join('')}</ol>`;
}

function teamName(teamId) {
  const team = (state.data.teams || []).find((t) => t.id === teamId);
  return team ? team.name : teamId || '';
}

function renderDetail() {
  const item = state.ranking && state.ranking.items.find((it) => it.key === state.selectedKey);
  if (!item) {
    emptyDetail();
    return;
  }

  const gearName = getGearType(state.gear).name;

  els.detail.innerHTML = `
    <p class="eyebrow">Product Detail</p>
    <div class="detail-icon">${gearIcon(state.gear)}</div>
    <h2>${esc(item.brand)} ${esc(item.model)}</h2>
    <p class="detail-sub">${esc(item.brand)} · ${esc(gearName)}</p>
    <div class="detail-count"><b>${item.count}</b><span>명 사용 · ${item.rank}위</span></div>
    <div class="bar bar-accent" aria-hidden="true"><span style="width:${item.rate.toFixed(1)}%"></span></div>
    <div class="stat-grid">
      <div class="stat"><small>사용률</small><b>${item.rate.toFixed(1)}%</b></div>
      <div class="stat"><small>시즌</small><b>${esc(currentSeasonText())}</b></div>
    </div>
    <div class="detail-players">
      <p class="eyebrow">Using Pro Players</p>
      <ul class="chips">${item.players.map((p) => {
        const extra = [teamName(p.team), p.color, p.edition, p.fromSeason ? `${p.fromSeason} 시즌 정보` : null].filter(Boolean).join(' · ');
        return `<li><a class="chip" href="${playerUrl(state.game.id, p.id)}">${esc(p.name)}${extra ? `<small>${esc(extra)}</small>` : ''}</a></li>`;
      }).join('')}</ul>
    </div>`;
}

// ----- 데이터 -----

// 전체 시즌: 모든 시즌 파일을 합쳐 선수마다 가장 최근 시즌 기록 하나만 남김
async function loadAllSeasons(game) {
  const seasons = [...game.seasons].sort((a, b) => a - b);
  const datas = (await Promise.all(seasons.map((s) => loadSeasonData(game.id, s)))).filter(Boolean);
  if (!datas.length) return null;
  const players = new Map();
  const teams = new Map();
  const sources = [];
  datas.forEach((d) => {
    d.teams.forEach((t) => teams.set(t.id, t));
    sources.push(...(d.gearSources || []));
    d.players.forEach((p) => {
      const hasGear = Object.values(p.gear).some(Boolean);
      const prev = players.get(p.id);
      // 나중 시즌이 앞 시즌을 덮어씀. 단, 나중 시즌에 장비가 없으면 앞 시즌 장비를 유지
      if (!prev || hasGear || !Object.values(prev.gear).some(Boolean)) players.set(p.id, p);
    });
  });
  return { players: [...players.values()], teams: [...teams.values()], gearSources: sources };
}

async function load() {
  const id = ++state.loadId;
  renderHeader();
  renderLoading();

  const data = state.season === ALL
    ? await loadAllSeasons(state.game)
    : await loadSeasonData(state.game.id, state.season);
  if (id !== state.loadId) return; // 그사이 다른 선택을 했으면 무시

  state.data = data;
  if (!data || !Array.isArray(data.players)) {
    state.ranking = null;
    renderEmpty();
    return;
  }
  computeAndRender();
}

function computeAndRender() {
  state.ranking = computeRanking(state.data.players, state.gear);
  state.selectedKey = state.ranking.items.length ? state.ranking.items[0].key : null;
  renderList();
  renderDetail();
}

function syncUrl() {
  updateParams({ game: state.game.id, season: state.season, gear: state.gear });
}

// ----- 이벤트 -----
els.seasonSelect.addEventListener('change', () => {
  state.season = els.seasonSelect.value === ALL ? ALL : Number(els.seasonSelect.value);
  syncUrl();
  load();
});

els.gameTabs.addEventListener('click', (e) => {
  const tab = e.target.closest('[data-game]');
  if (!tab || e.metaKey || e.ctrlKey || e.shiftKey) return; // 새 탭으로 열기는 그대로 둠
  e.preventDefault();
  state.game = getGame(tab.dataset.game);
  state.season = seasonFor(state.game, state.season);
  syncUrl();
  load();
});

els.gearTabs.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-gear]');
  if (!btn || btn.dataset.gear === state.gear) return;
  state.gear = btn.dataset.gear;
  syncUrl();
  renderGearTabs();
  if (state.data && Array.isArray(state.data.players)) computeAndRender();
  else renderEmpty();
});

els.rankBody.addEventListener('click', (e) => {
  const row = e.target.closest('[data-key]');
  if (!row) return;
  state.selectedKey = row.dataset.key;
  els.rankBody.querySelectorAll('.rank-item').forEach((r) => r.classList.toggle('active', r === row));
  renderDetail();
});

syncUrl();
load();
