from app.services.actividad import minimizar_texto


def test_minimizar_texto_redacta_email_rut_y_secretos():
    texto = (
        "Usuario persona@empresa.cl RUT 12.345.678-5 "
        "token=secreto password:clave credential=archivo"
    )

    resultado = minimizar_texto(texto)

    assert "persona@empresa.cl" not in resultado
    assert "12.345.678-5" not in resultado
    assert "secreto" not in resultado
    assert "clave" not in resultado
    assert "archivo" not in resultado
