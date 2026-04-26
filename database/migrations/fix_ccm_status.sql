-- Migração: corrige constraint de motivo_devolucao e adiciona status em saf_solicitacoes
-- Execute no SQL Editor do Supabase.

-- 1. Remove constraint que exige motivo_devolucao em recusas
--    (a coluna continua existindo, mas passou a ser opcional)
ALTER TABLE public.saf_controle_ccm
  DROP CONSTRAINT IF EXISTS chk_motivo_devolucao;

-- 2. Adiciona coluna de status na tabela de solicitações do solicitante
--    Valores: 'Pendente' (default), 'Aprovada', 'Duplicada'
ALTER TABLE public.saf_solicitacoes
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'Pendente';

ALTER TABLE public.saf_solicitacoes
  DROP CONSTRAINT IF EXISTS saf_solicitacoes_status_check;

ALTER TABLE public.saf_solicitacoes
  ADD CONSTRAINT saf_solicitacoes_status_check
  CHECK (status IN ('Pendente', 'Aprovada', 'Duplicada'));

-- 3. Sincroniza linhas já existentes: aprovadas no CCM → status 'Aprovada'
UPDATE public.saf_solicitacoes s
SET    status = 'Aprovada'
FROM   public.saf_controle_ccm c
WHERE  c.solicitacao_id = s.id
  AND  c.status = 'APROVADA';
