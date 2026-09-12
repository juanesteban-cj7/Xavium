from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class VerificationCodeDialog(QDialog):
    def __init__(self, parent, title: str, message: str, token: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message))

        self.input_codigo = QLineEdit(token)
        self.input_codigo.setReadOnly(True)
        self.input_codigo.selectAll()
        layout.addWidget(self.input_codigo)

        fila_botones = QHBoxLayout()
        self.boton_copiar = QPushButton("Copiar código")
        self.boton_copiar.clicked.connect(self._copiar_codigo)
        fila_botones.addWidget(self.boton_copiar)

        boton_verificar = QPushButton("Verificar")
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
