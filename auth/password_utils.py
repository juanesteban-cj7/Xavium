"""
password_utils.py
Hashing y verificación de contraseñas usando bcrypt.

Nunca se almacena ni se compara la contraseña en texto plano.
bcrypt incluye salt automático por hash, protegiendo contra
ataques de tablas rainbow incluso si la BD se filtra.
"""

import bcrypt

_BCRYPT_ROUNDS = 12  # costo computacional; 12 es un estándar razonable en 2026


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash corrupto o formato inesperado -> tratar como no coincide,
        # nunca lanzar un error que exponga detalles internos al usuario
        return False
