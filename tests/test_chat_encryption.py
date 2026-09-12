"""
test_chat_encryption.py
Pruebas del cifrado por conversación y de message_store.py:
- Cada conversación tiene su propia clave.
- Los mensajes se guardan cifrados en la BD (nunca texto plano).
- Solo los participantes de una conversación pueden leerla.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db_connection import Base
from database import models  # noqa: F401
from database.models import Mensaje
from profile.interests_catalog import seed_catalog
from auth.register import register_user, verify_email
from chat.encryption import (
    cifrar_clave_conversacion,
    cifrar_mensaje,
    descifrar_clave_conversacion,
    descifrar_mensaje,
    generar_clave_conversacion,
)
from chat.message_store import (
    NoAutorizadoError,
    enviar_mensaje,
    listar_conversaciones_usuario,
    marcar_mensajes_como_leidos,
    obtener_mensajes,
    obtener_o_crear_conversacion,
)


@pytest.fixture()
def session_db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    seed_catalog(session)
    session.commit()

    yield session
    session.close()


def _crear_usuario_activo(session_db, nombre, correo, facultad="Ingeniería"):
    resultado = register_user(
        session_db,
        nombre=nombre,
        edad=20,
        correo_institucional=correo,
        facultad_nombre=facultad,
        password="ClaveSegura1",
        password_confirm="ClaveSegura1",
    )
    verify_email(session_db, correo, resultado.token_verificacion)
    session_db.commit()
    return resultado.usuario_id


# --------------------------------------------------------------
# Pruebas de cifrado puro (sin BD)
# --------------------------------------------------------------
def test_cifrar_y_descifrar_mensaje():
    clave = generar_clave_conversacion()
    cifrado = cifrar_mensaje("Hola, ¿cómo estás?", clave)
    assert cifrado != "Hola, ¿cómo estás?"
    assert descifrar_mensaje(cifrado, clave) == "Hola, ¿cómo estás?"


def test_clave_conversacion_se_puede_envolver_y_recuperar():
    clave_original = generar_clave_conversacion()
    clave_envuelta = cifrar_clave_conversacion(clave_original)
    clave_recuperada = descifrar_clave_conversacion(clave_envuelta)
    assert clave_recuperada == clave_original


def test_dos_conversaciones_tienen_claves_distintas():
    clave_a = generar_clave_conversacion()
    clave_b = generar_clave_conversacion()
    assert clave_a != clave_b


# --------------------------------------------------------------
# Pruebas de message_store (con BD)
# --------------------------------------------------------------
def test_crear_conversacion_es_idempotente(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")

    conv1 = obtener_o_crear_conversacion(session_db, a_id, b_id)
    conv2 = obtener_o_crear_conversacion(session_db, b_id, a_id)  # orden invertido

    assert conv1.id == conv2.id


def test_mensaje_se_guarda_cifrado_en_bd(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)

    texto_secreto = "Nos vemos en la cafetería a las 3"
    enviar_mensaje(session_db, conversacion.id, a_id, texto_secreto)
    session_db.commit()

    fila_cruda = session_db.query(Mensaje).filter(
        Mensaje.conversacion_id == conversacion.id
    ).first()

    # El texto plano NUNCA debe aparecer tal cual en la columna cifrada
    assert texto_secreto not in fila_cruda.contenido_cifrado


def test_obtener_mensajes_descifra_correctamente(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)

    enviar_mensaje(session_db, conversacion.id, a_id, "Hola Beto")
    enviar_mensaje(session_db, conversacion.id, b_id, "Hola Ana")
    session_db.commit()

    mensajes = obtener_mensajes(session_db, conversacion.id, a_id)

    assert [m.contenido for m in mensajes] == ["Hola Beto", "Hola Ana"]
    assert mensajes[0].es_propio is True
    assert mensajes[1].es_propio is False


def test_usuario_ajeno_no_puede_leer_conversacion(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    c_id = _crear_usuario_activo(session_db, "Carla", "carla@javeriana.edu.co")

    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)
    enviar_mensaje(session_db, conversacion.id, a_id, "Mensaje privado")
    session_db.commit()

    with pytest.raises(NoAutorizadoError):
        obtener_mensajes(session_db, conversacion.id, c_id)


def test_usuario_ajeno_no_puede_enviar_a_conversacion_ajena(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    c_id = _crear_usuario_activo(session_db, "Carla", "carla@javeriana.edu.co")

    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)

    with pytest.raises(NoAutorizadoError):
        enviar_mensaje(session_db, conversacion.id, c_id, "Intento de intrusión")


def test_marcar_como_leidos(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)

    enviar_mensaje(session_db, conversacion.id, a_id, "Uno")
    enviar_mensaje(session_db, conversacion.id, a_id, "Dos")
    session_db.commit()

    marcados = marcar_mensajes_como_leidos(session_db, conversacion.id, b_id)
    session_db.commit()

    assert marcados == 2
    mensajes = obtener_mensajes(session_db, conversacion.id, b_id)
    assert all(m.leido for m in mensajes)


def test_listar_conversaciones_usuario(session_db):
    a_id = _crear_usuario_activo(session_db, "Ana", "ana@javeriana.edu.co")
    b_id = _crear_usuario_activo(session_db, "Beto", "beto@javeriana.edu.co")
    conversacion = obtener_o_crear_conversacion(session_db, a_id, b_id)
    enviar_mensaje(session_db, conversacion.id, b_id, "Hola Ana, ¿cómo vas?")
    session_db.commit()

    resumenes = listar_conversaciones_usuario(session_db, a_id)

    assert len(resumenes) == 1
    assert resumenes[0].otro_usuario_nombre == "Beto"
    assert resumenes[0].ultimo_mensaje == "Hola Ana, ¿cómo vas?"
    assert resumenes[0].mensajes_no_leidos == 1