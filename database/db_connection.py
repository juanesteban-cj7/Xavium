import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


def _carpeta_persistente_datos() -> str:
    """
    Devuelve una carpeta donde guardar xavium.db que sobreviva entre
    ejecuciones, tanto corriendo con 'python main.py' como empaquetado
    con PyInstaller.

    - Modo normal (python main.py): junto a este archivo (database/).
    - Modo .exe (PyInstaller --onefile): __file__ apunta a una carpeta
      temporal que se borra al cerrar el programa, así que usamos la
      carpeta donde vive el .exe en su lugar (sys.executable), que sí
      persiste entre ejecuciones.
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(__file__)

    carpeta = os.path.join(base, "database")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


# Configuración de la base de datos SQLite
DB_PATH = os.path.join(_carpeta_persistente_datos(), "xavium.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from database import models
    from security.encryption_utils import decrypt_text

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

    inspector = inspect(engine)
    if "usuarios" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("usuarios")]
        if "correo" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE usuarios ADD COLUMN correo VARCHAR(255)"))
                usuarios = conn.execute(
                    text("SELECT id, correo_cifrado FROM usuarios")
                ).mappings()
                for usuario in usuarios:
                    correo = decrypt_text(usuario["correo_cifrado"])
                    conn.execute(
                        text("UPDATE usuarios SET correo = :correo WHERE id = :id"),
                        {"correo": correo, "id": usuario["id"]},
                    )
                conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS ix_usuarios_correo ON usuarios (correo)")
                )

    inspector = inspect(engine)
    if "conversaciones" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("conversaciones")]
        if "grupo_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE conversaciones ADD COLUMN grupo_id VARCHAR(36)")
                )
                conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS ix_conversaciones_grupo_id ON conversaciones (grupo_id)")
                )


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