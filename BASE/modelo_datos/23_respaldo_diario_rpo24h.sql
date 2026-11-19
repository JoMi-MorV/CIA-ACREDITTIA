UPDATE ops_jobs
   SET cron_expr = '0 2 * * *'
 WHERE clave = 'admin_backup'
   AND cron_expr = '0 2 * * 0';

INSERT INTO app_schema_migrations (version) VALUES (23)
ON CONFLICT DO NOTHING;
