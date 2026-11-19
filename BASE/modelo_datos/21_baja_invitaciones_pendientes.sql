-- Permite eliminar físicamente una invitación nunca aceptada sin mutar el
-- contenido histórico de actividad. La FK user_id usa ON DELETE SET NULL.
ALTER TABLE password_reset_tokens
  ADD COLUMN uso text NOT NULL DEFAULT 'reset';

UPDATE password_reset_tokens
   SET uso = 'invitacion'
 WHERE expires_at - created_at >= interval '71 hours';

ALTER TABLE password_reset_tokens
  ADD CONSTRAINT ck_password_reset_tokens_uso
  CHECK (uso IN ('reset', 'restablecimiento', 'invitacion'));

CREATE OR REPLACE FUNCTION fn_solo_insert() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE'
     AND TG_TABLE_NAME IN ('actividad', 'bitacora_cambios')
     AND current_user = 'acredittia_owner'
     AND COALESCE(current_setting('app.retention_purge', true), 'off') = 'on' THEN
    RETURN OLD;
  END IF;

  IF TG_TABLE_NAME = 'actividad' AND TG_OP = 'UPDATE' THEN
    IF OLD.user_id IS NOT NULL
       AND NEW.user_id IS NULL
       AND (to_jsonb(OLD) - 'user_id') IS NOT DISTINCT FROM
           (to_jsonb(NEW) - 'user_id') THEN
      RETURN NEW;
    END IF;
  END IF;

  RAISE EXCEPTION 'La tabla % es de sólo inserción (append-only)', TG_TABLE_NAME
    USING ERRCODE = '55000';
END $$;

INSERT INTO app_schema_migrations (version) VALUES (21)
ON CONFLICT DO NOTHING;
