"""
encryption.py
Cifrado de mensajes de chat con una clave simétrica única POR
CONVERSACIÓN (no una sola clave global para todos los chats).

Esquema (envelope encryption):
1. Al crear una conversación, se genera una clave Fernet aleatoria
   ("clave de conversación").
2. Esa clave se cifra con la clave maestra de la app (FERNET_KEY de
   config/.env) y se guarda cifrada en la columna
   Conversacion.clave_cifrada.
3. Cada mensaje se cifra con la clave de conversación (no con la
   clave maestra directamente).

Ventajas sobre usar una sola clave global para todo:
- Si se necesita revocar/rotar el acceso a una conversación puntual,
  no afecta a las demás.
- Es un paso conceptual más cercano a como funcionan los sistemas de
  cifrado de mensajería reales (aunque, como se explicó antes, esto
  sigue sin ser E2EE real: el servidor/app sigue teniendo la clave
  maestra y por lo tanto puede llegar a descifrar cualquier conversación).
"""

from cryptography.fernet import Fernet

from security.encryption_utils import decrypt_text, encrypt_text


def generar_clave_conversacion() -> bytes:
    """Genera una nueva clave Fernet aleatoria para una conversación."""
    return Fernet.generate_key()


def cifrar_clave_conversacion(clave_conversacion: bytes) -> str:
    """
    Cifra la clave de conversación con la clave maestra de la app,
    para poder guardarla en la base de datos de forma segura.
    """
    return encrypt_text(clave_conversacion.decode("utf-8"))


def descifrar_clave_conversacion(clave_cifrada: str) -> bytes:
    """Descifra la clave de conversación usando la clave maestra."""
    return decrypt_text(clave_cifrada).encode("utf-8")


def cifrar_mensaje(texto_plano: str, clave_conversacion: bytes) -> str:
    """Cifra el contenido de un mensaje con la clave de su conversación."""
    fernet_conversacion = Fernet(clave_conversacion)
    return fernet_conversacion.encrypt(texto_plano.encode("utf-8")).decode("utf-8")


def descifrar_mensaje(texto_cifrado: str, clave_conversacion: bytes) -> str:
    """Descifra el contenido de un mensaje con la clave de su conversación."""
    fernet_conversacion = Fernet(clave_conversacion)
    return fernet_conversacion.decrypt(texto_cifrado.encode("utf-8")).decode("utf-8")