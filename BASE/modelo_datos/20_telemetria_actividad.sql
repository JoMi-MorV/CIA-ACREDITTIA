CREATE TABLE IF NOT EXISTS ops_sesiones_actividad (
  session_id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  started_at timestamptz NOT NULL,
  last_heartbeat_at timestamptz NOT NULL,
  ended_at timestamptz,
  CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE INDEX IF NOT EXISTS ix_ops_sesiones_actividad_heartbeat
  ON ops_sesiones_actividad (last_heartbeat_at);
CREATE INDEX IF NOT EXISTS ix_ops_sesiones_actividad_user
  ON ops_sesiones_actividad (user_id);
CREATE INDEX IF NOT EXISTS ix_ops_sesiones_actividad_company
  ON ops_sesiones_actividad (company_id);

CREATE TABLE IF NOT EXISTS ops_actividad_usuario_diaria (
  fecha date NOT NULL,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  segundos_activos bigint NOT NULL DEFAULT 0 CHECK (segundos_activos >= 0),
  PRIMARY KEY (fecha, user_id)
);

CREATE INDEX IF NOT EXISTS ix_ops_actividad_usuario_empresa_fecha
  ON ops_actividad_usuario_diaria (company_id, fecha);
CREATE INDEX IF NOT EXISTS ix_ops_actividad_usuario_user
  ON ops_actividad_usuario_diaria (user_id);

CREATE TABLE IF NOT EXISTS ops_actividad_empresa_diaria (
  fecha date NOT NULL,
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  segundos_activos bigint NOT NULL DEFAULT 0 CHECK (segundos_activos >= 0),
  PRIMARY KEY (fecha, company_id)
);

CREATE INDEX IF NOT EXISTS ix_ops_actividad_empresa_company
  ON ops_actividad_empresa_diaria (company_id);

ALTER TABLE ops_sesiones_actividad ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops_sesiones_actividad FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_ops_sesiones_actividad ON ops_sesiones_actividad;
CREATE POLICY p_ops_sesiones_actividad ON ops_sesiones_actividad
  FOR ALL
  USING ((app_is_admin() AND current_user = 'acredittia_owner') OR (
    company_id = NULLIF(current_setting('app.company_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
  ))
  WITH CHECK (
    company_id = NULLIF(current_setting('app.company_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
  );

ALTER TABLE ops_actividad_usuario_diaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops_actividad_usuario_diaria FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_ops_actividad_usuario_diaria ON ops_actividad_usuario_diaria;
CREATE POLICY p_ops_actividad_usuario_diaria ON ops_actividad_usuario_diaria
  FOR ALL
  USING ((app_is_admin() AND current_user = 'acredittia_owner') OR (
    company_id = NULLIF(current_setting('app.company_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
  ))
  WITH CHECK (
    company_id = NULLIF(current_setting('app.company_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
  );

ALTER TABLE ops_actividad_empresa_diaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops_actividad_empresa_diaria FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_ops_actividad_empresa_diaria ON ops_actividad_empresa_diaria;
CREATE POLICY p_ops_actividad_empresa_diaria ON ops_actividad_empresa_diaria
  FOR ALL
  USING (app_is_admin() OR company_id =
    NULLIF(current_setting('app.company_id', true), '')::uuid)
  WITH CHECK (app_is_admin() OR company_id =
    NULLIF(current_setting('app.company_id', true), '')::uuid);

GRANT SELECT, INSERT, UPDATE, DELETE ON ops_sesiones_actividad,
  ops_actividad_usuario_diaria, ops_actividad_empresa_diaria TO acredittia_app;
GRANT SELECT, DELETE ON ops_sesiones_actividad,
  ops_actividad_usuario_diaria, ops_actividad_empresa_diaria TO acredittia_owner;

CREATE OR REPLACE FUNCTION ops_resumen_actividad_usuario(
  p_desde date, p_hasta date
)
RETURNS TABLE (segundos_activos numeric, usuarios_medidos bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
  PERFORM set_config('app.is_admin', 'true', true);
  RETURN QUERY
    SELECT COALESCE(SUM(a.segundos_activos), 0),
           COUNT(DISTINCT a.user_id)
      FROM public.ops_actividad_usuario_diaria AS a
     WHERE a.fecha >= p_desde AND a.fecha < p_hasta;
END
$$;

ALTER FUNCTION ops_resumen_actividad_usuario(date, date) OWNER TO acredittia_owner;
REVOKE ALL ON FUNCTION ops_resumen_actividad_usuario(date, date) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ops_resumen_actividad_usuario(date, date)
  TO acredittia_app;

CREATE OR REPLACE FUNCTION ops_podar_telemetria_actividad()
RETURNS TABLE (sesiones_podadas bigint, agregados_usuario_podados bigint,
               agregados_empresa_podados bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_inicio timestamptz;
  v_sesiones bigint;
  v_usuarios bigint;
  v_empresas bigint;
BEGIN
  SELECT effective_at INTO STRICT v_inicio
    FROM public.privacy_retention_policy WHERE id = true;
  PERFORM set_config('app.is_admin', 'true', true);

  DELETE FROM public.ops_sesiones_actividad
   WHERE last_heartbeat_at >= v_inicio
     AND last_heartbeat_at < now() - interval '90 days';
  GET DIAGNOSTICS v_sesiones = ROW_COUNT;

  DELETE FROM public.ops_actividad_usuario_diaria
   WHERE fecha >= v_inicio::date
     AND fecha < ((now() AT TIME ZONE 'America/Santiago')::date - 90);
  GET DIAGNOSTICS v_usuarios = ROW_COUNT;

  DELETE FROM public.ops_actividad_empresa_diaria
   WHERE fecha >= v_inicio::date
     AND fecha < ((now() AT TIME ZONE 'America/Santiago')::date - interval '12 months');
  GET DIAGNOSTICS v_empresas = ROW_COUNT;

  RETURN QUERY SELECT v_sesiones, v_usuarios, v_empresas;
END
$$;

ALTER FUNCTION ops_podar_telemetria_actividad() OWNER TO acredittia_owner;
REVOKE ALL ON FUNCTION ops_podar_telemetria_actividad() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ops_podar_telemetria_actividad()
  TO acredittia_app, acredittia_worker;

INSERT INTO app_schema_migrations (version) VALUES (20) ON CONFLICT DO NOTHING;
