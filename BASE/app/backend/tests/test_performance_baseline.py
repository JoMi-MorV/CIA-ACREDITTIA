from scripts.performance_baseline import percentil, resumir


def test_percentil_calcula_el_menor_valores_necesario():
    assert percentil([20, 10, 30, 40], 0.95) == 40
    assert percentil([20, 10, 30, 40], 0.50) == 20
    assert percentil([], 0.95) is None


def test_resumir_reporta_p95_errores_y_codigos():
    resultados = {
        "/health": [(10, 200), (20, 200), (30, 500), (40, 200), (50, 200)],
    }

    resumen = resumir(["/health"], resultados)

    assert resumen["/health"]["latencia_p95_ms"] == 50
    assert resumen["/health"]["errores_http"] == 1
    assert resumen["/health"]["codigos_http"] == {"200": 4, "500": 1}
