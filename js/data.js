// 데이터 불러오기
// - Supabase 설정(config.js)이 있으면 Supabase 테이블에서 읽음
//   season_data(game, season) → 게임 + 시즌 데이터, site_index('main') → 검색 / 선수 / 팀 화면용 요약
// - 설정이 없거나 Supabase에서 못 불러오면 data/ 폴더의 JSON 파일을 읽음
//   data/{game}/{season}.json, data/index.json
// 둘 다 못 불러오면 null을 돌려줌

const dataCache = new Map();
const useSupabase = Boolean(SUPABASE_URL && SUPABASE_KEY);

function fetchJson(url, options) {
  return fetch(url, { cache: 'no-cache', ...options })
    .then((res) => (res.ok ? res.json() : null))
    .catch(() => null);
}

// Supabase REST(PostgREST)로 한 행의 data 칸만 받음 (행이 없으면 null)
function fetchSupabase(table, filters) {
  const headers = { apikey: SUPABASE_KEY, Accept: 'application/vnd.pgrst.object+json' };
  // 예전 형식 anon 키(JWT)는 Authorization에도 넣음. 새 형식(sb_publishable_…)은 apikey만 씀
  if (!SUPABASE_KEY.startsWith('sb_')) headers.Authorization = `Bearer ${SUPABASE_KEY}`;
  const query = new URLSearchParams({ select: 'data', ...filters });
  return fetchJson(`${SUPABASE_URL.replace(/\/$/, '')}/rest/v1/${table}?${query}`, { headers })
    .then((row) => (row ? row.data : null));
}

function loadCached(key, fromSupabase, localPath) {
  if (dataCache.has(key)) return dataCache.get(key);
  const promise = (useSupabase ? fromSupabase() : Promise.resolve(null))
    .then((data) => {
      if (data) return data;
      if (useSupabase) console.warn(`Supabase에서 ${key}를 불러오지 못해 ${localPath} 파일을 읽어요.`);
      return fetchJson(localPath);
    });
  dataCache.set(key, promise);
  return promise;
}

function loadSeasonData(gameId, season) {
  return loadCached(
    `${gameId}/${season}`,
    () => fetchSupabase('season_data', { game: `eq.${gameId}`, season: `eq.${season}` }),
    `data/${gameId}/${season}.json`,
  );
}

function loadIndex() {
  return loadCached('index', () => fetchSupabase('site_index', { id: 'eq.main' }), 'data/index.json');
}

function dataErrorText() {
  return location.protocol === 'file:'
    ? '파일을 직접 열면 브라우저가 JSON 불러오기를 막아요. VS Code Live Server 등 로컬 서버로 열어 주세요.'
    : '데이터를 불러오지 못했어요.';
}
