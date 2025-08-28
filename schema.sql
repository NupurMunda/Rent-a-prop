-- Saved searches
create table if not exists public.saved_searches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade,
  city text,
  ltypes text[] default '{"rent","sell","commission"}',
  query text,
  created_at timestamptz default now(),
  last_seen timestamptz default now()
);
create index if not exists saved_searches_user_idx on public.saved_searches(user_id);

alter table public.saved_searches enable row level security;
create policy if not exists "saved searches read" on public.saved_searches for select using (auth.uid() = user_id);
create policy if not exists "saved searches write" on public.saved_searches for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
