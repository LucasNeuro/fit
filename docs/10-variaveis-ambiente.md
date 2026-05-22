# 10 — Variáveis de ambiente

## Modelo UAZAPI (seu servidor)

```
┌─────────────────────────────────────────────────────────┐
│  Servidor UAZAPI (1 URL + 1 Admin Token)                │
│  ex: https://onnzetecnologia.uazapi.com                 │
│                                                         │
│  Webhook GLOBAL ──POST──► FIT /webhook/uazapi?wh=SECRET │
│                                                         │
│  Instância A (Academia 1 - número 1)  ──► gym_id 1      │
│  Instância B (Academia 1 - número 2)  ──► gym_id 1      │
│  Instância C (Academia 2 - número 1)  ──► gym_id 2      │
│  (até 3 números por academia)                           │
└─────────────────────────────────────────────────────────┘
```

O payload do webhook traz **`instance_id`** → Supabase tabela `gym_whatsapp_instances` → academia + token da instância.

---

## `backend/.env` — o que preencher

### Obrigatório para AgentOS + agente

| Variável | Exemplo / origem |
|----------|------------------|
| `MISTRAL_API_KEY` | console.mistral.ai |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Mesma tela (secret) |

### UAZAPI (servidor único)

| Variável | O que é |
|----------|---------|
| `UAZAPI_BASE_URL` | **Server URL** do painel (ex: `https://onnzetecnologia.uazapi.com`) |
| `UAZAPI_ADMIN_TOKEN` | **Admin Token** — criar instâncias (`/instance/create`) |
| `UAZAPI_SEND_TEXT_PATH` | Geralmente `/send/text` (confirmar na doc UAZAPI) |
| `PUBLIC_API_URL` | URL do Render/ngrok — montar webhook global |

**Não use** token de instância no `.env`. Tokens ficam em `gym_whatsapp_instances` (onboarding ou painel). Ver [11-onboarding-whatsapp.md](./11-onboarding-whatsapp.md).

### Webhook global

| Variável | O que é |
|----------|---------|
| `WEBHOOK_SECRET` | Mesmo valor do `?wh=` no painel **Webhook Global** |
| `WEBHOOK_VALIDATE_QUERY` | `true` em produção; `false` só para teste local rápido |

**URL no painel UAZAPI (dev com ngrok):**

```
https://SEU-NGROK.ngrok-free.app/webhook/uazapi?wh=SEU_WEBHOOK_SECRET
```

ou (compatível):

```
https://SEU-NGROK.ngrok-free.app/api/whatsapp/webhook?wh=SEU_WEBHOOK_SECRET
```

**Eventos no painel (como na sua captura):**

- Escutar: `messages` (e opcional `connection`)
- Excluir: `wasSentByApi`, `isGroupYes`

---

## Cadastrar instâncias

**Recomendado:** mini-onboarding no AgentOS (`iniciar_conexao_whatsapp`) ou painel futuro.

Alternativa manual: criar no UAZAPI + `INSERT` em `gym_whatsapp_instances` (máx. 3 por academia).

---

## Frontend (depois)

Só `frontend/.env` com `VITE_SUPABASE_ANON_KEY` — nunca Admin Token nem Mistral.

---

## Rodar local

```bash
# Terminal 1 — API + webhook
cd backend
.venv\Scripts\activate
uvicorn api.main:app --reload --port 8000

# Terminal 2 — ngrok
ngrok http 8000

# Terminal 3 — AgentOS (testar IA sem WhatsApp)
python run.py
```

AgentOS: http://127.0.0.1:7780 (não precisa UAZAPI).
