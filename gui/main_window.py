"""
main_window.py
Ventana principal de la aplicación Xavium.

Contiene un QStackedWidget que alterna entre login, registro y la
pantalla de bienvenida (post-login). Conserva el estado mínimo de la
sesión activa en memoria y guarda el token cifrado para restaurarlo al
abrir la aplicación nuevamente, hasta que se cierre la sesión.
"""

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from database.db_connection import get_session
from auth.login import logout_user
from auth.session_manager import validate_session
from database.models import Usuario
from security.encryption_utils import decrypt_text, encrypt_text

from gui.login_view import LoginView
from gui.register_view import RegisterView
from gui.home_view import HomeView
from gui.search_view import SearchView
from gui.chat_view import ChatView


class MainWindow(QMainWindow):
    SESSION_KEY = "sesion/token"
    SETTINGS = ("Xavium", "Xavium")

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
        self.home_view = HomeView(
            on_logout=self.manejar_logout,
            on_ir_a_busqueda=self.mostrar_busqueda,
        )
        self.search_view = SearchView(
            on_abrir_chat=self.mostrar_chat,
            on_volver=self.mostrar_home,
        )
        self.chat_view = ChatView(on_volver=self.mostrar_busqueda)

        self.stack.addWidget(self.login_view)     # índice 0
        self.stack.addWidget(self.register_view)  # índice 1
        self.stack.addWidget(self.home_view)       # índice 2
        self.stack.addWidget(self.search_view)     # índice 3
        self.stack.addWidget(self.chat_view)       # índice 4

        if not self._restaurar_sesion():
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

    def mostrar_busqueda(self):
        if self.usuario_id is None:
            return

        self.search_view.preparar(self.usuario_id)
        self.stack.setCurrentWidget(self.search_view)

    def mostrar_chat(self, otro_usuario_id: str, otro_usuario_nombre: str):
        if self.usuario_id is None:
            return

        self.chat_view.preparar(
            self.usuario_id, otro_usuario_id, otro_usuario_nombre
        )
        self.stack.setCurrentWidget(self.chat_view)

    def manejar_login_exitoso(self, usuario_id: str, nombre: str, token_sesion: str):
        self.usuario_id = usuario_id
        self.usuario_nombre = nombre
        self.token_sesion = token_sesion
        QSettings(*self.SETTINGS).setValue(
            self.SESSION_KEY, encrypt_text(token_sesion)
        )

        self.home_view.set_nombre_usuario(nombre)
        self.showFullScreen()
        self.mostrar_home()

    def manejar_logout(self):
        if self.token_sesion:
            with get_session() as session:
                logout_user(session, self.token_sesion, usuario_id=self.usuario_id)
                session.commit()

        QSettings(*self.SETTINGS).remove(self.SESSION_KEY)

        self.usuario_id = None
        self.usuario_nombre = None
        self.token_sesion = None

        self.showNormal()
        self.mostrar_login()

    def _restaurar_sesion(self) -> bool:
        token_cifrado = QSettings(*self.SETTINGS).value(self.SESSION_KEY, "")
        if not token_cifrado:
            return False

        try:
            token_sesion = decrypt_text(token_cifrado)
            with get_session() as session:
                usuario_id = validate_session(session, token_sesion)
                usuario = (
                    session.query(Usuario).filter(Usuario.id == usuario_id).first()
                    if usuario_id
                    else None
                )
        except Exception:
            usuario_id = None
            usuario = None

        if usuario is None:
            QSettings(*self.SETTINGS).remove(self.SESSION_KEY)
            return False

        self.usuario_id = usuario.id
        self.usuario_nombre = usuario.nombre
        self.token_sesion = token_sesion
        self.home_view.set_nombre_usuario(usuario.nombre)
        self.showFullScreen()
        self.mostrar_home()
        return True