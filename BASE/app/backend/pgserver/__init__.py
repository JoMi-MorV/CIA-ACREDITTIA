from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass

DEFAULT_IMAGE = os.environ.get("PGSERVER_IMAGE", "postgres:16-alpine")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run(cmd: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=capture, check=False)


@dataclass
class Server:
    data_dir: str
    port: int
    container_name: str
    image: str = DEFAULT_IMAGE

    def get_uri(self) -> str:
        return (
            f"postgresql://postgres:postgres@localhost:{self.port}/postgres"
            f"?host=localhost&port={self.port}"
        )

    def stop(self) -> None:
        _run(["docker", "rm", "-f", self.container_name], capture=False)

    def __del__(self) -> None:
        try:
            self.stop()
        except Exception:
            pass


def get_server(data_dir: str) -> Server:
    """Levanta PostgreSQL usando Docker en vez de depender de `pgserver` inexistente.

    La API de pruebas espera un objeto con `get_uri()` y `stop()`, así que esta
    compatibilidad local conserva la interfaz esperada por `tests/conftest.py`.
    """
    if shutil.which("docker") is None:
        raise RuntimeError("Docker no está instalado ni disponible en PATH; se necesita para arrancar PostgreSQL temporal")

    data_dir = os.path.abspath(data_dir)
    port = _find_free_port()
    volume_name = "acredittia-pgserver-" + str(abs(hash(data_dir)))[:12]
    container_name = volume_name

    _run(["docker", "rm", "-f", container_name], capture=False)
    _run(["docker", "volume", "rm", "-f", volume_name], capture=False)

    result = _run([
        "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:5432",
        "-e", "POSTGRES_USER=postgres",
        "-e", "POSTGRES_PASSWORD=postgres",
        "-e", "POSTGRES_DB=postgres",
        "-v", f"{volume_name}:/var/lib/postgresql/data",
        DEFAULT_IMAGE,
    ])
    if result.returncode != 0:
        raise RuntimeError(f"No se pudo arrancar PostgreSQL con Docker: {result.stderr.strip() or result.stdout.strip()}")

    os.environ["PGSERVER_CONTAINER"] = container_name
    deadline = time.time() + 90
    while time.time() < deadline:
        r = _run(["docker", "exec", container_name, "pg_isready", "-U", "postgres", "-d", "postgres"])
        if r.returncode == 0:
            return Server(data_dir=data_dir, port=port, container_name=container_name, image=DEFAULT_IMAGE)
        time.sleep(2)

    logs = _run(["docker", "logs", container_name], capture=True)
    raise RuntimeError(
        "PostgreSQL no quedó listo en el tiempo esperado.\n"
        f"last logs:\n{logs.stdout[-3000:]}\n{logs.stderr[-3000:]}"
    )
