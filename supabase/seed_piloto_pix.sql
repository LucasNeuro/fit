-- =============================================================================
-- Cadastrar PIX da academia (rodar no Supabase SQL Editor)
-- CNPJ: 62449971000170 — Play Pag LTDA
-- =============================================================================

-- 1) Criar colunas (se ainda não existirem)
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_key TEXT;
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_type TEXT DEFAULT 'CNPJ';
ALTER TABLE gyms ADD COLUMN IF NOT EXISTS pix_name TEXT;

-- 2) Atualizar academia piloto
UPDATE gyms
SET
  pix_key = '62449971000170',
  pix_type = 'CNPJ',
  pix_name = 'Empresa Play Pag LTDA',
  agent_config = COALESCE(agent_config, '{}'::jsonb) || jsonb_build_object(
    'pix_key', '62449971000170',
    'pix_type', 'CNPJ',
    'pix_name', 'Empresa Play Pag LTDA'
  ),
  updated_at = now()
WHERE slug = 'piloto';

-- 3) Conferir (deve retornar 1 linha)
SELECT id, slug, name, pix_key, pix_type, pix_name
FROM gyms
WHERE slug = 'piloto';

-- Se não retornou linha, liste academias existentes:
-- SELECT slug, name FROM gyms ORDER BY name;
