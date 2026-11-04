"""Pruebas de persistencia del catálogo inicial."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from database import models  # noqa: F401  (registra los modelos en Base)
from database.db_connection import Base
from profile.interests_catalog import FACULTADES


def test_bootstrap_persiste_facultades_en_una_nueva_sesion(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine)

    @contextmanager
    def get_test_session():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_session", get_test_session)

    main.bootstrap_datos_iniciales()

    with get_test_session() as session:
        facultades = [facultad.nombre for facultad in session.query(models.Facultad).all()]

    assert set(facultades) == set(FACULTADES)