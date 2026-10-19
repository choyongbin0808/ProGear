// 팀 화면: 게임 → 시즌 → (대회 필터) → 팀 목록 → 팀 선수별 장비 표

mountHeader('teams', { season: true });
mountFooter();

const els = {
  seasonSelect: document.getElementById('season-select'),
  gameTabs: document.getElementById('game-tabs'),
  eyebrow: document.getElementById('eyebrow'),
  title: document.getElementById('page-title'),
  sub: document.getElementById('page-sub'),
  controls: document.getElementById('controls'),
  body: document.getElementById('team-body'),
};

const params = getParams();
const state = {
  game: getGame(params.get('game')) || GAMES[0],
  season: null,
  team: params.get('team') || null,
  competition: params.get('comp') || 'all',
  data: null,
  loadId: 0,
};
state.season = normalizeSeason(state.game, params.get('season') ?? CURRENT_SEASON);

function syncUrl() {
  updateParams({
    game: state.game.id, season: state.season, team: state.team,
    comp: state.competition === 'all' ? null : state.competition,
  });
}

function renderTop() {
  els.gameTabs.innerHTML = GAMES.map((g) => {
    const active = g.id === state.game.id;
    return `<a class="game-tab${active ? ' active' : ''}" href="${teamUrl(g.id, normalizeSeason(g, state.season))}" data-game="${g.id}"
      style="--from:${g.theme.from}"${active ? ' aria-current="page"' : ''}><span class="dot"></span>${esc(g.name)}</a>`;
  }).join('');
  fillSeasonSelect(els.seasonSelect, state.game.seasons, state.season, state.game.seasonLabels);
  setNavContext(state.game.id, state.season);
}

function teamStats(teamId) {
  const players = state.data.players.filter((p) => p.team === teamId);
  return { players, withGear: players.filter((p) => Object.values(p.gear).some(Boolean)).length };
}

function renderTeamList() {
  const label = state.game.seasonLabels[state.season];
  els.eyebrow.textContent = 'Teams';
  els.title.innerHTML = `${esc(state.game.name)} 팀${label ? ` <span class="badge badge-dark">${esc(label)}</span>` : ''}`;
  const roster = state.data.players.length;
  const withGear = state.data.players.filter((p) => Object.values(p.gear).some(Boolean)).length;
  els.sub.innerHTML = `${esc(seasonText(state.season, label))} · 대상 대회에 나온 팀 ${state.data.teams.length}개 · 장비 확인 ${withGear}/${roster}명`
    + (isLowCoverage(withGear, roster) ? '<span class="coverage-warn">장비 출처에 등록된 선수가 적어, 많은 선수가 "미확인"으로 나와요.</span>' : '');
  document.title = `${state.game.name} ${state.season} 시즌 팀 · ProGear`;

  const comps = state.data.competitions;
  els.controls.innerHTML = comps.length > 1 ? `
    <label class="visually-hidden" for="comp-select">대회 선택</label>
    <select id="comp-select" class="select">
      <option value="all">모든 대회</option>
      ${comps.map((c) => `<option value="${esc(c.id)}"${c.id === state.competition ? ' selected' : ''}>${esc(c.name)}</option>`).join('')}
    </select>` : '';

  const teams = state.data.teams
    .filter((t) => state.competition === 'all' || t.competitions.includes(state.competition))
    .map((t) => ({ ...t, ...teamStats(t.id) }))
    .sort((a, b) => b.withGear - a.withGear || a.name.localeCompare(b.name));

  if (!teams.length) {
    els.body.innerHTML = emptyState('이 대회에 등록된 팀이 없어요', '아직 열리지 않은 대회일 수 있어요.');
    return;
  }

  els.body.innerHTML = `<div class="team-grid">${teams.map((t) => `
    <a class="team-card" href="${teamUrl(state.game.id, state.season, t.id)}" data-team="${esc(t.id)}">
      <span class="team-initial" style="--from:${state.game.theme.from}">${esc(t.name.slice(0, 1).toUpperCase())}</span>
      <span class="team-info">
        <b>${esc(t.name)}</b>
        <small>선수 ${t.players.length}명 · 장비 확인 ${t.withGear}명</small>
      </span>
    </a>`).join('')}</div>`;
}

function renderTeam() {
  const team = state.data.teams.find((t) => t.id === state.team);
  if (!team) {
    state.team = null;
    syncUrl();
    renderTeamList();
    return;
  }
  const label = state.game.seasonLabels[state.season];
  const { players, withGear } = teamStats(team.id);
  const compNames = state.data.competitions.filter((c) => team.competitions.includes(c.id)).map((c) => c.name);

  els.eyebrow.innerHTML = `<a class="back-link" href="${teamUrl(state.game.id, state.season)}" data-back>← ${esc(state.game.name)} 팀 목록</a>`;
  els.title.innerHTML = `${esc(team.name)}${label ? ` <span class="badge badge-dark">${esc(label)}</span>` : ''}`;
  els.sub.textContent = `${seasonText(state.season, label)} · 선수 ${players.length}명 중 장비 확인 ${withGear}명 · ${compNames.join(', ')}`;
  els.controls.innerHTML = '';
  document.title = `${team.name} ${state.season} 시즌 장비 · ProGear`;

  const rows = players.map((p) => `
    <tr>
      <th scope="row">
        <a href="${playerUrl(state.game.id, p.id)}" class="player-link">${esc(p.name)}</a>
        ${p.role ? `<small>${esc(p.role)}</small>` : ''}
      </th>
      ${GEAR_TYPES.map((t) => `<td>${gearLabel(p.gear[t.id], { fromSeason: p.gearFromSeason })}</td>`).join('')}
    </tr>`).join('');

  els.body.innerHTML = `
    <div class="panel table-panel">
      <div class="table-scroll">
        <table class="gear-table">
          <thead><tr><th scope="col">선수</th>${GEAR_TYPES.map((t) => `<th scope="col">${esc(t.name)}</th>`).join('')}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
    <p class="note">순위에서는 색상 · 에디션이 달라도 같은 제품으로 셉니다. 여기서는 선수가 쓰는 색상과 에디션까지 표시해요.
      '○○○○ 시즌 정보'는 이 시즌 장비가 확인되지 않아, 가장 최근에 확인된 이전 시즌 장비를 보여준다는 뜻이에요.</p>`;
}

function render() {
  renderTop();
  if (!state.data) {
    els.title.textContent = state.game.name;
    els.sub.textContent = '';
    els.controls.innerHTML = '';
    els.body.innerHTML = emptyState('데이터를 불러오지 못했어요', dataErrorText());
    return;
  }
  if (state.team) renderTeam();
  else renderTeamList();
}

async function load() {
  const id = ++state.loadId;
  renderTop();
  els.body.innerHTML = '<p class="muted">불러오는 중…</p>';
  const data = await loadSeasonData(state.game.id, state.season);
  if (id !== state.loadId) return;
  state.data = data && Array.isArray(data.players) ? data : null;
  render();
}

els.seasonSelect.addEventListener('change', () => {
  state.season = Number(els.seasonSelect.value);
  state.competition = 'all';
  syncUrl();
  load();
});

els.gameTabs.addEventListener('click', (e) => {
  const tab = e.target.closest('[data-game]');
  if (!tab || e.metaKey || e.ctrlKey || e.shiftKey) return;
  e.preventDefault();
  state.game = getGame(tab.dataset.game);
  state.season = normalizeSeason(state.game, state.season);
  state.team = null;
  state.competition = 'all';
  syncUrl();
  load();
});

els.controls.addEventListener('change', (e) => {
  if (e.target.id !== 'comp-select') return;
  state.competition = e.target.value;
  syncUrl();
  renderTeamList();
});

document.addEventListener('click', (e) => {
  const card = e.target.closest('[data-team], [data-back]');
  if (!card || e.metaKey || e.ctrlKey || e.shiftKey) return;
  e.preventDefault();
  state.team = card.dataset.team || null;
  syncUrl();
  render();
  window.scrollTo({ top: 0 });
});

syncUrl();
load();
