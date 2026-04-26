# Contexto do Projeto: Sistema SAF (Solicitação de Abertura de Falhas)

## Visão Geral
[cite_start]O sistema SAF é uma aplicação web responsiva que atua como um "cockpit" de entrada para a criação de solicitações de manutenção[cite: 10, 18]. [cite_start]O objetivo é centralizar a triagem de falhas e integrar os dados bidirecionalmente com o sistema SAP (atualmente via Mocks de BAPI/REST para desenvolvimento)[cite: 18]. 

## Stack Tecnológico
* **Back-end:** Python 3 com Flask.
* **Banco de Dados:** PostgreSQL (hospedado no Supabase).
* **Armazenamento de Arquivos:** Supabase Storage (para upload de fotos/evidências).
* [cite_start]**Integração:** Mock de APIs SAP (simulando BAPI_ALM_NOTIF_CREATE, SAVE e COMMIT)[cite: 87, 88, 90].

## Regras de Negócio e Perfis (RBAC)
[cite_start]O sistema possui controle de acesso com 3 perfis[cite: 9]:
1.  [cite_start]**Solicitante:** Cria solicitações, edita (apenas se devolvido pelo CCM) e pode cancelar (apenas se a Ordem SAP não tiver sido gerada)[cite: 11, 12, 31].
2.  [cite_start]**CCM (Centro de Controle de Manutenção):** Avalia as solicitações[cite: 13, 14]. [cite_start]Pode "Aprovar" (dispara criação no SAP), pedir "Complemento" (devolve ao solicitante) ou "Cancelar" [cite: 33-42].
3.  [cite_start]**Administrador:** Acesso a logs de auditoria e configurações gerais[cite: 15, 16].

## Fluxo de Integração e Status
* **Aprovação Síncrona:** Quando o CCM aprova, o Flask deve realizar uma chamada atômica para a API do SAP. [cite_start]Em caso de sucesso, o SAP retorna o número da Nota (`QMNUM`), que é salvo no banco local [cite: 22-24, 34-35].
* [cite_start]**Cancelamento:** Se houver falha de comunicação com a API do SAP ao tentar cancelar uma nota existente, o sistema deve aplicar rollback e não alterar o status local[cite: 94]. [cite_start]O botão de cancelar deve ser permanentemente bloqueado se o campo de Ordem de Manutenção (`QMEL-AUFNR`) estiver preenchido[cite: 31].
* [cite_start]**Dados Mestres:** O sistema usa tabelas de cache locais de Locais de Instalação, Equipamentos e Sintomas para aplicar filtros dinâmicos e hierárquicos no front-end [cite: 72-75].

## Estrutura do Banco de Dados (Supabase/Postgres)
O banco foi normalizado nas seguintes tabelas principais:
* `usuarios`: Autenticação e definição do perfil.
* `saf_solicitacoes`: Guarda apenas os dados da falha preenchidos pelo solicitante (texto, equipamento, url da foto).
* `saf_controle_ccm`: Workflow 1:1 com a solicitação (status, motivos de devolução).
* `saf_integracao_sap`: Isolamento dos dados do SAP (QMNUM, AUFNR).
* `logs_auditoria`: Registro de rastreabilidade (LGPD).
* `locais_instalacao`, `equipamentos`, `sintomas_catalogo`: Cache para Search Help dinâmico.