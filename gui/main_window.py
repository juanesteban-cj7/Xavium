"""
main_window.py
Ventana principal de la aplicación Xavium.

Contiene un QStackedWidget que alterna entre la vista de login
y la vista de registro. Aún sin lógica de backend/autenticación:
solo maneja la navegación entre pantallas.
"""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from gui.login_view import LoginView
from gui.register_view import RegisterView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Xavium")
        self.setMinimumSize(500, 560)
        self.setStyleSheet("background-color: #1E5AA8;")

        # Contenedor que permite cambiar entre login y registro
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_view = LoginView(on_ir_a_registro=self.mostrar_registro)
        self.register_view = RegisterView(on_ir_a_login=self.mostrar_login)

        self.stack.addWidget(self.login_view)     # índice 0
        self.stack.addWidget(self.register_view)  # índice 1

        self.mostrar_login()

    def mostrar_login(self):
        self.stack.setCurrentWidget(self.login_view)

    def mostrar_registro(self):
        self.stack.setCurrentWidget(self.register_view)
