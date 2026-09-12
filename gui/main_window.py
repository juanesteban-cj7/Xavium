"""
main_window.py
Ventana principal de la aplicación Xavium.

Contiene un QStackedWidget que alterna entre login, registro y la
pantalla de bienvenida (post-login). También guarda en memoria el
estado mínimo de la sesión activa (usuario_id, nombre, token) mientras
la app está abierta.
"""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from database.db_connection import get_session
from auth.login import logout_user

from gui.login_view import LoginView
from gui.register_view import RegisterView
from gui.home_view import HomeView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Xavium")
        self.setMinimumSize(500, 560)
        self.setStyleSheet("background-color: #1E5AA8;")

        # Estado de sesión en memoria (mientras la app está abierta)
        self.usuario_id = None
        self.usuario_nombre = None
        self.token_sesion = None

        # Contenedor que permite cambiar entre vistas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_view = LoginView(
            on_ir_a_registro=self.mostrar_registro,
            on_login_exitoso=self.manejar_login_exitoso,
        )
        self.register_view = RegisterView(on_ir_a_login=self.mostrar_login)
        self.home_view = HomeView(on_logout=self.manejar_logout)

        self.stack.addWidget(self.login_view)     # índice 0
        self.stack.addWidget(self.register_view)  # índice 1
        self.stack.addWidget(self.home_view)       # índice 2

        self.mostrar_login()

    def mostrar_login(self):
        self.stack.setCurrentWidget(self.login_view)

    def mostrar_registro(self):
        # Refresca el catálogo de facultades cada vez que se entra a
        # registro, por si la BD cambió desde que se abrió la app.
        self.register_view._cargar_facultades()
        self.stack.setCurrentWidget(self.register_view)

    def mostrar_home(self):
        self.stack.setCurrentWidget(self.home_view)

    def manejar_login_exitoso(self, usuario_id: str, nombre: str, token_sesion: str):
        self.usuario_id = usuario_id
        self.usuario_nombre = nombre
        self.token_sesion = token_sesion

        self.home_view.set_nombre_usuario(nombre)
        self.mostrar_home()

    def manejar_logout(self):
        if self.token_sesion:
            with get_session() as session:
                logout_user(session, self.token_sesion, usuario_id=self.usuario_id)

        self.usuario_id = None
        self.usuario_nombre = None
        self.token_sesion = None

        self.mostrar_login()