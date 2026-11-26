-- La auditoría es inmutable y debe sobrevivir al borrado de una solicitud
-- rechazada. company_id conserva el UUID histórico, aunque ya no exista la fila
-- de companies correspondiente.
DO $$
DECLARE
  v_constraint text;
BEGIN
  SELECT conname
    INTO v_constraint
    FROM pg_constraint
   WHERE conrelid = 'actividad'::regclass
     AND confrelid = 'companies'::regclass
     AND contype = 'f'
     AND cardinality(conkey) = 1
     AND conkey[1] = (
       SELECT attnum
         FROM pg_attribute
        WHERE attrelid = 'actividad'::regclass
          AND attname = 'company_id'
          AND NOT attisdropped
     );

  IF v_constraint IS NOT NULL THEN
    EXECUTE format('ALTER TABLE actividad DROP CONSTRAINT %I', v_constraint);
  END IF;
END $$;

INSERT INTO app_schema_migrations (version) VALUES (25)
ON CONFLICT DO NOTHING;
