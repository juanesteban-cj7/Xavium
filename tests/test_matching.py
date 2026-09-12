"""
test_matching.py
Pruebas del algoritmo de similitud (Jaccard) y del motor de búsqueda.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db_connection import Base
from database import models  # noqa: F401
from profile.interests_catalog import seed_catalog
from profile.profile_manager import set_interests
from auth.register import register_user, verify_email
from matching.matching_algorithm import calcular_jaccard, calcular_similitud
from matching.search_engine import buscar_estudiantes


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


def _crear_usuario_activo(session_db, nombre, correo, facultad, intereses):
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
    set_interests(session_db, resultado.usuario_id, intereses)
    session_db.commit()
    return resultado.usuario_id


# --------------------------------------------------------------
# Pruebas del algoritmo de similitud (unitarias, sin BD)
# --------------------------------------------------------------
def test_jaccard_conjuntos_identicos():
    a = {"Música", "Cine"}
    b = {"Música", "Cine"}
    assert calcular_jaccard(a, b) == 1.0


def test_jaccard_sin_interseccion():
    a = {"Música"}
    b = {"Ajedrez"}
    assert calcular_jaccard(a, b) == 0.0


def test_jaccard_conjuntos_vacios():
    assert calcular_jaccard(set(), set()) == 0.0


def test_jaccard_interseccion_parcial():
    a = {"Música", "Cine", "Ajedrez"}
    b = {"Música", "Cine", "Fútbol"}
    # Intersección = 2 (Música, Cine), Unión = 4
    assert calcular_jaccard(a, b) == pytest.approx(2 / 4)


def test_similitud_con_bonus_misma_facultad():
    resultado = calcular_similitud(
        {"Música"}, {"Música"}, facultad_a="Ingeniería", facultad_b="Ingeniería"
    )
    assert resultado.misma_facultad is True
    assert resultado.score_intereses == 1.0
    assert resultado.score > resultado.score_intereses  # el bonus se sumó


def test_similitud_sin_bonus_facultad_distinta():
    resultado = calcular_similitud(
        {"Música"}, {"Música"}, facultad_a="Ingeniería", facultad_b="Derecho"
    )
    assert resultado.misma_facultad is False
    assert resultado.score == resultado.score_intereses


# --------------------------------------------------------------
# Pruebas del motor de búsqueda (con BD en memoria)
# --------------------------------------------------------------
def test_busqueda_excluye_al_propio_usuario(session_db):
    yo_id = _crear_usuario_activo(
        session_db, "Yo Mismo", "yo@javeriana.edu.co", "Ingeniería", ["Música"]
    )
    resultados = buscar_estudiantes(session_db, yo_id)
    assert all(r.usuario_id != yo_id for r in resultados)


def test_busqueda_ordena_por_similitud_descendente(session_db):
    yo_id = _crear_usuario_activo(
        session_db,
        "Yo Mismo",
        "yo@javeriana.edu.co",
        "Ingeniería",
        ["Música", "Cine", "Ajedrez"],
    )
    _crear_usuario_activo(
        session_db,
        "Muy Afín",
        "afin@javeriana.edu.co",
        "Derecho",
        ["Música", "Cine", "Ajedrez"],  # coincide 100%
    )
    _crear_usuario_activo(
        session_db,
        "Poco Afín",
        "poco@javeriana.edu.co",
        "Derecho",
        ["Música"],  # coincide parcialmente
    )
    _crear_usuario_activo(
        session_db,
        "Nada Afín",
        "nada@javeriana.edu.co",
        "Derecho",
        ["Fútbol"],  # no coincide
    )

    resultados = buscar_estudiantes(session_db, yo_id)

    nombres_en_orden = [r.nombre for r in resultados]
    assert nombres_en_orden.index("Muy Afín") < nombres_en_orden.index("Poco Afín")
    assert nombres_en_orden.index("Poco Afín") < nombres_en_orden.index("Nada Afín")


def test_busqueda_filtro_por_facultad(session_db):
    yo_id = _crear_usuario_activo(
        session_db, "Yo Mismo", "yo@javeriana.edu.co", "Ingeniería", ["Música"]
    )
    _crear_usuario_activo(
        session_db, "De Ingeniería", "ing@javeriana.edu.co", "Ingeniería", ["Música"]
    )
    _crear_usuario_activo(
        session_db, "De Derecho", "der@javeriana.edu.co", "Derecho", ["Música"]
    )

    resultados = buscar_estudiantes(session_db, yo_id, facultad_filtro="Ingeniería")

    assert len(resultados) == 1
    assert resultados[0].nombre == "De Ingeniería"


def test_busqueda_solo_con_intereses_comunes(session_db):
    yo_id = _crear_usuario_activo(
        session_db, "Yo Mismo", "yo@javeriana.edu.co", "Ingeniería", ["Música"]
    )
    _crear_usuario_activo(
        session_db, "Sin Nada En Comun", "otro@javeriana.edu.co", "Derecho", ["Fútbol"]
    )

    resultados_con_filtro = buscar_estudiantes(
        session_db, yo_id, solo_con_intereses_comunes=True
    )
    resultados_sin_filtro = buscar_estudiantes(
        session_db, yo_id, solo_con_intereses_comunes=False
    )

    assert len(resultados_con_filtro) == 0
    assert len(resultados_sin_filtro) == 1


def test_busqueda_incluye_intereses_comunes_en_resultado(session_db):
    yo_id = _crear_usuario_activo(
        session_db,
        "Yo Mismo",
        "yo@javeriana.edu.co",
        "Ingeniería",
        ["Música", "Cine"],
    )
    _crear_usuario_activo(
        session_db,
        "Compatible",
        "compatible@javeriana.edu.co",
        "Derecho",
        ["Música", "Ajedrez"],
    )

    resultados = buscar_estudiantes(session_db, yo_id)

    assert resultados[0].intereses_comunes == ["Música"]