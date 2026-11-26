CREATE TABLE IF NOT EXISTS solicitudes_suscripcion (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  tipo text NOT NULL CHECK (tipo IN ('cambio_plan', 'regularizacion')),
  plan_id uuid REFERENCES planes(id) ON DELETE RESTRICT,
  estado text NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente', 'aprobada', 'rechazada')),
  motivo text NOT NULL CHECK (length(btrim(motivo)) >= 12),
  solicitado_por uuid REFERENCES users(id) ON DELETE SET NULL,
  solicitado_at timestamptz NOT NULL DEFAULT now(),
  resuelto_por uuid REFERENCES users(id),
  resuelto_at timestamptz,
  motivo_resolucion text,
  CONSTRAINT ck_solicitud_suscripcion_tipo_plan CHECK (
    (tipo = 'cambio_plan' AND plan_id IS NOT NULL)
    OR (tipo = 'regularizacion' AND plan_id IS NULL)
  ),
  CONSTRAINT ck_solicitud_suscripcion_resolucion CHECK (
    (estado = 'pendiente' AND resuelto_por IS NULL AND resuelto_at IS NULL
      AND motivo_resolucion IS NULL)
    OR (estado IN ('aprobada', 'rechazada') AND resuelto_por IS NOT NULL
      AND resuelto_at IS NOT NULL AND motivo_resolucion IS NOT NULL)
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_solicitudes_suscripcion_pendiente
  ON solicitudes_suscripcion (company_id, tipo)
  WHERE estado = 'pendiente';
CREATE INDEX IF NOT EXISTS ix_solicitudes_suscripcion_empresa_fecha
  ON solicitudes_suscripcion (company_id, solicitado_at DESC);
CREATE INDEX IF NOT EXISTS ix_solicitudes_suscripcion_plan
  ON solicitudes_suscripcion (plan_id);
CREATE INDEX IF NOT EXISTS ix_solicitudes_suscripcion_solicitante
  ON solicitudes_suscripcion (solicitado_por);
CREATE INDEX IF NOT EXISTS ix_solicitudes_suscripcion_resolutor
  ON solicitudes_suscripcion (resuelto_por);

GRANT SELECT, INSERT, UPDATE, DELETE ON solicitudes_suscripcion TO acredittia_app;
ALTER TABLE solicitudes_suscripcion ENABLE ROW LEVEL SECURITY;
ALTER TABLE solicitudes_suscripcion FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS p_solicitudes_suscripcion_read
  ON solicitudes_suscripcion;
DROP POLICY IF EXISTS p_solicitudes_suscripcion_insert
  ON solicitudes_suscripcion;
DROP POLICY IF EXISTS p_solicitudes_suscripcion_admin_update
  ON solicitudes_suscripcion;
DROP POLICY IF EXISTS p_solicitudes_suscripcion_admin_delete
  ON solicitudes_suscripcion;
CREATE POLICY p_solicitudes_suscripcion_read
  ON solicitudes_suscripcion FOR SELECT
  USING (app_is_admin() OR company_id = app_company_id());
CREATE POLICY p_solicitudes_suscripcion_insert
  ON solicitudes_suscripcion FOR INSERT
  WITH CHECK (
    app_is_admin()
    OR (
      company_id = app_company_id()
      AND estado = 'pendiente'
      AND resuelto_por IS NULL
      AND resuelto_at IS NULL
      AND solicitado_por =
        NULLIF(current_setting('app.user_id', true), '')::uuid
    )
  );
CREATE POLICY p_solicitudes_suscripcion_admin_update
  ON solicitudes_suscripcion FOR UPDATE
  USING (app_is_admin()) WITH CHECK (app_is_admin());
CREATE POLICY p_solicitudes_suscripcion_admin_delete
  ON solicitudes_suscripcion FOR DELETE
  USING (app_is_admin());

CREATE OR REPLACE FUNCTION ops_estado_cuenta(p_company uuid)
RETURNS text
LANGUAGE plpgsql STABLE AS $$
DECLARE
  v_vencidas          integer;
  v_max_atraso        integer;
  v_trial_vto         date;
  v_regularizado_at   timestamptz;
BEGIN
  SELECT max(resuelto_at)
    INTO v_regularizado_at
    FROM solicitudes_suscripcion
   WHERE company_id = p_company
     AND tipo = 'regularizacion'
     AND estado = 'aprobada';

  SELECT count(*),
         COALESCE(max(extract(day FROM now() - emitida_at)::integer - 14), 0)
    INTO v_vencidas, v_max_atraso
    FROM facturas
   WHERE company_id = p_company
     AND estado = 'pendiente'
     AND emitida_at < now() - interval '14 days'
     AND (v_regularizado_at IS NULL OR emitida_at > v_regularizado_at);

  IF v_vencidas >= 2 OR v_max_atraso > 30 THEN
    RETURN 'moroso';
  END IF;

  SELECT trial_hasta INTO v_trial_vto
    FROM suscripciones
   WHERE company_id = p_company AND estado = 'trial';

  IF v_vencidas = 1
     OR (v_trial_vto IS NOT NULL AND v_trial_vto < current_date
         AND v_trial_vto >= current_date - 15
         AND (v_regularizado_at IS NULL
              OR v_trial_vto > v_regularizado_at::date)) THEN
    RETURN 'en_riesgo';
  END IF;
  RETURN 'al_dia';
END $$;

INSERT INTO app_schema_migrations (version) VALUES (24)
ON CONFLICT DO NOTHING;
