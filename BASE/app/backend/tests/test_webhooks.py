from __future__ import annotations

from app.routers import webhooks
from tests.conftest import API


def test_estado_pago_no_confunde_unpaid_con_paid():
    assert webhooks._estado_de_pago({"status": "unpaid"}) == "desconocido"
    assert webhooks._estado_de_pago({"status": "not_succeeded"}) == "desconocido"


def test_estado_pago_reconoce_eventos_terminales():
    assert webhooks._estado_de_pago(
        {"type": "payment_intent.succeeded"}) == "pagado"
    assert webhooks._estado_de_pago(
        {"type": "invoice.payment_failed"}) == "fallido"


def test_estado_pago_conflictivo_falla_cerrado():
    assert webhooks._estado_de_pago({
        "status": "paid",
        "event": "payment.failed",
    }) == "desconocido"
    assert webhooks._estado_de_pago({
        "status": "unpaid",
        "event": "payment.succeeded",
    }) == "desconocido"


def test_conciliacion_no_consulta_ni_actualiza_con_estado_desconocido(monkeypatch):
    def no_debe_abrir_sesion(**kwargs):
        raise AssertionError("no se debe consultar la factura")

    monkeypatch.setattr(webhooks, "worker_session", no_debe_abrir_sesion)
    status, body = webhooks._conciliar(
        {"gateway_ref": "invoice-ref", "status": "unpaid"})

    assert status == 200
    assert body["conciliado"] is False
    assert body["motivo"] == "estado_no_reconocido"


def test_webhook_rechaza_cuerpo_sobredimensionado_antes_de_validar_firma(
        app_cliente, monkeypatch):
    monkeypatch.setattr(webhooks, "MAX_WEBHOOK_BODY_BYTES", 4)
    response = app_cliente.post(
        f"{API}/webhooks/pagos", content=b"12345",
        headers={"content-type": "application/json"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "CUERPO_DEMASIADO_GRANDE"
