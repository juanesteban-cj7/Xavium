"""
register.py
Lógica de registro de nuevos estudiantes y verificación de correo
institucional mediante token.

Flujo:
1. register_user() valida los datos, crea el usuario en estado
   "pendiente_verificacion" y genera un token de verificación.
2. send_verification_email() (o el mecanismo que se conecte después)
   entrega ese token al estudiante por correo.
3. verify_email() confirma el token y activa la cuenta.

Nota sobre envío real de correos: sin presupuesto para un servicio
de email transaccional, este módulo deja la función de "envío" como
un punto de integración (envía por SMTP si está configurado en
config/.env; si no, registra el token para pruebas/desarrollo en
vez de fallar).
"""

import secrets
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional


def _utcnow_naive() -> datetime:
    """UTC naive, consistente con database/models.py (ver nota allí)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from sqlalchemy.orm import Session

from config import settings
from database.models import EstadoCuenta, Facultad, Usuario
from security.audit_log import EventoSeguridad, log_event
from security.encryption_utils import encrypt_text, hash_lookup, hash_token
from security.input_validation import (
    ValidationError,
    validate_edad,
    validate_facultad_nombre,
    validate_institutional_email,
    validate_nombre,
    validate_password_strength,
    validate_passwords_match,
)
from auth.password_utils import hash_password


@dataclass
class ResultadoRegistro:
    usuario_id: str
    correo: str
    token_verificacion: str  # se entrega solo aquí; nunca se guarda en crudo


@dataclass
class ResultadoReenvioVerificacion:
    correo: str
    token_verificacion: str  # se entrega solo aquí; nunca se guarda en crudo


def _generar_token_verificacion() -> str:
    return secrets.token_urlsafe(24)


def register_user(
    session_db: Session,
    nombre: str,
    edad,
    correo_institucional: str,
    facultad_nombre: str,
    password: str,
    password_confirm: str,
    ip_origen: Optional[str] = None,
) -> ResultadoRegistro:
    """
    Registra un nuevo estudiante. Lanza ValidationError (mensaje seguro
    para mostrar en la GUI) si algún dato no es válido o el correo ya
    está registrado.
    """
    # 1. Validar todos los campos (nunca confiar en el input de la GUI)
    nombre_limpio = validate_nombre(nombre)
    edad_valida = validate_edad(edad)
    correo_valido = validate_institutional_email(correo_institucional)
    facultad_nombre_limpio = validate_facultad_nombre(facultad_nombre)
    validate_password_strength(password)
    validate_passwords_match(password, password_confirm)

    # 2. Verificar que el correo no esté ya registrado
    existente = (
        session_db.query(Usuario).filter(Usuario.correo == correo_valido).first()
    )
    if existente is not None:
        log_event(
            session_db,
            EventoSeguridad.REGISTRO_FALLIDO,
            ip_origen=ip_origen,
            detalle="Intento de registro con correo ya existente",
        )
        raise ValidationError("Ya existe una cuenta registrada con ese correo.")

    # 3. Resolver facultad (debe existir en el catálogo)
    facultad = (
        session_db.query(Facultad)
        .filter(Facultad.nombre == facultad_nombre_limpio)
        .first()
    )
    if facultad is None:
        raise ValidationError("La facultad seleccionada no es válida.")

    # 4. Generar token de verificación (se guarda solo su hash)
    token_verificacion = _generar_token_verificacion()
    expiracion_token = _utcnow_naive() + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS
    )

    # 5. Crear usuario
    nuevo_usuario = Usuario(
        nombre=nombre_limpio,
        edad=edad_valida,
        correo=correo_valido,
        correo_hash=hash_lookup(correo_valido),
        correo_cifrado=encrypt_text(correo_valido),
        facultad_id=facultad.id,
        password_hash=hash_password(password),
        estado_cuenta=EstadoCuenta.PENDIENTE_VERIFICACION,
        token_verificacion_hash=hash_token(token_verificacion),
        token_verificacion_expira=expiracion_token,
    )
    session_db.add(nuevo_usuario)
    session_db.flush()  # para obtener nuevo_usuario.id antes del log

    log_event(
        session_db,
        EventoSeguridad.REGISTRO_EXITOSO,
        usuario_id=nuevo_usuario.id,
        ip_origen=ip_origen,
        detalle=f"Registro creado, pendiente de verificación: {correo_valido}",
    )

    return ResultadoRegistro(
        usuario_id=nuevo_usuario.id,
        correo=correo_valido,
        token_verificacion=token_verificacion,
    )


def verify_email(session_db: Session, correo_institucional: str, token: str) -> bool:
    """
    Confirma el token de verificación enviado al correo y activa la
    cuenta (estado_cuenta -> ACTIVO). Devuelve True si se verificó.
    """
    usuario = (
        session_db.query(Usuario).filter(Usuario.correo == correo_institucional.strip().lower()).first()
    )

    if usuario is None:
        raise ValidationError("No existe una cuenta con ese correo.")

    if usuario.estado_cuenta == EstadoCuenta.ACTIVO:
        return True  # ya estaba verificada, no es un error

    if usuario.token_verificacion_hash != hash_token(token):
        raise ValidationError("El código de verificación no es válido.")

    if (
        usuario.token_verificacion_expira is None
        or usuario.token_verificacion_expira < _utcnow_naive()
    ):
        raise ValidationError(
            "El código de verificación expiró. Solicita uno nuevo."
        )

    usuario.estado_cuenta = EstadoCuenta.ACTIVO
    usuario.token_verificacion_hash = None
    usuario.token_verificacion_expira = None

    log_event(
        session_db,
        EventoSeguridad.EMAIL_VERIFICADO,
        usuario_id=usuario.id,
        detalle="Cuenta activada tras verificación de correo",
    )

    return True


def resend_verification_code(
    session_db: Session, correo_institucional: str
) -> ResultadoReenvioVerificacion:
    """Genera un nuevo código para una cuenta que aún no está verificada."""
    correo_valido = validate_institutional_email(correo_institucional)
    usuario = (
        session_db.query(Usuario).filter(Usuario.correo == correo_valido).first()
    )

    if usuario is None:
        raise ValidationError("No existe una cuenta pendiente con ese correo.")

    if usuario.estado_cuenta == EstadoCuenta.ACTIVO:
        raise ValidationError("Esta cuenta ya está verificada. Puedes iniciar sesión.")

    if usuario.estado_cuenta == EstadoCuenta.SUSPENDIDO:
        raise ValidationError("Esta cuenta se encuentra suspendida.")

    token_verificacion = _generar_token_verificacion()
    usuario.token_verificacion_hash = hash_token(token_verificacion)
    usuario.token_verificacion_expira = _utcnow_naive() + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS
    )

    return ResultadoReenvioVerificacion(
        correo=correo_valido,
        token_verificacion=token_verificacion,
    )


def send_verification_email(correo_destino: str, token: str) -> bool:
    """
    Envía el correo de verificación si SMTP está configurado en
    config/.env. Si no está configurado (caso más probable dado el
    presupuesto $0 del proyecto), no falla: registra el token para
    que el equipo de desarrollo pueda probar el flujo manualmente.

    Devuelve True si el correo se envió realmente, False si solo
    quedó registrado localmente (modo desarrollo).
    """
    if not settings.SMTP_CONFIGURADO:
        print(
            f"[DEV] SMTP no configurado. Token de verificación para "
            f"{correo_destino}: {token}"
        )
        return False

    mensaje = EmailMessage()
    mensaje["Subject"] = "Verifica tu cuenta de Xavium"
    mensaje["From"] = settings.SMTP_FROM
    mensaje["To"] = correo_destino
    mensaje.set_content(
        f"Hola,\n\nTu código de verificación de Xavium es:\n\n{token}\n\n"
        f"Este código expira en {settings.EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS} horas."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as servidor:
        servidor.starttls()
        servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        servidor.send_message(mensaje)

    return True
