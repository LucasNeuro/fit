# 03 — Stack e estrutura do repositório

## Stack tecnológica

| Camada | Tecnologia | Onde |
|--------|------------|------|
| **Agente** | [Agno](https://docs.agno.com) (Python) | `backend/agents/` |
| **LLM** | [Mistral](https://docs.mistral.ai) via `MistralChat` | `backend/agents/` |
| **API** | FastAPI | `backend/api/` |
| **Banco** | Supabase (Postgres + Auth + RLS) | `supabase/` |
| **WhatsApp + CRM** | UAZAPI | Integrado no `backend/` |
| **Painel (depois)** | [TanStack Start](https://tanstack.com/start) + React + TypeScript | `frontend/` |
| **UI/CSS** | [Tailwind CSS 4](https://tailwindcss.com) + [daisyUI 5](https://daisyui.com) | `frontend/` |

## Por que essa stack

| Escolha | Motivo |
|---------|--------|
| Agno + Mistral | Agente no Python; tools e Mistral nativos |
| FastAPI | Webhooks UAZAPI, QR, cron jobs, APIs para o painel |
| Supabase | Banco + Auth do painel; RLS multi-tenant |
| UAZAPI | WhatsApp + mini CRM por conversa |
| TanStack Start | React full-stack; exemplo oficial Supabase; server functions |
| DaisyUI | Componentes via classes Tailwind; temas + dashboard rápido |
| **Backend primeiro** | Valor do FIT está no superagente; UI consome APIs prontas |

## Separação `backend/` vs `frontend/`

| Pasta | Responsabilidade | Quando |
|-------|------------------|--------|
| **`backend/`** | Superagente, webhooks, tools, jobs, validação QR, REST interno | **Agora** |
| **`frontend/`** | Dashboard dono, CRM visual, CRUD, PWA `/porta` | **Depois** |
| **`supabase/`** | Migrations, seed, tipos — usado por ambos | Desde o início |
| **`docs/`** | Especificações | Contínuo |

O agente **não vive** no frontend. O frontend só chama Supabase (RLS) e, quando necessário, rotas do `backend/` (ex: check-in QR).

## Estrutura alvo do monorepo

```
fit/
├── docs/
├── backend/
│   ├── agents/
│   │   ├── main.py                 # Agent Agno principal
│   │   ├── tools/
│   │   │   ├── supabase.py         # horários, reservas, planos, matrículas
│   │   │   ├── uazapi.py           # send_message, edit_lead
│   │   │   ├── qr.py               # gerar/validar tokens presença
│   │   │   └── crm.py              # sync crm_contacts
│   │   └── prompts/
│   │       └── recepcionista.md
│   ├── api/
│   │   ├── main.py                 # FastAPI app
│   │   └── routes/
│   │       ├── webhook.py          # UAZAPI inbound
│   │       ├── health.py
│   │       ├── attendance.py       # check-in/out QR
│   │       └── jobs.py             # lembretes, cobrança (cron)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/styles/app.css          # @import tailwindcss + @plugin daisyui
│   └── README.md                   # Placeholder até iniciar TanStack Start
├── supabase/
│   ├── migrations/
│   │   ├── 001_fase1_core.sql
│   │   ├── 002_enrollments.sql
│   │   └── 003_attendance_qr.sql
│   └── seed.sql
├── .env.example                    # opcional: referência raiz
└── README.md
```

## Variáveis de ambiente (`backend/.env`)

```bash
# Mistral
MISTRAL_API_KEY=

# Supabase (service role — só no backend)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# UAZAPI
UAZAPI_BASE_URL=
UAZAPI_TOKEN=

# API
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_SECRET=

# QR / segurança
QR_SIGNING_SECRET=

# App
ENV=development
LOG_LEVEL=info
```

## Variáveis de ambiente (`frontend/.env`) — depois

```bash
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=http://localhost:8000   # backend FastAPI
```

**Nunca** colocar `SUPABASE_SERVICE_ROLE_KEY` ou `MISTRAL_API_KEY` no frontend.

## Dependências Python (`backend/requirements.txt`)

```
agno
mistralai
fastapi
uvicorn
supabase
httpx
pydantic
python-dotenv
qrcode[pil]
```

## Dependências frontend — depois

```bash
# TanStack Start (quando iniciar frontend/)
npm create @tanstack/start@latest
npm install tailwindcss @tailwindcss/vite daisyui
npm install @supabase/supabase-js @tanstack/react-query
# opcional: html5-qrcode (PWA /porta)
```

Ver instalação completa: [07-painel-tanstack-start.md](./07-painel-tanstack-start.md)

## Modelos Mistral no Agno

```python
from agno.agent import Agent
from agno.models.mistral import MistralChat

agent = Agent(
    model=MistralChat(id="mistral-small-latest"),
    markdown=True,
)
```

Documentação: https://docs.agno.com/cookbook/models/open-source/mistral

## TanStack Start + DaisyUI (referência)

- TanStack Start: https://tanstack.com/start/latest/docs/framework/react/overview
- daisyUI + React/Vite: https://daisyui.com/docs/install/react/
- Supabase + Start: exemplo `start-supabase-basic` na doc TanStack
- Tema FIT: ver [07-painel-tanstack-start.md](./07-painel-tanstack-start.md)

## Ambientes

| Ambiente | Backend | Frontend | Supabase | UAZAPI |
|----------|---------|----------|----------|--------|
| `development` | localhost:8000 | localhost:3000 (futuro) | projeto dev | instância teste |
| `staging` | URL staging | URL staging | staging | piloto |
| `production` | URL prod | URL prod | prod | 1 instância / academia |

## Comunicação entre camadas

| De → Para | Protocolo |
|-----------|-----------|
| UAZAPI → backend | Webhook HTTP POST |
| backend → UAZAPI | REST (mensagem, editLead) |
| backend → Supabase | `supabase-py` (service role) |
| frontend → Supabase | `@supabase/supabase-js` (anon + RLS) |
| frontend → backend | HTTP REST (QR scan, ações que exigem segredo) |
