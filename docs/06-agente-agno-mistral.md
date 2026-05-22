# 06 — Agente Agno + Mistral

## Responsabilidade

O agente é a **recepcionista digital** da academia: entende mensagens em português, consulta dados reais via tools, responde no WhatsApp e mantém o CRM atualizado.

---

## Modelos Mistral

| Cenário | Model ID | Motivo |
|---------|----------|--------|
| Default (90% das msgs) | `mistral-small-latest` | Custo e latência |
| Vendas / objeções / recuperação | `mistral-large-latest` | Qualidade de persuasão |
| Extração estruturada | `mistral-small-latest` + `output_schema` | Pydantic para reservas |

### Setup Agno (padrão oficial FIT)

```python
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.mistral import MistralChat
from agno.tools import tool
from agno.run import RunContext

from agents.tools.fit_tools import FIT_TOOLS

agent = Agent(
    name="FIT Recepcionista",
    model=MistralChat(id="mistral-small-latest"),
    db=SqliteDb(db_file="backend/tmp/fit_agent.db"),
    session_id=f"{gym_id}:{wa_chatid}",
    user_id=member_id,
    session_state={"gym_id": gym_id, "member_id": member_id, "wa_chatid": wa_chatid},
    instructions=[...],  # prompts/recepcionista.md
    tools=FIT_TOOLS,     # funções com @tool + RunContext
    markdown=True,
    add_history_to_context=True,
    num_history_runs=5,
)

run = agent.run(user_message)
reply = run.content
```

**Implementação:** `backend/agents/runner.py` + `backend/agents/tools/fit_tools.py`

### Padrões Agno que seguimos

| Padrão | Onde no FIT |
|--------|-------------|
| `MistralChat` | `runner.py` |
| `@tool` + docstring | `fit_tools.py` |
| `RunContext` + `session_state` | tools leem `gym_id`, `member_id`, `wa_chatid` |
| `SqliteDb` + `add_history_to_context` | histórico por conversa WhatsApp |
| `session_id` | `{gym_id}:{wa_chatid}` |
| `instructions` | prompt em `recepcionista.md` |
| `agent.run()` → `.content` | `runner.py` |

**Histórico duplo (proposital):**

- **Agno `SqliteDb`** — contexto do LLM na conversa
- **Supabase `messages`** — painel do dono e auditoria

---

## Intents (Fase 1)

| Intent | Descrição | Tools típicas |
|--------|-----------|---------------|
| `AGENDAR_AULA` | Quer marcar horário | `listar_horarios`, `criar_reserva` |
| `CONSULTAR_HORARIOS` | Pergunta disponibilidade | `listar_horarios` |
| `CONSULTAR_PLANOS` | Preços e benefícios | `listar_planos` |
| `CONFIRMAR_PRESENCA` | Responde lembrete | `confirmar_booking` |
| `COBRANCA` | Dúvida sobre pagamento | `status_pagamento`, link externo |
| `FEEDBACK` | Avalia aula | `salvar_feedback` |
| `FALAR_HUMANO` | Quer atendente | `atualizar_lead` (ticket aberto) |
| `OUTRO` | Não classificado | Resposta genérica ou handoff |

Classificação: pode ser regra + keywords no MVP; Mistral Small para ambíguos.

---

## Tools (Fase 1 — obrigatórias)

### 1. `listar_horarios`

```
Input:  gym_id, modality (opcional), date (opcional, ISO)
Output: lista { slot_id, modality, starts_at, vagas }
Fonte:  class_slots WHERE booked_count < capacity
```

### 2. `criar_reserva`

```
Input:  gym_id, member_id, slot_id
Output: { booking_id, status, mensagem_confirmacao }
Regras: incrementar booked_count; falhar se lotado
Pós:    editLead status=experimental, tag agendou
```

### 3. `listar_planos`

```
Input:  gym_id
Output: lista { name, price_cents, description }
Fonte:  plans WHERE active = true
```

### 4. `buscar_ou_criar_membro`

```
Input:  gym_id, phone, wa_chatid, name (opcional)
Output: member_id
```

### 5. `atualizar_lead`

```
Input:  wa_chatid, payload (lead_status, tags, fields, ticket)
Output: success bool
Fonte:  UAZAPI POST /chat/editLead + sync crm_contacts
```

---

## System prompt (base)

Arquivo: `agents/prompts/recepcionista.md`

```markdown
Você é a recepcionista digital da academia {{gym_name}}.

Regras:
- Responda em português brasileiro, tom amigável e direto.
- NUNCA invente preços, horários ou políticas — use sempre as ferramentas.
- Se não houver vaga ou plano, diga claramente e ofereça alternativa.
- Uma pergunta de cada vez quando faltar informação.
- Se o cliente pedir humano, atendente ou reclamar gravemente: use atualizar_lead com ticket aberto.
- Não peça CPF ou dados sensíveis sem necessidade.
- Após agendar ou demonstrar interesse em plano, atualize o CRM com atualizar_lead.

Contexto da academia:
{{agent_config}}
```

---

## Structured output (reserva)

```python
from pydantic import BaseModel, Field

class ReservaRequest(BaseModel):
    slot_id: str = Field(..., description="UUID do horário")
    confirmar: bool = Field(..., description="Cliente confirmou?")
```

Usar em `criar_reserva` quando o modelo extrair intenção de confirmação.

---

## Fluxo completo por mensagem

```
1. Webhook recebe mensagem
2. buscar_ou_criar_membro()
3. Carregar últimas 5–10 messages do Supabase
4. Agent.run(user_message)
   ├── classificar intent (implícito no run)
   ├── chamar tools
   └── gerar resposta
5. Enviar texto via UAZAPI
6. Salvar message outbound
7. Se CRM mudou → atualizar_lead()
```

---

## Guardrails

| Regra | Implementação |
|-------|---------------|
| Sem alucinação de preço | Tool obrigatória para `CONSULTAR_PLANOS` |
| Sem alucinação de horário | Tool obrigatória para horários |
| Rate limit | Máx. 1 resposta por 2s por chat (debounce) |
| Grupos WhatsApp | Ignorar `wa_isGroup` se true no payload |
| Stop word | Respeitar `chatbot_stopConversation` da instância UAZAPI |

---

## Memória e contexto

| Tipo | Onde |
|------|------|
| Curto prazo | `num_history_runs` no Agno + `messages` Supabase |
| CRM | `crm_contacts` + campos UAZAPI |
| Longo prazo (futuro) | Agno Knowledge / embeddings — não no MVP |

---

## Testes manuais (aceite)

| # | Entrada | Esperado |
|---|---------|----------|
| 1 | "Quais horários de funcional amanhã?" | Lista real do banco |
| 2 | "Quero o das 18h" | Reserva confirmada + tag `agendou` |
| 3 | "Quanto custa o mensal?" | Preço exato do plano |
| 4 | "Quero falar com alguém" | Ticket aberto + msg empática |
| 5 | "Qual o preço do plano ouro?" (não existe) | "Não temos esse plano" + lista disponíveis |
