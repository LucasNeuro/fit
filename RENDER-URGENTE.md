# ⚠️ RENDER — LEIA ANTES DO DEPLOY

## Problema atual (100% configuração)

Se o log mostra:

```
Cloning from https://github.com/LucasNeuro/mkt
commit afcd0f5 ... group management
ModuleNotFoundError: No module named 'api'
```

**Você NÃO está deployando o FIT.** O serviço FitBot aponta para o repo **mkt** (bot antigo).

---

## Correção (5 minutos)

### 1. Trocar repositório no Render

Dashboard → **FitBot** → **Settings** → **Repository**

| Campo | Valor CORRETO |
|-------|----------------|
| Repository | **LucasNeuro/fit** |
| Branch | **main** |

Salvar.

### 2. Build & Deploy

| Campo | Valor |
|-------|--------|
| Root Directory | *(vazio)* |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/health` |

**Alternativa** (Root Directory = `backend`):

| Build | `pip install -r requirements.txt` |
| Start | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |

### 3. Python

Environment → `PYTHON_VERSION` = **3.12.8**

### 4. Variáveis (Environment)

```
MISTRAL_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
UAZAPI_BASE_URL=https://onnzetecnologia.uazapi.com
UAZAPI_ADMIN_TOKEN=...
WEBHOOK_SECRET=...
WEBHOOK_VALIDATE_QUERY=true
PUBLIC_API_URL=https://fitbot-k26i.onrender.com
UAZAPI_SEND_TEXT_PATH=/send/text
ENV=production
PYTHON_VERSION=3.12.8
```

Opcional SQL agent: `SUPABASE_DB_URL=postgresql+psycopg://...`

### 5. Manual Deploy

Deploy latest commit. O log **deve** mostrar:

```
Cloning from https://github.com/LucasNeuro/fit
commit 57cd1e8 (ou mais novo)
```

### 6. Testar

https://fitbot-k26i.onrender.com/health → `{"status":"ok",...}`

---

## Como saber que está certo

| Errado (mkt) | Certo (fit) |
|--------------|-------------|
| `LucasNeuro/mkt` | `LucasNeuro/fit` |
| commit `afcd0f5` | commit recente do fit |
| requirements: fastapi linha 1 | instala agno, mistral, psycopg |
| No module named 'api' | Server started |

---

## Opção: criar serviço novo

Se não conseguir trocar o repo:

1. **New Web Service** → repo **LucasNeuro/fit**
2. Use a tabela acima
3. Apague o FitBot antigo (mkt)
