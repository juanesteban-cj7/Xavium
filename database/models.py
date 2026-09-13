"""
models.py
Definición de tablas (ORM) de la base de datos de Xavium.

Notas de seguridad relevantes al modelo:
- password_hash: nunca se guarda la contraseña en texto plano (bcrypt).
- correo: correo institucional legible y validado, usado para identificar
    la cuenta.
- correo_hash y correo_cifrado: columnas antiguas conservadas para migrar
    instalaciones existentes; el código nuevo usa correo.
- contenido_cifrado (mensajes): igual filosofía, cifrado en reposo.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database.db_connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """
    Devuelve la hora actual en UTC como datetime 'naive' (sin tzinfo).

    Nota técnica: SQLite no preserva de forma confiable el offset de
    timezone al guardar/releer con SQLAlchemy, lo que provocaba errores
    al comparar fechas (offset-aware vs naive). Para evitarlo, toda la
    app trabaja con UTC naive de forma consistente (se asume siempre
    UTC, nunca hora local).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EstadoCuenta(str, enum.Enum):
    PENDIENTE_VERIFICACION = "pendiente_verificacion"
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"


# --------------------------------------------------------------
# Catálogos
# --------------------------------------------------------------
class Facultad(Base):
    __tablename__ = "facultades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="facultad")


class Interes(Base):
    __tablename__ = "intereses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    categoria = Column(String(100), nullable=True)


# --------------------------------------------------------------
# Usuarios
# --------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=_uuid)

    nombre = Column(String(150), nullable=False)
    edad = Column(Integer, nullable=False)

    correo = Column(String(255), unique=True, nullable=False, index=True)

    # Columnas heredadas de la versión que ocultaba el correo.
    correo_hash = Column(String(64), unique=True, nullable=False, index=True)
    correo_cifrado = Column(Text, nullable=False)

    facultad_id = Column(Integer, ForeignKey("facultades.id"), nullable=False)
    facultad = relationship("Facultad", back_populates="usuarios")

    password_hash = Column(String(255), nullable=False)

    fecha_registro = Column(DateTime(), default=_utcnow, nullable=False)
    estado_cuenta = Column(
        Enum(EstadoCuenta), default=EstadoCuenta.PENDIENTE_VERIFICACION, nullable=False
    )

    # --- Verificación de correo institucional ---
    token_verificacion_hash = Column(String(64), nullable=True)
    token_verificacion_expira = Column(DateTime(), nullable=True)

    # --- Protección contra fuerza bruta (login) ---
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime(), nullable=True)

    intereses = relationship(
        "Interes", secondary="usuario_intereses", backref="usuarios"
    )
    sesiones = relationship("Sesion", back_populates="usuario")


class UsuarioInteres(Base):
    __tablename__ = "usuario_intereses"

    usuario_id = Column(String(36), ForeignKey("usuarios.id"), primary_key=True)
    interes_id = Column(Integer, ForeignKey("intereses.id"), primary_key=True)


# --------------------------------------------------------------
# Chat
# --------------------------------------------------------------
class Conversacion(Base):
    __tablename__ = "conversaciones"

    id = Column(String(36), primary_key=True, default=_uuid)
    usuario1_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    usuario2_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    grupo_id = Column(String(36), ForeignKey("grupos.id"), unique=True, nullable=True)
    fecha_creacion = Column(DateTime(), default=_utcnow, nullable=False)

    # Clave simétrica única de esta conversación (Fernet), a su vez
    # cifrada con la clave maestra de la app (envelope encryption).
    # Así, aunque se filtre la clave maestra, comprometer UNA
    # conversación no expone directamente todas las demás sin antes
    # descifrar cada clave individual — y permite, a futuro, rotar
    # la clave maestra sin tener que re-cifrar todos los mensajes.
    clave_cifrada = Column(Text, nullable=False)

    mensajes = relationship("Mensaje", back_populates="conversacion")


class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(String(36), primary_key=True, default=_uuid)
    conversacion_id = Column(String(36), ForeignKey("conversaciones.id"), nullable=False)
    emisor_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)

    # Contenido cifrado (AES/Fernet) — nunca texto plano en BD
    contenido_cifrado = Column(Text, nullable=False)

    fecha_envio = Column(DateTime(), default=_utcnow, nullable=False)
    leido = Column(Boolean, default=False, nullable=False)

    conversacion = relationship("Conversacion", back_populates="mensajes")



# --------------------------------------------------------------
# Contactos y categorías
# --------------------------------------------------------------
class Contacto(Base):
    __tablename__ = "contactos"

    id = Column(String(36), primary_key=True, default=_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    contacto_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    fecha_agregado = Column(DateTime(), default=_utcnow, nullable=False)


class CategoriaContacto(Base):
    __tablename__ = "categorias_contacto"

    id = Column(String(36), primary_key=True, default=_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    color = Column(String(20), nullable=False, default="#1E5AA8")
    fecha_creacion = Column(DateTime(), default=_utcnow, nullable=False)


class CategoriaContactoMiembro(Base):
    __tablename__ = "categoria_contacto_miembros"

    categoria_id = Column(
        String(36), ForeignKey("categorias_contacto.id"), primary_key=True
    )
    contacto_id = Column(String(36), ForeignKey("contactos.id"), primary_key=True)


# --------------------------------------------------------------
# Grupos
# --------------------------------------------------------------
class Grupo(Base):
    __tablename__ = "grupos"

    id = Column(String(36), primary_key=True, default=_uuid)
    creador_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)
    nombre = Column(String(120), nullable=False)
    fecha_creacion = Column(DateTime(), default=_utcnow, nullable=False)


class GrupoMiembro(Base):
    __tablename__ = "grupo_miembros"

    grupo_id = Column(String(36), ForeignKey("grupos.id"), primary_key=True)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), primary_key=True)
    fecha_ingreso = Column(DateTime(), default=_utcnow, nullable=False)


# --------------------------------------------------------------
# Sesiones
# --------------------------------------------------------------
class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(String(36), primary_key=True, default=_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False)

    # Solo se guarda el HASH del token, nunca el token en texto plano
    token_hash = Column(String(64), unique=True, nullable=False, index=True)

    fecha_creacion = Column(DateTime(), default=_utcnow, nullable=False)
    fecha_expiracion = Column(DateTime(), nullable=False)
    ip_origen = Column(String(45), nullable=True)
    activa = Column(Boolean, default=True, nullable=False)

    usuario = relationship("Usuario", back_populates="sesiones")


# --------------------------------------------------------------
# Auditoría de seguridad
# --------------------------------------------------------------
class LogSeguridad(Base):
    __tablename__ = "logs_seguridad"

    id = Column(String(36), primary_key=True, default=_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=True)

    tipo_evento = Column(String(100), nullable=False)
    fecha = Column(DateTime(), default=_utcnow, nullable=False)
    ip_origen = Column(String(45), nullable=True)
    detalle = Column(Text, nullable=True)