# FIT — Backend (Superagente)

API FastAPI + agente **Agno** + **Mistral** + Supabase + UAZAPI.

## Setup

### 1. Variáveis de ambiente

| Arquivo | O que vai aqui |
|---------|----------------|
| **`backend/.env`** | Mistral, Supabase **service role**, UAZAPI — **segredos do servidor** |
| **`frontend/.env`** | Só `VITE_SUPABASE_*` e `VITE_API_URL` — **chaves públicas** (depois) |
| **`.env` na raiz** (opcional) | Mesmas vars do backend; o código lê `backend/.env` primeiro |

```bash
cd backend
copy .env.example .env
# Preencha: MISTRAL_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
```

Referência completa: [../.env.example](../.env.example)

### 2. Ambiente Python

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### 3. Supabase

No SQL Editor do Supabase, execute em ordem:

1. `../supabase/migrations/001_fase1_core.sql`
2. `../supabase/migrations/002_enrollments.sql`
3. `../supabase/migrations/003_attendance_qr.sql`
4. `../supabase/migrations/004_gym_whatsapp_instances.sql`
5. `../supabase/seed.sql`

### Logs no terminal (Rich)

Com `LOG_LEVEL=info` (padrão) ou `debug`, o terminal mostra painéis coloridos:

- **webhook** — mensagem recebida, ignorada, academia não encontrada
- **agent** — entrada, resposta, tempo em ms
- **tool** — cada tool chamada pelo Agno
- **uazapi** — envio WhatsApp, criar instância

```bash
# Mais verboso
LOG_LEVEL=debug
```

### 4. Testar agente no AgentOS (UI Agno)

```powershell
cd backend
.venv\Scripts\activate
python run.py
```

- URL no [os.agno.com](https://os.agno.com): **Local** → `http://127.0.0.1:7780` → REFRESH
- API webhook (depois): porta **8000** — não confundir com AgentOS

**Windows + SSL:** `SSL_VERIFY=false` no `backend/.env` (só dev local).

Teste no terminal (sem UI):

```bash
python scripts/test_agent.py "Quais horários de funcional?"
```

### 5. Rodar API (webhook WhatsApp)

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- Webhook: `POST http://localhost:8000/webhook/uazapi`

### 6. Expor webhook (dev)

```bash
ngrok http 8000
```

Configure na UAZAPI: `https://<seu-ngrok>.ngrok.io/webhook/uazapi?wh=SEU_WEBHOOK_SECRET`

Deploy produção: [../docs/12-deploy-render.md](../docs/12-deploy-render.md)

## Teste local (sem WhatsApp)

```bash
curl -X POST http://localhost:8000/webhook/uazapi \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Quais horários de funcional amanhã?\",\"chatId\":\"5511999999999@s.whatsapp.net\",\"phone\":\"5511999999999\"}"
```

## Estrutura

```
backend/
├── api/           # FastAPI (webhook, health, attendance)
├── agents/        # Agno + Mistral + tools
├── core/          # config, supabase, uazapi, services
└── requirements.txt
```

## Roadmap backend

| Fase | Status |
|------|--------|
| 1 Agendamento + agente | Em implementação |
| 2 CRM sync + jobs | Próximo |
| 3 Matrículas | SQL pronto |
| 4 QR presença | Rota `/attendance/check-in` inicial |

Ver [docs/08-fases-e-roadmap.md](../docs/08-fases-e-roadmap.md).
