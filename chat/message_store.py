"""
message_store.py
Persistencia de conversaciones y mensajes cifrados.

Toda la lógica de "quién puede ver qué" vive aquí: nunca se debe
devolver el contenido de una conversación a alguien que no sea uno
de sus dos participantes (ver _verificar_participante).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from database.models import Conversacion, Grupo, GrupoMiembro, Mensaje, Usuario
from chat.encryption import (
    cifrar_clave_conversacion,
    cifrar_mensaje,
    descifrar_clave_conversacion,
    descifrar_mensaje,
    generar_clave_conversacion,
)
from security.input_validation import ValidationError, sanitize_text

MAX_LONGITUD_MENSAJE = 2000


class NoAutorizadoError(Exception):
    """Se lanza cuando un usuario intenta acceder a una conversación ajena."""


@dataclass
class MensajeDescifrado:
    id: str
    emisor_id: str
    contenido: str
    fecha_envio: datetime
    leido: bool
    es_propio: bool


@dataclass
class ResumenConversacion:
    conversacion_id: str
    otro_usuario_id: str
    otro_usuario_nombre: str
    ultimo_mensaje: Optional[str]
    fecha_ultimo_mensaje: Optional[datetime]
    mensajes_no_leidos: int


def _verificar_participante(conversacion: Conversacion, usuario_id: str) -> None:
    if usuario_id not in (conversacion.usuario1_id, conversacion.usuario2_id):
        raise NoAutorizadoError(
            "No tienes acceso a esta conversación."
        )


def obtener_o_crear_conversacion(
    session_db: Session, usuario_a_id: str, usuario_b_id: str
) -> Conversacion:
    """
    Devuelve la conversación existente entre dos usuarios, o la crea
    (con su propia clave de cifrado) si es la primera vez que se
    contactan. El orden de los IDs no importa.
    """
    if usuario_a_id == usuario_b_id:
        raise ValidationError("No puedes iniciar una conversación contigo mismo.")

    conversacion = (
        session_db.query(Conversacion)
        .filter(
            or_(
                and_(
                    Conversacion.usuario1_id == usuario_a_id,
                    Conversacion.usuario2_id == usuario_b_id,
                ),
                and_(
                    Conversacion.usuario1_id == usuario_b_id,
                    Conversacion.usuario2_id == usuario_a_id,
                ),
            )
        )
        .first()
    )

    if conversacion is not None:
        return conversacion

    clave_conversacion = generar_clave_conversacion()
    conversacion = Conversacion(
        usuario1_id=usuario_a_id,
        usuario2_id=usuario_b_id,
        clave_cifrada=cifrar_clave_conversacion(clave_conversacion),
    )
    session_db.add(conversacion)
    session_db.flush()

    return conversacion


def obtener_o_crear_conversacion_grupo(
    session_db: Session, grupo_id: str, usuario_id: str
) -> Conversacion:
    """Devuelve la conversación única del grupo si el usuario es miembro."""
    grupo = session_db.query(Grupo).filter(Grupo.id == grupo_id).first()
    miembro = session_db.query(GrupoMiembro).filter(
        GrupoMiembro.grupo_id == grupo_id,
        GrupoMiembro.usuario_id == usuario_id,
    ).first()
    if grupo is None or miembro is None:
        raise NoAutorizadoError("No tienes acceso a este grupo.")

    conversacion = (
        session_db.query(Conversacion)
        .filter(Conversacion.grupo_id == grupo_id)
        .first()
    )
    if conversacion is not None:
        return conversacion

    conversacion = Conversacion(
        usuario1_id=grupo.creador_id,
        usuario2_id=grupo.creador_id,
        grupo_id=grupo_id,
        clave_cifrada=cifrar_clave_conversacion(generar_clave_conversacion()),
    )
    session_db.add(conversacion)
    session_db.flush()
    return conversacion


def enviar_mensaje(
    session_db: Session, conversacion_id: str, emisor_id: str, texto_plano: str
) -> Mensaje:
    """Cifra y guarda un nuevo mensaje dentro de una conversación existente."""
    conversacion = (
        session_db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    )
    if conversacion is None:
        raise ValidationError("La conversación no existe.")

    _verificar_participante(conversacion, emisor_id)

    texto_limpio = sanitize_text(texto_plano, max_length=MAX_LONGITUD_MENSAJE)
    if not texto_limpio:
        raise ValidationError("El mensaje no puede estar vacío.")

    clave_conversacion = descifrar_clave_conversacion(conversacion.clave_cifrada)
    contenido_cifrado = cifrar_mensaje(texto_limpio, clave_conversacion)

    mensaje = Mensaje(
        conversacion_id=conversacion_id,
        emisor_id=emisor_id,
        contenido_cifrado=contenido_cifrado,
        leido=False,
    )
    session_db.add(mensaje)
    session_db.flush()

    return mensaje


def enviar_mensaje_grupo(
    session_db: Session, grupo_id: str, emisor_id: str, texto_plano: str
) -> Mensaje:
    conversacion = obtener_o_crear_conversacion_grupo(session_db, grupo_id, emisor_id)
    return _enviar_mensaje_en_conversacion(session_db, conversacion, emisor_id, texto_plano)


def _enviar_mensaje_en_conversacion(
    session_db: Session, conversacion: Conversacion, emisor_id: str, texto_plano: str
) -> Mensaje:
    texto_limpio = sanitize_text(texto_plano, max_length=MAX_LONGITUD_MENSAJE)
    if not texto_limpio:
        raise ValidationError("El mensaje no puede estar vacío.")

    clave_conversacion = descifrar_clave_conversacion(conversacion.clave_cifrada)
    mensaje = Mensaje(
        conversacion_id=conversacion.id,
        emisor_id=emisor_id,
        contenido_cifrado=cifrar_mensaje(texto_limpio, clave_conversacion),
        leido=False,
    )
    session_db.add(mensaje)
    session_db.flush()
    return mensaje


def obtener_mensajes_grupo(
    session_db: Session, grupo_id: str, usuario_id: str
) -> List[MensajeDescifrado]:
    conversacion = obtener_o_crear_conversacion_grupo(session_db, grupo_id, usuario_id)
    clave_conversacion = descifrar_clave_conversacion(conversacion.clave_cifrada)
    return [
        MensajeDescifrado(
            id=mensaje.id,
            emisor_id=mensaje.emisor_id,
            contenido=descifrar_mensaje(mensaje.contenido_cifrado, clave_conversacion),
            fecha_envio=mensaje.fecha_envio,
            leido=mensaje.leido,
            es_propio=mensaje.emisor_id == usuario_id,
        )
        for mensaje in sorted(conversacion.mensajes, key=lambda item: item.fecha_envio)
    ]


def obtener_mensajes(
    session_db: Session, conversacion_id: str, usuario_solicitante_id: str
) -> List[MensajeDescifrado]:
    """
    Devuelve el historial descifrado de una conversación, ordenado
    cronológicamente. Lanza NoAutorizadoError si quien pregunta no es
    parte de la conversación.
    """
    conversacion = (
        session_db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    )
    if conversacion is None:
        raise ValidationError("La conversación no existe.")

    _verificar_participante(conversacion, usuario_solicitante_id)

    clave_conversacion = descifrar_clave_conversacion(conversacion.clave_cifrada)

    mensajes_ordenados = sorted(conversacion.mensajes, key=lambda m: m.fecha_envio)

    return [
        MensajeDescifrado(
            id=m.id,
            emisor_id=m.emisor_id,
            contenido=descifrar_mensaje(m.contenido_cifrado, clave_conversacion),
            fecha_envio=m.fecha_envio,
            leido=m.leido,
            es_propio=(m.emisor_id == usuario_solicitante_id),
        )
        for m in mensajes_ordenados
    ]


def marcar_mensajes_como_leidos(
    session_db: Session, conversacion_id: str, usuario_receptor_id: str
) -> int:
    """
    Marca como leídos todos los mensajes de la conversación que NO
    fueron enviados por usuario_receptor_id (es decir, los que le
    llegaron a él). Devuelve cuántos se marcaron.
    """
    conversacion = (
        session_db.query(Conversacion).filter(Conversacion.id == conversacion_id).first()
    )
    if conversacion is None:
        raise ValidationError("La conversación no existe.")

    _verificar_participante(conversacion, usuario_receptor_id)

    no_leidos = [
        m
        for m in conversacion.mensajes
        if m.emisor_id != usuario_receptor_id and not m.leido
    ]
    for mensaje in no_leidos:
        mensaje.leido = True

    return len(no_leidos)


def listar_conversaciones_usuario(
    session_db: Session, usuario_id: str
) -> List[ResumenConversacion]:
    """
    Lista todas las conversaciones del usuario, con un resumen de cada
    una (para mostrar una "bandeja de entrada" en la GUI): nombre del
    otro participante, último mensaje, y cantidad de no leídos.
    """
    conversaciones = (
        session_db.query(Conversacion)
        .filter(
            or_(
                Conversacion.usuario1_id == usuario_id,
                Conversacion.usuario2_id == usuario_id,
            )
        )
        .all()
    )

    resumenes: List[ResumenConversacion] = []
    for conversacion in conversaciones:
        otro_usuario_id = (
            conversacion.usuario2_id
            if conversacion.usuario1_id == usuario_id
            else conversacion.usuario1_id
        )
        otro_usuario = (
            session_db.query(Usuario).filter(Usuario.id == otro_usuario_id).first()
        )
        if otro_usuario is None:
            continue  # cuenta eliminada u otro caso borde; se omite de la lista

        mensajes_ordenados = sorted(conversacion.mensajes, key=lambda m: m.fecha_envio)

        ultimo_mensaje_texto = None
        fecha_ultimo = None
        if mensajes_ordenados:
            clave_conversacion = descifrar_clave_conversacion(conversacion.clave_cifrada)
            ultimo = mensajes_ordenados[-1]
            ultimo_mensaje_texto = descifrar_mensaje(
                ultimo.contenido_cifrado, clave_conversacion
            )
            fecha_ultimo = ultimo.fecha_envio

        no_leidos = sum(
            1
            for m in mensajes_ordenados
            if m.emisor_id != usuario_id and not m.leido
        )

        resumenes.append(
            ResumenConversacion(
                conversacion_id=conversacion.id,
                otro_usuario_id=otro_usuario.id,
                otro_usuario_nombre=otro_usuario.nombre,
                ultimo_mensaje=ultimo_mensaje_texto,
                fecha_ultimo_mensaje=fecha_ultimo,
                mensajes_no_leidos=no_leidos,
            )
        )

    # Conversaciones con mensajes más recientes primero; las que aún
    # no tienen ningún mensaje quedan al final.
    resumenes.sort(
        key=lambda r: r.fecha_ultimo_mensaje or datetime.min, reverse=True
    )

    return resumenes