# Deploy FIT no Render (passo a passo)

## 1. Subir código no GitHub

No PowerShell:

```powershell
cd C:\Users\anima\OneDrive\Desktop\fit
git init
git add .
git commit -m "FIT backend API + webhook UAZAPI"
```

Crie um repo vazio no GitHub (ex: `fit-academia`) e:

```powershell
git remote add origin https://github.com/SEU_USUARIO/fit-academia.git
git branch -M main
git push -u origin main
```

## 2. Criar serviço no Render

1. https://dashboard.render.com → **New +** → **Web Service**
2. Conecte o repositório GitHub
3. Configuração:

| Campo | Valor |
|-------|--------|
| Name | `fit-api` |
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

### Se falhar com `No module named 'api'`

1. **Repositório errado** — o log mostra `LucasNeuro/mkt`; use **`LucasNeuro/fit`**.
2. **Root Directory vazio** — preencha: `backend`.
3. **Python 3.14** — em Environment adicione `PYTHON_VERSION` = `3.12.8`.
4. Salve e faça **Manual Deploy**. Teste: `https://fitbot-k26i.onrender.com/health`.

Alternativa com raiz do repo (Root Directory vazio):

| Build | `pip install -r requirements.txt` |
| Start | `bash start.sh` |

4. **Environment** — adicione (valores do seu `backend/.env`):

```
MISTRAL_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
UAZAPI_BASE_URL=https://onnzetecnologia.uazapi.com
UAZAPI_ADMIN_TOKEN=...
WEBHOOK_SECRET=...          (mesmo do painel UAZAPI ?wh=)
WEBHOOK_VALIDATE_QUERY=true
PUBLIC_API_URL=https://fit-api.onrender.com   (troque pelo URL real após criar)
DEFAULT_GYM_ID=...          (UUID do seed — gym_id_para_env)
UAZAPI_SEND_TEXT_PATH=/send/text
ENV=production
```

**Não** use `SSL_VERIFY=false` no Render.

5. **Create Web Service** → aguarde deploy verde
6. Copie a URL: `https://fit-api-xxxx.onrender.com`
7. Atualize `PUBLIC_API_URL` no Render com essa URL exata → **Save** (redeploy se pedir)

## 3. Testar API

```
https://SEU-SERVICO.onrender.com/health
```

Deve retornar `{"status":"ok",...}`

## 4. Webhook global na UAZAPI

### Opção A — Painel uazapiGO

**Webhook Global:**

```
https://SEU-SERVICO.onrender.com/webhook/uazapi?wh=SEU_WEBHOOK_SECRET
```

- Eventos: `messages`, `connection`
- Excluir: `wasSentByApi`, `isGroupYes`

### Opção B — Script

```powershell
cd backend
.venv\Scripts\activate
python scripts/setup_global_webhook.py --url https://SEU-SERVICO.onrender.com
```

## 5. WhatsApp

Instância criada no painel UAZAPI + linha em `gym_whatsapp_instances` no Supabase (ver doc 13).

Envie mensagem no número conectado → Render processa → agente responde.
