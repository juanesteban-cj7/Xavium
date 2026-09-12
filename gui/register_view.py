"""
register_view.py
Vista de registro de Xavium, conectada al backend real:
- Carga facultades desde la base de datos (profile/profile_manager.py)
- Registra al estudiante mediante auth/register.py
- Solicita el código de verificación de correo y lo confirma
  mediante auth/register.py::verify_email
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QHBoxLayout,
    QMessageBox,
    QInputDialog,
)
from PyQt6.QtCore import Qt

from database.db_connection import get_session
from profile.profile_manager import list_facultades
from security.input_validation import ValidationError
from auth.register import register_user, send_verification_email, verify_email
from gui.verification_code_dialog import mostrar_codigo_desarrollo

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

TEXTO_PLACEHOLDER_FACULTAD = "Selecciona tu facultad"

MAX_INTENTOS_VERIFICACION = 3


class RegisterView(QWidget):
    def __init__(self, on_ir_a_login=None):
        """
        on_ir_a_login: callback que se ejecuta cuando el usuario
        quiere volver a la vista de login (también se usa tras un
        registro + verificación exitosos).
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

        # Facultad (cargada dinámicamente desde la BD)
        self.combo_facultad = QComboBox()
        self.combo_facultad.setStyleSheet(INPUT_STYLE)
        self.combo_facultad.setFixedHeight(40)
        layout.addWidget(self.combo_facultad)
        self._cargar_facultades()

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

    def _cargar_facultades(self):
        """Carga el catálogo de facultades desde la BD en el combo."""
        self.combo_facultad.clear()
        self.combo_facultad.addItem(TEXTO_PLACEHOLDER_FACULTAD)
        try:
            with get_session() as session:
                nombres = list_facultades(session)
            self.combo_facultad.addItems(nombres)
        except Exception as exc:
            # No debe tumbar la GUI si la BD no está disponible al abrir esta vista
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo cargar el catálogo de facultades:\n{exc}",
            )

    def limpiar_formulario(self):
        self.input_nombre.clear()
        self.input_edad.clear()
        self.input_correo.clear()
        self.input_password.clear()
        self.input_password_confirm.clear()
        self.combo_facultad.setCurrentIndex(0)

    def on_registrar_click(self):
        nombre = self.input_nombre.text()
        edad = self.input_edad.text()
        correo = self.input_correo.text()
        facultad = self.combo_facultad.currentText()
        password = self.input_password.text()
        password_confirm = self.input_password_confirm.text()

        try:
            with get_session() as session:
                resultado = register_user(
                    session,
                    nombre=nombre,
                    edad=edad,
                    correo_institucional=correo,
                    facultad_nombre=facultad,
                    password=password,
                    password_confirm=password_confirm,
                )
                # Se guardan los datos que necesitamos fuera de la sesión
                # (la sesión de BD se cierra al salir del "with")
                usuario_id = resultado.usuario_id
                correo_normalizado = resultado.correo
                token_verificacion = resultado.token_verificacion
        except ValidationError as error:
            QMessageBox.warning(self, "No se pudo registrar", str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error inesperado",
                f"Ocurrió un error al registrar la cuenta:\n{error}",
            )
            return

        # Intentar enviar el correo de verificación (o registrar el token
        # en consola si SMTP no está configurado — ver auth/register.py)
        enviado_por_correo = send_verification_email(correo_normalizado, token_verificacion)

        self._solicitar_codigo_verificacion(
            correo_normalizado, enviado_por_correo, token_verificacion
        )

    def _solicitar_codigo_verificacion(
        self, correo: str, enviado_por_correo: bool, token_dev: str
    ):
        if enviado_por_correo:
            mensaje_info = (
                f"Cuenta creada. Enviamos un código de verificación a:\n{correo}"
            )
            QMessageBox.information(self, "Verifica tu correo", mensaje_info)
        else:
            codigo = mostrar_codigo_desarrollo(
                self,
                "Verifica tu correo",
                "Cuenta creada. Copia este código para completar la verificación:",
                token_dev,
            )
            if codigo is None:
                self.limpiar_formulario()
                self._ir_a_login()
                return

            try:
                with get_session() as session:
                    verify_email(session, correo, codigo)
                QMessageBox.information(
                    self,
                    "¡Listo!",
                    "Tu correo fue verificado. Ya puedes iniciar sesión.",
                )
                self.limpiar_formulario()
                self._ir_a_login()
                return
            except ValidationError as error:
                QMessageBox.warning(self, "Código incorrecto", str(error))
                self.limpiar_formulario()
                self._ir_a_login()
                return

        intentos_restantes = MAX_INTENTOS_VERIFICACION
        while intentos_restantes > 0:
            codigo, confirmado = QInputDialog.getText(
                self,
                "Verificación de correo",
                "Ingresa el código de verificación:",
            )

            if not confirmado:
                QMessageBox.information(
                    self,
                    "Verificación pendiente",
                    "Puedes verificar tu cuenta más tarde. "
                    "Mientras tanto no podrás iniciar sesión.",
                )
                self.limpiar_formulario()
                self._ir_a_login()
                return

            try:
                with get_session() as session:
                    verify_email(session, correo, codigo.strip())
                QMessageBox.information(
                    self, "¡Listo!", "Tu correo fue verificado. Ya puedes iniciar sesión."
                )
                self.limpiar_formulario()
                self._ir_a_login()
                return
            except ValidationError as error:
                intentos_restantes -= 1
                if intentos_restantes > 0:
                    QMessageBox.warning(
                        self,
                        "Código incorrecto",
                        f"{error}\nIntentos restantes: {intentos_restantes}",
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Verificación fallida",
                        "Agotaste los intentos. Podrás verificar tu cuenta "
                        "más tarde desde la pantalla de inicio de sesión.",
                    )
                    self.limpiar_formulario()
                    self._ir_a_login()
                    return

    def _ir_a_login(self):
        if self.on_ir_a_login:
            self.on_ir_a_login()