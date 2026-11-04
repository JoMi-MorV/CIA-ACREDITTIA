"""Ejecuta una línea base HTTP reproducible para RNF-PER-01."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Iterable


def percentil(valores: Iterable[float], porcentaje: float) -> float | None:
    muestras = sorted(valores)
    if not muestras:
        return None
    indice = math.ceil(len(muestras) * porcentaje) - 1
    return muestras[max(0, indice)]


def ejecutar_solicitud(url: str, bearer_token: str | None) -> tuple[float, int]:
    inicio = time.perf_counter()
    headers = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
    except urllib.error.URLError:
        status = 0
    return (time.perf_counter() - inicio) * 1000, status


def resumir(rutas: list[str], resultados: dict[str, list[tuple[float, int]]]) -> dict:
    resumen = {}
    for ruta in rutas:
        latencias_estado = resultados[ruta]
        latencias = [duracion for duracion, _ in latencias_estado]
        estados = [estado for _, estado in latencias_estado]
        resumen[ruta] = {
            "solicitudes": len(latencias),
            "latencia_media_ms": round(statistics.mean(latencias), 1),
            "latencia_p95_ms": round(percentil(latencias, 0.95) or 0, 1),
            "latencia_max_ms": round(max(latencias), 1),
            "errores_http": sum(estado == 0 or estado >= 400 for estado in estados),
            "codigos_http": dict(sorted(
                (str(codigo), estados.count(codigo))
                for codigo in set(estados)
            )),
        }
    return resumen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--paths", required=True,
                        help="Rutas separadas por coma")
    parser.add_argument("--requests", type=int, default=100,
                        help="Solicitudes por ruta")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--token")
    parser.add_argument("--p95-limit-ms", type=float, default=800)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rutas = [ruta.strip() for ruta in args.paths.split(",") if ruta.strip()]
    base_url = args.base_url.rstrip("/")
    if not rutas:
        raise SystemExit("Debe indicar al menos una ruta")
    if args.requests < 1 or args.concurrency < 1:
        raise SystemExit("--requests y --concurrency deben ser mayores que cero")

    resultados: dict[str, list[tuple[float, int]]] = defaultdict(list)
    urls = [(ruta, f"{base_url}{ruta}") for ruta in rutas for _ in range(args.requests)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futuros = {
            pool.submit(ejecutar_solicitud, url, args.token): ruta
            for ruta, url in urls
        }
        for futuro in concurrent.futures.as_completed(futuros):
            duracion, estado = futuro.result()
            resultados[futuros[futuro]].append((duracion, estado))

    informe = {
        "base_url": base_url,
        "solicitudes_por_ruta": args.requests,
        "concurrencia": args.concurrency,
        "limite_p95_ms": args.p95_limit_ms,
        "rutas": resumir(rutas, resultados),
    }
    texto = json.dumps(informe, indent=2, ensure_ascii=False)
    print(texto)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as archivo:
            archivo.write(texto + "\n")

    cumple = all(
        ruta["latencia_p95_ms"] <= args.p95_limit_ms
        and ruta["errores_http"] == 0
        for ruta in informe["rutas"].values()
    )
    return 0 if cumple else 1


if __name__ == "__main__":
    raise SystemExit(main())
