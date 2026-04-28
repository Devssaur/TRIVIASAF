-- =============================================================================
-- SEED DE DADOS MVP SAF – ARBORIZAÇÃO REAL SAP-PM
-- Baseado no treinamento "Processo SAP-PM" da MVP SAF (Linhas 11/12/13)
--
-- Execute APÓS add_geo_grupo_catalogo.sql
--
-- Estrutura do SAP-PM MVP SAF:
--   TV11 – Linha 11 Coral     | TV12 – Linha 12 Safira   | TV13 – Linha 13 Jade
--   TV36 – Multilinhas 11/12/13
--
-- Tipos de Nota: YE (Corretiva Emergencial) | YP (Corretiva Programada)
--               YR (Reparo)                 | YS (Serviço Eventual)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────
-- 0. Limpa dados de teste genéricos anteriores
-- ─────────────────────────────────────────────────────────────
DELETE FROM equipamentos
WHERE local_id_sap IN (
  'BR-SP-UTIL-001','BR-SP-PROD-001','BR-SP-PROD-002',
  'BR-RJ-UTIL-001','BR-RJ-PROD-001',
  '10000001','10000002','10000003','10000004','10000005',
  '10000006','10000007','10000008','10000009'
);

DELETE FROM locais_instalacao
WHERE id_sap IN (
  'BR-SP-UTIL-001','BR-SP-PROD-001','BR-SP-PROD-002',
  'BR-RJ-UTIL-001','BR-RJ-PROD-001'
);

DELETE FROM sintomas_catalogo
WHERE codigo IN (
  'EL-001','EL-002','EL-003','EL-004',
  'ME-001','ME-002','ME-003','ME-004','ME-005',
  'HI-001','HI-002','HI-003',
  'IN-001','IN-002','IN-003'
);

-- ─────────────────────────────────────────────────────────────
-- 1. LOCAIS DE INSTALAÇÃO (TPLNR) — Arborização real MVP SAF
--    Nível: Sistemas de cada linha + equipes TV36
--    id_sap = código TPLNR exato do SAP
-- ─────────────────────────────────────────────────────────────

-- Remove locais anteriores da MVP SAF (se existirem) para evitar conflito
DELETE FROM equipamentos WHERE local_id_sap IN (
  'TV11','TV11-2','TV11-3','TV11-4','TV11-5','TV11-6','TV11-7','TV11-8',
  'TV12','TV12-2','TV12-3','TV12-4','TV12-5','TV12-6','TV12-7','TV12-8',
  'TV13','TV13-2','TV13-3','TV13-4','TV13-5','TV13-6','TV13-7','TV13-8',
  'TV36','TV36-1','TV36-5','TV36-8',
  -- Equipes operacionais
  'TV36ECVN','TV36EDBO','TV36EEGO','TV36ESGU',
  'TV36ACVN','TV36ASGU',
  'TV36VCVN','TV36VJPB','TV36VEGO',
  'TV36SCVN','TV36SBAS','TV36SJBO','TV36SSMP',
  'TV36TCCO','TV36TBAS',
  'TV36RCCO','TV36RCVN','TV36REGT','TV36RGUA','TV36RLUZ','TV36RSMP',
  'TV36MCFA','TV36MPAC',
  'TV36VAUX','TV36LABO','TV36OFIC',
  'TV36CCVN','TV36CEGO','TV36CGUA','TV36CITI','TV36CLUZ'
);

DELETE FROM locais_instalacao WHERE id_sap IN (
  'TV11','TV11-2','TV11-3','TV11-4','TV11-5','TV11-6','TV11-7','TV11-8',
  'TV12','TV12-2','TV12-3','TV12-4','TV12-5','TV12-6','TV12-7','TV12-8',
  'TV13','TV13-2','TV13-3','TV13-4','TV13-5','TV13-6','TV13-7','TV13-8',
  'TV36','TV36-1','TV36-5','TV36-8',
  'TV36ECVN','TV36EDBO','TV36EEGO','TV36ESGU',
  'TV36ACVN','TV36ASGU',
  'TV36VCVN','TV36VJPB','TV36VEGO',
  'TV36SCVN','TV36SBAS','TV36SJBO','TV36SSMP',
  'TV36TCCO','TV36TBAS',
  'TV36RCCO','TV36RCVN','TV36REGT','TV36RGUA','TV36RLUZ','TV36RSMP',
  'TV36MCFA','TV36MPAC',
  'TV36VAUX','TV36LABO','TV36OFIC',
  'TV36CCVN','TV36CEGO','TV36CGUA','TV36CITI','TV36CLUZ'
);

-- Insere locais de instalação (sistemas das linhas)
INSERT INTO locais_instalacao (id_sap, codigo, descricao, ativo, sincronizado_em)
VALUES
  -- ── Linha 11 – CORAL ────────────────────────────────────
  ('TV11',    'TV11',    'MVP SAF LINHA 11 - CORAL',            true, now()),
  ('TV11-2',  'TV11-2',  'L11 - SISTEMA DE ENERGIA',            true, now()),
  ('TV11-3',  'TV11-3',  'L11 - SISTEMA DE REDE AÉREA',         true, now()),
  ('TV11-4',  'TV11-4',  'L11 - SISTEMA SINALIZAÇÃO',           true, now()),
  ('TV11-5',  'TV11-5',  'L11 - SISTEMA TELECOM',               true, now()),
  ('TV11-6',  'TV11-6',  'L11 - SISTEMA VIA PERMANENTE',        true, now()),
  ('TV11-7',  'TV11-7',  'L11 - SISTEMA CIVIL',                 true, now()),
  ('TV11-8',  'TV11-8',  'L11 - SISTEMA AUXILIARES',            true, now()),

  -- ── Linha 12 – SAFIRA ───────────────────────────────────
  ('TV12',    'TV12',    'MVP SAF LINHA 12 - SAFIRA',           true, now()),
  ('TV12-2',  'TV12-2',  'L12 - SISTEMA DE ENERGIA',            true, now()),
  ('TV12-3',  'TV12-3',  'L12 - SISTEMA DE REDE AÉREA',         true, now()),
  ('TV12-4',  'TV12-4',  'L12 - SISTEMA SINALIZAÇÃO',           true, now()),
  ('TV12-5',  'TV12-5',  'L12 - SISTEMA TELECOM',               true, now()),
  ('TV12-6',  'TV12-6',  'L12 - SISTEMA VIA PERMANENTE',        true, now()),
  ('TV12-7',  'TV12-7',  'L12 - SISTEMA CIVIL',                 true, now()),
  ('TV12-8',  'TV12-8',  'L12 - SISTEMA AUXILIARES',            true, now()),

  -- ── Linha 13 – JADE ─────────────────────────────────────
  ('TV13',    'TV13',    'MVP SAF LINHA 13 - JADE',             true, now()),
  ('TV13-2',  'TV13-2',  'L13 - SISTEMA DE ENERGIA',            true, now()),
  ('TV13-3',  'TV13-3',  'L13 - SISTEMA DE REDE AÉREA',         true, now()),
  ('TV13-4',  'TV13-4',  'L13 - SISTEMA SINALIZAÇÃO',           true, now()),
  ('TV13-5',  'TV13-5',  'L13 - SISTEMA TELECOM',               true, now()),
  ('TV13-6',  'TV13-6',  'L13 - SISTEMA VIA PERMANENTE',        true, now()),
  ('TV13-7',  'TV13-7',  'L13 - SISTEMA CIVIL',                 true, now()),
  ('TV13-8',  'TV13-8',  'L13 - SISTEMA AUXILIARES',            true, now()),

  -- ── TV36 – Multilinhas ──────────────────────────────────
  ('TV36',    'TV36',    'MVP SAF L11, L12 E L13',              true, now()),
  ('TV36-1',  'TV36-1',  'MATERIAL RODANTE E VEÍCULOS AUXILIARES', true, now()),
  ('TV36-5',  'TV36-5',  'TELECOM MULTILINHAS (CCO)',           true, now()),
  ('TV36-8',  'TV36-8',  'SISTEMA AUXILIARES MULTILINHAS',      true, now()),

  -- ── Equipes / Centros de Trabalho (ENERGIA) ─────────────
  ('TV36ECVN','TV36ECVN','ENERGIA - BASE CALMON VIANA',         true, now()),
  ('TV36EDBO','TV36EDBO','ENERGIA - BASE DOM BOSCO',            true, now()),
  ('TV36EEGO','TV36EEGO','ENERGIA - BASE ENGENHEIRO GOULART',   true, now()),
  ('TV36ESGU','TV36ESGU','ENERGIA - BASE SEBASTIÃO GUALBERTO',  true, now()),

  -- ── Equipes / Centros de Trabalho (REDE AÉREA) ──────────
  ('TV36ACVN','TV36ACVN','REDE AÉREA - BASE CALMON VIANA',      true, now()),
  ('TV36ASGU','TV36ASGU','REDE AÉREA - BASE SEBASTIÃO GUALBERTO', true, now()),

  -- ── Equipes / Centros de Trabalho (VIA PERMANENTE) ──────
  ('TV36VCVN','TV36VCVN','VIA PERMANENTE - BASE CALMON',        true, now()),
  ('TV36VJPB','TV36VJPB','VIA PERMANENTE - BASE JUNDIAPEBA',    true, now()),
  ('TV36VEGO','TV36VEGO','VIA PERMANENTE - BASE LUZ',           true, now()),

  -- ── Equipes / Centros de Trabalho (SINALIZAÇÃO) ─────────
  ('TV36SCVN','TV36SCVN','SINALIZAÇÃO - BASE CALMON VIANA',     true, now()),
  ('TV36SBAS','TV36SBAS','SINALIZAÇÃO - BASE BRÁS',             true, now()),
  ('TV36SJBO','TV36SJBO','SINALIZAÇÃO - BASE JOSÉ BONIFÁCIO',   true, now()),
  ('TV36SSMP','TV36SSMP','SINALIZAÇÃO - BASE SÃO MIGUEL PAULISTA', true, now()),

  -- ── Equipes / Centros de Trabalho (TELECOM) ─────────────
  ('TV36TCCO','TV36TCCO','TELECOM - BASE CCO',                  true, now()),
  ('TV36TBAS','TV36TBAS','TELECOM - BASE BRÁS',                 true, now()),

  -- ── Equipes / Centros de Trabalho (RESTABELECIMENTO) ────
  ('TV36RCCO','TV36RCCO','RESTABELECIMENTO - BASE CCO',         true, now()),
  ('TV36RCVN','TV36RCVN','RESTABELECIMENTO - BASE CALMON VIANA', true, now()),
  ('TV36REGT','TV36REGT','RESTABELECIMENTO - BASE ENG. GOULART', true, now()),
  ('TV36RGUA','TV36RGUA','RESTABELECIMENTO - BASE GUAIANASES',  true, now()),
  ('TV36RLUZ','TV36RLUZ','RESTABELECIMENTO - BASE LUZ',         true, now()),
  ('TV36RSMP','TV36RSMP','RESTABELECIMENTO - BASE SÃO MIGUEL PAULISTA', true, now()),

  -- ── Equipes / Centros de Trabalho (MATERIAL RODANTE) ────
  ('TV36MCFA','TV36MCFA','MRO - CAF POSTO AVANÇADO (EXTERNO)',  true, now()),
  ('TV36MPAC','TV36MPAC','MRO - POSTO AVANÇADO (INTERNO)',      true, now()),

  -- ── Equipes / Centros de Trabalho (CIVIL) ───────────────
  ('TV36CCVN','TV36CCVN','CIVIL - BASE CALMON VIANA',           true, now()),
  ('TV36CEGO','TV36CEGO','CIVIL - BASE ENG. GOULART',           true, now()),
  ('TV36CGUA','TV36CGUA','CIVIL - BASE GUAIANASES',             true, now()),
  ('TV36CITI','TV36CITI','CIVIL - BASE ITAIM PAULISTA',         true, now()),
  ('TV36CLUZ','TV36CLUZ','CIVIL - BASE LUZ',                    true, now()),

  -- ── Equipes / Centros de Trabalho (LABORATÓRIO/OFICINAS) 
  ('TV36VAUX','TV36VAUX','VEÍCULOS AUXILIARES',                 true, now()),
  ('TV36LABO','TV36LABO','LABORATÓRIO',                         true, now()),
  ('TV36OFIC','TV36OFIC','OFICINAS',                            true, now());

-- ─────────────────────────────────────────────────────────────
-- 2. EQUIPAMENTOS (EQUNR) — exemplos reais do treinamento
--    + equipamentos representativos de cada sistema
--    grupo_catalogo = perfil de catálogo SAP (filtra sintomas válidos)
--
--    Grupos usados:
--      ER = Escada Rolante       EL = Eletromecânico / Elétrico Geral
--      MR = Material Rodante     VP = Via Permanente
--      CI = Civil / Predial      TE = Telecom
--      SI = Sinalização          RE = Rede Aérea
-- ─────────────────────────────────────────────────────────────

INSERT INTO equipamentos (id_sap, codigo, descricao, local_id_sap, local_instalacao_id, grupo_catalogo, ativo, sincronizado_em)
VALUES
  -- ── Sistema TELECOM L11 (slide 9: SONORIZAÇÃO estação Luz) ──
  ('10001549', '10001549', 'SONORIZAÇÃO - ESTAÇÃO LUZ (L11 TELECOM)',    'TV11', NULL, 'TE', true, now()),

  -- ── Sistema ENERGIA L11 (slide 9: SPDA estação Brás) ────────
  ('10002537', '10002537', 'SPDA - ESTAÇÃO BRÁS (L11 ENERGIA)',          'TV11', NULL, 'EL', true, now()),

  -- ── Sistema VIA PERMANENTE L12 (slide 10) ───────────────────
  ('10002530', '10002530', 'TRILHO - TV12-SUP-LUZ_BAS-V01',             'TV12', NULL, 'VP', true, now()),
  ('10002512', '10002512', 'FIXAÇÃO - TV12-SUP-LUZ_BAS-V01',            'TV12', NULL, 'VP', true, now()),
  ('10002235', '10002235', 'LASTRO - TV12-SUP-LUZ_BAS-V01',             'TV12', NULL, 'VP', true, now()),

  -- ── Sistema CIVIL L13 (slide 11: sanitários Eng. Goulart) ───
  ('10004335', '10004335', 'HIDROSANITÁRIO - EST. ENG. GOULART (L13)',   'TV13', NULL, 'CI', true, now()),
  ('10004336', '10004336', 'VASO SANITÁRIO - EST. ENG. GOULART (L13)',   'TV13', NULL, 'CI', true, now()),
  ('10004337', '10004337', 'LAVABO - EST. ENG. GOULART (L13)',           'TV13', NULL, 'CI', true, now()),

  -- ── Material Rodante (slide 12) ─────────────────────────────
  ('10002777', '10002777', 'TREM 01 - FROTA 8500',                       'TV36', NULL, 'MR', true, now()),

  -- ── Oficinas (slide 12) ─────────────────────────────────────
  ('20001549', '20001549', 'MÁQUINA DE LAVAR TRENS 01',                  'TV36', NULL, 'EL', true, now()),

  -- ── Escadas Rolantes e Elevadores — Linha 11 ─────────────────
  ('30000003', '30000003', 'ESCADA ROLANTE - EST. BRÁS (L11) - MB 01',   'TV11', NULL, 'ER', true, now()),
  ('30000004', '30000004', 'ESCADA ROLANTE - EST. BRÁS (L11) - MB 02',   'TV11', NULL, 'ER', true, now()),
  ('30000006', '30000006', 'ELEVADOR - EST. BRÁS (L11) - EL 01',         'TV11', NULL, 'ER', true, now()),

  -- ── Escadas Rolantes e Elevadores — Linha 13 ─────────────────
  ('30000001', '30000001', 'ESCADA ROLANTE - EST. LUZ (L13) - MB 01',    'TV13', NULL, 'ER', true, now()),
  ('30000002', '30000002', 'ESCADA ROLANTE - EST. LUZ (L13) - MB 02',    'TV13', NULL, 'ER', true, now()),
  ('30000005', '30000005', 'ELEVADOR - EST. LUZ (L13) - EL 01',          'TV13', NULL, 'ER', true, now()),

  -- ── Equipamentos elétricos / energia — Linha 11 ─────────────
  ('40000001', '40000001', 'SUBESTAÇÃO RETIFICADORA - BRÁS (L11)',        'TV11', NULL, 'EL', true, now()),
  ('40000002', '40000002', 'TRANSFORMADOR DE FORÇA - LUZ (L11)',          'TV11', NULL, 'EL', true, now()),
  ('40000004', '40000004', 'PAINEL CCIM - ESTAÇÃO BRÁS (L11)',            'TV11', NULL, 'EL', true, now()),

  -- ── Equipamentos elétricos / energia — Linha 13 ─────────────
  ('40000003', '40000003', 'GRUPO GERADOR - ENG. GOULART (L13)',          'TV13', NULL, 'EL', true, now()),

  -- ── Via Permanente (Máquinas de Chave) — Linha 11 ────────────
  ('10002541', '10002541', 'MÁQUINA DE CHAVE - CHV 13 KM 04/16 (L11)',   'TV11', NULL, 'VP', true, now()),
  ('50000001', '50000001', 'TRILHO - TRECHO BRÁS-LUZ (L11)',             'TV11', NULL, 'VP', true, now()),

  -- ── Via Permanente — Linha 12 ────────────────────────────────
  ('50000002', '50000002', 'DORMENTE - TRECHO LUZ-BRÁS (L12)',           'TV12', NULL, 'VP', true, now()),

  -- ── Sinalização — Linha 11 ───────────────────────────────────
  ('60000001', '60000001', 'BALIZADOR PRINCIPAL - ESTAÇÃO BRÁS (L11)',   'TV11', NULL, 'SI', true, now()),
  ('60000002', '60000002', 'CIRCUITO DE TRILHO - CV11 KM 02 (L11)',      'TV11', NULL, 'SI', true, now()),

  -- ── Telecom / Multimídia — Linha 11 ──────────────────────────
  ('70000001', '70000001', 'SISTEMA CFTV - ESTAÇÃO LUZ (L11)',           'TV11', NULL, 'TE', true, now()),
  ('70000002', '70000002', 'RÁDIO BASE - ESTAÇÃO BRÁS (L11)',            'TV11', NULL, 'TE', true, now()),

  -- ── Rede Aérea — Linha 11 ────────────────────────────────────
  ('80000001', '80000001', 'FIOS AÉREOS TRECHO LUZ-BRÁS (L11)',         'TV11', NULL, 'RE', true, now()),
  ('80000002', '80000002', 'ISOLADOR SECCIONADOR - BRÁS (L11)',          'TV11', NULL, 'RE', true, now());

-- ─────────────────────────────────────────────────────────────
-- 3. CATÁLOGO DE SINTOMAS — usado pela Operação (Catálogo B SAP)
--    Perfis por grupo_catalogo de equipamento (RBNR / CatalogProfile)
--    Baseado no slide 38: "Catálogo de Sintomas utilizado exclusivamente pela Operação"
--
--    Campos:
--      grupo       = grupo SAP (2 letras = grupo_catalogo do equipamento)
--      codigo_item = código dentro do grupo
--      descricao   = sintoma observado pelo operador/solicitante
-- ─────────────────────────────────────────────────────────────

-- Limpa sintomas anteriores da MVP SAF
DELETE FROM sintomas_catalogo
WHERE grupo IN ('ER','EL','MR','VP','CI','TE','SI','RE');

-- ── ESCADA ROLANTE (ER) — Perfil exato do slide 38 ───────────
-- Defeitos: Desgastado, Quebrado, Queimado, Travado, Obstruído,
--           Solto, Corroído, Deformado, Ressecado, Desregulado
-- Parte Objeto: Motor Elétrico, Painel Elétrico, Rolamento, Acoplamento,
--              Sensor, Vedação, Correntes, Cabeamento
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('ER-001','ER','001','Escada parada / sem movimento',          'B', true, now()),
  ('ER-002','ER','002','Escada com movimento irregular / tremor','B', true, now()),
  ('ER-003','ER','003','Ruído anormal no degrau ou corrente',    'B', true, now()),
  ('ER-004','ER','004','Corrente / degrau desgastado',           'B', true, now()),
  ('ER-005','ER','005','Corrente / degrau quebrado ou solto',    'B', true, now()),
  ('ER-006','ER','006','Motor elétrico queimado / sem resposta', 'B', true, now()),
  ('ER-007','ER','007','Painel elétrico com falha ou alarme',    'B', true, now()),
  ('ER-008','ER','008','Sensor de emergência acionado',          'B', true, now()),
  ('ER-009','ER','009','Rolamento com travamento ou calor excessivo','B', true, now()),
  ('ER-010','ER','010','Obstrução no trajeto (objeto estranho)', 'B', true, now()),
  ('ER-011','ER','011','Corrosão visível na estrutura ou degrau','B', true, now()),
  ('ER-012','ER','012','Cabeamento exposto ou danificado',       'B', true, now()),
  -- Elevador (mesmo grupo ER = equipamentos de transporte vertical)
  ('ER-020','ER','020','Elevador parado / porta não abre',       'B', true, now()),
  ('ER-021','ER','021','Elevador com trepidação ou ruído',       'B', true, now()),
  ('ER-022','ER','022','Porta do elevador com falha de fechamento','B', true, now());

-- ── ELETROMECÂNICO / ELÉTRICO GERAL (EL) ─────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('EL-001','EL','001','Falta de energia / desligamento',        'B', true, now()),
  ('EL-002','EL','002','Disjuntor desarmado',                    'B', true, now()),
  ('EL-003','EL','003','Sobrecarga / aquecimento excessivo',     'B', true, now()),
  ('EL-004','EL','004','Curto-circuito ou faísca visível',       'B', true, now()),
  ('EL-005','EL','005','Falha no painel de controle / alarme',   'B', true, now()),
  ('EL-006','EL','006','Transformador com ruído ou vibração',    'B', true, now()),
  ('EL-007','EL','007','Gerador não parte / falha no arranque',  'B', true, now()),
  ('EL-008','EL','008','Bateria/UPS sem carga',                  'B', true, now()),
  ('EL-009','EL','009','Cabeamento exposto ou danificado',       'B', true, now());

-- ── MATERIAL RODANTE (MR) ─────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('MR-001','MR','001','Trem parado em via (falha de tração)',   'B', true, now()),
  ('MR-002','MR','002','Porta da composição com falha',          'B', true, now()),
  ('MR-003','MR','003','Ar condicionado da composição inoperante','B', true, now()),
  ('MR-004','MR','004','Ruído anormal no boggie / rodeiro',      'B', true, now()),
  ('MR-005','MR','005','Freio com irregularidade',               'B', true, now()),
  ('MR-006','MR','006','Sistema de informação ao passageiro falhou','B', true, now()),
  ('MR-007','MR','007','Pantógrafo com defeito',                 'B', true, now());

-- ── VIA PERMANENTE (VP) ───────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('VP-001','VP','001','Deformação / empeno de trilho',          'B', true, now()),
  ('VP-002','VP','002','Fratura ou quebra de trilho',            'B', true, now()),
  ('VP-003','VP','003','Máquina de chave com falha de operação', 'B', true, now()),
  ('VP-004','VP','004','Dormente quebrado ou solto',             'B', true, now()),
  ('VP-005','VP','005','Fixação faltante ou solta',              'B', true, now()),
  ('VP-006','VP','006','Lastro com deslocamento / falta',        'B', true, now()),
  ('VP-007','VP','007','JIC / isolador com falha',               'B', true, now());

-- ── CIVIL / PREDIAL (CI) ─────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('CI-001','CI','001','Infiltração / vazamento hídrico',        'B', true, now()),
  ('CI-002','CI','002','Vaso sanitário com falha ou obstrução',  'B', true, now()),
  ('CI-003','CI','003','Iluminação apagada ou piscando',         'B', true, now()),
  ('CI-004','CI','004','Piso danificado / irregular',            'B', true, now()),
  ('CI-005','CI','005','Ar condicionado de estação inoperante',  'B', true, now()),
  ('CI-006','CI','006','Portão / cancela com falha de operação', 'B', true, now()),
  ('CI-007','CI','007','Bebedouro sem funcionamento',            'B', true, now()),
  ('CI-008','CI','008','Lixeira / mobiliário danificado',        'B', true, now());

-- ── TELECOM (TE) ─────────────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('TE-001','TE','001','Sonorização sem áudio / distorcida',     'B', true, now()),
  ('TE-002','TE','002','Painel de informação ao passageiro apagado','B', true, now()),
  ('TE-003','TE','003','CFTV sem imagem / câmera com falha',     'B', true, now()),
  ('TE-004','TE','004','Rádio base sem comunicação',             'B', true, now()),
  ('TE-005','TE','005','Interfone com defeito',                  'B', true, now()),
  ('TE-006','TE','006','Relógio digital com hora incorreta',     'B', true, now());

-- ── SINALIZAÇÃO (SI) ─────────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('SI-001','SI','001','Balizador com falha de indicação',       'B', true, now()),
  ('SI-002','SI','002','Circuito de trilho com ocupação falsa',  'B', true, now()),
  ('SI-003','SI','003','Sinal de bloqueio aceso sem motivo',     'B', true, now()),
  ('SI-004','SI','004','Sistema SCADA/supervisório com alarme',  'B', true, now()),
  ('SI-005','SI','005','Detector de descarrilamento acionado',   'B', true, now());

-- ── REDE AÉREA (RE) ──────────────────────────────────────────
INSERT INTO sintomas_catalogo (codigo, grupo, codigo_item, descricao, tipo_catalogo, ativo, sincronizado_em)
VALUES
  ('RE-001','RE','001','Fio aéreo partido ou caído',             'B', true, now()),
  ('RE-002','RE','002','Tensão fora do padrão na catenária',     'B', true, now()),
  ('RE-003','RE','003','Isolador danificado ou estourado',       'B', true, now()),
  ('RE-004','RE','004','Seccionador com falha de manobra',       'B', true, now()),
  ('RE-005','RE','005','Aterramento com falha de continuidade',  'B', true, now());
