-- UHS 51860 Sync: run this ONCE in Supabase  ->  SQL Editor  ->  New query  ->  Run
-- Creates two private tables and five functions. The tables cannot be read directly;
-- every function requires your secret key (a hash of your sync password).

create table if not exists public.uhs_vaults (
  key        text primary key,
  students   jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.uhs_pdfs (
  key        text not null,
  app_no     text not null,
  size       integer not null,
  data       text not null,           -- PDF as base64
  updated_at timestamptz not null default now(),
  primary key (key, app_no)
);

-- Lock the tables: no direct access for the public API roles
alter table public.uhs_vaults enable row level security;
alter table public.uhs_pdfs   enable row level security;
revoke all on public.uhs_vaults from anon, authenticated;
revoke all on public.uhs_pdfs   from anon, authenticated;

create or replace function public.uhs_put_students(p_key text, p_students jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  if jsonb_typeof(p_students) <> 'array' then raise exception 'students must be an array'; end if;
  insert into uhs_vaults(key, students, updated_at) values (p_key, p_students, now())
  on conflict (key) do update set students = excluded.students, updated_at = now();
end $$;

create or replace function public.uhs_get_students(p_key text)
returns jsonb language plpgsql security definer set search_path = public as $$
declare r jsonb;
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  select students into r from uhs_vaults where key = p_key;
  return r;   -- null when this password has never been pushed
end $$;

create or replace function public.uhs_list_pdfs(p_key text)
returns table(app_no text, size integer) language plpgsql security definer set search_path = public as $$
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  return query select p.app_no, p.size from uhs_pdfs p where p.key = p_key;
end $$;

create or replace function public.uhs_put_pdf(p_key text, p_app_no text, p_size integer, p_data text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  insert into uhs_pdfs(key, app_no, size, data, updated_at) values (p_key, p_app_no, p_size, p_data, now())
  on conflict (key, app_no) do update set size = excluded.size, data = excluded.data, updated_at = now();
end $$;

create or replace function public.uhs_get_pdf(p_key text, p_app_no text)
returns text language plpgsql security definer set search_path = public as $$
declare r text;
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  select data into r from uhs_pdfs where key = p_key and app_no = p_app_no;
  return r;
end $$;

revoke all on function public.uhs_put_students(text, jsonb) from public;
revoke all on function public.uhs_get_students(text) from public;
revoke all on function public.uhs_list_pdfs(text) from public;
revoke all on function public.uhs_put_pdf(text, text, integer, text) from public;
revoke all on function public.uhs_get_pdf(text, text) from public;
grant execute on function public.uhs_put_students(text, jsonb) to anon, authenticated;
grant execute on function public.uhs_get_students(text) to anon, authenticated;
grant execute on function public.uhs_list_pdfs(text) to anon, authenticated;
grant execute on function public.uhs_put_pdf(text, text, integer, text) to anon, authenticated;
grant execute on function public.uhs_get_pdf(text, text) to anon, authenticated;
