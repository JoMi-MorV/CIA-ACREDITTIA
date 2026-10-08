-- Ciclo de vida reversible del contrato, separado del estado operacional.
ALTER TABLE contratos
  ADD COLUMN IF NOT EXISTS ciclo_estado text NOT NULL DEFAULT 'activo',
  ADD COLUMN IF NOT EXISTS ciclo_actualizado_at timestamptz,
  ADD COLUMN IF NOT EXISTS ciclo_motivo text,
  ADD COLUMN IF NOT EXISTS ciclo_actor_id uuid REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE contratos
  DROP CONSTRAINT IF EXISTS ck_contratos_ciclo_estado;
ALTER TABLE contratos
  ADD CONSTRAINT ck_contratos_ciclo_estado
  CHECK (ciclo_estado IN ('activo', 'desactivado', 'finalizado'));

CREATE INDEX IF NOT EXISTS ix_contratos_company_ciclo
  ON contratos (company_id, ciclo_estado, nombre);
CREATE INDEX IF NOT EXISTS ix_contratos_ciclo_actor
  ON contratos (ciclo_actor_id);

INSERT INTO app_schema_migrations (version) VALUES (11) ON CONFLICT DO NOTHING;
