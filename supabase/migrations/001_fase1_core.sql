-- FIT Fase 1: core tables
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- gyms
CREATE TABLE gyms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  phone_whatsapp TEXT,
  uazapi_instance_id TEXT,
  uazapi_token TEXT,
  agent_config JSONB NOT NULL DEFAULT '{"assistant_name":"Ana","tone":"friendly"}'::jsonb,
  fields_map JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- members
CREATE TABLE members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  phone TEXT NOT NULL,
  wa_chatid TEXT,
  name TEXT,
  email TEXT,
  status TEXT NOT NULL DEFAULT 'lead' CHECK (status IN ('lead', 'ativo', 'inativo')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gym_id, phone)
);

-- plans
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  price_cents INT NOT NULL,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- class_slots
CREATE TABLE class_slots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  modality TEXT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ,
  capacity INT NOT NULL DEFAULT 20,
  booked_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (booked_count >= 0),
  CHECK (booked_count <= capacity)
);

-- bookings
CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  slot_id UUID NOT NULL REFERENCES class_slots(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX bookings_slot_member_active
  ON bookings (slot_id, member_id)
  WHERE status != 'cancelled';

-- messages
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  wa_chatid TEXT NOT NULL,
  member_id UUID REFERENCES members(id) ON DELETE SET NULL,
  direction TEXT NOT NULL CHECK (direction IN ('in', 'out')),
  body TEXT NOT NULL,
  raw JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- crm_contacts (mirror UAZAPI)
CREATE TABLE crm_contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  wa_chatid TEXT NOT NULL,
  member_id UUID REFERENCES members(id) ON DELETE SET NULL,
  lead_status TEXT NOT NULL DEFAULT 'novo',
  lead_tags TEXT[] NOT NULL DEFAULT '{}',
  lead_notes TEXT,
  lead_is_ticket_open BOOLEAN NOT NULL DEFAULT false,
  lead_kanban_order INT NOT NULL DEFAULT 0,
  field_01 TEXT, field_02 TEXT, field_03 TEXT, field_04 TEXT, field_05 TEXT,
  field_06 TEXT, field_07 TEXT, field_08 TEXT, field_09 TEXT, field_10 TEXT,
  field_11 TEXT, field_12 TEXT, field_13 TEXT, field_14 TEXT, field_15 TEXT,
  field_16 TEXT, field_17 TEXT, field_18 TEXT, field_19 TEXT, field_20 TEXT,
  synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (gym_id, wa_chatid)
);

-- indexes
CREATE INDEX idx_messages_gym_created ON messages (gym_id, created_at DESC);
CREATE INDEX idx_bookings_gym_slot ON bookings (gym_id, slot_id);
CREATE INDEX idx_members_gym_phone ON members (gym_id, phone);
CREATE INDEX idx_crm_gym_status ON crm_contacts (gym_id, lead_status);
CREATE INDEX idx_slots_gym_starts ON class_slots (gym_id, starts_at);

-- updated_at trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER gyms_updated_at BEFORE UPDATE ON gyms
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER members_updated_at BEFORE UPDATE ON members
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER crm_contacts_updated_at BEFORE UPDATE ON crm_contacts
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
