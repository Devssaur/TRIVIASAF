Criar sumario


1 - Banco de dados
1. Tabela: usuarios
Responsável pela autenticação única e pelo Gerenciamento de Perfis (RBAC).
Coluna
Tipo
Descrição e Regras
id
UUID (PK)
Identificador único do banco.
nome
String
Nome completo.
email
String
Login de acesso.
senha_hash
String
Senha criptografada.
perfil
Enum
Valores permitidos: 'Solicitante', 'CCM' ou 'Administrador'.





2. Tabela: saf_solicitacoes Armazena exclusivamente os dados de entrada preenchidos pelo Solicitante .
Coluna
Tipo (Postgres)
Correspondência SAP / Regras
id
UUID (PK)
Chave primária da tabela.
ticket_saf
SERIAL
Chave sequencial visual para o usuário (Ticket SAF).
notificador_id
UUID (FK)
Relacionamento com usuarios.id (QMEL-QMNAM).
titulo_falha
VARCHAR(40)
Descrição resumida da falha (QMEL-QMTXT).
descricao_longa
TEXT
Detalhamento livre (Rich Text).
local_instalacao
VARCHAR
Código SAP do local selecionado (QMEL-TPLNR).
equipamento
VARCHAR
Código SAP do equipamento (QMEL-EQUNR).
prioridade
INTEGER
Grau de prioridade de 1 a 4 (QMEL-PRIOK).
sintoma_codigo
VARCHAR
Código do sintoma/dano selecionado (QMEL-QMCOD).
data_inicio_avaria
DATE
(QMEL-AUSVN e STRMN) .
hora_inicio_avaria
TIME
(QMEL-AUZTV e STRUR) .
anexo_evidencia_url
TEXT
Link do Supabase Storage para a foto.
criado_em
TIMESTAMP
Data e hora de abertura no app.




3. Tabela: saf_controle_ccm Relacionamento 1:1 com a solicitação. Isola o fluxo de trabalho gerencial do CCM.
Coluna
Tipo (Postgres)
Descrição e Regras
id
UUID (PK)
Identificador único.
solicitacao_id
UUID (FK)
Relacionamento com saf_solicitacoes.id.
status
VARCHAR
'Pendente CCM', 'Confirmado', 'Necessário Complemento' ou 'Cancelado'.
motivo_complemento
TEXT
Preenchido pelo CCM, visível ao solicitante.
motivo_cancelamento
TEXT
Exigido se a nota for cancelada (pelo CCM ou Solicitante).
avaliado_por_id
UUID (FK)
Relacionamento com usuarios.id (quem fez a triagem).
data_avaliacao
TIMESTAMP
Data/hora do último parecer do CCM.

4. Tabela: saf_integracao_sap Relacionamento 1:1 com a solicitação. Isola estritamente as respostas e as chaves sistêmicas da API .
Coluna
Tipo (Postgres)
Descrição e Regras
id
UUID (PK)
Identificador único.
solicitacao_id
UUID (FK)
Relacionamento com saf_solicitacoes.id.
tipo_nota
VARCHAR
Ex: 'M2' para corretiva, 'M1' para preventiva (QMEL-QMART).
sap_qmnum
VARCHAR(12)
Número da Nota retornado pelo SAP após sucesso.
sap_aufnr
VARCHAR(12)
Número da Ordem no SAP. Se não nulo, bloqueia cancelamento.
ultima_sincronizacao
TIMESTAMP
Quando o Job atualizou o status da Ordem.



Módulo de Dados Mestres (Cache)
Tabelas utilizadas para o cache diário, evitando validações lentas na interface e garantindo hierarquia .
5. Tabela: locais_instalacao
Coluna
Tipo (Postgres)
Descrição e Regras
id_sap
VARCHAR (PK)
Código original no SAP (TPLNR).
descricao
VARCHAR
Nome legível para o Search Help.



6. Tabela: equipamentos
Coluna
Tipo (Postgres)
Descrição e Regras
id_sap
VARCHAR (PK)
Código original no SAP (EQUNR).
local_id_sap
VARCHAR (FK)
Relacionamento com locais_instalacao.id_sap para o filtro hierárquico.



7. Tabela: sintomas_catalogo
Coluna
Tipo (Postgres)
Descrição e Regras
id
UUID (PK)
Identificador da linha.
equipamento_id_sap
VARCHAR (FK)
Relacionamento com equipamentos.id_sap.
grupo_codigo
VARCHAR
Código do Grupo (QMGRP) do Catálogo C.
sintoma_codigo
VARCHAR
Código do Sintoma (QMCOD).
descricao
VARCHAR
Descrição visual do defeito.




8. Tabela: logs_auditoria Exigência para o Perfil de Administrador e compliance com a LGPD.
Coluna
Tipo (Postgres)
Descrição e Regras
id
UUID (PK)
Identificador da ação.
usuario_id
UUID (FK)
Quem acionou o evento (usuarios.id).
evento
VARCHAR
Ex: 'LOGIN', 'CRIACAO_SAF', 'BAPI_CREATE_ERROR'.
payload
JSONB
Registro JSON com os dados que foram trafegados (API request/response).
criado_em
TIMESTAMP
Data/hora exata do log.


