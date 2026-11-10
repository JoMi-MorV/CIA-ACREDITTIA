CREATE TABLE IF NOT EXISTS privacy_retention_policy (
  id boolean PRIMARY KEY DEFAULT true CHECK (id),
  effective_at timestamptz NOT NULL
);

INSERT INTO privacy_retention_policy (id, effective_at)
VALUES (true, TIMESTAMPTZ '2026-11-09 00:00:00-03')
ON CONFLICT (id) DO NOTHING;

REVOKE ALL ON privacy_retention_policy FROM PUBLIC, acredittia_app, acredittia_worker;
GRANT USAGE ON SCHEMA public TO acredittia_owner;
GRANT SELECT ON privacy_retention_policy TO acredittia_owner;

CREATE OR REPLACE FUNCTION fn_solo_insert() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE'
     AND TG_TABLE_NAME IN ('actividad', 'bitacora_cambios')
     AND current_user = 'acredittia_owner'
     AND COALESCE(current_setting('app.retention_purge', true), 'off') = 'on' THEN
    RETURN OLD;
  END IF;
  RAISE EXCEPTION 'La tabla % es de sólo inserción (append-only)', TG_TABLE_NAME
    USING ERRCODE = '55000';
END $$;

CREATE OR REPLACE FUNCTION fn_bitacora_minimizar(p_valor jsonb)
RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
  v_resultado jsonb;
  v_clave text;
  v_valor jsonb;
  v_texto text;
BEGIN
  IF jsonb_typeof(p_valor) = 'object' THEN
    v_resultado := '{}'::jsonb;
    FOR v_clave, v_valor IN SELECT key, value FROM jsonb_each(p_valor) LOOP
      IF v_clave ~* '(email|(^|_)rut($|_)|password|token|secret|credential|nombre|apellido|telefono|phone|direccion|domicilio|nacimiento|fecha_nac|url|blob|contenido|descripcion|comentario|motivo|metadata|archivo)' THEN
        v_resultado := v_resultado || jsonb_build_object(v_clave, '[dato omitido]');
      ELSE
        v_resultado := v_resultado || jsonb_build_object(
          v_clave, fn_bitacora_minimizar(v_valor));
      END IF;
    END LOOP;
    RETURN v_resultado;
  ELSIF jsonb_typeof(p_valor) = 'array' THEN
    SELECT COALESCE(jsonb_agg(fn_bitacora_minimizar(value) ORDER BY ordinalidad),
                    '[]'::jsonb)
      INTO v_resultado
      FROM jsonb_array_elements(p_valor) WITH ORDINALITY AS elementos(value, ordinalidad);
    RETURN v_resultado;
  ELSIF jsonb_typeof(p_valor) = 'string' THEN
    v_texto := p_valor #>> '{}';
    v_texto := regexp_replace(
      v_texto, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
      '[email redactado]', 'gi');
    v_texto := regexp_replace(
      v_texto, '\m[0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3}-[0-9kK]\M',
      '[rut redactado]', 'gi');
    RETURN to_jsonb(v_texto);
  END IF;
  RETURN p_valor;
END $$;

CREATE OR REPLACE FUNCTION fn_bitacora() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  cambios jsonb := '{}'::jsonb;
  k text;
  v_old jsonb;
  v_new jsonb;
  v_company uuid;
  v_id uuid;
BEGIN
  IF TG_OP = 'UPDATE' THEN
    v_old := fn_bitacora_minimizar(to_jsonb(OLD));
    v_new := fn_bitacora_minimizar(to_jsonb(NEW));
    FOR k IN SELECT jsonb_object_keys(v_new) LOOP
      IF k NOT IN ('updated_at') AND (v_old -> k) IS DISTINCT FROM (v_new -> k) THEN
        cambios := cambios || jsonb_build_object(
          k, jsonb_build_object('antes', v_old -> k, 'despues', v_new -> k));
      END IF;
    END LOOP;
    IF cambios = '{}'::jsonb THEN RETURN NEW; END IF;
    v_company := (v_new ->> 'company_id')::uuid;
    v_id := (v_new ->> 'id')::uuid;
  ELSIF TG_OP = 'DELETE' THEN
    v_old := fn_bitacora_minimizar(to_jsonb(OLD));
    cambios := jsonb_build_object('_registro', v_old);
    v_company := (v_old ->> 'company_id')::uuid;
    v_id := (v_old ->> 'id')::uuid;
  ELSE
    v_new := fn_bitacora_minimizar(to_jsonb(NEW));
    cambios := jsonb_build_object('_registro', v_new);
    v_company := (v_new ->> 'company_id')::uuid;
    v_id := (v_new ->> 'id')::uuid;
  END IF;

  INSERT INTO bitacora_cambios (tabla, registro_id, company_id, operacion, campos, app_user)
  VALUES (TG_TABLE_NAME, v_id, v_company, TG_OP, cambios,
          current_setting('app.user_id', true));
  RETURN COALESCE(NEW, OLD);
END $$;

CREATE OR REPLACE FUNCTION ops_podar_privacidad()
RETURNS TABLE (
  actividad_podada bigint,
  bitacora_podada bigint,
  runs_podados bigint,
  incidentes_podados bigint,
  runs_timeout bigint,
  disponibilidad_podada bigint,
  metricas_podadas bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
  v_inicio timestamptz;
  v_actividad bigint;
  v_bitacora bigint;
  v_runs bigint;
  v_incidentes bigint;
  v_timeout bigint;
  v_disponibilidad bigint;
  v_metricas bigint;
BEGIN
  SELECT effective_at INTO STRICT v_inicio
    FROM public.privacy_retention_policy WHERE id = true;
  PERFORM set_config('app.is_admin', 'true', true);
  PERFORM set_config('app.retention_purge', 'on', true);

  UPDATE public.ops_job_runs r
     SET status = 'timeout', finished_at = now(),
         mensaje = COALESCE(r.mensaje, 'Marcado timeout: el worker no cerró el run')
    FROM public.ops_jobs j
   WHERE j.clave = r.job_clave AND r.status = 'running'
     AND r.created_at >= v_inicio
     AND r.started_at < now() - make_interval(secs => j.timeout_s * 2);
  GET DIAGNOSTICS v_timeout = ROW_COUNT;

  DELETE FROM public.actividad
   WHERE created_at >= v_inicio
     AND created_at < now() - interval '12 months';
  GET DIAGNOSTICS v_actividad = ROW_COUNT;

  DELETE FROM public.bitacora_cambios
   WHERE created_at >= v_inicio
     AND created_at < now() - interval '12 months';
  GET DIAGNOSTICS v_bitacora = ROW_COUNT;

  DELETE FROM public.ops_job_runs
   WHERE created_at >= v_inicio
     AND created_at < now() - interval '90 days';
  GET DIAGNOSTICS v_runs = ROW_COUNT;

  DELETE FROM public.ops_incidentes
   WHERE estado = 'resuelto'
     AND resuelto_at >= v_inicio
     AND resuelto_at < now() - interval '90 days';
  GET DIAGNOSTICS v_incidentes = ROW_COUNT;

  DELETE FROM public.ops_disponibilidad_diaria
   WHERE fecha >= v_inicio::date
     AND fecha < (now() - interval '12 months')::date;
  GET DIAGNOSTICS v_disponibilidad = ROW_COUNT;

  DELETE FROM public.metricas_mensuales
   WHERE mes >= date_trunc('month', v_inicio)::date
     AND mes < date_trunc('month', now() - interval '12 months')::date;
  GET DIAGNOSTICS v_metricas = ROW_COUNT;

  RETURN QUERY SELECT v_actividad, v_bitacora, v_runs, v_incidentes,
                      v_timeout, v_disponibilidad, v_metricas;
END $$;

ALTER FUNCTION ops_podar_privacidad() OWNER TO acredittia_owner;
GRANT SELECT, DELETE ON actividad, bitacora_cambios,
  ops_incidentes, ops_disponibilidad_diaria,
  metricas_mensuales TO acredittia_owner;
GRANT SELECT, UPDATE, DELETE ON ops_job_runs TO acredittia_owner;
GRANT SELECT ON ops_jobs TO acredittia_owner;
REVOKE DELETE ON actividad, bitacora_cambios FROM acredittia_app, acredittia_worker;
REVOKE ALL ON FUNCTION ops_podar_privacidad() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ops_podar_privacidad()
  TO acredittia_app, acredittia_worker;

CREATE OR REPLACE FUNCTION ops_podar_telemetria()
RETURNS TABLE (runs_podados bigint, incidentes_podados bigint, runs_timeout bigint)
LANGUAGE sql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
  SELECT result.runs_podados, result.incidentes_podados, result.runs_timeout
    FROM public.ops_podar_privacidad() AS result
$$;

ALTER FUNCTION ops_podar_telemetria() OWNER TO acredittia_owner;
REVOKE ALL ON FUNCTION ops_podar_telemetria() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ops_podar_telemetria()
  TO acredittia_app, acredittia_worker;

INSERT INTO app_schema_migrations (version) VALUES (16) ON CONFLICT DO NOTHING;
