-- El despachador revisa reportes con expresiones cron cada minuto.
UPDATE ops_jobs
   SET cron_expr = '* * * * *'
 WHERE clave = 'reportes_programados'
   AND cron_expr IS DISTINCT FROM '* * * * *';

INSERT INTO app_schema_migrations (version) VALUES (12) ON CONFLICT DO NOTHING;
