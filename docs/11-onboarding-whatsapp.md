# 11 — Onboarding WhatsApp (via painel — não no chat do agente)

> **Atualizado:** o agente de chat **não** faz mais onboarding de WhatsApp. Conexão será pelo **painel TanStack**. Ver [13-deploy-render-uazapi.md](./13-deploy-render-uazapi.md).

# 11 — Onboarding WhatsApp (sem instância no .env) — referência técnica

## Por que NÃO usar `UAZAPI_DEFAULT_INSTANCE_TOKEN`

| Abordagem errada | Abordagem FIT |
|------------------|---------------|
| Token fixo no `.env` | Token retornado em `/instance/create` → salvo no Supabase |
| 1 academia chumbada | N instâncias via `gym_whatsapp_instances` (até 3 por academia) |
| Dono não autonomia | Dono configura pelo agente ou futuro painel |

No `.env` do servidor ficam só:

- `UAZAPI_BASE_URL` — seu servidor (ex: `https://onnzetecnologia.uazapi.com`)
- `UAZAPI_ADMIN_TOKEN` — Admin Token do painel uazapiGO
- `WEBHOOK_SECRET` — parâmetro `?wh=` do webhook global
- `PUBLIC_API_URL` — URL do Render (ex: `https://fit-api.onrender.com`)

**Nenhum token de instância no .env.**

---

## Fluxo mini-onboarding (AgentOS / WhatsApp)

```
Dono: "Quero conectar meu WhatsApp"
        │
        ▼
academia_tem_whatsapp → 0 instâncias?
        │
        ▼
iniciar_conexao_whatsapp
   → POST /instance/create (admintoken)
   → adminField01 = gym_id
   → Salva id + token em gym_whatsapp_instances
   → Retorna paircode / instruções QR
        │
        ▼
Dono escaneia QR no celular
        │
        ▼
status_conexao_whatsapp → connected
        │
        ▼
Atendimento normal (horários, planos, reservas)
```

---

## Testar no AgentOS (agora, sem frontend)

```bash
cd backend
.venv\Scripts\activate
python run.py
```

Frases de teste:

1. `A academia já tem whatsapp configurado?`
2. `Quero conectar o whatsapp da recepção`
3. `Qual o status da conexão?`
4. `Quais horários de funcional amanhã?` (após conectado + seed)

Requer: `MISTRAL_API_KEY`, `SUPABASE_*`, `UAZAPI_ADMIN_TOKEN`.

---

## Deploy Render + webhook global

1. Deploy `backend/` no Render → URL `https://fit-xxx.onrender.com`
2. `PUBLIC_API_URL=https://fit-xxx.onrender.com` no Render env
3. Painel UAZAPI → Webhook Global:

```json
{
  "url": "https://fit-xxx.onrender.com/webhook/uazapi?wh=SEU_WEBHOOK_SECRET",
  "events": ["messages", "connection"],
  "excludeMessages": ["wasSentByApi", "isGroupYes"]
}
```

Ou via API: `POST /globalwebhook` com `admintoken` (script futuro / painel admin).

---

## Futuro painel TanStack

O dono fará o mesmo fluxo na UI:

- Botão "Conectar WhatsApp"
- Backend chama `iniciar_conexao_whatsapp` logic
- Exibe QR na tela
- Lista até 3 números

O agente e o painel **compartilham** `gym_whatsapp_instances` + Admin API.
