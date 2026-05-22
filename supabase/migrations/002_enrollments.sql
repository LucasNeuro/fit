-- FIT Fase 3: matrículas
CREATE TABLE enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
  starts_at DATE NOT NULL,
  ends_at DATE,
  status TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo', 'trancado', 'cancelado')),
  payment_status TEXT NOT NULL DEFAULT 'em_dia' CHECK (payment_status IN ('em_dia', 'inadimplente')),
  external_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_enrollments_gym_member ON enrollments (gym_id, member_id);

CREATE TRIGGER enrollments_updated_at BEFORE UPDATE ON enrollments
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
