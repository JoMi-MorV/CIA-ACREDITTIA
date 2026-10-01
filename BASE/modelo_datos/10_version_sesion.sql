-- Invalida JWT anteriores cuando cambia el estado de acceso de una cuenta.
BEGIN;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_version integer NOT NULL DEFAULT 0;
INSERT INTO app_schema_migrations (version) VALUES (9) ON CONFLICT DO NOTHING;
COMMIT;
