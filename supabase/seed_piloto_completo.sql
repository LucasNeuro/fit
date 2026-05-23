-- =============================================================================
-- FIT — Seed completo academia de teste (slug: piloto)
-- Execute no Supabase SQL Editor APÓS migrations 001–004.
-- Idempotente: pode rodar mais de uma vez.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Academia + agente (Ana)
-- -----------------------------------------------------------------------------
INSERT INTO gyms (
  name,
  slug,
  phone_whatsapp,
  agent_config,
  fields_map
) VALUES (
  'Academia Piloto FIT',
  'piloto',
  '5511999887766',
  '{
    "assistant_name": "Ana",
    "tone": "friendly",
    "language": "pt-BR",
    "greeting": "Olá! Sou a Ana da Academia Piloto FIT. Posso ajudar com horários, planos ou agendar sua aula experimental.",
    "business_hours": "Seg–Sex 6h–22h | Sáb 8h–14h",
    "address": "Av. Paulista, 1000 — São Paulo, SP",
    "policies": {
      "cancelamento_aula": "Até 2h antes da aula",
      "experimental": "1 aula grátis para novos leads"
    }
  }'::jsonb,
  '{
    "lead_field01": "Objetivo",
    "lead_field02": "Modalidade interesse",
    "lead_field03": "Última aula agendada",
    "lead_field05": "Data experimental"
  }'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  phone_whatsapp = EXCLUDED.phone_whatsapp,
  agent_config = EXCLUDED.agent_config,
  fields_map = EXCLUDED.fields_map,
  updated_at = now();

-- -----------------------------------------------------------------------------
-- 2. Planos e preços
-- -----------------------------------------------------------------------------
INSERT INTO plans (gym_id, name, price_cents, description, active)
SELECT g.id, v.name, v.price_cents, v.description, true
FROM gyms g
CROSS JOIN (VALUES
  ('Day Use', 3500, '1 dia de acesso — musculação + cardio'),
  ('Mensal', 12990, 'Acesso ilimitado + 1 avaliação física'),
  ('Trimestral', 32990, '3 meses — economia de 15%'),
  ('Semestral', 59990, '6 meses — economia de 23%'),
  ('Anual', 99990, '12 meses — melhor custo-benefício'),
  ('Família (2 pessoas)', 19990, 'Mensal para 2 integrantes do mesmo núcleo'),
  ('Funcional 8x/mês', 8990, 'Pacote 8 aulas de funcional no mês'),
  ('Personal 4 sessões', 44990, '4 sessões com personal trainer')
) AS v(name, price_cents, description)
WHERE g.slug = 'piloto'
  AND NOT EXISTS (
    SELECT 1 FROM plans p WHERE p.gym_id = g.id AND p.name = v.name
  );

-- Desativa plano antigo "Trimestral" duplicado se existir só com preço antigo (opcional)
-- UPDATE plans SET active = false WHERE gym_id = (SELECT id FROM gyms WHERE slug='piloto') AND name = 'Trimestral' AND price_cents = 30000;

-- -----------------------------------------------------------------------------
-- 3. Horários (próximos 14 dias) — recria slots futuros da piloto
-- -----------------------------------------------------------------------------
DELETE FROM bookings b
USING gyms g, class_slots cs
WHERE g.slug = 'piloto'
  AND b.gym_id = g.id
  AND b.slot_id = cs.id
  AND cs.gym_id = g.id
  AND cs.starts_at >= (CURRENT_DATE AT TIME ZONE 'America/Sao_Paulo');

DELETE FROM class_slots cs
USING gyms g
WHERE g.slug = 'piloto'
  AND cs.gym_id = g.id
  AND cs.starts_at >= (CURRENT_DATE AT TIME ZONE 'America/Sao_Paulo');

INSERT INTO class_slots (gym_id, modality, starts_at, ends_at, capacity, booked_count)
SELECT g.id, v.modality,
  ((CURRENT_DATE + d) AT TIME ZONE 'America/Sao_Paulo') + v.t_start,
  ((CURRENT_DATE + d) AT TIME ZONE 'America/Sao_Paulo') + v.t_end,
  v.cap, 0
FROM gyms g
CROSS JOIN generate_series(0, 13) AS d
CROSS JOIN (VALUES
  ('funcional',     TIME '06:30', TIME '07:30', 12),
  ('funcional',     TIME '12:00', TIME '13:00', 15),
  ('funcional',     TIME '18:00', TIME '19:00', 15),
  ('funcional',     TIME '19:30', TIME '20:30', 15),
  ('musculação',    TIME '07:00', TIME '08:00', 25),
  ('musculação',    TIME '17:00', TIME '18:00', 25),
  ('yoga',          TIME '08:00', TIME '09:00', 10),
  ('yoga',          TIME '19:00', TIME '20:00', 10),
  ('pilates',       TIME '09:00', TIME '10:00', 8),
  ('pilates',       TIME '18:30', TIME '19:30', 8),
  ('spinning',      TIME '06:00', TIME '06:45', 20),
  ('spinning',      TIME '20:00', TIME '20:45', 20),
  ('crossfit',      TIME '07:30', TIME '08:30', 12),
  ('crossfit',      TIME '18:00', TIME '19:00', 12)
) AS v(modality, t_start, t_end, cap)
WHERE g.slug = 'piloto';

-- -----------------------------------------------------------------------------
-- 4. Alunos fictícios (leads, ativos, inativo)
-- -----------------------------------------------------------------------------
INSERT INTO members (gym_id, phone, wa_chatid, name, email, status)
SELECT g.id, v.phone, v.wa_chatid, v.name, v.email, v.status
FROM gyms g
CROSS JOIN (VALUES
  ('5511911111111', '5511911111111@s.whatsapp.net', 'João Silva',     'joao.silva@email.test',    'lead'),
  ('5511922222222', '5511922222222@s.whatsapp.net', 'Maria Santos',   'maria.santos@email.test',  'lead'),
  ('5511933333333', '5511933333333@s.whatsapp.net', 'Pedro Costa',    'pedro.costa@email.test',   'ativo'),
  ('5511944444444', '5511944444444@s.whatsapp.net', 'Ana Oliveira',   'ana.oliveira@email.test',  'ativo'),
  ('5511955555555', '5511955555555@s.whatsapp.net', 'Carlos Souza',   'carlos.souza@email.test',  'inativo'),
  ('5511966666666', '5511966666666@s.whatsapp.net', 'Fernanda Lima',  'fernanda.lima@email.test', 'lead'),
  ('5511977777777', '5511977777777@s.whatsapp.net', 'Ricardo Mendes', 'ricardo.mendes@email.test','ativo'),
  ('5511988888888', '5511988888888@s.whatsapp.net', 'Juliana Rocha',  'juliana.rocha@email.test', 'lead')
) AS v(phone, wa_chatid, name, email, status)
WHERE g.slug = 'piloto'
ON CONFLICT (gym_id, phone) DO UPDATE SET
  wa_chatid = EXCLUDED.wa_chatid,
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  status = EXCLUDED.status,
  updated_at = now();

-- -----------------------------------------------------------------------------
-- 5. CRM (status do funil)
-- -----------------------------------------------------------------------------
INSERT INTO crm_contacts (
  gym_id, wa_chatid, member_id, lead_status, lead_tags, lead_notes, lead_is_ticket_open
)
SELECT g.id, m.wa_chatid, m.id, v.lead_status, v.lead_tags, v.lead_notes, v.ticket
FROM gyms g
JOIN members m ON m.gym_id = g.id
JOIN (VALUES
  ('5511911111111@s.whatsapp.net', 'novo',        ARRAY['site','musculação'], 'Veio pelo Instagram', false),
  ('5511922222222@s.whatsapp.net', 'contato',     ARRAY['whatsapp'], 'Pediu tabela de preços', false),
  ('5511933333333@s.whatsapp.net', 'matriculado', ARRAY['mensal','vip'], 'Aluno desde jan/2025', false),
  ('5511944444444@s.whatsapp.net', 'matriculado', ARRAY['trimestral'], NULL, false),
  ('5511955555555@s.whatsapp.net', 'inativo',     ARRAY['cancelou'], 'Cancelou em mar/2025', false),
  ('5511966666666@s.whatsapp.net', 'qualificado', ARRAY['funcional','experimental'], 'Quer aula experimental sábado', false),
  ('5511977777777@s.whatsapp.net', 'matriculado', ARRAY['anual'], NULL, false),
  ('5511988888888@s.whatsapp.net', 'experimental', ARRAY['agendou','yoga'], 'Aula experimental agendada', false)
) AS v(wa_chatid, lead_status, lead_tags, lead_notes, ticket)
  ON m.wa_chatid = v.wa_chatid
WHERE g.slug = 'piloto'
ON CONFLICT (gym_id, wa_chatid) DO UPDATE SET
  member_id = EXCLUDED.member_id,
  lead_status = EXCLUDED.lead_status,
  lead_tags = EXCLUDED.lead_tags,
  lead_notes = EXCLUDED.lead_notes,
  lead_is_ticket_open = EXCLUDED.lead_is_ticket_open,
  updated_at = now();

-- -----------------------------------------------------------------------------
-- 6. Matrículas (enrollments) — alunos ativos
-- -----------------------------------------------------------------------------
INSERT INTO enrollments (gym_id, member_id, plan_id, starts_at, ends_at, status, payment_status)
SELECT g.id, m.id, p.id, v.starts_at::date, v.ends_at::date, 'ativo', v.payment
FROM gyms g
CROSS JOIN (VALUES
  ('5511933333333', 'Mensal',     '2025-01-01'::text, NULL::text,         'em_dia'),
  ('5511944444444', 'Trimestral', '2025-02-01'::text, '2025-05-01'::text, 'em_dia'),
  ('5511977777777', 'Anual',      '2024-06-01'::text, '2025-06-01'::text, 'em_dia')
) AS v(phone, plan_name, starts_at, ends_at, payment)
JOIN members m ON m.gym_id = g.id AND m.phone = v.phone
JOIN plans p ON p.gym_id = g.id AND p.name = v.plan_name
WHERE g.slug = 'piloto'
  AND NOT EXISTS (
    SELECT 1 FROM enrollments e
    WHERE e.gym_id = g.id AND e.member_id = m.id AND e.plan_id = p.id AND e.status = 'ativo'
  );

-- -----------------------------------------------------------------------------
-- 7. Reservas (algumas aulas já ocupadas)
-- -----------------------------------------------------------------------------
WITH gym AS (SELECT id AS gym_id FROM gyms WHERE slug = 'piloto'),
slot_pick AS (
  SELECT cs.id AS slot_id, cs.modality, cs.starts_at
  FROM class_slots cs
  JOIN gym ON cs.gym_id = gym.gym_id
  WHERE cs.modality = 'funcional'
    AND cs.starts_at::date = CURRENT_DATE + 1
    AND cs.starts_at::time = TIME '18:00'
  LIMIT 1
),
mem AS (
  SELECT m.id AS member_id, m.phone
  FROM members m
  JOIN gym ON m.gym_id = gym.gym_id
  WHERE m.phone IN ('5511911111111', '5511966666666')
)
INSERT INTO bookings (gym_id, member_id, slot_id, status)
SELECT gym.gym_id, mem.member_id, slot_pick.slot_id, 'confirmed'
FROM gym, slot_pick, mem
WHERE NOT EXISTS (
  SELECT 1 FROM bookings b
  WHERE b.slot_id = slot_pick.slot_id AND b.member_id = mem.member_id AND b.status != 'cancelled'
);

UPDATE class_slots cs SET booked_count = sub.cnt
FROM (
  SELECT b.slot_id, COUNT(*)::int AS cnt
  FROM bookings b
  JOIN gyms g ON b.gym_id = g.id AND g.slug = 'piloto'
  WHERE b.status = 'confirmed'
  GROUP BY b.slot_id
) sub
WHERE cs.id = sub.slot_id;

-- Yoga amanhã 19h — Fernanda
WITH gym AS (SELECT id AS gym_id FROM gyms WHERE slug = 'piloto'),
slot_y AS (
  SELECT cs.id AS slot_id
  FROM class_slots cs
  JOIN gym ON cs.gym_id = gym.gym_id
  WHERE cs.modality = 'yoga'
    AND cs.starts_at::date = CURRENT_DATE + 2
    AND cs.starts_at::time = TIME '19:00'
  LIMIT 1
),
mem_f AS (
  SELECT m.id AS member_id
  FROM members m
  JOIN gym ON m.gym_id = gym.gym_id
  WHERE m.phone = '5511966666666'
)
INSERT INTO bookings (gym_id, member_id, slot_id, status)
SELECT gym.gym_id, mem_f.member_id, slot_y.slot_id, 'confirmed'
FROM gym, slot_y, mem_f
WHERE NOT EXISTS (
  SELECT 1 FROM bookings b
  WHERE b.slot_id = slot_y.slot_id AND b.member_id = mem_f.member_id AND b.status != 'cancelled'
);

UPDATE class_slots cs SET booked_count = (
  SELECT COUNT(*) FROM bookings b WHERE b.slot_id = cs.id AND b.status = 'confirmed'
)
WHERE cs.gym_id = (SELECT id FROM gyms WHERE slug = 'piloto')
  AND cs.id IN (SELECT slot_id FROM bookings WHERE gym_id = cs.gym_id);

-- -----------------------------------------------------------------------------
-- 8. Histórico de mensagens (demo)
-- -----------------------------------------------------------------------------
INSERT INTO messages (gym_id, wa_chatid, member_id, direction, body)
SELECT g.id, m.wa_chatid, m.id, v.dir, v.body
FROM gyms g
JOIN members m ON m.gym_id = g.id AND m.phone = '5511911111111'
CROSS JOIN (VALUES
  ('in',  'Oi, quero saber os planos'),
  ('out', 'Olá João! Temos Mensal R$ 129,90, Trimestral e mais. Quer ver horários de funcional?'),
  ('in',  'Sim, amanhã à noite'),
  ('out', 'Perfeito! Posso reservar uma vaga para você.')
) AS v(dir, body)
WHERE g.slug = 'piloto'
  AND NOT EXISTS (
    SELECT 1 FROM messages msg
    WHERE msg.gym_id = g.id AND msg.wa_chatid = m.wa_chatid AND msg.body = v.body
  );

-- -----------------------------------------------------------------------------
-- 9. Presença (amostra)
-- -----------------------------------------------------------------------------
INSERT INTO attendance (gym_id, member_id, check_in_at, check_out_at, source)
SELECT g.id, m.id, now() - interval '2 days', now() - interval '2 days' + interval '1 hour', 'manual'
FROM gyms g
JOIN members m ON m.gym_id = g.id AND m.phone = '5511933333333'
WHERE g.slug = 'piloto'
  AND NOT EXISTS (
    SELECT 1 FROM attendance a
    WHERE a.gym_id = g.id AND a.member_id = m.id
      AND a.check_in_at::date = (now() - interval '2 days')::date
  );

-- -----------------------------------------------------------------------------
-- WhatsApp: cadastre no painel → gym_whatsapp_instances (não no agente)
-- -----------------------------------------------------------------------------

-- gym_id vem do webhook (instância WhatsApp) ou tools do agente — não use .env
SELECT
  g.id AS gym_id_para_env,
  g.name,
  g.slug,
  (SELECT COUNT(*) FROM plans p WHERE p.gym_id = g.id AND p.active) AS planos,
  (SELECT COUNT(*) FROM class_slots cs WHERE cs.gym_id = g.id AND cs.starts_at >= now()) AS horarios_futuros,
  (SELECT COUNT(*) FROM members m WHERE m.gym_id = g.id) AS membros,
  (SELECT COUNT(*) FROM crm_contacts c WHERE c.gym_id = g.id) AS crm,
  (SELECT COUNT(*) FROM bookings b WHERE b.gym_id = g.id AND b.status = 'confirmed') AS reservas
FROM gyms g
WHERE g.slug = 'piloto';
