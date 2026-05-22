-- Academia piloto FIT (dev)
-- id da academia = UUID automático (DEFAULT gen_random_uuid() na tabela gyms)

INSERT INTO gyms (
  name,
  slug,
  phone_whatsapp,
  agent_config
) VALUES (
  'Academia Piloto FIT',
  'piloto',
  '5511999999999',
  '{"assistant_name":"Ana","tone":"friendly","greeting":"Olá! Sou a Ana da Academia Piloto FIT. Posso ajudar com horários, planos ou agendamento."}'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  phone_whatsapp = EXCLUDED.phone_whatsapp,
  agent_config = EXCLUDED.agent_config;

-- Planos (gym_id vem da tabela — tipo uuid correto)
INSERT INTO plans (gym_id, name, price_cents, description, active)
SELECT g.id, v.name, v.price_cents, v.description, true
FROM gyms g
CROSS JOIN (VALUES
  ('Mensal', 12000, 'Acesso ilimitado + 1 avaliação física'),
  ('Trimestral', 30000, '3 meses com 10% de desconto')
) AS v(name, price_cents, description)
WHERE g.slug = 'piloto'
  AND NOT EXISTS (
    SELECT 1 FROM plans p
    WHERE p.gym_id = g.id AND p.name = v.name
  );

-- Horários funcional: próximos 5 dias 18h e 19h30
INSERT INTO class_slots (gym_id, modality, starts_at, ends_at, capacity, booked_count)
SELECT
  g.id,
  'funcional',
  (CURRENT_DATE + d) + TIME '18:00',
  (CURRENT_DATE + d) + TIME '19:00',
  15,
  0
FROM gyms g
CROSS JOIN generate_series(1, 5) AS d
WHERE g.slug = 'piloto'
UNION ALL
SELECT
  g.id,
  'funcional',
  (CURRENT_DATE + d) + TIME '19:30',
  (CURRENT_DATE + d) + TIME '20:30',
  15,
  0
FROM gyms g
CROSS JOIN generate_series(1, 5) AS d
WHERE g.slug = 'piloto';

-- Copie gym_id_para_env para backend/.env → DEFAULT_GYM_ID=
SELECT id AS gym_id_para_env, name, slug
FROM gyms
WHERE slug = 'piloto';

-- WhatsApp: use onboarding no agente (iniciar_conexao_whatsapp), não precisa seed aqui.
