// 장비 사용 순위 계산
// - brand + model로 묶음: 색상 / 에디션만 다르면 같은 제품, 버전이 다르면 model이 달라서 다른 제품
// - 분모는 해당 장비가 확인된(null이 아닌) 선수 수

function gearKey(item) {
  return `${item.brand} ${item.model}`.trim().toLowerCase();
}

function computeRanking(players, gearType) {
  const groups = new Map();
  let total = 0;

  players.forEach((player) => {
    const item = player.gear && player.gear[gearType];
    if (!item || !item.model) return;
    total += 1;

    const key = gearKey(item);
    if (!groups.has(key)) {
      groups.set(key, { key, brand: item.brand, model: item.model, players: [] });
    }
    groups.get(key).players.push({
      id: player.id,
      name: player.name,
      team: player.team,
      color: item.color || null,
      edition: item.edition || null,
      fromSeason: player.gearFromSeason || null, // 이전 시즌 장비로 채운 경우
    });
  });

  const items = [...groups.values()]
    .map((g) => ({ ...g, count: g.players.length }))
    .sort((a, b) => b.count - a.count || `${a.brand} ${a.model}`.localeCompare(`${b.brand} ${b.model}`));

  // 같은 수는 같은 순위 (1, 2, 2, 4 …)
  items.forEach((item, i) => {
    item.rank = i > 0 && items[i - 1].count === item.count ? items[i - 1].rank : i + 1;
    item.rate = total ? (item.count / total) * 100 : 0;
    item.players.sort((a, b) => a.name.localeCompare(b.name));
  });

  return { total, items };
}
