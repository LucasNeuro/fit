# 02 — Arquitetura

## Visão geral

```
┌─────────────────┐     ┌──────────┐     ┌──────────────────────────┐
│ Aluno WhatsApp  │◄───►│  UAZAPI  │────►│ backend/                 │
└─────────────────┘     └────┬─────┘     │  api/ (FastAPI webhook)  │
                             │           │  agents/ (Agno + Mistral)  │
                             │           └────────────┬─────────────┘
                             │                        │ tools
                             ▼                        ▼
                      editLead (CRM)            ┌─────────────┐
                                                │  Supabase   │
                                                └──────┬──────┘
                                                       │
                              (depois)                 │
                                                ┌──────▼──────┐
                                                │ frontend/   │
                                                │ TanStack    │
                                                │ Start       │
                                                └─────────────┘

Presença: [QR WhatsApp] → recepção escaneia → backend/api/attendance → Supabase
```

## Pastas e responsabilidades

| Pasta | Papel |
|-------|-------|
| `backend/` | **Superagente** — única fonte de lógica IA, WhatsApp, jobs, QR |
| `frontend/` | **Visualização** — painel dono, leitor QR (consome Supabase + API) |
| `supabase/` | Persistência compartilhada |
| `docs/` | Contrato do sistema |

## Fonte da verdade

| Dado | Sistema | Observação |
|------|---------|------------|
| Envio/recebimento WhatsApp | UAZAPI | Canal oficial |
| CRM operacional (status, tags, kanban) | UAZAPI `editLead` | Espelhado em `crm_contacts` |
| Planos, horários, reservas | Supabase | Agente **nunca inventa** — só tools |
| Matrículas | Supabase `enrollments` | Backend + agente |
| Presença / QR | Supabase `qr_tokens`, `attendance` | Backend gera e valida |
| Histórico de mensagens | Supabase `messages` | Ilimitado |
| Config do agente por academia | Supabase `gyms.agent_config` | Tom, nome, regras |

## Chaves de correlação

| Chave | Uso |
|-------|-----|
| `gym_id` | Tenant (multi-academia / RLS) |
| `wa_chatid` | ID do chat WhatsApp |
| `phone` | Telefone normalizado |
| `member_id` | Aluno no Supabase |

## Fluxo: mensagem inbound

1. UAZAPI → `POST backend/api/webhook/uazapi`
2. Identifica `gym_id` pela instância
3. Persiste `messages` (in)
4. Resolve/cria `members`
5. `backend/agents/` — Agno + Mistral + tools
6. Resposta via UAZAPI
7. Persiste `messages` (out)
8. `editLead` + sync `crm_contacts` se CRM mudou

## Fluxo: presença QR

1. Agente ou job gera token → `qr_tokens` + imagem QR → WhatsApp
2. Recepção: `frontend/porta` (futuro) ou app leitor → `POST backend/api/attendance/check-in`
3. Backend valida token, grava `attendance`
4. Opcional: mensagem confirmação via UAZAPI

## Fluxo: handoff humano

- `lead_isTicketOpen: true`, tag `humano`
- Opcional: `chatbot_disableUntil`
- Painel (futuro) lista tickets abertos

## Princípios de design

1. **LLM + tools** — Preços e horários só do Supabase.
2. **Log antes de processar** — Toda mensagem inbound gravada.
3. **Fail-safe** — Handoff humano na dúvida.
4. **RLS** — Isolamento por `gym_id`.
5. **Backend primeiro** — Frontend é cliente; não duplicar lógica de negócio no React.
6. **CRM híbrido** — UAZAPI operação; Supabase relatórios.

## Integrações futuras

| Sistema | Modo |
|---------|------|
| BioGym / ERP | Sync `external_id` em `enrollments` |
| Pagamento Pix | Link externo; status em `enrollments` |
| UI | `frontend/` — Tailwind CSS + daisyUI 5 |
