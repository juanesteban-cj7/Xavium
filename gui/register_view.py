"""
register_view.py
Vista de registro de Xavium.

Por el momento solo contiene la interfaz gráfica (sin lógica de
backend/validación real). Los campos quedan listos para conectarse
en pasos posteriores con el módulo `auth` y el catálogo de facultades.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt

INPUT_STYLE = """
QLineEdit, QComboBox {
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

# Catálogo temporal de facultades (luego vendrá de profile/interests_catalog.py o BD)
FACULTADES_PLACEHOLDER = [
    "Selecciona tu facultad",
    "Ingeniería",
    "Ciencias Económicas y Administrativas",
    "Ciencias de la Salud",
    "Ciencias Sociales y Humanas",
    "Derecho",
    "Artes y Diseño",
]


class RegisterView(QWidget):
    def __init__(self, on_ir_a_login=None):
        """
        on_ir_a_login: callback que se ejecuta cuando el usuario
        quiere volver a la vista de login.
        """
        super().__init__()
        self.on_ir_a_login = on_ir_a_login

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(60, 30, 60, 30)
        self.setLayout(layout)

        # Título / marca
        titulo = QLabel("Xavium")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "color: white; font-size: 30px; font-weight: bold;"
        )
        layout.addWidget(titulo)

        subtitulo = QLabel("Crea tu cuenta de estudiante")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #D6E4F5; font-size: 13px;")
        layout.addWidget(subtitulo)

        layout.addSpacing(8)

        # Nombre
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo")
        self.input_nombre.setStyleSheet(INPUT_STYLE)
        self.input_nombre.setFixedHeight(40)
        layout.addWidget(self.input_nombre)

        # Edad
        self.input_edad = QLineEdit()
        self.input_edad.setPlaceholderText("Edad")
        self.input_edad.setStyleSheet(INPUT_STYLE)
        self.input_edad.setFixedHeight(40)
        layout.addWidget(self.input_edad)

        # Correo institucional
        self.input_correo = QLineEdit()
        self.input_correo.setPlaceholderText("Correo institucional")
        self.input_correo.setStyleSheet(INPUT_STYLE)
        self.input_correo.setFixedHeight(40)
        layout.addWidget(self.input_correo)

        # Facultad
        self.combo_facultad = QComboBox()
        self.combo_facultad.addItems(FACULTADES_PLACEHOLDER)
        self.combo_facultad.setStyleSheet(INPUT_STYLE)
        self.combo_facultad.setFixedHeight(40)
        layout.addWidget(self.combo_facultad)

        # Contraseña
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet(INPUT_STYLE)
        self.input_password.setFixedHeight(40)
        layout.addWidget(self.input_password)

        # Confirmar contraseña
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setPlaceholderText("Confirmar contraseña")
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setStyleSheet(INPUT_STYLE)
        self.input_password_confirm.setFixedHeight(40)
        layout.addWidget(self.input_password_confirm)

        layout.addSpacing(6)

        # Botón registrarse
        self.boton_registrar = QPushButton("Registrarse")
        self.boton_registrar.setFixedHeight(44)
        self.boton_registrar.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.boton_registrar.clicked.connect(self.on_registrar_click)
        layout.addWidget(self.boton_registrar)

        # Enlace hacia login
        fila_login = QHBoxLayout()
        fila_login.setAlignment(Qt.AlignmentFlag.AlignCenter)

        texto_pregunta = QLabel("¿Ya tienes cuenta?")
        texto_pregunta.setStyleSheet("color: #D6E4F5; font-size: 13px;")
        fila_login.addWidget(texto_pregunta)

        self.boton_ir_login = QPushButton("Inicia sesión")
        self.boton_ir_login.setStyleSheet(LINK_BUTTON_STYLE)
        self.boton_ir_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_ir_login.clicked.connect(self._ir_a_login)
        fila_login.addWidget(self.boton_ir_login)

        layout.addLayout(fila_login)

    def on_registrar_click(self):
        # Placeholder: aquí se conectará la lógica de registro (auth/register.py)
        print(
            f"[REGISTRO] nombre={self.input_nombre.text()} "
            f"edad={self.input_edad.text()} "
            f"correo={self.input_correo.text()} "
            f"facultad={self.combo_facultad.currentText()}"
        )

    def _ir_a_login(self):
        if self.on_ir_a_login:
            self.on_ir_a_login()
