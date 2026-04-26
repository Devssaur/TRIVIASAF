# TRIVIASAF — Sistema de Abertura de Falhas

Aplicação web responsiva que atua como cockpit de entrada para criação e triagem de solicitações de manutenção, com integração bidirecional ao SAP (via Mock de BAPI/REST).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Back-end | Python 3.13 + Flask |
| Banco de dados | PostgreSQL (Supabase) |
| Armazenamento | Supabase Storage |
| Integração | Mock SAP (BAPI_ALM_NOTIF_CREATE) |

---

## Pré-requisitos

- Python 3.13+
- Conta no [Supabase](https://supabase.com)
- Git

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Devssaur/TRIVIASAF.git
cd TRIVIASAF

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instale as dependências
pip install flask supabase python-dotenv
```

---

## Configuração

Crie o arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_KEY=<sua-chave-anon>
```

---

## Banco de Dados

Execute os scripts na ordem abaixo no **SQL Editor** do Supabase:

| Arquivo | Descrição |
|---|---|
| `database/schema_saf.sql` | Criação das tabelas, índices e triggers |
| `database/policies_rls.sql` | Políticas de segurança RLS |
| `database/seed_usuarios.sql` | Usuários de teste |

---

## Executando

```bash
python app.py
```

Acesse: `http://127.0.0.1:5000/`

---

## Rotas da API

### Autenticação — `/api/auth`

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/login` | Login com email e senha |

```json
// POST /api/auth/login
{ "email": "joao@empresa.com", "senha": "senha123" }
```

---

### Solicitações — `/api/solicitacoes`

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/solicitacoes/criar` | Cria nova SAF |
| GET | `/api/solicitacoes/minhas-safs/<usuario_id>` | Lista SAFs do solicitante |

```json
// POST /api/solicitacoes/criar
{
  "usuario_id": "<uuid>",
  "titulo": "Bomba com vazamento",
  "descricao": "Identificado vazamento no selo mecânico",
  "local_id": 1,
  "equipamento_id": 2,
  "prioridade": "ALTA"
}
```

---

### CCM — `/api/ccm`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/ccm/pendentes` | Lista SAFs aguardando triagem |
| POST | `/api/ccm/avaliar/<saf_id>` | Avalia uma SAF |

```json
// POST /api/ccm/avaliar/<saf_id>
// status: "Confirmado" | "Necessário Complemento" | "Cancelado"
{
  "status": "Confirmado",
  "avaliado_por_id": "<uuid-do-ccm>"
}
```

---

### Dados Mestres — `/api/dados`

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/dados/locais` | Lista locais de instalação |
| GET | `/api/dados/equipamentos/<local_id>` | Equipamentos por local |
| GET | `/api/dados/sintomas/<equipamento_id>` | Catálogo de sintomas |

---

## Perfis de Acesso (RBAC)

| Perfil | Permissões |
|---|---|
| `SOLICITANTE` | Cria, edita (se devolvida) e cancela SAFs (sem ordem SAP) |
| `CCM` | Avalia SAFs: Aprovar, Devolver ou Cancelar |
| `ADMIN` | Acesso a logs de auditoria e configurações |

---

## Estrutura do Projeto

```
TRIVIASAF/
├── app.py                  # Ponto de entrada Flask
├── .env                    # Credenciais (não versionado)
├── .gitignore
├── contexto.md             # Documento de requisitos do projeto
├── database/
│   ├── schema_saf.sql      # DDL das tabelas
│   ├── policies_rls.sql    # Políticas RLS do Supabase
│   └── seed_usuarios.sql   # Dados de teste
└── routes/
    ├── auth.py             # Autenticação
    ├── solicitacoes.py     # CRUD de SAFs
    ├── ccm.py              # Triagem CCM
    └── dados_mestres.py    # Cache de dados SAP
```

