-- Seed de dados de teste para a tabela usuarios
-- Execute este script no SQL Editor do Supabase para popular usuários de teste

insert into usuarios (id, nome, email, senha_hash, perfil, ativo)
values
  (
    gen_random_uuid(),
    'João Silva',
    'joao@empresa.com',
    'senha123',
    'SOLICITANTE',
    true
  ),
  (
    gen_random_uuid(),
    'Maria CCM',
    'maria@empresa.com',
    'senha456',
    'CCM',
    true
  ),
  (
    gen_random_uuid(),
    'Admin Sistema',
    'admin@empresa.com',
    'senha789',
    'ADMIN',
    true
  );
