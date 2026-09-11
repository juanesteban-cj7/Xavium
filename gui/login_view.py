"""
login_view.py
Vista de inicio de sesión de Xavium.

Por el momento solo contiene la interfaz gráfica (sin lógica de
backend/autenticación). Los campos y botones quedan listos para
conectarse en pasos posteriores con el módulo `auth`.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt

INPUT_STYLE = """
QLineEdit {
    background-color: white;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    color: #1E1E1E;
}
"""

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: white;
    color: #1E5AA8;
    font-size: 16px;
    font-weight: bold;
    border-radius: 8px;
    padding: 10px;
}
QPushButton:hover {
    background-color: #E6EEF8;
}
QPushButton:pressed {
    background-color: #C9DAF0;
}
"""

LINK_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: white;
    font-size: 13px;
    text-decoration: underline;
    border: none;
}
QPushButton:hover {
    color: #D6E4F5;
}
"""


class LoginView(QWidget):
    def __init__(self, on_ir_a_registro=None):
        """
        on_ir_a_registro: callback que se ejecuta cuando el usuario
        quiere cambiar a la vista de registro.
        """
        super().__init__()
        self.on_ir_a_registro = on_ir_a_registro

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(14)
        layout.setContentsMargins(60, 40, 60, 40)
        self.setLayout(layout)

        # Título / marca
        titulo = QLabel("Xavium")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "color: white; font-size: 34px; font-weight: bold;"
        )
        layout.addWidget(titulo)

        subtitulo = QLabel("Inicia sesión con tu correo institucional")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #D6E4F5; font-size: 13px;")
        layout.addWidget(subtitulo)

        layout.addSpacing(10)

        # Campo correo institucional
        self.input_correo = QLineEdit()
        self.input_correo.setPlaceholderText("Correo institucional")
        self.input_correo.setStyleSheet(INPUT_STYLE)
        self.input_correo.setFixedHeight(42)
        layout.addWidget(self.input_correo)

        # Campo contraseña
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet(INPUT_STYLE)
        self.input_password.setFixedHeight(42)
        layout.addWidget(self.input_password)

        layout.addSpacing(6)

        # Botón iniciar sesión
        self.boton_login = QPushButton("Iniciar sesión")
        self.boton_login.setFixedHeight(44)
        self.boton_login.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.boton_login.clicked.connect(self.on_login_click)
        layout.addWidget(self.boton_login)

        # Enlace hacia registro
        fila_registro = QHBoxLayout()
        fila_registro.setAlignment(Qt.AlignmentFlag.AlignCenter)

        texto_pregunta = QLabel("¿No tienes cuenta?")
        texto_pregunta.setStyleSheet("color: #D6E4F5; font-size: 13px;")
        fila_registro.addWidget(texto_pregunta)

        self.boton_ir_registro = QPushButton("Regístrate")
        self.boton_ir_registro.setStyleSheet(LINK_BUTTON_STYLE)
        self.boton_ir_registro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_ir_registro.clicked.connect(self._ir_a_registro)
        fila_registro.addWidget(self.boton_ir_registro)

        layout.addLayout(fila_registro)

    def on_login_click(self):
        # Placeholder: aquí se conectará la lógica de autenticación (auth/login.py)
        print(
            f"[LOGIN] correo={self.input_correo.text()} "
            f"password={'*' * len(self.input_password.text())}"
        )

    def _ir_a_registro(self):
        if self.on_ir_a_registro:
            self.on_ir_a_registro()
