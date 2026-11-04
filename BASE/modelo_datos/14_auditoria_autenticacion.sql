ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_login_ok';
ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_login_failed';
ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_logout';
ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_refresh_rotated';
ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_refresh_failed';
ALTER TYPE actividad_tipo ADD VALUE IF NOT EXISTS 'auth_session_revoked';

ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS session_id uuid;
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_session_id ON refresh_tokens(session_id);
CREATE INDEX IF NOT EXISTS ix_actividad_auth_module_created
    ON actividad(created_at DESC) WHERE modulo = 'auth';

COMMENT ON COLUMN refresh_tokens.session_id IS
    'Correlación no reutilizable entre eventos de una misma sesión; nunca contiene el refresh token.';
INSERT INTO app_schema_migrations (version) VALUES (14) ON CONFLICT DO NOTHING;
