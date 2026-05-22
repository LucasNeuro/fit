# 13 — Deploy Render + webhook global UAZAPI

Foco atual: **API em produção** + **webhook global**. WhatsApp conecta pelo **painel** (próxima fase), não pelo chat do agente.

---

## 1. Deploy no Render

1. Push do repo `fit` no GitHub.
2. [Render](https://render.com) → **New → Web Service** → conecte o repo.
3. Configuração:

| Campo | Valor |
|-------|--------|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/health` |

4. **Environment** (copie de `backend/.env`, sem `SSL_VERIFY=false`):

| Variável | Exemplo |
|----------|---------|
| `MISTRAL_API_KEY` | sua chave |
| `SUPABASE_URL` | URL Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | service role |
| `UAZAPI_BASE_URL` | `https://onnzetecnologia.uazapi.com` |
| `UAZAPI_ADMIN_TOKEN` | Admin Token painel |
| `WEBHOOK_SECRET` | token longo (mesmo do `?wh=`) |
| `WEBHOOK_VALIDATE_QUERY` | `true` |
| `PUBLIC_API_URL` | `https://SEU-SERVICO.onrender.com` |
| `DEFAULT_GYM_ID` | UUID da academia (seed) |
| `UAZAPI_SEND_TEXT_PATH` | `/send/text` |
| `ENV` | `production` |

5. Deploy → anote a URL: `https://fit-api-xxxx.onrender.com`

6. Teste: `https://SEU-SERVICO.onrender.com/health` → `{"status":"ok"}`

---

## 2. Webhook global na UAZAPI

No painel **uazapiGO** → **Webhook Global**:

```
URL: https://SEU-SERVICO.onrender.com/webhook/uazapi?wh=SEU_WEBHOOK_SECRET
```

**Eventos:** `messages`, `connection`  
**Excluir:** `wasSentByApi`, `isGroupYes`

Ou via script (com `PUBLIC_API_URL` no `.env` local apontando para Render):

```bash
cd backend
.venv\Scripts\activate
python scripts/setup_global_webhook.py
```

---

## 3. Instância WhatsApp (painel — não no agente)

Por enquanto, no painel UAZAPI ou SQL:

1. Crie instância no UAZAPI (`/instance/create` com `adminField01` = `gym_id`).
2. Insira em `gym_whatsapp_instances` (ou aguarde painel TanStack).

O agente **não** guia mais onboarding no chat.

---

## 4. Testar WhatsApp real

1. Número conectado na UAZAPI.
2. Instância mapeada no Supabase.
3. Mensagem no WhatsApp → Render recebe webhook → agente responde.

---

## 5. AgentOS (dev local — opcional)

```bash
cd backend
.venv\Scripts\activate
python run.py
```

`http://127.0.0.1:7780` — só para testar IA no chat, sem falar de QR/WhatsApp.

---

## Roadmap

| Agora | Depois |
|-------|--------|
| Render + webhook | Painel TanStack (conectar WA, playbook) |
| Agente atendimento | Melhorar prompts e tools |
