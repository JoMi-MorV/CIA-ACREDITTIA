"""Cifrado, creación, inspección y restauración controlada de respaldos."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tarfile
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import psycopg
from cryptography.exceptions import InvalidTag
from psycopg import sql as pgsql
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.engine import URL, make_url

from ..config import settings

_MAGIC = b"ACRBACKUP1"
_CHUNK_SIZE = 1024 * 1024
_FORMAT = "acredittia-backup-v1"


class BackupError(RuntimeError):
    """Error operacional seguro para presentar al administrador."""


def _key() -> bytes:
    encoded = os.environ.get("BACKUP_ENCRYPTION_KEY", "")
    try:
        key = base64.b64decode(encoded.encode("ascii"), altchars=b"-_", validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise BackupError("BACKUP_ENCRYPTION_KEY no está configurada como clave válida") from exc
    if len(key) != 32:
        raise BackupError("BACKUP_ENCRYPTION_KEY debe ser una clave URL-safe base64 de 32 bytes")
    return key


def backup_configured() -> bool:
    if (settings.storage_backend != "local" or not settings.backup_database_url
            or not all(shutil.which(command)
                       for command in ("pg_dump", "pg_restore"))):
        return False
    try:
        _key()
    except BackupError:
        return False
    return True


def _backup_root() -> Path:
    root = Path(settings.backups_dir).expanduser()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise BackupError("El destino de respaldos debe ser un directorio local seguro")
    return root.resolve()


def _database_url() -> URL:
    return make_url(settings.backup_database_url or settings.database_url)


def _same_database_target(first: URL, second: URL) -> bool:
    return (
        (first.host or "").casefold(),
        first.port or 5432,
        first.database,
    ) == (
        (second.host or "").casefold(),
        second.port or 5432,
        second.database,
    )


def _pg_environment(url: URL) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE",
                "PGSSLMODE", "PGOPTIONS"):
        env.pop(key, None)
    if url.host:
        env["PGHOST"] = url.host
    if url.port:
        env["PGPORT"] = str(url.port)
    if url.username:
        env["PGUSER"] = url.username
    if url.password:
        env["PGPASSWORD"] = url.password
    if url.database:
        env["PGDATABASE"] = url.database
    if url.query.get("sslmode"):
        env["PGSSLMODE"] = str(url.query["sslmode"])
    return env


def _pg_args(url: URL) -> list[str]:
    args: list[str] = []
    if url.host:
        args += ["--host", url.host]
    if url.port:
        args += ["--port", str(url.port)]
    if url.username:
        args += ["--username", url.username]
    if url.database:
        args += ["--dbname", url.database]
    return args


def _run(command: list[str], env: dict[str, str], timeout: int = 3600) -> str:
    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True,
                                timeout=timeout, check=False)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        raise BackupError(f"No se pudo completar la operación PostgreSQL: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout or "sin detalle")[-2000:]
        raise BackupError(f"Falló la operación PostgreSQL: {detail}")
    return result.stdout


def _encrypt(source: Path, destination: Path) -> None:
    aes = AESGCM(_key())
    prefix = os.urandom(8)
    with source.open("rb") as src, destination.open("xb") as dst:
        os.chmod(destination, 0o600)
        dst.write(_MAGIC + prefix)
        index = 0
        while chunk := src.read(_CHUNK_SIZE):
            nonce = prefix + struct.pack(">I", index)
            encrypted = aes.encrypt(nonce, chunk, _MAGIC + struct.pack(">I", index))
            dst.write(struct.pack(">I", len(encrypted)))
            dst.write(encrypted)
            index += 1
            if index >= 2**32:
                raise BackupError("El respaldo excede el tamaño máximo admitido")
        nonce = prefix + struct.pack(">I", index)
        final = aes.encrypt(nonce, b"", _MAGIC + struct.pack(">I", index))
        dst.write(struct.pack(">I", len(final)))
        dst.write(final)


def _decrypt(source: Path, destination: Path) -> None:
    aes = AESGCM(_key())
    with source.open("rb") as src, destination.open("xb") as dst:
        header = src.read(len(_MAGIC) + 8)
        if len(header) != len(_MAGIC) + 8 or not header.startswith(_MAGIC):
            raise BackupError("El archivo no es un respaldo Acredittia válido")
        prefix = header[len(_MAGIC):]
        index = 0
        final_seen = False
        while True:
            raw_size = src.read(4)
            if not raw_size:
                break
            if len(raw_size) != 4:
                raise BackupError("Respaldo incompleto o corrupto")
            size = struct.unpack(">I", raw_size)[0]
            if size < 16 or size > _CHUNK_SIZE + 16:
                raise BackupError("Respaldo contiene un bloque inválido")
            encrypted = src.read(size)
            if len(encrypted) != size:
                raise BackupError("Respaldo incompleto o corrupto")
            nonce = prefix + struct.pack(">I", index)
            try:
                chunk = aes.decrypt(nonce, encrypted,
                                    _MAGIC + struct.pack(">I", index))
            except InvalidTag as exc:
                raise BackupError("No se pudo autenticar el respaldo; revise la clave y su integridad") from exc
            if not chunk:
                final_seen = True
                if src.read(1):
                    raise BackupError("El respaldo contiene datos después del bloque final")
                break
            dst.write(chunk)
            index += 1
            if index >= 2**32:
                raise BackupError("El respaldo excede el tamaño máximo admitido")
        if not final_seen:
            raise BackupError("Respaldo incompleto: falta el bloque de cierre autenticado")


def _add_uploads(archive: tarfile.TarFile) -> int:
    root = Path(settings.storage_dir).resolve()
    count = 0
    directory = tarfile.TarInfo("uploads")
    directory.type = tarfile.DIRTYPE
    archive.addfile(directory)
    if not root.exists():
        return count
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current)
        for name in list(dirs):
            item = base / name
            if item.is_symlink():
                raise BackupError("El almacenamiento contiene enlaces simbólicos; no se puede respaldar con seguridad")
        for name in files:
            item = base / name
            if item.is_symlink() or not item.is_file():
                raise BackupError("El almacenamiento contiene un elemento no regular; respaldo cancelado")
            archive.add(item, arcname=str(PurePosixPath(
                "uploads", item.relative_to(root).as_posix())),
                        recursive=False)
            count += 1
    return count


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(*, reason: str = "programado") -> dict:
    """Crea un pg_dump + copia local de archivos y cifra el paquete completo."""
    if settings.storage_backend != "local":
        raise BackupError("El respaldo integrado solo admite STORAGE_BACKEND=local")
    _key()
    root = _backup_root()
    backup_id = uuid.uuid4().hex
    created = datetime.now(timezone.utc)
    filename = f"acredittia-{created:%Y%m%dT%H%M%SZ}-{backup_id[:8]}.acb"
    encrypted_path = root / filename
    temporary_path = root / f".{backup_id}.partial"
    with tempfile.TemporaryDirectory(prefix="acredittia-backup-") as workdir:
        work = Path(workdir)
        dump_path = work / "database.dump"
        url = _database_url()
        if not _same_database_target(url, make_url(settings.database_url)):
            raise BackupError(
                "BACKUP_DATABASE_URL debe apuntar a la misma base activa de DATABASE_URL")
        with dump_path.open("wb") as dump:
            try:
                result = subprocess.run(
                    ["pg_dump", "--format=custom", "--no-owner", "--no-acl",
                     *_pg_args(url)],
                    env=_pg_environment(url), stdout=dump, stderr=subprocess.PIPE,
                    check=False, timeout=3600)
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
                raise BackupError(f"No se pudo ejecutar pg_dump: {exc}") from exc
        if result.returncode:
            raise BackupError(f"No se pudo respaldar PostgreSQL: {result.stderr.decode(errors='replace')[-2000:]}")
        manifest = {
            "format": _FORMAT,
            "id": backup_id,
            "created_at": created.isoformat(),
            "schema_version": settings.schema_version_esperada,
            "reason": reason[:120],
            "database_dump_sha256": _sha256(dump_path),
        }
        manifest_path = work / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        archive_path = work / "package.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(dump_path, arcname="database.dump")
            archive.add(manifest_path, arcname="manifest.json")
            file_count = _add_uploads(archive)
        try:
            _encrypt(archive_path, temporary_path)
            os.replace(temporary_path, encrypted_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
    summary = {
        "id": backup_id, "file": filename, "created_at": created.isoformat(),
        "schema_version": settings.schema_version_esperada,
        "size_bytes": encrypted_path.stat().st_size,
        "files": file_count, "status": "ready", "reason": reason[:120],
    }
    sidecar = root / f"{backup_id}.json"
    sidecar_tmp = root / f".{backup_id}.json.partial"
    try:
        sidecar_tmp.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        os.chmod(sidecar_tmp, 0o600)
        os.replace(sidecar_tmp, sidecar)
    except Exception:
        sidecar_tmp.unlink(missing_ok=True)
        encrypted_path.unlink(missing_ok=True)
        raise
    _prune_backups(root, int(settings.backup_retention_count))
    return summary


def _prune_backups(root: Path, keep: int) -> None:
    if keep < 1:
        raise BackupError("La retención debe conservar al menos un respaldo")
    sidecars = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for sidecar in sidecars[keep:]:
        try:
            info = json.loads(sidecar.read_text(encoding="utf-8"))
            filename = info.get("file")
            if not isinstance(filename, str) or Path(filename).name != filename:
                raise BackupError("Metadatos de respaldo inválidos; no se eliminaron archivos")
            data = root / filename
            if data.exists():
                data.unlink()
            sidecar.unlink()
        except (OSError, ValueError, KeyError) as exc:
            raise BackupError(f"No se pudo aplicar la retención de respaldos: {exc}") from exc


def list_backups() -> list[dict]:
    root = _backup_root()
    rows = []
    for sidecar in root.glob("*.json"):
        try:
            item = json.loads(sidecar.read_text(encoding="utf-8"))
            file_path = root / item["file"]
            if file_path.is_file() and file_path.parent == root:
                rows.append(item)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(rows, key=lambda x: x["created_at"], reverse=True)


def backup_path(backup_id: str) -> Path:
    if not re_full_id(backup_id):
        raise BackupError("Identificador de respaldo inválido")
    root = _backup_root()
    sidecar = root / f"{backup_id}.json"
    try:
        info = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BackupError("No existe el respaldo solicitado") from exc
    filename = info.get("file")
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise BackupError("Metadatos de respaldo inválidos")
    path = root / filename
    if path.parent != root or not path.is_file():
        raise BackupError("No existe el archivo de respaldo")
    return path


def re_full_id(value: str) -> bool:
    return len(value) == 32 and all(ch in "0123456789abcdef" for ch in value)


def verify_backup(backup_id: str) -> dict:
    path = backup_path(backup_id)
    with tempfile.TemporaryDirectory(prefix="acredittia-verify-") as workdir:
        archive_path = Path(workdir) / "package.tar.gz"
        _decrypt(path, archive_path)
        try:
            with tarfile.open(archive_path, "r:gz") as archive:
                names = {member.name for member in archive.getmembers()}
                manifest_file = archive.extractfile("manifest.json")
                if manifest_file is None or "database.dump" not in names:
                    raise BackupError("El paquete no contiene manifiesto o dump de PostgreSQL")
                manifest = json.load(manifest_file)
                dump = archive.extractfile("database.dump")
                if dump is None:
                    raise BackupError("El paquete no contiene el dump de la base")
                digest_builder = hashlib.sha256()
                for chunk in iter(lambda: dump.read(_CHUNK_SIZE), b""):
                    digest_builder.update(chunk)
                digest = digest_builder.hexdigest()
                if digest != manifest.get("database_dump_sha256"):
                    raise BackupError("El dump no coincide con su huella de integridad")
                for member in archive.getmembers():
                    _safe_member(member)
        except (tarfile.TarError, OSError, json.JSONDecodeError) as exc:
            raise BackupError(f"El paquete está dañado: {exc}") from exc
    return {"id": backup_id, "valid": True,
            "schema_version": manifest.get("schema_version"),
            "created_at": manifest.get("created_at")}


def _safe_member(member: tarfile.TarInfo) -> None:
    path = PurePosixPath(member.name)
    if ("\\" in member.name or path.is_absolute() or ".." in path.parts
            or member.issym() or member.islnk()):
        raise BackupError("El paquete contiene una ruta no segura")
    if not (member.isfile() or member.isdir()):
        raise BackupError("El paquete contiene un tipo de archivo no permitido")
    if member.name not in ("database.dump", "manifest.json", "uploads"):
        if not member.name.startswith("uploads/"):
            raise BackupError("El paquete contiene un elemento fuera del alcance permitido")


def _maintenance_url() -> URL:
    raw_url = settings.backup_restore_database_url
    if not raw_url and settings.app_env != "production":
        raw_url = settings.backup_database_url
    if not raw_url:
        raise BackupError(
            "BACKUP_RESTORE_DATABASE_URL de mantenimiento no está configurada")
    return make_url(raw_url)


def _connect_maintenance():
    url = _maintenance_url().set(database="postgres")
    return psycopg.connect(url.render_as_string(hide_password=False), autocommit=True)


def _database_name(url: URL) -> str:
    name = url.database
    if not name or not name.replace("_", "").isalnum():
        raise BackupError("Nombre de base de datos no válido para restauración")
    return name


def _restore_uploads_from_backup(backup_id: str) -> None:
    with tempfile.TemporaryDirectory(prefix="acredittia-files-rollback-") as workdir:
        root = Path(workdir)
        package = root / "package.tar.gz"
        stage = root / "uploads"
        _decrypt(backup_path(backup_id), package)
        _extract_uploads(package, stage)
        _replace_uploads(stage)


def _restore_database(dump_path: Path, target_name: str) -> None:
    url = _maintenance_url().set(database=target_name)
    role = settings.backup_restore_role
    command = ["pg_restore", "--exit-on-error", "--no-owner", "--no-acl"]
    if role:
        command += ["--role", role]
    command += [*_pg_args(url), str(dump_path)]
    _run(command, _pg_environment(url), timeout=7200)


def _check_schema(database: str) -> None:
    url = _maintenance_url().set(database=database)
    try:
        with psycopg.connect(url.render_as_string(hide_password=False)) as conn:
            row = conn.execute(
                "SELECT max(version) FROM app_schema_migrations").fetchone()
    except psycopg.Error as exc:
        raise BackupError(f"No se pudo comprobar el esquema restaurado: {exc}") from exc
    if not row or row[0] != settings.schema_version_esperada:
        raise BackupError(
            f"El respaldo usa esquema {row[0] if row else 'desconocido'}; "
            f"se requiere {settings.schema_version_esperada}")


def _extract_uploads(archive_path: Path, stage: Path) -> None:
    stage.mkdir(mode=0o700)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            _safe_member(member)
            if member.name == "uploads":
                continue
            if not member.name.startswith("uploads/"):
                continue
            relative = PurePosixPath(member.name).relative_to("uploads")
            target = stage.joinpath(*relative.parts)
            if not target.resolve().is_relative_to(stage.resolve()):
                raise BackupError("Ruta de archivo fuera del destino de restauración")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = archive.extractfile(member)
                if stream is None:
                    raise BackupError("No se pudo leer un archivo del respaldo")
                with target.open("xb") as output:
                    shutil.copyfileobj(stream, output)


def _replace_uploads(stage: Path) -> None:
    target = Path(settings.storage_dir).resolve()
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    for child in target.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)
    for child in stage.iterdir():
        destination = target / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)


def restore_backup(backup_id: str, *, confirmation: str) -> dict:
    """Verifica en una BD aislada y luego sustituye la BD activa."""
    if confirmation != f"RESTAURAR {backup_id}":
        raise BackupError("La confirmación no coincide con el identificador de respaldo")
    if settings.storage_backend != "local":
        raise BackupError("La restauración integrada solo admite STORAGE_BACKEND=local")
    if settings.app_env == "production" and not settings.backup_restore_database_url:
        raise BackupError(
            "BACKUP_RESTORE_DATABASE_URL debe configurarse antes de restaurar en producción")
    if settings.app_env == "production" and not settings.backup_restore_role:
        raise BackupError(
            "BACKUP_RESTORE_ROLE debe configurarse antes de restaurar en producción")
    verify_backup(backup_id)
    encrypted = backup_path(backup_id)
    active_name = _database_name(make_url(settings.database_url))
    active_url = make_url(settings.database_url)
    maintenance_url = _maintenance_url()
    if not _same_database_target(active_url, maintenance_url):
        raise BackupError(
            "BACKUP_DATABASE_URL debe apuntar a la misma base activa que DATABASE_URL")
    restore_name = f"acr_restore_{uuid.uuid4().hex[:12]}"
    old_name = f"acr_pre_restore_{uuid.uuid4().hex[:12]}"
    root = _backup_root()
    with tempfile.TemporaryDirectory(prefix="acredittia-restore-") as workdir:
        work = Path(workdir)
        protected_backup = work / "selected.acb"
        shutil.copy2(encrypted, protected_backup)
        pre_restore = create_backup(reason=f"pre-restauración de {backup_id}")
        archive_path = work / "package.tar.gz"
        dump_path = work / "database.dump"
        upload_stage = work / "uploads"
        _decrypt(protected_backup, archive_path)
        with tarfile.open(archive_path, "r:gz") as archive:
            dump_member = archive.extractfile("database.dump")
            if dump_member is None:
                raise BackupError("No se encontró el dump de PostgreSQL")
            with dump_path.open("xb") as out:
                shutil.copyfileobj(dump_member, out)
        _extract_uploads(archive_path, upload_stage)

        with _connect_maintenance() as conn:
            role = settings.backup_restore_role
            if role:
                conn.execute(pgsql.SQL("CREATE DATABASE {} OWNER {}").format(
                    pgsql.Identifier(restore_name), pgsql.Identifier(role)))
            else:
                conn.execute(pgsql.SQL("CREATE DATABASE {}").format(
                    pgsql.Identifier(restore_name)))
        try:
            _restore_database(dump_path, restore_name)
            _check_schema(restore_name)
            with _connect_maintenance() as conn:
                conn.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()", (active_name,))
                conn.execute(
                    f"ALTER DATABASE \"{active_name}\" WITH ALLOW_CONNECTIONS false")
                conn.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()", (active_name,))
                conn.execute(f'ALTER DATABASE "{active_name}" RENAME TO "{old_name}"')
                try:
                    conn.execute(
                        f'ALTER DATABASE "{restore_name}" RENAME TO "{active_name}"')
                except Exception:
                    conn.execute(f'ALTER DATABASE "{old_name}" RENAME TO "{active_name}"')
                    conn.execute(
                        f"ALTER DATABASE \"{active_name}\" WITH ALLOW_CONNECTIONS true")
                    raise
            try:
                _replace_uploads(upload_stage)
            except Exception:
                file_rollback_error = None
                try:
                    _restore_uploads_from_backup(pre_restore["id"])
                except Exception as rollback_exc:
                    file_rollback_error = rollback_exc
                with _connect_maintenance() as conn:
                    conn.execute(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = %s AND pid <> pg_backend_pid()", (active_name,))
                    conn.execute(f'ALTER DATABASE "{active_name}" RENAME TO "{restore_name}"')
                    conn.execute(f'ALTER DATABASE "{old_name}" RENAME TO "{active_name}"')
                    conn.execute(
                        f"ALTER DATABASE \"{active_name}\" WITH ALLOW_CONNECTIONS true")
                if file_rollback_error:
                    raise BackupError(
                        f"Falló la restauración de archivos y también su reversión; "
                        f"conserve el respaldo previo {pre_restore['id']}: "
                        f"{file_rollback_error}")
                raise
            try:
                with _connect_maintenance() as conn:
                    conn.execute(f'DROP DATABASE "{old_name}"')
            except Exception as exc:
                raise BackupError(
                    f"Restauración completada; la base anterior {old_name} quedó preservada "
                    f"y requiere limpieza: {exc}") from exc
        except Exception:
            with _connect_maintenance() as conn:
                exists = conn.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (restore_name,)).fetchone()
                if exists:
                    conn.execute(f'DROP DATABASE "{restore_name}"')
            raise
    return {"restored_backup_id": backup_id, "pre_restore_backup_id": pre_restore["id"],
            "schema_version": settings.schema_version_esperada,
            "status": "restored"}
