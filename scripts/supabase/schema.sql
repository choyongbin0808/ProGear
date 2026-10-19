-- ProGear Supabase 테이블
-- Supabase 대시보드 → SQL Editor에 붙여 넣고 한 번 실행
--
-- 사이트가 읽던 JSON 파일을 그대로 jsonb로 저장함
--   data/{game}/{season}.json → season_data (game, season)
--   data/index.json           → site_index (id = 'main')
-- 방문자(anon 키)는 읽기만 가능, 쓰기는 secret(service_role) 키로 올리는 scripts/upload_supabase.py만 함

create table if not exists public.season_data (
  game text not null,
  season integer not null,
  data jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (game, season)
);

create table if not exists public.site_index (
  id text primary key default 'main',
  data jsonb not null,
  updated_at timestamptz not null default now()
);

alter table public.season_data enable row level security;
alter table public.site_index enable row level security;

drop policy if exists "누구나 읽기" on public.season_data;
create policy "누구나 읽기" on public.season_data for select to anon, authenticated using (true);

drop policy if exists "누구나 읽기" on public.site_index;
create policy "누구나 읽기" on public.site_index for select to anon, authenticated using (true);

grant select on public.season_data, public.site_index to anon, authenticated;
