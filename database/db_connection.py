import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuración de la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), "xavium.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from database import models

    Base.metadata.create_all(bind=engine)

    # Migración automática si falta la columna clave_cifrada
    inspector = inspect(engine)
    if "conversaciones" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("conversaciones")]
        if "clave_cifrada" not in columns:
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN clave_cifrada TEXT")
                )
                conn.commit()


def get_session():
    """Retorna una nueva sesión de la base de datos."""
    return SessionLocal()


def get_db():
    """Generador para dependencias o uso con context manager."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()