"""
login.py
Lógica de inicio de sesión: verificación de credenciales, límite de
intentos fallidos (protección contra fuerza bruta) y creación de
sesión activa.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


def _utcnow_naive() -> datetime:
    """UTC naive, consistente con database/models.py (ver nota allí)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy.orm import Session

from config import settings
from database.models import EstadoCuenta, Usuario
from security.audit_log import EventoSeguridad, log_event
from security.input_validation import ValidationError
from auth.password_utils import verify_password
from auth.session_manager import create_session


@dataclass
class ResultadoLogin:
    usuario_id: str
    nombre: str
    token_sesion: str


def _esta_bloqueado(usuario: Usuario) -> bool:
    return (
        usuario.bloqueado_hasta is not None
        and usuario.bloqueado_hasta > _utcnow_naive()
    )


def login_user(
    session_db: Session,
    correo_institucional: str,
    password: str,
    ip_origen: Optional[str] = None,
) -> ResultadoLogin:
    """
    Autentica a un estudiante. Lanza ValidationError con un mensaje
    genérico y seguro en cada caso de fallo (nunca se revela si el
    problema fue "correo no existe" vs "contraseña incorrecta", para
    no facilitar enumeración de cuentas).
    """
    correo_normalizado = correo_institucional.strip().lower()
    usuario = (
        session_db.query(Usuario).filter(Usuario.correo == correo_normalizado).first()
    )

    mensaje_generico = "Correo o contraseña incorrectos."

    if usuario is None:
        log_event(
            session_db,
            EventoSeguridad.LOGIN_FALLIDO,
            ip_origen=ip_origen,
            detalle="Correo no registrado",
        )
        raise ValidationError(mensaje_generico)

    # Cuenta bloqueada temporalmente por demasiados intentos fallidos
    if _esta_bloqueado(usuario):
        log_event(
            session_db,
            EventoSeguridad.LOGIN_FALLIDO,
            usuario_id=usuario.id,
            ip_origen=ip_origen,
            detalle="Intento de login con cuenta bloqueada temporalmente",
        )
        minutos_restantes = int(
            (usuario.bloqueado_hasta - _utcnow_naive()).total_seconds() / 60
        ) + 1
        raise ValidationError(
            f"Cuenta bloqueada temporalmente por múltiples intentos fallidos. "
            f"Intenta de nuevo en {minutos_restantes} minuto(s)."
        )

    # Cuenta aún no verificada
    if usuario.estado_cuenta == EstadoCuenta.PENDIENTE_VERIFICACION:
        raise ValidationError(
            "Debes verificar tu correo institucional antes de iniciar sesión."
        )

    if usuario.estado_cuenta == EstadoCuenta.SUSPENDIDO:
        raise ValidationError("Esta cuenta se encuentra suspendida.")

    # Verificar contraseña
    if not verify_password(password, usuario.password_hash):
        usuario.intentos_fallidos += 1

        if usuario.intentos_fallidos >= settings.MAX_LOGIN_ATTEMPTS:
            usuario.bloqueado_hasta = _utcnow_naive() + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
            usuario.intentos_fallidos = 0
            log_event(
                session_db,
                EventoSeguridad.CUENTA_BLOQUEADA,
                usuario_id=usuario.id,
                ip_origen=ip_origen,
                detalle=f"Bloqueada por {settings.LOGIN_LOCKOUT_MINUTES} minutos",
            )
        else:
            log_event(
                session_db,
                EventoSeguridad.LOGIN_FALLIDO,
                usuario_id=usuario.id,
                ip_origen=ip_origen,
                detalle=f"Intento fallido #{usuario.intentos_fallidos}",
            )

        raise ValidationError(mensaje_generico)

    # Login exitoso: resetear contador de intentos fallidos
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None

    token_sesion = create_session(session_db, usuario.id, ip_origen=ip_origen)

    log_event(
        session_db,
        EventoSeguridad.LOGIN_EXITOSO,
        usuario_id=usuario.id,
        ip_origen=ip_origen,
    )

    return ResultadoLogin(
        usuario_id=usuario.id, nombre=usuario.nombre, token_sesion=token_sesion
    )


def logout_user(session_db: Session, token_sesion: str, usuario_id: Optional[str] = None) -> None:
    from auth.session_manager import invalidate_session

    invalidate_session(session_db, token_sesion)
    log_event(session_db, EventoSeguridad.LOGOUT, usuario_id=usuario_id)
