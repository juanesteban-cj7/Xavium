"""
home_view.py
Pantalla mínima que se muestra tras un login exitoso.

Esta es una vista temporal/placeholder mientras se desarrollan las
vistas reales de búsqueda (search_view.py) y chat (chat_view.py) en
las Fases 4-6. Su propósito actual es permitir probar el flujo
completo de login -> sesión activa -> logout.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: white;
    color: #1E5AA8;
    font-size: 14px;
    font-weight: bold;
    border-radius: 8px;
    padding: 8px 20px;
}
QPushButton:hover {
    background-color: #E6EEF8;
}
QPushButton:pressed {
    background-color: #C9DAF0;
}
"""


class HomeView(QWidget):
    def __init__(self, on_logout=None):
        """
        on_logout: callback que se ejecuta al presionar "Cerrar sesión".
        """
        super().__init__()
        self.on_logout = on_logout

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        self.setLayout(layout)

        self.label_bienvenida = QLabel("")
        self.label_bienvenida.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_bienvenida.setStyleSheet(
            "color: white; font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(self.label_bienvenida)

        subtitulo = QLabel(
            "Tu cuenta fue verificada y la sesión quedó activa.\n"
            "Las funciones de búsqueda y chat llegarán en las próximas fases."
        )
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet("color: #D6E4F5; font-size: 13px;")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        layout.addSpacing(10)

        self.boton_logout = QPushButton("Cerrar sesión")
        self.boton_logout.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.boton_logout.setFixedWidth(180)
        self.boton_logout.clicked.connect(self._cerrar_sesion)
        layout.addWidget(self.boton_logout, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_nombre_usuario(self, nombre: str):
        self.label_bienvenida.setText(f"¡Bienvenido, {nombre}!")

    def _cerrar_sesion(self):
        if self.on_logout:
            self.on_logout()