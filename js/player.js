// 선수 화면: 프로필 + 장비 5종(색상 / 에디션) + 시즌별 장비 변화 + 출처

mountHeader('players');
mountFooter();

const main = document.getElementById('player-main');
const params = getParams();
const game = getGame(params.get('game'));
const playerId = params.get('id');

function sameGear(a, b) {
  if (!a || !b) return !a && !b;
  return a.brand === b.brand && a.model === b.model;
}

const SITE_NAMES = { prosettings: 'ProSettings.net', esportsettings: 'EsportSettings', esportsmice: 'EsportsMice' };

function sourceLinks(record) {
  return (record.gearSources || []).map((url) => {
    const site = url.includes('web.archive.org') ? 'Wayback Machine'
      : url.includes('esportsettings') ? 'EsportSettings'
        : url.includes('esportsmice') ? 'EsportsMice' : 'ProSettings.net';
    return `<a href="${esc(url)}" target="_blank" rel="noopener">${site}</a>`;
  }).join(' · ');
}

function render(entries) {
  // entries: [{ season, data, record }] 최신 시즌이 앞
  const latest = entries[0];
  const withGear = entries.find((e) => Object.values(e.record.gear).some(Boolean));
  const shown = withGear || latest;
  const team = latest.data.teams.find((t) => t.id === latest.record.team);
  const label = game.seasonLabels[shown.season];

  document.title = `${latest.record.name} 장비 · ProGear`;

  const gearCards = GEAR_TYPES.map((t) => {
    const item = shown.record.gear[t.id];
    return `
      <div class="gear-card${item ? '' : ' is-empty'}">
        <div class="gear-card-head"><span class="gear-ico">${gearIcon(t.id)}</span><small>${esc(t.name)}</small></div>
        ${item ? `
          <b>${esc(item.brand)} ${esc(item.model)}</b>
          <div class="gear-tags">
            ${item.color ? `<span class="tag-color">${esc(item.color)}</span>` : ''}
            ${item.edition ? `<span class="tag-edition">${esc(item.edition)}</span>` : ''}
            ${shown.record.gearFromSeason ? fromSeasonTag(shown.record.gearFromSeason) : ''}
          </div>
          <small class="muted">${SITE_NAMES[item.site] || 'ProSettings.net'}</small>
          <a class="gear-rank-link" href="${rankingUrl(game.id, shown.season, t.id)}">${shown.season} 시즌 ${esc(t.name)} 순위 보기 →</a>`
        : '<b class="muted">미확인</b><small class="muted">출처에서 찾지 못했어요</small>'}
      </div>`;
  }).join('');

  const historyRows = entries.map((e, i) => {
    const prev = entries[i + 1];
    const seasonLabel = game.seasonLabels[e.season];
    const teamName = (e.data.teams.find((t) => t.id === e.record.team) || {}).name || e.record.team;
    return `
      <tr>
        <th scope="row">
          <a href="${teamUrl(game.id, e.season, e.record.team)}">${e.season}${seasonLabel ? ` <span class="badge badge-dark">${esc(seasonLabel)}</span>` : ''}</a>
          <small>${esc(teamName)}</small>
        </th>
        ${GEAR_TYPES.map((t) => {
          const cur = e.record.gear[t.id];
          const changed = prev && cur && prev.record.gear[t.id] && !sameGear(cur, prev.record.gear[t.id]);
          return `<td>${gearLabel(cur, { fromSeason: e.record.gearFromSeason })}${changed ? ' <span class="tag-change">변경</span>' : ''}</td>`;
        }).join('')}
      </tr>`;
  }).join('');

  const sourceRows = entries.map((e) => `
    <li><b>${e.season} 시즌</b>${e.record.gearFromSeason ? ` <span class="muted">(${e.record.gearFromSeason} 시즌 정보 사용)</span>` : ''} ${sourceLinks(e.record) || '<span class="muted">장비 출처 없음</span>'}
      ${e.record.gearUpdatedAt ? `<span class="muted">· 수정일 ${esc(e.record.gearUpdatedAt)}</span>` : ''}
      ${e.record.gearCheckedAt ? `<span class="muted">· 확인일 ${esc(e.record.gearCheckedAt)}</span>` : ''}</li>`).join('');

  main.innerHTML = `
    <div class="page-head">
      <p class="eyebrow"><a class="back-link" href="search.html?q=${encodeURIComponent(latest.record.name)}">← 검색</a></p>
      <div class="player-head">
        <span class="player-avatar" style="--from:${game.theme.from};--to:${game.theme.to}">${esc(latest.record.name.slice(0, 1).toUpperCase())}</span>
        <div>
          <h1 class="page-h1">${esc(latest.record.name)}</h1>
          <p class="page-sub">
            <span class="game-pill" style="--from:${game.theme.from}"><span class="dot"></span>${esc(game.name)}</span>
            ${team ? `<a href="${teamUrl(game.id, latest.season, team.id)}">${esc(team.name)}</a>` : ''}
            ${latest.record.role ? ` · ${esc(latest.record.role)}` : ''}
            · <a href="${esc(latest.record.liquipedia)}" target="_blank" rel="noopener">Liquipedia</a>
          </p>
        </div>
      </div>
    </div>

    <section class="section-block">
      <div class="block-head">
        <h2>${esc(seasonText(shown.season, label))} 장비</h2>
        <small class="muted">${!withGear ? '확인된 장비가 없어요'
          : shown.record.gearFromSeason ? `이 시즌 정보가 없어 가장 최근에 확인된 ${shown.record.gearFromSeason} 시즌 장비를 표시해요`
          : '시즌 마지막으로 사용한 장비'}</small>
      </div>
      <div class="gear-cards">${gearCards}</div>
    </section>

    <section class="section-block">
      <div class="block-head"><h2>시즌별 장비</h2><small class="muted">앞 시즌과 모델이 다르면 '변경'으로 표시</small></div>
      <div class="panel table-panel">
        <div class="table-scroll">
          <table class="gear-table">
            <thead><tr><th scope="col">시즌 · 팀</th>${GEAR_TYPES.map((t) => `<th scope="col">${esc(t.name)}</th>`).join('')}</tr></thead>
            <tbody>${historyRows}</tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="section-block">
      <div class="block-head"><h2>출처</h2></div>
      <ul class="source-list">${sourceRows}</ul>
    </section>`;
}

async function init() {
  if (!game || !playerId) {
    main.innerHTML = emptyState('선수를 찾을 수 없어요', '<a href="search.html">검색</a>에서 선수를 찾아 주세요.');
    return;
  }
  const index = await loadIndex();
  if (!index) {
    main.innerHTML = emptyState('데이터를 불러오지 못했어요', dataErrorText());
    return;
  }
  const seasons = [...new Set(index.players.filter((p) => p.game === game.id && p.id === playerId).map((p) => p.season))].sort((a, b) => b - a);
  if (!seasons.length) {
    main.innerHTML = emptyState('선수를 찾을 수 없어요', '<a href="search.html">검색</a>에서 다시 찾아 주세요.');
    return;
  }
  const datas = await Promise.all(seasons.map((s) => loadSeasonData(game.id, s)));
  const entries = seasons.map((season, i) => {
    const data = datas[i];
    const record = data && data.players.find((p) => p.id === playerId);
    return record ? { season, data, record } : null;
  }).filter(Boolean);
  if (!entries.length) {
    main.innerHTML = emptyState('데이터를 불러오지 못했어요', dataErrorText());
    return;
  }
  render(entries);
}

init();
