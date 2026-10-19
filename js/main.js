// 메인 화면: 시즌 선택(전체 시즌 포함) + 게임 카드 5개

mountHeader('games', { season: true });
mountFooter();

const ALL = 'all'; // 전체 시즌 총 랭킹

const seasonSelect = document.getElementById('season-select');
const gameGrid = document.getElementById('game-grid');
const seasonNote = document.getElementById('season-note');

let season = getParams().get('season') === ALL ? ALL : parseSeason(getParams().get('season'));
let stats = null; // data/index.json의 시즌별 선수 수 (없어도 화면은 동작)

function renderCard(game) {
  const all = season === ALL;
  const available = all || game.seasons.includes(season);
  const label = all ? null : game.seasonLabels[season];
  const style = `--from:${game.theme.from};--to:${game.theme.to};--a:${game.theme.a};--b:${game.theme.b}`;
  const [main, sub] = game.title;
  const s = !all && stats && stats[game.id] && stats[game.id][season];
  const low = available && s && isLowCoverage(s.withGear, s.players);
  const caption = !available
    ? `${Math.min(...game.seasons)} 시즌부터`
    : all ? `${Math.min(...game.seasons)}~${Math.max(...game.seasons)} 총 랭킹`
      : s ? `장비 확인 ${s.withGear}/${s.players}명` : seasonText(season, label);

  const art = `
    <div class="art" style="${style}">
      <span class="shape shape-b"></span>
      <span class="shape shape-a"></span>
      <span class="shade"></span>
      <span class="tag">${esc(game.tag)}</span>
      ${label ? `<span class="badge badge-dark">${esc(label)}</span>` : ''}
      <span class="title"><b>${esc(main)}</b>${sub ? `<span>${esc(sub)}</span>` : ''}</span>
    </div>
    <div class="caption">
      <span>${esc(game.name)}</span>
      <small>${esc(caption)}</small>
    </div>
    ${low ? '<p class="card-warn">확인 인원이 적어 일부 선수 기준이에요</p>' : ''}`;

  if (!available) {
    return `<div class="game-card is-disabled" aria-disabled="true" title="${season} 시즌에는 다루지 않아요">${art}</div>`;
  }
  return `<a class="game-card" href="${rankingUrl(game.id, season)}">${art}</a>`;
}

function render() {
  gameGrid.innerHTML = GAMES.map(renderCard).join('');
  if (season === ALL) {
    seasonNote.textContent = '전체 시즌 · 선수마다 가장 최근 장비로 한 번씩 센 총 랭킹';
    setNavContext(GAMES[0].id, CURRENT_SEASON);
  } else {
    const count = GAMES.filter((g) => g.seasons.includes(season)).length;
    seasonNote.textContent = `${season} 시즌 · ${count}개 게임`;
    setNavContext(GAMES[0].id, season);
  }
}

fillSeasonSelect(seasonSelect, SEASONS, season);
seasonSelect.insertAdjacentHTML('afterbegin', `<option value="${ALL}"${season === ALL ? ' selected' : ''}>전체 시즌 (총 랭킹)</option>`);
seasonSelect.addEventListener('change', () => {
  season = seasonSelect.value === ALL ? ALL : Number(seasonSelect.value);
  updateParams({ season });
  render();
});

render();
loadIndex().then((index) => {
  if (!index) return;
  stats = index.seasons;
  render();
});
