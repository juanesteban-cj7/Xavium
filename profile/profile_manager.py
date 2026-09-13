"""
profile_manager.py
CRUD de perfil de usuario e intereses.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from database.models import Facultad, Interes, Usuario
from security.input_validation import (
    ValidationError,
    validate_edad,
    validate_facultad_nombre,
    validate_nombre,
)


@dataclass
class PerfilUsuario:
    id: str
    nombre: str
    edad: int
    correo: str  # descifrado solo para mostrarlo al propio usuario
    facultad: str
    intereses: List[str] = field(default_factory=list)


def _to_perfil(usuario: Usuario) -> PerfilUsuario:
    return PerfilUsuario(
        id=usuario.id,
        nombre=usuario.nombre,
        edad=usuario.edad,
            correo=usuario.correo,
        facultad=usuario.facultad.nombre if usuario.facultad else "",
        intereses=[interes.nombre for interes in usuario.intereses],
    )


def get_profile(session_db: Session, usuario_id: str) -> Optional[PerfilUsuario]:
    usuario = session_db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        return None
    return _to_perfil(usuario)


def update_profile(
    session_db: Session,
    usuario_id: str,
    nombre: Optional[str] = None,
    edad=None,
    facultad_nombre: Optional[str] = None,
) -> PerfilUsuario:
    usuario = session_db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise ValidationError("Usuario no encontrado.")

    if nombre is not None:
        usuario.nombre = validate_nombre(nombre)

    if edad is not None:
        usuario.edad = validate_edad(edad)

    if facultad_nombre is not None:
        nombre_limpio = validate_facultad_nombre(facultad_nombre)
        facultad = (
            session_db.query(Facultad).filter(Facultad.nombre == nombre_limpio).first()
        )
        if facultad is None:
            raise ValidationError("La facultad seleccionada no es válida.")
        usuario.facultad_id = facultad.id

    session_db.flush()
    return _to_perfil(usuario)


def set_interests(session_db: Session, usuario_id: str, nombres_intereses: List[str]) -> PerfilUsuario:
    """Reemplaza por completo la lista de intereses del usuario."""
    usuario = session_db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise ValidationError("Usuario no encontrado.")

    intereses_validos = (
        session_db.query(Interes).filter(Interes.nombre.in_(nombres_intereses)).all()
    )

    if len(intereses_validos) != len(set(nombres_intereses)):
        raise ValidationError("Uno o más intereses seleccionados no son válidos.")

    usuario.intereses = intereses_validos
    session_db.flush()
    return _to_perfil(usuario)


def list_facultades(session_db: Session) -> List[str]:
    return [f.nombre for f in session_db.query(Facultad).order_by(Facultad.nombre).all()]


def list_intereses_catalogo(session_db: Session) -> List[dict]:
    return [
        {"nombre": i.nombre, "categoria": i.categoria}
        for i in session_db.query(Interes).order_by(Interes.categoria, Interes.nombre).all()
    ]
