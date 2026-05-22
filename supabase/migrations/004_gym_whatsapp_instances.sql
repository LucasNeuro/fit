-- Até 3 números WhatsApp (instâncias UAZAPI) por academia no mesmo servidor
CREATE TABLE gym_whatsapp_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  uazapi_instance_id TEXT NOT NULL,
  uazapi_instance_token TEXT,
  label TEXT,
  phone_display TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT false,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (uazapi_instance_id)
);

CREATE INDEX idx_gym_wa_instances_gym ON gym_whatsapp_instances (gym_id);

-- Máximo 3 instâncias ativas por academia
CREATE OR REPLACE FUNCTION check_max_instances_per_gym()
RETURNS TRIGGER AS $$
BEGIN
  IF (
    SELECT COUNT(*) FROM gym_whatsapp_instances
    WHERE gym_id = NEW.gym_id AND active = true
  ) >= 3 THEN
    RAISE EXCEPTION 'Academia já possui 3 instâncias WhatsApp ativas';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_max_instances_per_gym
  BEFORE INSERT ON gym_whatsapp_instances
  FOR EACH ROW EXECUTE FUNCTION check_max_instances_per_gym();
