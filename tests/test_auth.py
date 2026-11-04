"""
test_auth.py
Pruebas del flujo de registro, verificación de correo y login.

Usa una base de datos SQLite en memoria, aislada de la BD real de
desarrollo, para no ensuciar datos reales al correr los tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db_connection import Base
from database import models  # noqa: F401  (registra los modelos en Base)
from profile.interests_catalog import seed_catalog
from security.input_validation import ValidationError
from auth.register import register_user, resend_verification_code, verify_email
from auth.login import login_user


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


def _registrar_usuario_valido(session_db, correo="juan.perez@javeriana.edu.co"):
    return register_user(
        session_db,
        nombre="Juan Pérez",
        edad=20,
        correo_institucional=correo,
        facultad_nombre="Ingeniería",
        password="Segura123",
        password_confirm="Segura123",
    )


def test_registro_exitoso(session_db):
    resultado = _registrar_usuario_valido(session_db)
    session_db.commit()

    assert resultado.usuario_id is not None
    assert resultado.correo == "juan.perez@javeriana.edu.co"
    assert resultado.token_verificacion  # se generó un token


def test_registro_rechaza_dominio_no_institucional(session_db):
    with pytest.raises(ValidationError):
        register_user(
            session_db,
            nombre="Juan Pérez",
            edad=20,
            correo_institucional="juan.perez@gmail.com",
            facultad_nombre="Ingeniería",
            password="Segura123",
            password_confirm="Segura123",
        )


def test_registro_rechaza_correo_duplicado(session_db):
    _registrar_usuario_valido(session_db)
    session_db.commit()

    with pytest.raises(ValidationError):
        _registrar_usuario_valido(session_db)  # mismo correo


def test_registro_rechaza_passwords_no_coinciden(session_db):
    with pytest.raises(ValidationError):
        register_user(
            session_db,
            nombre="Juan Pérez",
            edad=20,
            correo_institucional="juan.perez@javeriana.edu.co",
            facultad_nombre="Ingeniería",
            password="Segura123",
            password_confirm="OtraClave456",
        )


def test_login_falla_si_no_ha_verificado_correo(session_db):
    resultado = _registrar_usuario_valido(session_db)
    session_db.commit()

    with pytest.raises(ValidationError):
        login_user(session_db, "juan.perez@javeriana.edu.co", "Segura123")

    nuevo_codigo = resend_verification_code(
        session_db, "juan.perez@javeriana.edu.co"
    )
    session_db.commit()

    with pytest.raises(ValidationError):
        verify_email(
            session_db,
            "juan.perez@javeriana.edu.co",
            resultado.token_verificacion,
        )

    assert verify_email(
        session_db,
        "juan.perez@javeriana.edu.co",
        nuevo_codigo.token_verificacion,
    )


def test_flujo_completo_registro_verificacion_login(session_db):
    resultado_registro = _registrar_usuario_valido(session_db)
    session_db.commit()

    verificado = verify_email(
        session_db, "juan.perez@javeriana.edu.co", resultado_registro.token_verificacion
    )
    session_db.commit()
    assert verificado is True

    resultado_login = login_user(session_db, "juan.perez@javeriana.edu.co", "Segura123")
    session_db.commit()

    assert resultado_login.usuario_id == resultado_registro.usuario_id
    assert resultado_login.token_sesion  # se creó una sesión


def test_registro_y_verificacion_persisten_entre_sesiones(session_db):
    resultado_registro = _registrar_usuario_valido(session_db)
    session_db.commit()
    session_db.close()

    resultado_verificacion = None
    engine = session_db.get_bind()
    TestingSessionLocal = sessionmaker(bind=engine)
    with TestingSessionLocal() as verification_session:
        resultado_verificacion = verify_email(
            verification_session,
            "juan.perez@javeriana.edu.co",
            resultado_registro.token_verificacion,
        )
        verification_session.commit()

    with TestingSessionLocal() as confirmed_session:
        usuario = confirmed_session.query(models.Usuario).filter_by(
            correo="juan.perez@javeriana.edu.co"
        ).one()

    assert resultado_verificacion is True
    assert usuario.estado_cuenta == models.EstadoCuenta.ACTIVO


def test_login_falla_con_password_incorrecta(session_db):
    resultado_registro = _registrar_usuario_valido(session_db)
    verify_email(
        session_db, "juan.perez@javeriana.edu.co", resultado_registro.token_verificacion
    )
    session_db.commit()

    with pytest.raises(ValidationError):
        login_user(session_db, "juan.perez@javeriana.edu.co", "ClaveIncorrecta1")


def test_bloqueo_tras_intentos_fallidos(session_db):
    resultado_registro = _registrar_usuario_valido(session_db)
    verify_email(
        session_db, "juan.perez@javeriana.edu.co", resultado_registro.token_verificacion
    )
    session_db.commit()

    # Agotar los intentos permitidos con contraseña incorrecta
    from config import settings

    for _ in range(settings.MAX_LOGIN_ATTEMPTS):
        with pytest.raises(ValidationError):
            login_user(session_db, "juan.perez@javeriana.edu.co", "ClaveIncorrecta1")
    session_db.commit()

    # El siguiente intento, incluso con la contraseña correcta, debe
    # rechazarse por bloqueo temporal
    with pytest.raises(ValidationError):
        login_user(session_db, "juan.perez@javeriana.edu.co", "Segura123")
