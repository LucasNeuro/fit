# 08 — Fases e roadmap

## Estratégia: backend completo → frontend depois

```
┌─────────────────────────────────────────────────────────────┐
│  AGORA: backend/ — superagente + todas as regras de negócio │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  DEPOIS: frontend/ — TanStack Start + DaisyUI               │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend — Fase 1: Agente + agendamento

**Objetivo:** WhatsApp respondendo com dados reais e reserva funcionando.

### Entregas (`backend/`)

- [ ] `supabase/migrations/001_fase1_core.sql`
- [ ] `backend/api` — webhook + health
- [ ] `backend/agents` — Agno + Mistral Small
- [ ] Tools: `listar_horarios`, `criar_reserva`, `listar_planos`, `buscar_ou_criar_membro`, `atualizar_lead`
- [ ] UAZAPI `updateFieldsMap` + `editLead`
- [ ] `seed.sql` academia piloto

### DoD

> *"Horários de funcional amanhã?"* → lista real. *"Quero o das 18h"* → reserva + CRM `experimental` + tag `agendou`.

---

## Backend — Fase 2: CRM sync + jobs

**Objetivo:** CRM espelhado, lembretes e cobrança automáticos.

### Entregas

- [ ] Sync `crm_contacts` (pós `editLead` + webhook)
- [ ] Job lembrete (2h antes da aula)
- [ ] Job cobrança básica (mensagem + link)
- [ ] Handoff humano estável
- [ ] Endpoints REST documentados para o futuro painel

### DoD

> Lembrete enviado automaticamente para booking de amanhã; CRM no Supabase igual UAZAPI.

---

## Backend — Fase 3: Matrículas

**Objetivo:** Aluno ativo/inadimplente no sistema; agente reconhece status.

### Entregas

- [ ] `002_enrollments.sql`
- [ ] Tools: `status_matricula`, `listar_inadimplentes`
- [ ] Agente atualiza CRM `matriculado` / tag `cobranca`
- [ ] Regra opcional: bloquear QR se inadimplente

### DoD

> Matrícula ativa no Supabase → agente trata como aluno e não como lead frio.

---

## Backend — Fase 4: Presença QR

**Objetivo:** QR na porta sem depender do painel.

### Entregas

- [ ] `003_attendance_qr.sql`
- [ ] `backend/agents/tools/qr.py` + `api/routes/attendance.py`
- [ ] Token HMAC, TTL, uso único
- [ ] Agente/job envia QR no WhatsApp antes da aula
- [ ] `POST /attendance/check-in` e `check-out`
- [ ] Teste com curl/Postman (sem frontend)

### DoD

> Token válido → check-in em `attendance`; token expirado → 401; aluno recebe QR no WhatsApp.

---

## Frontend — Fase 5: TanStack Start (painel)

**Objetivo:** Dono gerencia visualmente o que o backend já faz.

### Entregas (`frontend/`)

- [ ] Scaffold TanStack Start + Supabase Auth
- [ ] Tailwind 4 + daisyUI 5 + tema `fit` aplicados
- [ ] Dashboard, conversas, leads, planos, horários, agendamentos
- [ ] Matrículas, presença, `/porta` QR
- [ ] `.env` com `VITE_API_URL` apontando para backend

### DoD

> Dono loga, vê operação do dia, escaneia QR em `/porta` conectado ao backend.

### Fora de escopo até Fase 5

- Qualquer tela React
- BioGym, pagamento integrado, app nativo

---

## Timeline sugerida

| Período | Foco |
|---------|------|
| Semanas 1–2 | Backend Fase 1 |
| Semanas 3–4 | Backend Fase 2–3 |
| Semanas 5–6 | Backend Fase 4 |
| Semanas 7–9 | Frontend Fase 5 (TanStack Start + DaisyUI) |
| Semana 10+ | Piloto 3 academias, cobrança |

---

## Validação comercial (paralelo)

| Semana | Ação |
|--------|------|
| 1 | 10 entrevistas donos |
| 2–6 | Demo WhatsApp (backend Fase 1–2) |
| 7+ | Demo painel (frontend) |

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Frontend antes do backend | **Bloqueado** por esta spec |
| Escopo backend | Fases 1–4 sequenciais com DoD |
| Consistência visual | Componentes em `components/ui/` + tema `fit` único |
| Custo Mistral | Small default; limites por plano |
