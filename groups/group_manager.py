"""
group_manager.py
CRUD básico de grupos y sus miembros.
"""
from sqlalchemy.orm import Session, joinedload
from database.models import Grupo, GrupoMiembro, Usuario
from security.input_validation import ValidationError


def crear_grupo(session: Session, creador_id: str, nombre: str):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre del grupo no puede estar vacío.")
    grupo = Grupo(creador_id=creador_id, nombre=nombre)
    session.add(grupo)
    session.flush()
    session.add(GrupoMiembro(grupo_id=grupo.id, usuario_id=creador_id))
    session.flush()
    return grupo


def listar_grupos(session: Session, usuario_id: str):
    return (
        session.query(Grupo)
        .join(GrupoMiembro, Grupo.id == GrupoMiembro.grupo_id)
        .filter(GrupoMiembro.usuario_id == usuario_id)
        .order_by(Grupo.fecha_creacion, Grupo.nombre)
        .all()
    )


def listar_miembros(session: Session, grupo_id: str, usuario_id: str):
    miembro = session.query(GrupoMiembro).filter(
        GrupoMiembro.grupo_id == grupo_id,
        GrupoMiembro.usuario_id == usuario_id
    ).first()
    if not miembro:
        raise ValidationError("No tienes acceso a este grupo.")
    return (
        session.query(Usuario)
        .options(joinedload(Usuario.facultad))
        .join(GrupoMiembro, Usuario.id == GrupoMiembro.usuario_id)
        .filter(GrupoMiembro.grupo_id == grupo_id)
        .order_by(Usuario.nombre)
        .all()
    )


def agregar_miembro(session: Session, grupo_id: str, solicitante_id: str, usuario_id: str):
    grupo = session.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo or grupo.creador_id != solicitante_id:
        raise ValidationError("Solo el creador puede agregar miembros.")
    if not session.query(Usuario).filter(Usuario.id == usuario_id).first():
        raise ValidationError("El estudiante no existe.")
    if session.query(GrupoMiembro).filter(
        GrupoMiembro.grupo_id == grupo_id, GrupoMiembro.usuario_id == usuario_id
    ).first():
        return
    session.add(GrupoMiembro(grupo_id=grupo_id, usuario_id=usuario_id))
    session.flush()


def eliminar_miembro(session: Session, grupo_id: str, solicitante_id: str, usuario_id: str):
    grupo = session.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not grupo or grupo.creador_id != solicitante_id:
        raise ValidationError("Solo el creador puede quitar miembros.")
    if usuario_id == grupo.creador_id:
        raise ValidationError("El creador no puede salir del grupo.")
    session.query(GrupoMiembro).filter(
        GrupoMiembro.grupo_id == grupo_id, GrupoMiembro.usuario_id == usuario_id
    ).delete(synchronize_session=False)
    session.flush()
