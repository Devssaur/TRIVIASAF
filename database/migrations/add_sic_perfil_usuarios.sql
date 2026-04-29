-- Adiciona suporte ao perfil SIC na tabela de usuarios
-- Ajusta a constraint para aceitar os quatro perfis do sistema.

alter table if exists public.usuarios
  drop constraint if exists usuarios_perfil_check;

alter table if exists public.usuarios
  add constraint usuarios_perfil_check
  check (perfil in ('Solicitante', 'CCM', 'Administrador', 'SIC'));
