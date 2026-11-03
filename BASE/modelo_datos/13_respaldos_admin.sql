INSERT INTO ops_jobs
  (clave, nombre, tipo, cron_expr, componente, activo, timeout_s)
VALUES
  ('admin_backup', 'Respaldo ADMIN', 'programado', '0 2 * * 0',
   'storage', false, 7200)
ON CONFLICT (clave) DO NOTHING;

INSERT INTO app_schema_migrations (version) VALUES (13) ON CONFLICT DO NOTHING;
