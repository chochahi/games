-- UHS Sync HARDENING (v2): run this ONCE in Supabase -> SQL Editor, AFTER supabase-setup.sql.
-- Safe to run again at any time.
--
-- What it does
--   * Each page (matric / inter) gets exactly ONE cloud vault. Its password is set by the
--     FIRST "Save & Push Sync" you do from that page - nothing to register by hand.
--     After that, nobody can create another vault for that page, so strangers who find your
--     project URL + key cannot fill your free storage.
--   * MATRIC : up to 500 students, each PDF up to 250 KB.
--   * INTER  : up to 200 students PER STREAM (Arts, Commerce, Science), each PDF up to 150 KB.
--   * The pages must be the new matric.html / inter.html (they tell the database which page is syncing).
--
-- To start over for a page (forget its password and DELETE its cloud data), run one of:
--     select public.uhs_reset_app('matric');
--     select public.uhs_reset_app('inter');

-- ---------------------------------------------------------------------------
-- 0. Clean up the earlier "register passwords by hand" version, if it was run
-- ---------------------------------------------------------------------------
drop function if exists public.uhs_register_password(text, text, text);
drop table    if exists public.uhs_allowed_keys;

-- ---------------------------------------------------------------------------
-- 1. Remember which page owns each vault
-- ---------------------------------------------------------------------------
alter table public.uhs_vaults add column if not exists app text;

-- ---------------------------------------------------------------------------
-- 2. Remove the old, unlimited save functions (otherwise they would still be callable)
-- ---------------------------------------------------------------------------
drop function if exists public.uhs_put_students(text, jsonb);
drop function if exists public.uhs_put_pdf(text, text, integer, text);

-- ---------------------------------------------------------------------------
-- 3. New save functions with limits
-- ---------------------------------------------------------------------------
create or replace function public.uhs_put_students(p_key text, p_app text, p_students jsonb)
returns void language plpgsql security definer set search_path = public as $$
declare
  v_app text;
  n int;
  worst int;
  worst_name text;
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  if p_app not in ('matric', 'inter') then raise exception 'unknown page'; end if;
  if jsonb_typeof(p_students) <> 'array' then raise exception 'students must be an array'; end if;
  if length(p_students::text) > 3000000 then raise exception 'student list too large (max 3 MB)'; end if;

  n := jsonb_array_length(p_students);
  if p_app = 'matric' then
    if n > 500 then raise exception 'Matric allows at most 500 students (you have %).', n; end if;
  else
    select c, f into worst, worst_name from (
      select coalesce(nullif(btrim(e->>'faculty'), ''), 'no faculty selected') as f, count(*)::int as c
      from jsonb_array_elements(p_students) e group by 1
    ) t order by c desc limit 1;
    if coalesce(worst, 0) > 200 then
      raise exception 'Inter allows at most 200 students per stream. "%" has %.', worst_name, worst;
    end if;
  end if;

  -- one vault per page; the first push claims it
  select app into v_app from uhs_vaults where key = p_key;
  if found then
    if v_app is not null and v_app <> p_app then
      raise exception 'This password already belongs to the other page. Use a different password here.';
    end if;
    if v_app is null and exists (select 1 from uhs_vaults where app = p_app and key <> p_key) then
      raise exception 'Cloud sync for % is already set up with a different password.', p_app;
    end if;
  else
    if exists (select 1 from uhs_vaults where app = p_app) then
      raise exception 'Cloud sync for % is already set up with a different password. Use that password, or reset it in the Supabase SQL Editor (see supabase-hardening.sql).', p_app;
    end if;
  end if;

  insert into uhs_vaults(key, app, students, updated_at) values (p_key, p_app, p_students, now())
  on conflict (key) do update set app = excluded.app, students = excluded.students, updated_at = now();
end $$;

create or replace function public.uhs_put_pdf(p_key text, p_app text, p_app_no text, p_size integer, p_data text)
returns void language plpgsql security definer set search_path = public as $$
declare
  v_app text;
  max_bytes int;
  max_pdfs int;
begin
  if p_key !~ '^[a-f0-9]{64}$' then raise exception 'invalid key'; end if;
  if p_app not in ('matric', 'inter') then raise exception 'unknown page'; end if;

  select app into v_app from uhs_vaults where key = p_key;
  if not found then raise exception 'Push the student list first (Save & Push Sync).'; end if;
  if v_app is distinct from p_app then raise exception 'This password belongs to a different page.'; end if;

  if p_app = 'matric' then max_bytes := 250 * 1024; max_pdfs := 500;
  else                     max_bytes := 150 * 1024; max_pdfs := 800;   -- 3 streams x 200, plus students without a stream
  end if;

  if p_app_no is null or length(p_app_no) = 0 or length(p_app_no) > 100 then raise exception 'invalid Sl. No'; end if;
  if p_size < 1 or p_size > max_bytes
     or length(p_data) > (max_bytes * 4 / 3) + 16 then
    raise exception 'PDF too large: % allows at most % KB per PDF.', initcap(p_app), max_bytes / 1024;
  end if;
  if (select count(*) from uhs_pdfs where key = p_key and app_no <> p_app_no) >= max_pdfs then
    raise exception 'too many PDFs in this vault (max %)', max_pdfs;
  end if;

  insert into uhs_pdfs(key, app_no, size, data, updated_at) values (p_key, p_app_no, p_size, p_data, now())
  on conflict (key, app_no) do update set size = excluded.size, data = excluded.data, updated_at = now();
end $$;

-- ---------------------------------------------------------------------------
-- 4. Start-over helper (usable only here in the SQL Editor, not from the web)
-- ---------------------------------------------------------------------------
create or replace function public.uhs_reset_app(p_app text)
returns text language plpgsql security definer set search_path = public as $$
begin
  delete from uhs_pdfs where key in (select key from uhs_vaults where app = p_app);
  delete from uhs_vaults where app = p_app;
  return 'cleared cloud data and password for ' || p_app;
end $$;
revoke all on function public.uhs_reset_app(text) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 5. Permissions: the pages (anon key) may only call the save/read functions
-- ---------------------------------------------------------------------------
revoke all on function public.uhs_put_students(text, text, jsonb) from public;
revoke all on function public.uhs_put_pdf(text, text, text, integer, text) from public;
grant execute on function public.uhs_put_students(text, text, jsonb) to anon, authenticated;
grant execute on function public.uhs_put_pdf(text, text, text, integer, text) to anon, authenticated;
