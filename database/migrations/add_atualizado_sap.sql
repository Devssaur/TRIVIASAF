-- Migração: adiciona coluna atualizado_sap em saf_controle_ccm
-- Execute no SQL Editor do Supabase.

ALTER TABLE public.saf_controle_ccm
  ADD COLUMN IF NOT EXISTS atualizado_sap boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.saf_controle_ccm.atualizado_sap
  IS 'Indica se o sistema SAP foi notificado/atualizado para esta solicitação.';
