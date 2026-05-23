-- Mantém class_slots.booked_count sincronizado com bookings confirmados
-- Evita overbooking quando booked_count fica desatualizado

CREATE OR REPLACE FUNCTION sync_class_slot_booked_count(p_slot_id uuid)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE class_slots cs
  SET booked_count = (
    SELECT COUNT(*)::int
    FROM bookings b
    WHERE b.slot_id = p_slot_id
      AND b.status <> 'cancelled'
  )
  WHERE cs.id = p_slot_id;
END;
$$;

CREATE OR REPLACE FUNCTION trg_bookings_sync_slot_count()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    PERFORM sync_class_slot_booked_count(NEW.slot_id);
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    IF OLD.slot_id IS DISTINCT FROM NEW.slot_id THEN
      PERFORM sync_class_slot_booked_count(OLD.slot_id);
    END IF;
    PERFORM sync_class_slot_booked_count(NEW.slot_id);
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    PERFORM sync_class_slot_booked_count(OLD.slot_id);
    RETURN OLD;
  END IF;
  RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_bookings_sync_slot_count ON bookings;
CREATE TRIGGER trg_bookings_sync_slot_count
  AFTER INSERT OR UPDATE OR DELETE ON bookings
  FOR EACH ROW
  EXECUTE FUNCTION trg_bookings_sync_slot_count();

-- Corrigir contadores atuais (rodar uma vez)
UPDATE class_slots cs
SET booked_count = sub.cnt
FROM (
  SELECT b.slot_id, COUNT(*)::int AS cnt
  FROM bookings b
  WHERE b.status <> 'cancelled'
  GROUP BY b.slot_id
) sub
WHERE cs.id = sub.slot_id;

-- Slots sem reservas → 0
UPDATE class_slots cs
SET booked_count = 0
WHERE NOT EXISTS (
  SELECT 1 FROM bookings b
  WHERE b.slot_id = cs.id AND b.status <> 'cancelled'
);
