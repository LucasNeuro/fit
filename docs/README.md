# FIT — Especificações do Projeto

Sistema de gestão para academias com assistente IA no WhatsApp (UAZAPI), mini CRM, matrículas e presença (QR).

## Estrutura do repositório

```
fit/
├── docs/          # Especificações
├── backend/       # Agente Agno + Mistral + FastAPI (prioridade agora)
├── frontend/      # TanStack Start + DaisyUI (depois do backend)
└── supabase/    # Migrations e seed (compartilhado)
```

## Documentos

| # | Arquivo | Conteúdo |
|---|---------|----------|
| 1 | [01-visao-produto.md](./01-visao-produto.md) | Problema, solução, planos, ROI |
| 2 | [02-arquitetura.md](./02-arquitetura.md) | Diagrama, fluxos, responsabilidades |
| 3 | [03-stack-e-repos.md](./03-stack-e-repos.md) | Stack, pastas `backend/` e `frontend/` |
| 4 | [04-banco-dados.md](./04-banco-dados.md) | Schema SQL, RLS, índices |
| 5 | [05-uazapi-whatsapp-crm.md](./05-uazapi-whatsapp-crm.md) | Webhooks, fieldsMap, editLead |
| 6 | [06-agente-agno-mistral.md](./06-agente-agno-mistral.md) | Tools, prompts, intents |
| 7 | [07-painel-tanstack-start.md](./07-painel-tanstack-start.md) | Painel TanStack Start + DaisyUI |
| 8 | [08-fases-e-roadmap.md](./08-fases-e-roadmap.md) | Backend completo primeiro; frontend depois |
| 9 | [09-checklist-inicio-agente.md](./09-checklist-inicio-agente.md) | Checklist implementação em `backend/` |
| 10 | [10-variaveis-ambiente.md](./10-variaveis-ambiente.md) | `.env` backend vs frontend |
| 11 | [11-onboarding-whatsapp.md](./11-onboarding-whatsapp.md) | Criar instância via API, sem token no .env |
| 12 | [12-deploy-render.md](./12-deploy-render.md) | AgentOS local + API no Render + webhook |
| 13 | [13-deploy-render-uazapi.md](./13-deploy-render-uazapi.md) | Deploy Render + webhook global (foco atual) |

## Ordem de implementação

### Agora — `backend/` (superagente completo)

1. Webhook UAZAPI → Agno → Mistral → resposta WhatsApp
2. Supabase: todas as migrations (agendamento, CRM, matrículas, QR)
3. Tools + CRM + lembretes + cobrança + matrículas + presença QR
4. APIs REST para o futuro painel (`/attendance/check-in`, etc.)

### Depois — `frontend/` (TanStack Start + DaisyUI)

5. Painel do dono + PWA leitor QR na porta
6. Tema `fit` + layout drawer/navbar (daisyUI)

## Contato do projeto

- **Responsável:** Lucas Marcondès
- **Local:** Capão Redondo, São Paulo
