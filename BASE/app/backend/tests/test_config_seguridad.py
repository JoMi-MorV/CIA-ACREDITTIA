"""RF-SEG-03: rechazar configuraciones inseguras antes de arrancar."""
import pytest
from pydantic import ValidationError

from app.config import Settings, settings
from app import seeds
from tests.conftest import API


def configuracion(**cambios):
    valores = dict(app_env="production", jwt_secret="clave-exclusiva-de-prueba-" * 2,
                   seed_demo_enabled=False, auth_dev_reset_token_enabled=False,
                   db_rls_enabled=True, db_apply_schema_on_start=False)
    valores.update(cambios)
    return Settings(_env_file=None, **valores)


@pytest.mark.parametrize("cambio", [
    {"jwt_secret": "dev-secret-cambiar-en-produccion"},
    {"jwt_secret": "dev-" + "x" * 64},
    {"jwt_secret": "corta"},
    {"jwt_secret": " " * 40},
    {"seed_demo_enabled": True},
    {"auth_dev_reset_token_enabled": True},
    {"db_rls_enabled": False},
    {"db_apply_schema_on_start": True},
    {"app_env": "producion"},
])
def test_produccion_rechaza_configuracion_insegura(cambio):
    with pytest.raises(ValidationError):
        configuracion(**cambio)


def test_produccion_acepta_configuracion_sin_opciones_demo():
    assert configuracion().app_env == "production"


def test_error_de_configuracion_no_imprime_secretos():
    secreto = "secreto-privado-de-prueba-no-publicar"
    with pytest.raises(ValidationError) as error:
        configuracion(jwt_secret=secreto, seed_demo_enabled=True)
    assert secreto not in str(error.value)


def test_opciones_demo_desactivadas_por_defecto(monkeypatch):
    for clave in ("APP_ENV", "SEED_DEMO_ENABLED", "AUTH_DEV_RESET_TOKEN_ENABLED"):
        monkeypatch.delenv(clave, raising=False)
    config = Settings(_env_file=None)
    assert config.seed_demo_enabled is False
    assert config.auth_dev_reset_token_enabled is False


@pytest.mark.parametrize("entorno,habilitado", [("development", False), ("production", True)])
def test_semillas_no_acceden_a_bd_sin_autorizacion(monkeypatch, entorno, habilitado):
    monkeypatch.setattr(settings, "app_env", entorno)
    monkeypatch.setattr(settings, "seed_demo_enabled", habilitado)
    # None hace fallar cualquier intento de usar la BD antes de la guarda.
    with pytest.raises(RuntimeError, match="activación explícita"):
        seeds.run(None)


def test_arranque_sin_semillas(monkeypatch):
    import asyncio
    from unittest.mock import MagicMock
    from app import main

    monkeypatch.setattr(settings, "seed_demo_enabled", False)
    monkeypatch.setattr(settings, "queue_backend", "celery")
    for nombre in ("wait_for_db", "assert_schema_version", "recalcular_documentos"):
        monkeypatch.setattr(main, nombre, MagicMock())
    monkeypatch.setattr(main, "SessionLocal", MagicMock())
    sembrar = MagicMock()
    monkeypatch.setattr(seeds, "run", sembrar)

    async def arrancar():
        async with main.lifespan(main.app):
            sembrar.assert_not_called()

    asyncio.run(arrancar())


@pytest.mark.parametrize("entorno,habilitado", [("development", False), ("production", True)])
def test_recuperacion_no_expone_token(monkeypatch, app_cliente, empresa_a, entorno, habilitado):
    monkeypatch.setattr(settings, "app_env", entorno)
    monkeypatch.setattr(settings, "auth_dev_reset_token_enabled", habilitado)
    existente = app_cliente.post(f"{API}/auth/password/forgot", json={"email": empresa_a["email"]})
    inexistente = app_cliente.post(f"{API}/auth/password/forgot", json={"email": "nadie@empresa.cl"})
    assert existente.status_code == inexistente.status_code == 200
    assert existente.json() == inexistente.json()
    assert not any(clave.startswith("_dev") for clave in existente.json())
