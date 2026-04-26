-- Migração: campos SAP adicionais para integração bidirecional
-- Execute no SQL Editor do Supabase ANTES de ativar a integração SAP.

-- ───────────────────────────────────────────────────────────────
-- 1. Tipo da Nota e Status do SAP em saf_integracao_sap
-- ───────────────────────────────────────────────────────────────
ALTER TABLE public.saf_integracao_sap
  ADD COLUMN IF NOT EXISTS tipo_nota   text,         -- QMART: M1, M2, etc.
  ADD COLUMN IF NOT EXISTS jest_stat   text,         -- JEST-STAT: status no SAP (NOCO, CANCL, etc.)
  ADD COLUMN IF NOT EXISTS numero_ordem_sap text;    -- AUFNR: Ordem de Manutenção gerada no SAP

COMMENT ON COLUMN public.saf_integracao_sap.tipo_nota        IS 'Tipo da Nota SAP (QMART): M1=Preventiva, M2=Corretiva.';
COMMENT ON COLUMN public.saf_integracao_sap.jest_stat        IS 'Status do objeto SAP (JEST-STAT), ex: NOCO, CANCL, CLSD.';
COMMENT ON COLUMN public.saf_integracao_sap.numero_ordem_sap IS 'Número da Ordem de Manutenção SAP (AUFNR), se gerada.';

-- ───────────────────────────────────────────────────────────────
-- 2. Tipo da Nota no controle CCM (CCM define ao aprovar)
-- ───────────────────────────────────────────────────────────────
ALTER TABLE public.saf_controle_ccm
  ADD COLUMN IF NOT EXISTS tipo_nota text NOT NULL DEFAULT 'M2';

COMMENT ON COLUMN public.saf_controle_ccm.tipo_nota IS 'Tipo da Nota SAP definido pelo CCM na aprovação. M2=Corretiva (padrão), M1=Preventiva.';

-- ───────────────────────────────────────────────────────────────
-- 3. Rastreio de sincronização nas tabelas de cache de dados mestres
-- ───────────────────────────────────────────────────────────────
ALTER TABLE public.locais_instalacao
  ADD COLUMN IF NOT EXISTS sincronizado_em timestamptz;

ALTER TABLE public.equipamentos
  ADD COLUMN IF NOT EXISTS sincronizado_em timestamptz;

ALTER TABLE public.sintomas_catalogo
  ADD COLUMN IF NOT EXISTS sincronizado_em timestamptz;

COMMENT ON COLUMN public.locais_instalacao.sincronizado_em IS 'Última sincronização com o SAP via Edge Function.';
COMMENT ON COLUMN public.equipamentos.sincronizado_em      IS 'Última sincronização com o SAP via Edge Function.';
COMMENT ON COLUMN public.sintomas_catalogo.sincronizado_em IS 'Última sincronização com o SAP via Edge Function.';

-- ───────────────────────────────────────────────────────────────
-- 4. Índices adicionais
-- ───────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_saf_integracao_sap_qmnum
  ON public.saf_integracao_sap(qmnum);

CREATE INDEX IF NOT EXISTS idx_saf_integracao_sap_numero_ordem
  ON public.saf_integracao_sap(numero_ordem_sap);

CREATE INDEX IF NOT EXISTS idx_locais_instalacao_codigo
  ON public.locais_instalacao(codigo);

CREATE INDEX IF NOT EXISTS idx_equipamentos_codigo
  ON public.equipamentos(codigo);
