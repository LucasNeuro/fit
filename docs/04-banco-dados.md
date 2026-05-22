# 04 — Banco de dados (Supabase)

## Convenções

- IDs: `uuid` com `gen_random_uuid()`
- Timestamps: `timestamptz` com `now()` default
- Dinheiro: `price_cents` (inteiro)
- Telefone: string E.164 sem espaços (ex: `5511999999999`)
- Todas as tabelas de negócio têm `gym_id` + RLS

---

## Fase 1 — MVP (agente + agendamento)

### `gyms`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| name | text | Nome da academia |
| slug | text unique | URL amigável |
| phone_whatsapp | text | Número exibido |
| uazapi_instance_id | text | ID instância UAZAPI |
| uazapi_token | text | Token (criptografar em prod) |
| agent_config | jsonb | `{ "assistant_name": "...", "tone": "friendly" }` |
| fields_map | jsonb | Cache do fieldsMap UAZAPI |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `members`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK → gyms | |
| phone | text | Unique por gym |
| wa_chatid | text | ID WhatsApp |
| name | text | |
| email | text nullable | |
| status | text | `lead` \| `ativo` \| `inativo` |
| created_at | timestamptz | |
| updated_at | timestamptz | |

**Unique:** `(gym_id, phone)`

### `plans`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| name | text | Ex: "Mensal" |
| price_cents | int | Ex: 12000 = R$ 120 |
| description | text | |
| active | boolean | default true |

### `class_slots`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| modality | text | Ex: funcional, musculação |
| starts_at | timestamptz | |
| ends_at | timestamptz nullable | |
| capacity | int | default 20 |
| booked_count | int | default 0 |

### `bookings`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| member_id | uuid FK → members | |
| slot_id | uuid FK → class_slots | |
| status | text | `pending` \| `confirmed` \| `cancelled` |
| created_at | timestamptz | |

**Unique sugerido:** `(slot_id, member_id)` onde status != cancelled

### `messages`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| wa_chatid | text | |
| member_id | uuid FK nullable | |
| direction | text | `in` \| `out` |
| body | text | |
| raw | jsonb | Payload UAZAPI |
| created_at | timestamptz | |

### `crm_contacts` (espelho UAZAPI)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| wa_chatid | text unique per gym | |
| member_id | uuid FK nullable | |
| lead_status | text | Funil (ver doc 05) |
| lead_tags | text[] | |
| lead_notes | text | |
| lead_is_ticket_open | boolean | |
| lead_kanban_order | int | |
| field_01 … field_20 | text | Espelho lead_field01–20 |
| synced_at | timestamptz | |

---

## Fase 2 — Matrículas

### `enrollments`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| member_id | uuid FK | |
| plan_id | uuid FK → plans | |
| starts_at | date | |
| ends_at | date nullable | |
| status | text | `ativo` \| `trancado` \| `cancelado` |
| payment_status | text | `em_dia` \| `inadimplente` |
| external_id | text nullable | BioGym etc. |

---

## Fase 3 — Presença QR

### `qr_tokens`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| member_id | uuid FK | |
| token_hash | text | Hash do payload assinado |
| booking_id | uuid FK nullable | |
| expires_at | timestamptz | |
| used_at | timestamptz nullable | |
| created_at | timestamptz | |

### `attendance`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | uuid PK | |
| gym_id | uuid FK | |
| member_id | uuid FK | |
| check_in_at | timestamptz | |
| check_out_at | timestamptz nullable | |
| source | text | `qr` \| `manual` |
| qr_token_id | uuid FK nullable | |

---

## RLS (Row Level Security)

```sql
-- Exemplo: members
ALTER TABLE members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "members_gym_isolation" ON members
  FOR ALL
  USING (gym_id = (auth.jwt() ->> 'gym_id')::uuid);
```

| Contexto | Credencial |
|----------|------------|
| Painel TanStack Start (`frontend/`) | JWT do dono com claim `gym_id` |
| API / Agente | `SUPABASE_SERVICE_ROLE_KEY` (servidor apenas) |

---

## Índices recomendados

```sql
CREATE INDEX idx_messages_gym_created ON messages (gym_id, created_at DESC);
CREATE INDEX idx_bookings_gym_slot ON bookings (gym_id, slot_id);
CREATE INDEX idx_members_gym_phone ON members (gym_id, phone);
CREATE INDEX idx_crm_gym_status ON crm_contacts (gym_id, lead_status);
CREATE INDEX idx_slots_gym_starts ON class_slots (gym_id, starts_at);
CREATE INDEX idx_attendance_gym_checkin ON attendance (gym_id, check_in_at DESC);
```

---

## Seed (academia piloto)

Para desenvolvimento, inserir:

- 1 `gym` de teste
- 2 `plans` (Mensal R$ 120, Trimestral R$ 300)
- 5 `class_slots` (funcional próximos 7 dias)
- Opcional: 1 `member` de teste com seu telefone

Arquivo sugerido: `supabase/seed.sql`
