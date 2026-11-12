-- Tokens de un solo uso para confirmar un cambio de dirección de correo.
CREATE TABLE IF NOT EXISTS email_change_tokens (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  pending_email text NOT NULL,
  token_hash   text NOT NULL UNIQUE,
  expires_at   timestamptz NOT NULL,
  used_at      timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_email_change_user_pending
  ON email_change_tokens (user_id, created_at DESC)
  WHERE used_at IS NULL;

ALTER TABLE email_change_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_change_tokens FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_email_change_tokens ON email_change_tokens;
CREATE POLICY p_email_change_tokens ON email_change_tokens
  FOR ALL
  USING (app_is_admin() OR user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
  WITH CHECK (app_is_admin() OR user_id = NULLIF(current_setting('app.user_id', true), '')::uuid);

INSERT INTO app_schema_migrations (version) VALUES (18) ON CONFLICT DO NOTHING;
