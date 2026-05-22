# 05 — UAZAPI: WhatsApp e Mini CRM

## Visão

O UAZAPI é o **canal WhatsApp** e o **CRM operacional** por conversa. O FIT usa Supabase para dados de negócio e espelha o CRM no painel via `crm_contacts`.

---

## Endpoints principais

| Endpoint | Método | Uso no FIT |
|----------|--------|------------|
| Webhook (configurado no painel UAZAPI) | POST | Mensagens inbound → nossa API |
| Envio de mensagem | POST | Resposta do agente |
| `/instance/updateFieldsMap` | POST | Onboarding: labels dos 20 campos |
| `/chat/editLead` | POST | Atualizar lead após cada intent |

---

## Onboarding: `updateFieldsMap`

Executar **uma vez por instância** ao cadastrar academia:

```json
{
  "lead_field01": "tipo",
  "lead_field02": "plano_interesse",
  "lead_field03": "modalidade",
  "lead_field04": "ultima_aula",
  "lead_field05": "proxima_aula",
  "lead_field06": "origem",
  "lead_field07": "score",
  "lead_field08": "valor_estimado",
  "lead_field09": "vencimento",
  "lead_field10": "inadimplente",
  "lead_field11": "member_id",
  "lead_field12": "ultima_interacao",
  "lead_field13": "proximo_contato",
  "lead_field14": "objecao",
  "lead_field15": "experimental",
  "lead_field16": "gym_id",
  "lead_field17": "agente_versao",
  "lead_field18": "tags_resumo",
  "lead_field19": "resumo_ia",
  "lead_field20": "custom"
}
```

**Restrições UAZAPI:**

- Máximo **255 caracteres** por campo
- Apenas campos enviados são atualizados
- Campos vazios mantêm valor anterior

**Não usar** `lead_field19` para histórico completo — usar tabela `messages`.

---

## `editLead` — atualização por conversa

### Identificador obrigatório

```json
{
  "id": "5511999999999@s.whatsapp.net"
}
```

Aceita também `wa_fastid` conforme documentação UAZAPI.

### Campos nativos usados pelo FIT

| Campo | Uso |
|-------|-----|
| `lead_name` | Nome do lead/aluno |
| `lead_email` | Se informado pelo cliente |
| `lead_status` | Estágio no funil |
| `lead_tags` | Array de tags |
| `lead_notes` | Anotações livres |
| `lead_isTicketOpen` | Handoff humano |
| `lead_kanbanOrder` | Ordem no kanban do painel |
| `lead_assignedAttendant_id` | Atendente (fase 2) |
| `chatbot_disableUntil` | Pausar bot (timestamp UTC) |
| `lead_field01` … `lead_field20` | Campos customizados |

### Exemplo após agendamento

```json
{
  "id": "5511999999999@s.whatsapp.net",
  "lead_status": "experimental",
  "lead_tags": ["agendou", "funcional"],
  "lead_field03": "funcional",
  "lead_field05": "2026-05-23T18:00:00",
  "lead_field12": "2026-05-22T15:30:00Z",
  "lead_notes": "Aula experimental agendada sábado 18h"
}
```

---

## Funil `lead_status`

```
novo → contato → qualificado → experimental → proposta → matriculado → inadimplente → perdido
```

| Status | Quando definir |
|--------|----------------|
| `novo` | Primeira mensagem |
| `contato` | Agente respondeu |
| `qualificado` | Perguntou plano/preço |
| `experimental` | Agendou aula teste |
| `proposta` | Demonstrou intenção de fechar |
| `matriculado` | Enrollment ativo no Supabase |
| `inadimplente` | payment_status inadimplente |
| `perdido` | Sem resposta 30d ou desistiu |

---

## Tags automáticas

| Tag | Trigger |
|-----|---------|
| `agendou` | Booking confirmado |
| `plano-mensal` | Interesse em plano mensal |
| `cobranca` | Lembrete/cobrança enviada |
| `humano` | Handoff |
| `funcional` | Modalidade funcional |
| `vip` | Manual no painel |
| `reativar` | Ex-aluno retornou |

Tags inexistentes são **criadas automaticamente** pelo UAZAPI.

---

## Webhook inbound (estrutura esperada)

A API deve:

1. Validar origem (token/secret se disponível)
2. Extrair: `wa_chatid`, texto, tipo mídia, instance id
3. Mapear instance → `gym_id`
4. Retornar 200 rápido; processar agente async se necessário

> Documentar payload real da instância no primeiro teste em `backend/api/routes/webhook.py`.

---

## Sincronização com Supabase

Após cada `editLead` bem-sucedido:

1. Upsert em `crm_contacts` pelos mesmos campos
2. Atualizar `synced_at = now()`
3. Webhook UAZAPI de alteração de lead (se configurado) → mesma lógica

---

## Erros comuns

| HTTP | Causa | Ação |
|------|-------|------|
| 400 | Payload inválido | Log + não retentar |
| 401 | Token expirado | Alertar dono no painel |
| 404 | Instância/chat não existe | Criar member + retry |
| 500 | UAZAPI indisponível | Fila retry + mensagem fallback |
