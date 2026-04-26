-- Migração: adiciona colunas de nome e área do notificador em saf_solicitacoes
-- Execute no SQL Editor do Supabase.

ALTER TABLE public.saf_solicitacoes
  ADD COLUMN IF NOT EXISTS notificador_nome text,
  ADD COLUMN IF NOT EXISTS notificador_area text;

COMMENT ON COLUMN public.saf_solicitacoes.notificador_nome
  IS 'Nome do solicitante no momento da abertura (desnormalizado para evitar join).';
COMMENT ON COLUMN public.saf_solicitacoes.notificador_area
  IS 'Área do solicitante no momento da abertura (desnormalizado).';
