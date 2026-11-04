"""Provisiona el primer administrador sin usuarios ni credenciales demo."""
from __future__ import annotations

import os
import sys

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def provision_admin(*, email: str, password: str, name: str) -> str:
    if settings.app_env == "production" and settings.seed_demo_enabled:
        raise RuntimeError("No se pueden habilitar semillas demo en producción")
    if len(password) < 8 or not any(char.isupper() for char in password) or not any(char.isdigit() for char in password):
        raise RuntimeError("La contraseña debe tener 8 caracteres, una mayúscula y un dígito")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email.strip().lower()))
        if existing:
            return "existing"
        db.add(User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            role="admin",
            company_id=None,
            nombre=name.strip(),
            activo=True,
            status="approved",
        ))
        db.commit()
        return "created"


def main() -> int:
    email = os.environ.get("INITIAL_ADMIN_EMAIL", "").strip()
    password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
    name = os.environ.get("INITIAL_ADMIN_NAME", "Administrador inicial").strip()
    if not email or not password:
        print("Configure INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD.", file=sys.stderr)
        return 2
    try:
        result = provision_admin(email=email, password=password, name=name)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Administrador inicial: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
