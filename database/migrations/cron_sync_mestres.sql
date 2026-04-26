-- Migração: Agendamento da Edge Function sync-mestres-sap a cada 2 minutos
-- Requer extensões pg_cron e pg_net habilitadas no Supabase.
-- Execute no SQL Editor do Supabase.
--
-- ⚠️  ANTES de executar:
--   1. Substitua <PROJECT_REF> pelo ID do seu projeto Supabase.
--   2. Substitua <SERVICE_ROLE_KEY> pela sua chave service_role
--      (Supabase > Project Settings > API).
--   Alternativamente, use o painel Supabase > Cron Jobs para configurar visualmente.

-- Habilita as extensões (pode já estar habilitado)
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Remove job anterior se existir
SELECT cron.unschedule('sync-mestres-sap') 
WHERE EXISTS (
  SELECT 1 FROM cron.job WHERE jobname = 'sync-mestres-sap'
);

-- Agenda a Edge Function a cada 2 minutos
SELECT cron.schedule(
  'sync-mestres-sap',
  '*/2 * * * *',
  $$
    SELECT net.http_post(
      url     := 'https://<PROJECT_REF>.supabase.co/functions/v1/sync-mestres-sap',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer <SERVICE_ROLE_KEY>'
      ),
      body    := '{}'::jsonb
    );
  $$
);
