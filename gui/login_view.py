"""
login_view.py
Vista de inicio de sesión de Xavium, conectada al backend real
mediante auth/login.py.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from database.db_connection import get_session
from security.input_validation import ValidationError
from auth.login import login_user
from auth.register import (
    resend_verification_code,
    send_verification_email,
    verify_email,
)
from gui.verification_code_dialog import mostrar_codigo_desarrollo

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
    def __init__(self, on_ir_a_registro=None, on_login_exitoso=None):
        """
        on_ir_a_registro: callback para cambiar a la vista de registro.
        on_login_exitoso: callback(usuario_id, nombre, token_sesion) que
        se ejecuta cuando el login se completa correctamente.
        """
        super().__init__()
        self.on_ir_a_registro = on_ir_a_registro
        self.on_login_exitoso = on_login_exitoso

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

        self.boton_reenviar_verificacion = QPushButton(
            "Reenviar código de verificación"
        )
        self.boton_reenviar_verificacion.setStyleSheet(LINK_BUTTON_STYLE)
        self.boton_reenviar_verificacion.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.boton_reenviar_verificacion.clicked.connect(
            self.on_reenviar_verificacion_click
        )
        layout.addWidget(self.boton_reenviar_verificacion)

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
        correo = self.input_correo.text()
        password = self.input_password.text()

        try:
            with get_session() as session:
                resultado = login_user(session, correo, password)
        except ValidationError as error:
            QMessageBox.warning(self, "No se pudo iniciar sesión", str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error inesperado",
                f"Ocurrió un error al iniciar sesión:\n{error}",
            )
            return

        self.input_password.clear()

        if self.on_login_exitoso:
            self.on_login_exitoso(
                resultado.usuario_id, resultado.nombre, resultado.token_sesion
            )

    def _ir_a_registro(self):
        if self.on_ir_a_registro:
            self.on_ir_a_registro()

    def on_reenviar_verificacion_click(self):
        correo = self.input_correo.text()

        try:
            with get_session() as session:
                resultado = resend_verification_code(session, correo)
        except ValidationError as error:
            QMessageBox.warning(self, "No se pudo reenviar el código", str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error inesperado",
                f"Ocurrió un error al reenviar el código:\n{error}",
            )
            return

        enviado_por_correo = send_verification_email(
            resultado.correo, resultado.token_verificacion
        )
        if enviado_por_correo:
            QMessageBox.information(
                self,
                "Código reenviado",
                f"Enviamos un nuevo código de verificación a:\n{resultado.correo}",
            )
        else:
            codigo = mostrar_codigo_desarrollo(
                self,
                "Código reenviado",
                "Copia este nuevo código para completar la verificación:",
                resultado.token_verificacion,
            )
            if codigo is None:
                return

            try:
                with get_session() as session:
                    verify_email(session, resultado.correo, codigo)
                QMessageBox.information(
                    self,
                    "Correo verificado",
                    "Tu correo fue verificado. Ya puedes iniciar sesión.",
                )
            except ValidationError as error:
                QMessageBox.warning(self, "Código incorrecto", str(error))