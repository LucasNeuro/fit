# 09 — Checklist: implementar em `backend/`

Tudo abaixo é em **`backend/`** e **`supabase/`** — **não** criar `frontend/` até backend Fases 1–4 prontas.

---

## Pré-requisitos

- [ ] Conta [Mistral AI](https://console.mistral.ai) + `MISTRAL_API_KEY`
- [ ] Projeto [Supabase](https://supabase.com) criado
- [ ] Instância UAZAPI conectada (WhatsApp teste)
- [ ] Python 3.11+
- [ ] Node 20+ guardado para **depois** (TanStack Start)

---

## Dia 1 — Estrutura `backend/`

### 1.1 Pastas

```bash
mkdir -p backend/agents/tools backend/agents/prompts backend/api/routes supabase/migrations
```

- [ ] Estrutura conforme [03-stack-e-repos.md](./03-stack-e-repos.md)
- [ ] `frontend/README.md` placeholder (opcional)

### 1.2 Ambiente

- [ ] `backend/.env.example` → `backend/.env`
- [ ] Todas as chaves preenchidas

### 1.3 Supabase

- [ ] `supabase/migrations/001_fase1_core.sql`
- [ ] `supabase/seed.sql`
- [ ] Tabelas visíveis no Table Editor

### 1.4 UAZAPI

- [ ] Webhook → `https://<tunnel>/webhook/uazapi`
- [ ] `updateFieldsMap` ([05-uazapi-whatsapp-crm.md](./05-uazapi-whatsapp-crm.md))

---

## Dia 2 — API (`backend/api/`)

- [ ] `backend/api/main.py` — FastAPI
- [ ] `GET /health`
- [ ] `POST /webhook/uazapi` — log + 200
- [ ] Identificar `gym_id` + insert `messages` (in)
- [ ] `buscar_ou_criar_membro`

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

---

## Dia 3 — Agente (`backend/agents/`)

- [ ] `backend/requirements.txt`
- [ ] `agents/prompts/recepcionista.md`
- [ ] `agents/main.py` — Mistral Small
- [ ] Webhook chama agente
- [ ] Resposta UAZAPI + `messages` (out)
- [ ] E2E: WhatsApp → resposta < 60s

---

## Dia 4 — Tools Fase 1

- [ ] `listar_horarios`, `listar_planos`, `criar_reserva`
- [ ] Validação de capacidade
- [ ] 5 testes de aceite ([abaixo](#testes-de-aceite-fase-1))

---

## Dia 5 — CRM Fase 2 (backend)

- [ ] `atualizar_lead` + `crm_contacts` upsert
- [ ] Jobs lembrete + cobrança (APScheduler ou cron HTTP)

---

## Semana 3 — Matrículas Fase 3 (backend)

- [ ] `002_enrollments.sql`
- [ ] Tools matrícula + inadimplência
- [ ] CRM `matriculado` / `cobranca`

---

## Semana 4 — QR Fase 4 (backend)

- [ ] `003_attendance_qr.sql`
- [ ] `tools/qr.py` + `routes/attendance.py`
- [ ] QR no WhatsApp antes da aula
- [ ] Testar check-in via `curl` (sem frontend)

---

## Testes de aceite Fase 1

| # | Mensagem | Esperado | OK |
|---|----------|----------|-----|
| 1 | "Oi" | Saudação | [ ] |
| 2 | "Horários funcional amanhã" | Slots reais | [ ] |
| 3 | "Quero o das 18h" | Reserva OK | [ ] |
| 4 | "Quanto custa o mensal?" | Preço seed | [ ] |
| 5 | "Quero atendente" | Ticket aberto | [ ] |

---

## Definition of Done — Backend completo

```
[ ] Fases 1–4: webhook, agente, CRM, matrículas, QR/API attendance
[ ] Migrations 001–003 aplicadas
[ ] README raiz + backend/README com comandos
[ ] .env.example documentado
[ ] Frontend NÃO necessário para demonstrar produto no WhatsApp
```

---

## Depois do backend — Frontend

1. `npm create @tanstack/start@latest` em `frontend/`
2. Instalar Tailwind + daisyUI (ver [07-painel-tanstack-start.md](./07-painel-tanstack-start.md))
3. Aplicar tema `fit` e layout drawer

---

## Comandos úteis

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Tunnel
ngrok http 8000

# Health
curl http://localhost:8000/health
```

---

## Referência rápida

| Tópico | Arquivo |
|--------|---------|
| Pastas | [03-stack-e-repos.md](./03-stack-e-repos.md) |
| SQL | [04-banco-dados.md](./04-banco-dados.md) |
| CRM | [05-uazapi-whatsapp-crm.md](./05-uazapi-whatsapp-crm.md) |
| Agente | [06-agente-agno-mistral.md](./06-agente-agno-mistral.md) |
| Fases | [08-fases-e-roadmap.md](./08-fases-e-roadmap.md) |
| Painel (depois) | [07-painel-tanstack-start.md](./07-painel-tanstack-start.md) |
