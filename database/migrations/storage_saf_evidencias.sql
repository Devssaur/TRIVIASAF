-- =============================================================
--  Migração: Supabase Storage — bucket saf-evidencias
--  Execute no SQL Editor do Supabase (schema storage).
-- =============================================================

-- 1. Garante que a coluna existe na tabela de solicitações
ALTER TABLE public.saf_solicitacoes
  ADD COLUMN IF NOT EXISTS anexo_evidencia_url text;

COMMENT ON COLUMN public.saf_solicitacoes.anexo_evidencia_url
  IS 'URL pública da foto de evidência armazenada no Supabase Storage.';

-- 2. Cria o bucket (ignora se já existir)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'saf-evidencias',
  'saf-evidencias',
  true,
  10485760,            -- 10 MB max por arquivo
  ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- 3. Políticas RLS para storage.objects
--    (o bucket já tem public=true, mas policies de insert são necessárias)

DO $$
BEGIN

  -- 3.1 Leitura pública
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
      AND policyname = 'saf_evidencias_select_public'
  ) THEN
    CREATE POLICY "saf_evidencias_select_public"
      ON storage.objects FOR SELECT
      USING (bucket_id = 'saf-evidencias');
  END IF;

  -- 3.2 Insert: apenas usuários autenticados
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
      AND policyname = 'saf_evidencias_insert_auth'
  ) THEN
    CREATE POLICY "saf_evidencias_insert_auth"
      ON storage.objects FOR INSERT
      WITH CHECK (
        bucket_id = 'saf-evidencias'
        AND auth.role() = 'authenticated'
      );
  END IF;

  -- 3.3 Delete: dono do arquivo ou admin
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
      AND policyname = 'saf_evidencias_delete_owner'
  ) THEN
    CREATE POLICY "saf_evidencias_delete_owner"
      ON storage.objects FOR DELETE
      USING (
        bucket_id = 'saf-evidencias'
        AND (
          owner = auth.uid()
          OR EXISTS (
            SELECT 1 FROM public.usuarios u
            WHERE u.id = auth.uid() AND u.perfil = 'Administrador'
          )
        )
      );
  END IF;

END $$;
