// 사이트 전체에서 쓰는 게임 / 시즌 / 장비 설정

// Supabase 연결 (scripts/supabase/schema.sql 참고)
// - URL: 프로젝트 설정 → API의 Project URL
// - KEY: publishable 키(sb_publishable_…) 또는 anon 키. 읽기 전용이라 공개돼도 됨 (secret 키는 절대 넣지 않음)
// 둘 중 하나라도 비어 있으면 data/ 폴더의 JSON 파일을 읽음
const SUPABASE_URL = 'https://djvdtkzqmhdlzcnkwgxx.supabase.co';
const SUPABASE_KEY = '';

const SEASONS = [2023, 2024, 2025, 2026];
const CURRENT_SEASON = 2026;

const GAMES = [
  {
    id: 'lol',
    name: 'League of Legends',
    title: ['LEAGUE', 'OF LEGENDS'],
    tag: 'LCK · LPL · LEC · LCS',
    seasons: [2023, 2024, 2025, 2026],
    seasonLabels: {},
    theme: { from: '#1d5a72', to: '#2e2412', a: '#e2b64a', b: '#5ccfd5' },
  },
  {
    id: 'valorant',
    name: 'VALORANT',
    title: ['VALORANT'],
    tag: 'VCT',
    seasons: [2023, 2024, 2025, 2026],
    seasonLabels: {},
    theme: { from: '#d9706f', to: '#1b1220', a: '#2c2b3c', b: '#f2b3bb' },
  },
  {
    id: 'pubg',
    name: 'PUBG: BATTLEGROUNDS',
    title: ['PUBG', 'BATTLEGROUNDS'],
    tag: 'PGC · PNC · PGS',
    seasons: [2023, 2024, 2025, 2026],
    seasonLabels: {},
    theme: { from: '#c9a43a', to: '#1f1c12', a: '#3a3624', b: '#f4e2a1' },
  },
  {
    id: 'cs2',
    name: 'Counter-Strike 2',
    title: ['COUNTER', 'STRIKE 2'],
    tag: 'MAJOR',
    seasons: [2023, 2024, 2025, 2026],
    // 2023 시즌은 CS2 출시 전이라 CS:GO 대회 기준
    seasonLabels: { 2023: 'CS:GO' },
    theme: { from: '#c9c9c9', to: '#161616', a: '#232323', b: '#8a8a8a' },
  },
  {
    id: 'overwatch',
    name: 'Overwatch 2',
    title: ['OVERWATCH', 'CHAMPIONS SERIES'],
    tag: 'OWCS',
    // 2023 시즌은 제외
    seasons: [2024, 2025, 2026],
    seasonLabels: {},
    theme: { from: '#eea24a', to: '#3a1d0e', a: '#2f2f34', b: '#f3e6cc' },
  },
];

const GEAR_TYPES = [
  { id: 'mouse', name: '마우스' },
  { id: 'keyboard', name: '키보드' },
  { id: 'monitor', name: '모니터' },
  { id: 'headset', name: '헤드셋' },
  { id: 'mousepad', name: '마우스패드' },
];

function getGame(id) {
  return GAMES.find((g) => g.id === id) || null;
}

function getGearType(id) {
  return GEAR_TYPES.find((t) => t.id === id) || null;
}

// 게임에 없는 시즌이면 가장 가까운 시즌으로 바꿈 (예: Overwatch 2023 → 2024)
function normalizeSeason(game, season) {
  const s = Number(season);
  if (game.seasons.includes(s)) return s;
  if (!Number.isFinite(s)) return Math.max(...game.seasons);
  return game.seasons.reduce((best, cur) => (Math.abs(cur - s) < Math.abs(best - s) ? cur : best));
}

function parseSeason(value) {
  const s = Number(value);
  return SEASONS.includes(s) ? s : CURRENT_SEASON;
}
