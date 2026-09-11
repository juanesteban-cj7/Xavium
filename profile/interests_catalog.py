"""
interests_catalog.py
Catálogo predefinido de facultades e intereses, y función para
poblar (seed) la base de datos de forma idempotente (se puede
ejecutar varias veces sin duplicar registros).
"""

from sqlalchemy.orm import Session

from database.models import Facultad, Interes

FACULTADES = [
    "Ingeniería",
    "Ciencias Económicas y Administrativas",
    "Ciencias de la Salud",
    "Ciencias Sociales y Humanas",
    "Derecho",
    "Artes y Diseño",
    "Ciencias Naturales y Exactas",
    "Educación",
]

# (nombre, categoría)
INTERESES = [
    ("Fútbol", "Deportes"),
    ("Baloncesto", "Deportes"),
    ("Voleibol", "Deportes"),
    ("Running", "Deportes"),
    ("Gimnasio", "Deportes"),
    ("Ajedrez", "Juegos"),
    ("Videojuegos", "Juegos"),
    ("Rol y juegos de mesa", "Juegos"),
    ("Música", "Arte y cultura"),
    ("Cine", "Arte y cultura"),
    ("Teatro", "Arte y cultura"),
    ("Fotografía", "Arte y cultura"),
    ("Lectura", "Arte y cultura"),
    ("Pintura y dibujo", "Arte y cultura"),
    ("Inteligencia artificial", "Tecnología"),
    ("Desarrollo de software", "Tecnología"),
    ("Ciberseguridad", "Tecnología"),
    ("Robótica", "Tecnología"),
    ("Emprendimiento", "Negocios"),
    ("Finanzas personales", "Negocios"),
    ("Voluntariado", "Comunidad"),
    ("Medio ambiente", "Comunidad"),
    ("Debate", "Comunidad"),
    ("Idiomas", "Aprendizaje"),
    ("Viajes", "Estilo de vida"),
    ("Cocina", "Estilo de vida"),
]


def seed_catalog(session_db: Session) -> None:
    """
    Inserta facultades e intereses predefinidos si aún no existen.
    Seguro de llamar en cada arranque de la app (init_db + seed).
    """
    facultades_existentes = {f.nombre for f in session_db.query(Facultad).all()}
    for nombre in FACULTADES:
        if nombre not in facultades_existentes:
            session_db.add(Facultad(nombre=nombre))

    intereses_existentes = {i.nombre for i in session_db.query(Interes).all()}
    for nombre, categoria in INTERESES:
        if nombre not in intereses_existentes:
            session_db.add(Interes(nombre=nombre, categoria=categoria))
