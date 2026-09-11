"""
input_validation.py
Validación y sanitización de todo input proveniente de la GUI.

Nota: el uso de SQLAlchemy con consultas parametrizadas ya previene
inyección SQL a nivel de base de datos. Estas validaciones son una
capa adicional: datos íntegros, rangos razonables y feedback claro
al usuario (sin exponer detalles internos del sistema).
"""

import re

from config import settings

EDAD_MINIMA = 16
EDAD_MAXIMA = 100

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class ValidationError(Exception):
    """Error de validación de input, con mensaje seguro para mostrar al usuario."""


def sanitize_text(value: str, max_length: int = 255) -> str:
    """
    Limpia una cadena de texto: quita espacios sobrantes, elimina
    caracteres de control y limita su longitud máxima.
    """
    if value is None:
        return ""
    cleaned = value.strip()
    # Elimina caracteres de control (excepto espacios normales)
    cleaned = "".join(ch for ch in cleaned if ch.isprintable())
    return cleaned[:max_length]


def validate_nombre(nombre: str) -> str:
    nombre = sanitize_text(nombre, max_length=150)
    if len(nombre) < 2:
        raise ValidationError("El nombre debe tener al menos 2 caracteres.")
    if not re.match(r"^[A-Za-zÀ-ÿ\s'.-]+$", nombre):
        raise ValidationError("El nombre contiene caracteres no permitidos.")
    return nombre


def validate_edad(edad) -> int:
    try:
        edad_int = int(edad)
    except (TypeError, ValueError):
        raise ValidationError("La edad debe ser un número entero.")
    if not (EDAD_MINIMA <= edad_int <= EDAD_MAXIMA):
        raise ValidationError(
            f"La edad debe estar entre {EDAD_MINIMA} y {EDAD_MAXIMA} años."
        )
    return edad_int


def validate_institutional_email(correo: str) -> str:
    """
    Valida formato de correo y que pertenezca al dominio institucional
    configurado (config/settings.py -> INSTITUTIONAL_EMAIL_DOMAIN).
    """
    correo = sanitize_text(correo, max_length=255).lower()

    if not _EMAIL_REGEX.match(correo):
        raise ValidationError("El formato del correo no es válido.")

    if not correo.endswith(settings.INSTITUTIONAL_EMAIL_DOMAIN):
        raise ValidationError(
            f"Debes usar tu correo institucional "
            f"(dominio {settings.INSTITUTIONAL_EMAIL_DOMAIN})."
        )

    return correo


def validate_password_strength(password: str) -> str:
    """
    Valida que la contraseña cumpla una política mínima razonable:
    longitud mínima, al menos una letra y al menos un número.
    """
    if password is None or len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"La contraseña debe tener al menos "
            f"{settings.PASSWORD_MIN_LENGTH} caracteres."
        )
    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("La contraseña debe incluir al menos una letra.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("La contraseña debe incluir al menos un número.")
    return password


def validate_passwords_match(password: str, password_confirm: str) -> None:
    if password != password_confirm:
        raise ValidationError("Las contraseñas no coinciden.")


def validate_facultad_nombre(nombre: str) -> str:
    nombre = sanitize_text(nombre, max_length=150)
    if not nombre or nombre.lower().startswith("selecciona"):
        raise ValidationError("Debes seleccionar una facultad válida.")
    return nombre
