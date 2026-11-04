"""
main.py
Punto de entrada de la aplicación Xavium.

Antes de abrir la GUI:
1. Inicializa la base de datos (crea tablas si no existen).
2. Puebla el catálogo de facultades e intereses (idempotente).
"""

import sys

from PyQt6.QtWidgets import QApplication

from database.db_connection import init_db, get_session
from profile.interests_catalog import seed_catalog
from gui.main_window import MainWindow


def bootstrap_datos_iniciales() -> None:
    init_db()
    with get_session() as session:
        seed_catalog(session)
        session.commit()


def main():
    bootstrap_datos_iniciales()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
