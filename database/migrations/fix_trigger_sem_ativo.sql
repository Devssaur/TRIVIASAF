-- =============================================================
--  Correção: trigger fn_handle_new_auth_user sem coluna 'ativo'
--  (a tabela real não possui essa coluna)
--  Execute no SQL Editor do Supabase.
-- =============================================================

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
