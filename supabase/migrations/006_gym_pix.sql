-- Chave PIX por academia (matrícula / mensalidade via WhatsApp)
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_key TEXT;
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_type TEXT DEFAULT 'CNPJ';
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_name TEXT;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'gyms_pix_type_check'
  ) THEN
    ALTER TABLE gyms
      ADD CONSTRAINT gyms_pix_type_check
      CHECK (pix_type IS NULL OR pix_type IN ('CPF', 'CNPJ', 'PHONE', 'EMAIL', 'EVP'));
  END IF;
END $$;

COMMENT ON COLUMN gyms.pix_key IS 'Chave PIX da academia (CPF/CNPJ/telefone/email/EVP)';
COMMENT ON COLUMN gyms.pix_type IS 'Tipo: CPF, CNPJ, PHONE, EMAIL, EVP';
COMMENT ON COLUMN gyms.pix_name IS 'Nome exibido no botão PIX do WhatsApp';
