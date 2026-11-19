-- Unifica el tipo de token de recuperación con el valor usado por el esquema
-- desplegado antes de la baja controlada de invitaciones.
UPDATE password_reset_tokens
   SET uso = 'restablecimiento'
 WHERE uso = 'reset';

ALTER TABLE password_reset_tokens
  ALTER COLUMN uso SET DEFAULT 'restablecimiento';

ALTER TABLE password_reset_tokens
  DROP CONSTRAINT ck_password_reset_tokens_uso;

ALTER TABLE password_reset_tokens
  ADD CONSTRAINT ck_password_reset_tokens_uso
  CHECK (uso IN ('restablecimiento', 'invitacion'));

INSERT INTO app_schema_migrations (version) VALUES (22)
ON CONFLICT DO NOTHING;
