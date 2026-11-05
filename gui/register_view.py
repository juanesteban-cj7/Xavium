"""
register_view.py
Vista de registro de Xavium, conectada al backend real:
- Carga facultades desde la base de datos (profile/profile_manager.py)
- Registra al estudiante mediante auth/register.py
- Solicita el código de verificación de correo y lo confirma
  mediante auth/register.py::verify_email

Rediseño visual (glassmorfismo): solo cambia la presentación.
Los métodos con lógica no fueron modificados.
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
    QFrame,
)
from PyQt6.QtCore import Qt

from database.db_connection import get_session
from profile.profile_manager import list_facultades
from security.input_validation import ValidationError
from auth.register import register_user, send_verification_email, verify_email
from gui.verification_code_dialog import mostrar_codigo_desarrollo
from gui.theme import estilizar_boton, sombra_suave, espaciar_letras

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

        # Tarjeta de cristal centrada
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 20, 24, 20)

        tarjeta = QFrame()
        tarjeta.setObjectName("card")
        tarjeta.setFixedWidth(430)
        sombra_suave(tarjeta)
        raiz.addWidget(tarjeta, 0, Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(tarjeta)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 28, 40, 26)

        # Título / marca
        titulo = QLabel("Xavium")
        titulo.setObjectName("brandSmall")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        espaciar_letras(titulo, 1.5)
        layout.addWidget(titulo)

        subtitulo = QLabel("Crea tu cuenta de estudiante")
        subtitulo.setObjectName("subtitle")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitulo)

        layout.addSpacing(6)

        # Nombre
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo")
        self.input_nombre.setFixedHeight(42)
        layout.addWidget(self.input_nombre)

        # Edad
        self.input_edad = QLineEdit()
        self.input_edad.setPlaceholderText("Edad")
        self.input_edad.setFixedHeight(42)
        layout.addWidget(self.input_edad)

        # Correo institucional
        self.input_correo = QLineEdit()
        self.input_correo.setPlaceholderText("Correo institucional")
        self.input_correo.setFixedHeight(42)
        layout.addWidget(self.input_correo)

        # Facultad (cargada dinámicamente desde la BD)
        self.combo_facultad = QComboBox()
        self.combo_facultad.setFixedHeight(42)
        self.combo_facultad.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.combo_facultad)
        self._cargar_facultades()

        # Contraseña
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setFixedHeight(42)
        layout.addWidget(self.input_password)

        # Confirmar contraseña
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setPlaceholderText("Confirmar contraseña")
        self.input_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password_confirm.setFixedHeight(42)
        layout.addWidget(self.input_password_confirm)

        layout.addSpacing(4)

        # Botón registrarse
        self.boton_registrar = QPushButton("Registrarse")
        self.boton_registrar.setFixedHeight(46)
        estilizar_boton(self.boton_registrar, "primary")
        self.boton_registrar.clicked.connect(self.on_registrar_click)
        layout.addWidget(self.boton_registrar)

        # Enlace hacia login
        fila_login = QHBoxLayout()
        fila_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila_login.setSpacing(2)

        texto_pregunta = QLabel("¿Ya tienes cuenta?")
        texto_pregunta.setObjectName("muted")
        fila_login.addWidget(texto_pregunta)

        self.boton_ir_login = QPushButton("Inicia sesión")
        estilizar_boton(self.boton_ir_login, "link", brillo=False)
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
                session.commit()
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
                    session.commit()
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
                    session.commit()
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