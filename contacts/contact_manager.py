"""
contact_manager.py
CRUD de contactos y categorías personalizadas.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models import (
    Contacto, CategoriaContacto, CategoriaContactoMiembro, Usuario
)
from security.input_validation import ValidationError


def _user(session, usuario_id):
    return session.query(Usuario).filter(Usuario.id == usuario_id).first()


def listar_contactos(session, usuario_id) -> List[dict]:
    filas = (
        session.query(Contacto, Usuario)
        .join(Usuario, Contacto.contacto_id == Usuario.id)
        .filter(Contacto.usuario_id == usuario_id)
        .order_by(Usuario.nombre)
        .all()
    )
    return [{"id": c.id, "usuario_id": u.id, "nombre": u.nombre, "facultad": u.facultad.nombre if u.facultad else ""}
            for c, u in filas]


def agregar_contacto(session, usuario_id, contacto_id):
    if usuario_id == contacto_id:
        raise ValidationError("No puedes agregarte a ti mismo.")
    if not _user(session, contacto_id):
        raise ValidationError("El estudiante no existe.")
    existente = session.query(Contacto).filter(
        Contacto.usuario_id == usuario_id,
        Contacto.contacto_id == contacto_id
    ).first()
    if existente:
        return existente
    contacto = Contacto(usuario_id=usuario_id, contacto_id=contacto_id)
    session.add(contacto)
    session.flush()
    return contacto


def eliminar_contacto(session, usuario_id, contacto_id):
    contacto = session.query(Contacto).filter(
        Contacto.usuario_id == usuario_id,
        Contacto.contacto_id == contacto_id
    ).first()
    if not contacto:
        return False
    session.query(CategoriaContactoMiembro).filter(
        CategoriaContactoMiembro.contacto_id == contacto.id
    ).delete(synchronize_session=False)
    session.delete(contacto)
    session.flush()
    return True


def listar_categorias(session, usuario_id) -> List[dict]:
    return [
        {"id": c.id, "nombre": c.nombre, "color": c.color}
        for c in session.query(CategoriaContacto)
        .filter(CategoriaContacto.usuario_id == usuario_id)
        .order_by(CategoriaContacto.fecha_creacion, CategoriaContacto.nombre)
        .all()
    ]


def crear_categoria(session, usuario_id, nombre, color="#1E5AA8"):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre de la categoría no puede estar vacío.")
    if len(nombre) > 100:
        raise ValidationError("El nombre es demasiado largo.")
    categoria = CategoriaContacto(usuario_id=usuario_id, nombre=nombre, color=color)
    session.add(categoria)
    session.flush()
    return categoria


def _categoria_propia(session, usuario_id, categoria_id):
    c = session.query(CategoriaContacto).filter(
        CategoriaContacto.id == categoria_id,
        CategoriaContacto.usuario_id == usuario_id
    ).first()
    if not c:
        raise ValidationError("Categoría no encontrada.")
    return c


def cambiar_nombre_categoria(session, usuario_id, categoria_id, nombre):
    c = _categoria_propia(session, usuario_id, categoria_id)
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre no puede estar vacío.")
    c.nombre = nombre
    session.flush()
    return c


def cambiar_color_categoria(session, usuario_id, categoria_id, color):
    c = _categoria_propia(session, usuario_id, categoria_id)
    c.color = color
    session.flush()
    return c


def eliminar_categoria(session, usuario_id, categoria_id):
    c = _categoria_propia(session, usuario_id, categoria_id)
    session.query(CategoriaContactoMiembro).filter(
        CategoriaContactoMiembro.categoria_id == categoria_id
    ).delete(synchronize_session=False)
    session.delete(c)
    session.flush()


def contactos_de_categoria(session, usuario_id, categoria_id) -> List[dict]:
    _categoria_propia(session, usuario_id, categoria_id)
    filas = (
        session.query(CategoriaContactoMiembro, Contacto, Usuario)
        .join(Contacto, CategoriaContactoMiembro.contacto_id == Contacto.id)
        .join(Usuario, Contacto.contacto_id == Usuario.id)
        .filter(
            CategoriaContactoMiembro.categoria_id == categoria_id,
            Contacto.usuario_id == usuario_id,
        )
        .order_by(Usuario.nombre)
        .all()
    )
    return [{"id": c.id, "usuario_id": u.id, "nombre": u.nombre,
             "facultad": u.facultad.nombre if u.facultad else ""}
            for _, c, u in filas]


def establecer_contactos_categoria(session, usuario_id, categoria_id, contacto_ids):
    _categoria_propia(session, usuario_id, categoria_id)
    permitidos = {
        c.id for c in session.query(Contacto).filter(
            Contacto.usuario_id == usuario_id,
            Contacto.id.in_(contacto_ids or [])
        ).all()
    }
    session.query(CategoriaContactoMiembro).filter(
        CategoriaContactoMiembro.categoria_id == categoria_id
    ).delete(synchronize_session=False)
    for cid in permitidos:
        session.add(CategoriaContactoMiembro(
            categoria_id=categoria_id, contacto_id=cid
        ))
    session.flush()
