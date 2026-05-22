-- FIT Fase 4: presença QR
CREATE TABLE qr_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_qr_tokens_hash ON qr_tokens (token_hash);

CREATE TABLE attendance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  gym_id UUID NOT NULL REFERENCES gyms(id) ON DELETE CASCADE,
  member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  check_in_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  check_out_at TIMESTAMPTZ,
  source TEXT NOT NULL DEFAULT 'qr' CHECK (source IN ('qr', 'manual')),
  qr_token_id UUID REFERENCES qr_tokens(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attendance_gym_checkin ON attendance (gym_id, check_in_at DESC);
