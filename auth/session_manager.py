"""
session_manager.py
Manejo de sesión activa mediante tokens.

El token "en crudo" solo existe en memoria (se le entrega una vez al
cliente tras el login); en la base de datos solo se guarda su hash
(SHA-256), igual que se hace con contraseñas pero sin necesidad de
bcrypt (los tokens ya son aleatorios de alta entropía).
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


def _utcnow_naive() -> datetime:
    """UTC naive, consistente con database/models.py (ver nota allí)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy.orm import Session

from config import settings
from database.models import Sesion
from security.encryption_utils import hash_token


def generate_raw_token() -> str:
    """Genera un token de sesión aleatorio y criptográficamente seguro."""
    return secrets.token_urlsafe(32)


def create_session(session_db: Session, usuario_id: str, ip_origen: str = None) -> str:
    """
    Crea una nueva sesión para el usuario y devuelve el token en crudo
    (el único momento en que existe fuera de la memoria del cliente).
    """
    raw_token = generate_raw_token()
    expiracion = _utcnow_naive() + timedelta(
        hours=settings.SESSION_EXPIRATION_HOURS
    )

    nueva_sesion = Sesion(
        usuario_id=usuario_id,
        token_hash=hash_token(raw_token),
        fecha_expiracion=expiracion,
        ip_origen=ip_origen,
        activa=True,
    )
    session_db.add(nueva_sesion)
    session_db.flush()  # asegura que quede persistida antes de devolver el token

    return raw_token


def validate_session(session_db: Session, raw_token: str) -> Optional[str]:
    """
    Valida un token de sesión. Devuelve el usuario_id si es válida y
    no ha expirado, o None si no es válida (token incorrecto, expirado
    o cerrada mediante logout).
    """
    token_hash = hash_token(raw_token)
    sesion = (
        session_db.query(Sesion)
        .filter(Sesion.token_hash == token_hash, Sesion.activa == True)  # noqa: E712
        .first()
    )

    if sesion is None:
        return None

    if sesion.fecha_expiracion < _utcnow_naive():
        sesion.activa = False
        return None

    return sesion.usuario_id


def invalidate_session(session_db: Session, raw_token: str) -> bool:
    """Invalida una sesión (logout). Devuelve True si existía y se cerró."""
    token_hash = hash_token(raw_token)
    sesion = session_db.query(Sesion).filter(Sesion.token_hash == token_hash).first()

    if sesion is None:
        return False

    sesion.activa = False
    return True


def cleanup_expired_sessions(session_db: Session) -> int:
    """Marca como inactivas todas las sesiones ya expiradas. Devuelve cuántas."""
    ahora = _utcnow_naive()
    expiradas = (
        session_db.query(Sesion)
        .filter(Sesion.activa == True, Sesion.fecha_expiracion < ahora)  # noqa: E712
        .all()
    )
    for sesion in expiradas:
        sesion.activa = False
    return len(expiradas)
