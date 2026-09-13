from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame


HEADER_STYLE = """
QFrame#header {
    background: white;
    border: 3px solid #111111;
    border-bottom: 3px solid #111111;
}
QPushButton {
    background: transparent;
    border: none;
    color: #111111;
    font-size: 20px;
    padding: 8px 16px;
}
QPushButton:hover { background: #F1F1F1; }
QPushButton#hamburger {
    font-size: 28px;
    padding: 2px 10px;
}
QPushButton#search {
    border: 4px solid #D9232E;
    padding: 2px 9px;
}
"""


class AppHeader(QFrame):
    menu_clicked = pyqtSignal()

    def __init__(self, on_inicio=None, on_contactos=None, on_grupos=None, on_buscar=None):
        super().__init__()
        self.setObjectName("header")
        self.setFixedHeight(72)
        self.setStyleSheet(HEADER_STYLE)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(4)

        self.menu = QPushButton("☰")
        self.menu.setObjectName("hamburger")
        self.menu.setToolTip("Menú")
        self.menu.clicked.connect(self.menu_clicked.emit)
        lay.addWidget(self.menu)

        self.inicio = QPushButton("Inicio")
        self.contactos = QPushButton("Contactos")
        self.grupos = QPushButton("Grupos")
        self.buscar = QPushButton("Buscar")
        self.buscar.setObjectName("search")

        for button in (self.inicio, self.contactos, self.grupos):
            lay.addWidget(button)
        lay.addStretch()
        lay.addWidget(self.buscar)

        if on_inicio:
            self.inicio.clicked.connect(on_inicio)
        if on_contactos:
            self.contactos.clicked.connect(on_contactos)
        if on_grupos:
            self.grupos.clicked.connect(on_grupos)
        if on_buscar:
            self.buscar.clicked.connect(on_buscar)
