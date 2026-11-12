CREATE TABLE IF NOT EXISTS ops_ajustes_negocio (
    id boolean PRIMARY KEY DEFAULT true CHECK (id),
    valor_uf numeric(12, 2) NOT NULL DEFAULT 39000.00
        CHECK (valor_uf > 0),
    uf_vigente_desde date NOT NULL DEFAULT CURRENT_DATE,
    uf_fuente text NOT NULL DEFAULT 'Valor inicial de referencia',
    cac_clp numeric(14, 2) NOT NULL DEFAULT 0
        CHECK (cac_clp >= 0),
    margen_bruto_pct numeric(5, 2) NOT NULL DEFAULT 80
        CHECK (margen_bruto_pct BETWEEN 0 AND 100),
    objetivo_churn_pct numeric(5, 2) NOT NULL DEFAULT 2
        CHECK (objetivo_churn_pct BETWEEN 0 AND 100),
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid
);

INSERT INTO ops_ajustes_negocio (id)
VALUES (true)
ON CONFLICT (id) DO NOTHING;

ALTER TABLE ops_ajustes_negocio ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops_ajustes_negocio FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ops_ajustes_negocio_admin ON ops_ajustes_negocio;
CREATE POLICY ops_ajustes_negocio_admin ON ops_ajustes_negocio
    FOR ALL USING (app_is_admin()) WITH CHECK (app_is_admin());
REVOKE ALL ON ops_ajustes_negocio FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON ops_ajustes_negocio TO acredittia_app;
GRANT SELECT, INSERT, UPDATE ON ops_ajustes_negocio TO acredittia_owner;

INSERT INTO app_schema_migrations (version) VALUES (17) ON CONFLICT DO NOTHING;
