ALTER TABLE ops_job_runs
  ADD COLUMN IF NOT EXISTS progress_pct smallint
    CHECK (progress_pct BETWEEN 0 AND 100),
  ADD COLUMN IF NOT EXISTS progress_mensaje text;

INSERT INTO app_schema_migrations (version) VALUES (19) ON CONFLICT DO NOTHING;
