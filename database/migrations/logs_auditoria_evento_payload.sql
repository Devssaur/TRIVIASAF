-- Estrutura de auditoria para eventos administrativos
-- Compatível com rotas de admin que registram evento + payload.

create table if not exists public.logs_auditoria (
  id uuid not null default gen_random_uuid(),
  usuario_id uuid null,
  evento character varying not null,
  payload jsonb null,
  criado_em timestamp with time zone not null default now(),
  constraint logs_auditoria_pkey primary key (id),
  constraint logs_auditoria_usuario_id_fkey foreign key (usuario_id)
    references public.usuarios (id) on delete set null
) tablespace pg_default;

create index if not exists idx_logs_evento
  on public.logs_auditoria using btree (evento) tablespace pg_default;
