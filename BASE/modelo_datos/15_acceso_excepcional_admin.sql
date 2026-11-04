CREATE TABLE IF NOT EXISTS admin_access_grants (
    id uuid PRIMARY KEY,
    admin_user_id uuid NOT NULL REFERENCES users(id),
    granted_by uuid NOT NULL REFERENCES users(id),
    company_id uuid REFERENCES companies(id),
    recurso_tipo text NOT NULL,
    recurso_id uuid,
    motivo text NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    revoked_by uuid REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT admin_access_grants_motivo CHECK (length(motivo) >= 12 AND length(motivo) <= 240)
);

CREATE INDEX IF NOT EXISTS ix_admin_access_grants_admin_vigentes
    ON admin_access_grants(admin_user_id, expires_at) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_admin_access_grants_company
    ON admin_access_grants(company_id) WHERE company_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_admin_access_grants_granted_by ON admin_access_grants(granted_by);
CREATE INDEX IF NOT EXISTS ix_admin_access_grants_revoked_by ON admin_access_grants(revoked_by);

ALTER TABLE admin_access_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_access_grants FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS admin_access_grants_admin ON admin_access_grants;
CREATE POLICY admin_access_grants_admin ON admin_access_grants
    FOR ALL USING (app_is_admin()) WITH CHECK (app_is_admin());
REVOKE ALL ON admin_access_grants FROM acredittia_app;
GRANT SELECT, INSERT, UPDATE ON admin_access_grants TO acredittia_app;
INSERT INTO app_schema_migrations (version) VALUES (15) ON CONFLICT DO NOTHING;
