"""
encryption_utils.py
Funciones de cifrado/descifrado general y hashing determinístico
usadas en toda la aplicación (correo, mensajes de chat, etc.).

Cifrado: Fernet (AES-128 en modo CBC + HMAC para integridad), de la
librería `cryptography`. Es cifrado simétrico: la misma clave cifra
y descifra. Adecuado para "cifrado en reposo" de campos sensibles.

Importante (limitación honesta): esto NO es cifrado extremo a extremo
(E2EE) real. El servidor/aplicación tiene la clave y puede descifrar.
Protege contra "alguien robó la base de datos", no contra "el propio
sistema fue comprometido en ejecución".
"""

import hmac
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config import settings

_fernet = Fernet(settings.FERNET_KEY.encode())


class DescifradoError(Exception):
    """Se lanza cuando un valor cifrado no pudo descifrarse (token inválido o corrupto)."""


def encrypt_text(plain_text: str) -> str:
    """Cifra una cadena de texto y devuelve el resultado en formato string (base64)."""
    if plain_text is None:
        raise ValueError("No se puede cifrar un valor None")
    token = _fernet.encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(token: str) -> str:
    """Descifra una cadena previamente cifrada con encrypt_text()."""
    try:
        plain_bytes = _fernet.decrypt(token.encode("utf-8"))
        return plain_bytes.decode("utf-8")
    except InvalidToken as exc:
        raise DescifradoError("No fue posible descifrar el valor proporcionado") from exc


def hash_lookup(value: str) -> str:
    """
    Genera un hash determinístico (HMAC-SHA256) de un valor, usado como
    índice de búsqueda sin exponer el valor original en texto plano.

    Se usa, por ejemplo, para poder buscar un usuario por correo
    institucional sin guardar el correo en texto plano en ese campo.
    """
    normalized = value.strip().lower()
    return hmac.new(
        settings.HMAC_SECRET.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_token(raw_token: str) -> str:
    """
    Hashea tokens de sesión/verificación (SHA-256 simple, sin salt) antes
    de guardarlos en BD. No se usa bcrypt aquí porque los tokens ya son
    aleatorios de alta entropía (no son contraseñas elegidas por humanos).
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
