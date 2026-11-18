from __future__ import annotations

import pytest

from app.services.storage import LocalStorage


def test_local_storage_rechaza_rutas_fuera_de_la_raiz(tmp_path):
    storage = LocalStorage(str(tmp_path / "uploads"))

    with pytest.raises(ValueError, match="Ruta inválida"):
        storage._full("../uploads-escape/probe")


def test_local_storage_acepta_rutas_dentro_de_la_raiz(tmp_path):
    storage = LocalStorage(str(tmp_path / "uploads"))

    assert storage._full("tenant/document.pdf") == str(
        tmp_path / "uploads" / "tenant" / "document.pdf")
