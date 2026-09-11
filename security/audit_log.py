"""
audit_log.py
Registro de auditoría para eventos de seguridad relevantes:
logins fallidos/exitosos, registros, cambios de contraseña, etc.

No reemplaza un sistema de monitoreo en producción, pero deja
trazabilidad mínima para investigar incidentes.
"""

from sqlalchemy.orm import Session

from database.models import LogSeguridad


# Tipos de evento estandarizados (evita strings "mágicos" dispersos en el código)
class EventoSeguridad:
    REGISTRO_EXITOSO = "registro_exitoso"
    REGISTRO_FALLIDO = "registro_fallido"
    EMAIL_VERIFICADO = "email_verificado"
    LOGIN_EXITOSO = "login_exitoso"
    LOGIN_FALLIDO = "login_fallido"
    CUENTA_BLOQUEADA = "cuenta_bloqueada"
    LOGOUT = "logout"
    CAMBIO_PASSWORD = "cambio_password"


def log_event(
    session: Session,
    tipo_evento: str,
    usuario_id: str = None,
    ip_origen: str = None,
    detalle: str = None,
) -> None:
    """
    Registra un evento de seguridad en la tabla logs_seguridad.

    No hace commit por sí mismo si se usa dentro de un `with get_session()`
    (el commit ocurre al salir del context manager). Si se usa con una
    sesión manual, recuerda hacer session.commit() después.
    """
    entry = LogSeguridad(
        usuario_id=usuario_id,
        tipo_evento=tipo_evento,
        ip_origen=ip_origen,
        detalle=detalle,
    )
    session.add(entry)
