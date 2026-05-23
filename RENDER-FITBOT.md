# Render — checklist FitBot (fitbot-k26i)

## Problema atual

O log mostra commit **`afcd0f5`** (repo **mkt**, bot de grupos).  
O FIT está em **`LucasNeuro/fit`**, branch **`main`**.

Enquanto o Render apontar para **mkt**, vai falhar com `No module named 'api'`.

---

## Passo 1 — Conectar o repo certo

1. https://dashboard.render.com → serviço **fitbot-k26i**
2. **Settings** → **Build & Deploy**
3. **Repository** → **Edit** → escolha **`LucasNeuro/fit`** (não mkt)
4. **Branch:** `main`

---

## Passo 2 — Comandos (copie exatamente)

| Campo | Valor |
|-------|--------|
| **Root Directory** | *(deixe vazio)* |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |

> `app.py` na raiz do repo importa `backend/api/main.py` — funciona sem Root Directory.

**Python:** Environment → `PYTHON_VERSION` = `3.12.8`

---

## Passo 3 — Variáveis de ambiente

```
MISTRAL_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
UAZAPI_BASE_URL=https://onnzetecnologia.uazapi.com
UAZAPI_ADMIN_TOKEN=...
WEBHOOK_SECRET=...
WEBHOOK_VALIDATE_QUERY=true
PUBLIC_API_URL=https://fitbot-k26i.onrender.com
DEFAULT_GYM_SLUG=piloto
UAZAPI_SEND_TEXT_PATH=/send/text
ENV=production
```

Sem `SSL_VERIFY=false`.

---

## Passo 4 — Deploy

1. **Save Changes**
2. **Manual Deploy** → Deploy latest commit
3. Confirme que o commit é do **fit** (ex. `2858b8e` ou mais novo), **não** `afcd0f5`
4. Teste: https://fitbot-k26i.onrender.com/health

---

## Se ainda falhar

Logs devem mostrar `Started server process` — não `No module named 'api'`.

Alternativa Start Command:

```bash
bash start.sh
```

Build:

```bash
pip install -r backend/requirements.txt
```

Root Directory: `backend`  
Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
