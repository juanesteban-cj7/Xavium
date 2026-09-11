"""
db_connection.py
Conexión y manejo de sesión con la base de datos.

Usa SQLAlchemy como ORM. La URL de conexión sale de config/settings.py,
lo que permite cambiar de SQLite (desarrollo, $0 costo) a PostgreSQL
(ej. Supabase/Render) sin tocar el resto del código.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

# connect_args especial para SQLite: permite usarlo desde distintos hilos
# (necesario porque la GUI de PyQt6 corre en su propio hilo/proceso)
_connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def init_db() -> None:
    """
    Crea todas las tablas definidas en database/models.py si no existen.

    Nota: para un proyecto en producción se recomienda usar una
    herramienta de migraciones (ej. Alembic) en vez de create_all().
    Para esta fase (prototipo académico, $0 presupuesto) se mantiene
    simple; el directorio database/migrations/ queda reservado para
    cuando se incorpore Alembic más adelante.
    """
    # Importación tardía para evitar import circular con models.py
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """
    Context manager para obtener una sesión de base de datos segura:
    hace commit si todo sale bien, rollback si hay una excepción, y
    siempre cierra la sesión al final.

    Uso:
        with get_session() as session:
            session.add(objeto)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
