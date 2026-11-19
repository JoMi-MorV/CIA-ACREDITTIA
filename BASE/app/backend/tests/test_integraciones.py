"""Almacenamiento seguro y alcance actual de integraciones."""
import uuid

from app.database import worker_session
from app.models import Integracion
from tests.conftest import API


class SecretWriterFalso:
    def __init__(self):
        self.secrets = {}
        self.eliminados = []
        self.fallar_al_eliminar = False

    def write(self, ref, secreto):
        self.secrets[ref] = dict(secreto)

    def delete(self, ref):
        if self.fallar_al_eliminar:
            raise OSError("vault no disponible")
        self.eliminados.append(ref)
        self.secrets.pop(ref, None)


def test_secretos_de_integracion_quedan_fuera_de_la_api_y_de_la_bd(
        app_cliente, empresa_a, monkeypatch):
    from app.routers import integraciones

    vault = SecretWriterFalso()
    monkeypatch.setattr(integraciones, "get_secret_writer", lambda: vault)
    secreto = "token-integracion-no-exponer-91"
    credenciales = {"usuario": "cuenta-api", "token": secreto}

    creada = app_cliente.post(
        f"{API}/integraciones", headers=empresa_a["headers"],
        json={"tipo": "siga", "credenciales": credenciales})
    assert creada.status_code == 201, creada.text
    assert secreto not in creada.text
    assert creada.json()["credenciales_configuradas"] is True
    assert creada.json()["credenciales_pendientes"] is True
    assert creada.json()["conector_disponible"] is False

    iid = creada.json()["id"]
    ref = creada.json()["credenciales_ref"]
    assert vault.secrets[ref] == credenciales
    with worker_session(is_admin=True) as db:
        fila = db.get(Integracion, uuid.UUID(iid))
        assert fila is not None
        assert fila.credenciales_ref == ref
        assert secreto not in str(fila.config) + str(fila.credenciales_ref)

    rotada = app_cliente.patch(
        f"{API}/integraciones/{iid}", headers=empresa_a["headers"],
        json={"credenciales": {"usuario": "cuenta-api", "token": "token-nuevo"}})
    assert rotada.status_code == 200, rotada.text
    assert "token-nuevo" not in rotada.text
    assert vault.secrets[ref]["token"] == "token-nuevo"

    listado = app_cliente.get(
        f"{API}/integraciones", headers=empresa_a["headers"])
    assert listado.status_code == 200, listado.text
    assert secreto not in listado.text
    assert "token-nuevo" not in listado.text

    activa = app_cliente.patch(
        f"{API}/integraciones/{iid}", headers=empresa_a["headers"],
        json={"estado": "activa"})
    assert activa.status_code == 200, activa.text
    sync = app_cliente.post(
        f"{API}/integraciones/{iid}/sync", headers=empresa_a["headers"])
    assert sync.status_code == 409
    assert sync.json()["error"]["code"] == "CONECTOR_NO_DISPONIBLE"

    eliminada = app_cliente.delete(
        f"{API}/integraciones/{iid}", headers=empresa_a["headers"])
    assert eliminada.status_code == 200, eliminada.text
    assert vault.eliminados == [ref]
    assert ref not in vault.secrets


def test_fallo_al_eliminar_secreto_conserva_integracion_para_reintento(
        app_cliente, empresa_a, monkeypatch):
    from app.routers import integraciones

    vault = SecretWriterFalso()
    monkeypatch.setattr(integraciones, "get_secret_writer", lambda: vault)
    creada = app_cliente.post(
        f"{API}/integraciones", headers=empresa_a["headers"],
        json={"tipo": "siga", "credenciales": {"token": "secreto"}})
    assert creada.status_code == 201, creada.text
    iid = uuid.UUID(creada.json()["id"])

    vault.fallar_al_eliminar = True
    eliminada = app_cliente.delete(
        f"{API}/integraciones/{iid}", headers=empresa_a["headers"])
    assert eliminada.status_code == 503
    assert "secreto" not in eliminada.text

    with worker_session(is_admin=True) as db:
        assert db.get(Integracion, iid) is not None
