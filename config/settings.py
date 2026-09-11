"""
settings.py
Configuración centralizada de la aplicación Xavium.

Todas las rutas, constantes y valores sensibles se leen desde el
archivo .env (no se deben hardcodear secretos en el código fuente).
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Raíz del proyecto (carpeta university_connect/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables desde config/.env
load_dotenv(BASE_DIR / "config" / ".env")


def _get_env(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(
            f"Falta la variable de entorno obligatoria '{key}'. "
            f"Revisa config/.env (usa config/.env.example como referencia)."
        )
    return value


def _get_env_int(key: str, default: int) -> int:
    return int(os.getenv(key, default))


# --------------------------------------------------------------
# Base de datos
# --------------------------------------------------------------
_raw_db_url = _get_env("DATABASE_URL", "sqlite:///database/xavium.db")

# Si es SQLite con ruta relativa, la anclamos a la raíz del proyecto
# para que funcione sin importar desde dónde se ejecute main.py
if _raw_db_url.startswith("sqlite:///") and not _raw_db_url.startswith("sqlite:////"):
    relative_path = _raw_db_url.replace("sqlite:///", "", 1)
    absolute_path = BASE_DIR / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{absolute_path}"
else:
    DATABASE_URL = _raw_db_url

# --------------------------------------------------------------
# Dominio institucional permitido
# --------------------------------------------------------------
INSTITUTIONAL_EMAIL_DOMAIN = _get_env(
    "INSTITUTIONAL_EMAIL_DOMAIN", "@xavium.edu.co"
).lower()

# --------------------------------------------------------------
# Claves criptográficas
# --------------------------------------------------------------
FERNET_KEY = _get_env("FERNET_KEY")
HMAC_SECRET = _get_env("HMAC_SECRET")
SESSION_SECRET = _get_env("SESSION_SECRET")

# --------------------------------------------------------------
# Políticas de seguridad
# --------------------------------------------------------------
PASSWORD_MIN_LENGTH = _get_env_int("PASSWORD_MIN_LENGTH", 8)
MAX_LOGIN_ATTEMPTS = _get_env_int("MAX_LOGIN_ATTEMPTS", 5)
LOGIN_LOCKOUT_MINUTES = _get_env_int("LOGIN_LOCKOUT_MINUTES", 15)
SESSION_EXPIRATION_HOURS = _get_env_int("SESSION_EXPIRATION_HOURS", 12)
EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS = _get_env_int(
    "EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS", 24
)

# --------------------------------------------------------------
# Configuración SMTP (opcional)
# --------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = _get_env_int("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@xavium.edu.co")

SMTP_CONFIGURADO = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)
