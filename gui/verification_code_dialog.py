from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from gui.theme import estilizar_boton


class VerificationCodeDialog(QDialog):
    def __init__(self, parent, title: str, message: str, token: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(16)

        mensaje = QLabel(message)
        mensaje.setWordWrap(True)
        layout.addWidget(mensaje)

        self.input_codigo = QLineEdit(token)
        self.input_codigo.setObjectName("codeField")
        self.input_codigo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_codigo.setReadOnly(True)
        self.input_codigo.selectAll()
        layout.addWidget(self.input_codigo)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)
        self.boton_copiar = QPushButton("Copiar código")
        self.boton_copiar.setFixedHeight(44)
        estilizar_boton(self.boton_copiar)
        self.boton_copiar.clicked.connect(self._copiar_codigo)
        fila_botones.addWidget(self.boton_copiar)

        boton_verificar = QPushButton("Verificar")
        boton_verificar.setFixedHeight(44)
        estilizar_boton(boton_verificar, "primary")
        boton_verificar.clicked.connect(self.accept)
        fila_botones.addWidget(boton_verificar)

        layout.addLayout(fila_botones)

    def _copiar_codigo(self):
        self.input_codigo.selectAll()
        self.input_codigo.copy()
        self.boton_copiar.setText("¡Copiado!")


def mostrar_codigo_desarrollo(
    parent, title: str, message: str, token: str
) -> str | None:
    dialogo = VerificationCodeDialog(parent, title, message, token)
    if dialogo.exec() == QDialog.DialogCode.Accepted:
        return dialogo.input_codigo.text()
    return None
