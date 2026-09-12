"""
chat_view.py
Vista de conversacion entre el usuario actual y otro estudiante.
"""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chat.message_store import (
    enviar_mensaje,
    marcar_mensajes_como_leidos,
    obtener_mensajes,
    obtener_o_crear_conversacion,
)
from database.db_connection import get_session

INPUT_STYLE = """
QLineEdit {
    background-color: white;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    color: #1E1E1E;
}
"""

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: white;
    color: #1E5AA8;
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 8px 14px;
}
QPushButton:hover {
    background-color: #E6EEF8;
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


class ChatView(QWidget):
    def __init__(self, on_volver=None):
        super().__init__()
        self.on_volver = on_volver
        self.usuario_actual_id = None
        self.otro_usuario_id = None
        self.conversacion_id = None

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)
        self.setLayout(layout)

        fila_superior = QHBoxLayout()
        self.boton_volver = QPushButton("<- Volver")
        self.boton_volver.setStyleSheet(LINK_BUTTON_STYLE)
        self.boton_volver.clicked.connect(self._volver)
        fila_superior.addWidget(self.boton_volver)
        fila_superior.addStretch()
        layout.addLayout(fila_superior)

        self.titulo = QLabel("Chat")
        self.titulo.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        layout.addWidget(self.titulo)

        self.historial = QTextEdit()
        self.historial.setReadOnly(True)
        self.historial.setStyleSheet(
            "QTextEdit { background-color: white; border-radius: 8px; "
            "padding: 8px; color: #1E1E1E; font-size: 13px; }"
        )
        layout.addWidget(self.historial, stretch=1)

        fila_mensaje = QHBoxLayout()
        self.input_mensaje = QLineEdit()
        self.input_mensaje.setPlaceholderText("Escribe un mensaje...")
        self.input_mensaje.setStyleSheet(INPUT_STYLE)
        self.input_mensaje.returnPressed.connect(self._enviar)
        fila_mensaje.addWidget(self.input_mensaje, stretch=1)

        self.boton_enviar = QPushButton("Enviar")
        self.boton_enviar.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.boton_enviar.clicked.connect(self._enviar)
        fila_mensaje.addWidget(self.boton_enviar)
        layout.addLayout(fila_mensaje)

        self._timer = QTimer(self)
        self._timer.setInterval(1500)
        self._timer.timeout.connect(self._refrescar_mensajes)

    def preparar(self, usuario_actual_id: str, otro_usuario_id: str, nombre: str):
        self.usuario_actual_id = usuario_actual_id
        self.otro_usuario_id = otro_usuario_id
        self.conversacion_id = None
        self.titulo.setText(f"Chat con {nombre}")
        self.historial.clear()
        self.input_mensaje.clear()

        try:
            with get_session() as session:
                conversacion = obtener_o_crear_conversacion(
                    session, usuario_actual_id, otro_usuario_id
                )
            self.conversacion_id = conversacion.id
            self._refrescar_mensajes()
            self._timer.start()
        except Exception as exc:
            QMessageBox.critical(
                self, "No se pudo abrir el chat", f"Ocurrio un error:\n{exc}"
            )

    def _refrescar_mensajes(self):
        if not self.conversacion_id or not self.usuario_actual_id:
            return

        try:
            with get_session() as session:
                mensajes = obtener_mensajes(
                    session, self.conversacion_id, self.usuario_actual_id
                )
                marcar_mensajes_como_leidos(
                    session, self.conversacion_id, self.usuario_actual_id
                )
        except Exception as exc:
            self._mostrar_error("No se pudieron cargar los mensajes", exc)
            return

        texto = []
        for mensaje in mensajes:
            autor = "Tu" if mensaje.es_propio else self.titulo.text()[9:]
            texto.append(f"{autor}: {mensaje.contenido}")
        self.historial.setPlainText("\n\n".join(texto))
        cursor = self.historial.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.historial.setTextCursor(cursor)

    def _enviar(self):
        texto = self.input_mensaje.text().strip()
        if not texto or not self.conversacion_id or not self.usuario_actual_id:
            return

        try:
            with get_session() as session:
                enviar_mensaje(
                    session, self.conversacion_id, self.usuario_actual_id, texto
                )
        except Exception as exc:
            self._mostrar_error("No se pudo enviar el mensaje", exc)
            return

        self.input_mensaje.clear()
        self._refrescar_mensajes()

    def _mostrar_error(self, titulo: str, error: Exception):
        QMessageBox.warning(self, titulo, str(error))

    def _volver(self):
        self._timer.stop()
        if self.on_volver:
            self.on_volver()

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)
