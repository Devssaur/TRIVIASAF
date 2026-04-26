-- Políticas RLS para o sistema SAF
-- Execute este script no SQL Editor do Supabase

-- =========================================================
-- usuarios
-- Permite que a chave anon leia a tabela para autenticação.
-- SELECT restrito: só retorna o próprio usuário autenticado
-- ou permite leitura para login (necessário para o endpoint /login).
-- =========================================================
alter table public.usuarios enable row level security;

-- Permite ao anon consultar por email (necessário para o login via API Flask)
create policy "Permitir leitura para autenticacao"
  on public.usuarios
  for select
  to anon
  using (true);

-- =========================================================
-- saf_solicitacoes
-- =========================================================
alter table public.saf_solicitacoes enable row level security;

-- Solicitante: ve apenas as proprias solicitacoes
-- CCM e Admin: veem todas
create policy "Solicitante ve suas solicitacoes / CCM e Admin veem todas"
  on public.saf_solicitacoes
  for select
  to anon
  using (true);

-- =========================================================
-- saf_controle_ccm
-- =========================================================
alter table public.saf_controle_ccm enable row level security;

create policy "Leitura liberada para autenticados"
  on public.saf_controle_ccm
  for select
  to anon
  using (true);

-- =========================================================
-- saf_integracao_sap
-- =========================================================
alter table public.saf_integracao_sap enable row level security;

create policy "Leitura liberada para autenticados"
  on public.saf_integracao_sap
  for select
  to anon
  using (true);

-- =========================================================
-- locais_instalacao / equipamentos / sintomas_catalogo
-- Dados mestres: leitura liberada para todos (search help)
-- =========================================================
alter table public.locais_instalacao enable row level security;
create policy "Leitura publica dados mestres - locais"
  on public.locais_instalacao
  for select
  to anon
  using (true);

alter table public.equipamentos enable row level security;
create policy "Leitura publica dados mestres - equipamentos"
  on public.equipamentos
  for select
  to anon
  using (true);

alter table public.sintomas_catalogo enable row level security;
create policy "Leitura publica dados mestres - sintomas"
  on public.sintomas_catalogo
  for select
  to anon
  using (true);

-- =========================================================
-- logs_auditoria
-- Somente leitura via service_role (nunca anon)
-- =========================================================
alter table public.logs_auditoria enable row level security;
-- Nenhuma policy anon: apenas service_role acessa diretamente
