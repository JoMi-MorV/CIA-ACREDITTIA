import uuid
import re
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from sqlalchemy.orm import Session

from ..models import Actividad


EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
RUT_RE = re.compile(r"\b\d{1,2}(?:\.?\d{3}){2}-[\dkK]\b")
SECRETO_RE = re.compile(
    r"(?i)\b(password|contraseña|token|secret|api[_ -]?key|credential(?:es)?|vault[_ -]?ref)\b\s*[:=]\s*[^\s,;]+")
SIGNED_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
SENSITIVE_METADATA_KEY_RE = re.compile(
    r"(?i)(password|contrase|token|secret|api[_-]?key|credential|vault[_-]?ref|"
    r"private[_-]?key|authorization|cookie)")
SIGNED_QUERY_KEYS = {
    "sig", "signature", "token", "access_token", "x-amz-signature",
    "x-goog-signature", "se", "sp", "sv", "sr", "skoid", "sktid",
    "skt", "ske", "sks", "skv",
}


def _redactar_url_firmada(match: re.Match[str]) -> str:
    url = match.group(0)
    parsed = urlsplit(url.rstrip(".,);]"))
    if any(key.lower() in SIGNED_QUERY_KEYS
           for key, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        return "[URL firmada redactada]" + url[len(url.rstrip(".,);]")):]
    return url


def minimizar_texto(texto: str) -> str:
    texto = SIGNED_URL_RE.sub(_redactar_url_firmada, texto or "")
    texto = EMAIL_RE.sub("[email redactado]", texto or "")
    texto = RUT_RE.sub("[rut redactado]", texto)
    texto = SECRETO_RE.sub(r"\1=[redactado]", texto)
    return texto


def minimizar_metadata(valor: Any) -> Any:
    if isinstance(valor, str):
        return minimizar_texto(valor)
    if isinstance(valor, dict):
        return {
            clave: "[dato sensible redactado]"
            if SENSITIVE_METADATA_KEY_RE.search(str(clave))
            else minimizar_metadata(valor_hijo)
            for clave, valor_hijo in valor.items()
        }
    if isinstance(valor, list):
        return [minimizar_metadata(elemento) for elemento in valor]
    return valor


def log(
    db: Session, company_id: uuid.UUID | None, tipo: str, modulo: str, descripcion: str,
    user_id: uuid.UUID | None = None, entidad_tipo: str | None = None,
    entidad_id: uuid.UUID | None = None, plataforma: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(Actividad(
        company_id=company_id, user_id=user_id, tipo=tipo, modulo=modulo,
        descripcion=minimizar_texto(descripcion),
        entidad_tipo=entidad_tipo, entidad_id=entidad_id,
        plataforma=plataforma, meta=minimizar_metadata(metadata or {}),
    ))
