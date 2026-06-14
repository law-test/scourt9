-- 법원직.com — Supabase 스키마 (콘텐츠 공개읽기 + 사용자 RLS)
-- 적용: Supabase SQL Editor에 붙여넣기 → 이후 seed.sql 실행

-- ===== 콘텐츠 =====
create table if not exists subjects (
  id serial primary key,
  slug text unique not null,
  name text not null,
  sort int default 0
);

create table if not exists articles (
  id serial primary key,
  subject_id int references subjects(id) on delete cascade,
  article_no text not null,        -- 제262조
  title text,                      -- 청구의 변경
  body text,                       -- 조문 본문(법제처)
  pyeon text, jang text,
  anchor text,                     -- #제262조
  unique (subject_id, article_no)
);

create table if not exists exams (
  id serial primary key,
  subject_id int references subjects(id) on delete cascade,
  year int, season text,           -- 상/하/null
  name text default '법원직 9급',
  answer_key_source text
);

create table if not exists atoms (
  id bigserial primary key,
  subject_id int references subjects(id) on delete cascade,
  article_id int references articles(id) on delete set null,
  article_no text,                 -- 비정규화(조회 편의)
  pyeon text,
  ans char(1) default 'O',         -- 대표지문은 O
  statement text not null,         -- O 법리
  ref text,                        -- 근거(조문/판례)
  freq int default 1,              -- 빈출 횟수
  category text, topic text,
  verified boolean default false,
  created_at timestamptz default now()
);

create table if not exists atom_traps (   -- X 함정(틀린 지문)
  id bigserial primary key,
  atom_id bigint references atoms(id) on delete cascade,
  statement text not null,
  source_label text                -- 2008 문10-2
);

create table if not exists atom_sources ( -- 출처(연도별); 빈출수 = count(*)
  id bigserial primary key,
  atom_id bigint references atoms(id) on delete cascade,
  exam_id int references exams(id),
  source_label text,               -- 2024 문10-2
  year int, qno int
);

create table if not exists verifications (
  id bigserial primary key,
  atom_id bigint references atoms(id) on delete cascade,
  vdate date, result text, basis text, verifier text
);

create table if not exists news (
  id bigserial primary key,
  title text not null, url text, body text,
  source text, subject_slug text,
  published_at timestamptz default now()
);

-- ===== 사용자(Auth) =====
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nickname text, provider text,
  created_at timestamptz default now()
);

create table if not exists attempts (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete cascade,
  item_key text,                   -- O123 / X456 (프론트 OX id)
  article_no text,
  ox char(1), correct boolean,
  created_at timestamptz default now()
);

create table if not exists wrong_notes (
  user_id uuid references auth.users(id) on delete cascade,
  item_key text,
  created_at timestamptz default now(),
  primary key (user_id, item_key)
);

create table if not exists bookmarks (
  user_id uuid references auth.users(id) on delete cascade,
  article_no text,
  created_at timestamptz default now(),
  primary key (user_id, article_no)
);

-- ===== 자유게시판 =====
create table if not exists posts (
  id bigserial primary key,
  user_id uuid references auth.users(id) on delete set null,
  subject_slug text, category text default '일반',
  title text not null, body text,
  author_name text,
  created_at timestamptz default now()
);

create table if not exists comments (
  id bigserial primary key,
  post_id bigint references posts(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  body text, author_name text,
  created_at timestamptz default now()
);

-- ===== 인덱스 =====
create index if not exists idx_articles_sub on articles(subject_id, article_no);
create index if not exists idx_atoms_sub on atoms(subject_id, article_no);
create index if not exists idx_atoms_art on atoms(article_id);
create index if not exists idx_sources_atom on atom_sources(atom_id);
create index if not exists idx_traps_atom on atom_traps(atom_id);
create index if not exists idx_attempts_user on attempts(user_id);
create index if not exists idx_posts_board on posts(subject_slug, created_at desc);

-- ===== RLS =====
-- 콘텐츠: 공개 읽기
do $$
declare t text;
begin
  foreach t in array array['subjects','articles','exams','atoms','atom_traps','atom_sources','verifications','news']
  loop
    execute format('alter table %I enable row level security;', t);
    execute format('drop policy if exists "public_read" on %I;', t);
    execute format('create policy "public_read" on %I for select using (true);', t);
  end loop;
end$$;

-- 사용자 전용 테이블: 본인만
alter table profiles enable row level security;
drop policy if exists "self_profile" on profiles;
create policy "self_profile" on profiles for all using (auth.uid() = id) with check (auth.uid() = id);

alter table attempts enable row level security;
drop policy if exists "self_attempts" on attempts;
create policy "self_attempts" on attempts for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table wrong_notes enable row level security;
drop policy if exists "self_wrong" on wrong_notes;
create policy "self_wrong" on wrong_notes for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table bookmarks enable row level security;
drop policy if exists "self_bm" on bookmarks;
create policy "self_bm" on bookmarks for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 게시판: 읽기 공개, 작성/수정/삭제는 본인
alter table posts enable row level security;
drop policy if exists "posts_read" on posts;   create policy "posts_read" on posts for select using (true);
drop policy if exists "posts_ins" on posts;     create policy "posts_ins" on posts for insert with check (auth.uid() = user_id);
drop policy if exists "posts_upd" on posts;     create policy "posts_upd" on posts for update using (auth.uid() = user_id);
drop policy if exists "posts_del" on posts;     create policy "posts_del" on posts for delete using (auth.uid() = user_id);

alter table comments enable row level security;
drop policy if exists "cmt_read" on comments;   create policy "cmt_read" on comments for select using (true);
drop policy if exists "cmt_ins" on comments;    create policy "cmt_ins" on comments for insert with check (auth.uid() = user_id);
drop policy if exists "cmt_del" on comments;    create policy "cmt_del" on comments for delete using (auth.uid() = user_id);

-- 가입 시 프로필 자동 생성
create or replace function public.handle_new_user() returns trigger as $$
begin
  insert into public.profiles(id, nickname, provider)
  values (new.id, coalesce(new.raw_user_meta_data->>'name','수험생'), new.raw_app_meta_data->>'provider')
  on conflict (id) do nothing;
  return new;
end$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();
