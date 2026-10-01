-- Corrección incremental: índices de soporte de las FK de la consola.
-- Aplicar antes de arrancar la API; no modifica filas de negocio.
BEGIN;

CREATE INDEX IF NOT EXISTS ix_ops_jobs_componente ON ops_jobs (componente);
CREATE INDEX IF NOT EXISTS ix_ops_jobs_pausado_por ON ops_jobs (pausado_por);
CREATE INDEX IF NOT EXISTS ix_ops_runs_actor ON ops_job_runs (actor_user_id);
CREATE INDEX IF NOT EXISTS ix_ops_incidentes_creador ON ops_incidentes (creado_por);
CREATE INDEX IF NOT EXISTS ix_metricas_plan_plan ON metricas_mensuales_plan (plan_id);

CREATE TABLE IF NOT EXISTS app_schema_migrations (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON app_schema_migrations TO acredittia_app, acredittia_worker;
INSERT INTO app_schema_migrations (version) VALUES (8) ON CONFLICT DO NOTHING;

COMMIT;
