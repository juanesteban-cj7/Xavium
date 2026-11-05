from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFrame, QLabel

from gui.theme import estilizar_boton, sombra_suave, espaciar_letras


HEADER_STYLE = """
QFrame#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(255, 255, 255, 30%), stop:1 rgba(255, 255, 255, 13%));
    border: 1px solid rgba(255, 255, 255, 50%);
    border-radius: 22px;
}
QLabel#headerBrand {
    background: transparent;
    color: white;
    font-size: 22px;
    font-weight: 800;
    padding: 0px 18px 0px 4px;
}
QPushButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    color: white;
    font-size: 15px;
    font-weight: 600;
    padding: 9px 20px;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 22%);
    border: 1px solid rgba(255, 255, 255, 48%);
}
QPushButton:pressed {
    background: rgba(255, 255, 255, 12%);
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton#hamburger {
    font-size: 24px;
    padding: 2px 14px;
}
QPushButton#search {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2f9bff, stop:1 #1f4fd8);
    border: 1px solid rgba(255, 255, 255, 60%);
    font-weight: 700;
    padding: 9px 24px;
}
QPushButton#search:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #55b2ff, stop:1 #2f66f0);
    border: 1px solid white;
}
QPushButton#search:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1f86e6, stop:1 #173fb5);
}
"""


class AppHeader(QFrame):
    menu_clicked = pyqtSignal()

    def __init__(self, on_inicio=None, on_contactos=None, on_grupos=None, on_buscar=None):
        super().__init__()
        self.setObjectName("header")
        self.setFixedHeight(72)
        self.setStyleSheet(HEADER_STYLE)
        sombra_suave(self, desenfoque=36, opacidad=80, desplazamiento=8)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(6)

        self.menu = QPushButton("☰")
        self.menu.setObjectName("hamburger")
        self.menu.setToolTip("Menú")
        self.menu.clicked.connect(self.menu_clicked.emit)
        estilizar_boton(self.menu, "hamburger", brillo=False)
        lay.addWidget(self.menu)

        marca = QLabel("Xavium")
        marca.setObjectName("headerBrand")
        espaciar_letras(marca, 1.2)
        lay.addWidget(marca)

        self.inicio = QPushButton("Inicio")
        self.contactos = QPushButton("Contactos")
        self.grupos = QPushButton("Grupos")
        self.buscar = QPushButton("Buscar")
        self.buscar.setObjectName("search")

        for button in (self.inicio, self.contactos, self.grupos):
            estilizar_boton(button, brillo=False)
            lay.addWidget(button)
        lay.addStretch()
        estilizar_boton(self.buscar, "search", brillo=False)
        lay.addWidget(self.buscar)

        if on_inicio:
            self.inicio.clicked.connect(on_inicio)
        if on_contactos:
            self.contactos.clicked.connect(on_contactos)
        if on_grupos:
            self.grupos.clicked.connect(on_grupos)
        if on_buscar:
            self.buscar.clicked.connect(on_buscar)
