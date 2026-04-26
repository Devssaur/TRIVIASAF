-- =============================================================
--  Migração: campos aprovado, empresa, area em usuarios
--            + remoção de senha_hash
--            + ajuste de constraint de perfil
--            + trigger de auto-criação via Supabase Auth
--            + RLS de insert via service_role
--
--  Execute no SQL Editor do Supabase (como postgres / owner).
-- =============================================================

begin;

-- ------------------------------------------------------------------
-- 1. Ajustar constraint de perfil para aceitar os valores reais do banco
-- ------------------------------------------------------------------
alter table public.usuarios
  drop constraint if exists usuarios_perfil_check;

alter table public.usuarios
  add constraint usuarios_perfil_check
    check (perfil in ('Solicitante', 'CCM', 'Administrador'));

-- ------------------------------------------------------------------
-- 2. Adicionar colunas novas (idempotente via IF NOT EXISTS)
-- ------------------------------------------------------------------
alter table public.usuarios
  add column if not exists aprovado   boolean   not null default false,
  add column if not exists empresa    text,
  add column if not exists area       text;

-- ------------------------------------------------------------------
-- 3. Remover coluna de senha (a autenticação passa a ser 100% Supabase Auth)
-- ------------------------------------------------------------------
alter table public.usuarios
  drop column if exists senha_hash;

-- ------------------------------------------------------------------
-- 4. Trigger: ao criar um usuário via Supabase Auth (auth.users),
--    insere automaticamente um registro em public.usuarios com o
--    perfil padrão 'Solicitante' e aprovado = false.
--    Os campos nome, empresa e area são lidos dos metadados do sign-up.
-- ------------------------------------------------------------------
create or replace function public.fn_handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.usuarios (id, nome, email, perfil, aprovado, empresa, area)
  values (
    new.id,
    coalesce((new.raw_user_meta_data->>'nome')::text, new.email),
    new.email,
    coalesce((new.raw_user_meta_data->>'perfil')::text, 'Solicitante'),
    false,
    (new.raw_user_meta_data->>'empresa')::text,
    (new.raw_user_meta_data->>'area')::text
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

-- Cria o trigger no schema auth (requer permissão de superuser/postgres)
drop trigger if exists trg_on_auth_user_created on auth.users;
create trigger trg_on_auth_user_created
  after insert on auth.users
  for each row execute function public.fn_handle_new_auth_user();

-- ------------------------------------------------------------------
-- 5. RLS: permitir que service_role (backend Flask) gerencie usuários
--    A anon key ainda pode fazer SELECT para autenticar.
-- ------------------------------------------------------------------

-- Remover policies de insert antigas se existirem
drop policy if exists "Permitir insert service_role" on public.usuarios;
drop policy if exists "Permitir update perfil e aprovado pelo admin" on public.usuarios;

create policy "Permitir insert service_role"
  on public.usuarios
  for insert
  to service_role
  with check (true);

create policy "Permitir update perfil e aprovado pelo admin"
  on public.usuarios
  for update
  to service_role
  using (true)
  with check (true);

commit;
