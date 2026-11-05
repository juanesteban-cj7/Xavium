from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton

from gui.theme import estilizar_boton, sombra_suave


class MenuOverlay(QFrame):
    def __init__(self, on_logout=None):
        super().__init__()
        self.setObjectName("menuOverlay")
        self.setFixedWidth(260)
        self.setStyleSheet("""
        QFrame#menuOverlay {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #184aa0, stop:1 #0a255a);
            border: 1px solid rgba(255, 255, 255, 50%);
            border-radius: 22px;
        }
        QFrame#menuLine {
            background: rgba(255, 255, 255, 26%);
            border: none;
        }
        QPushButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 13px;
            text-align: left;
            padding: 13px 18px;
            font-size: 15px;
            font-weight: 600;
            color: white;
        }
        QPushButton:disabled {
            color: rgba(255, 255, 255, 64%);
            background: transparent;
            border: 1px solid transparent;
        }
        QPushButton:hover:enabled {
            background: rgba(255, 255, 255, 21%);
            border: 1px solid rgba(255, 255, 255, 42%);
        }
        QPushButton:pressed:enabled {
            background: rgba(255, 255, 255, 12%);
            padding-top: 13px;
            padding-bottom: 13px;
        }
        QPushButton#logout { color: #ffb9b9; font-weight: 700; }
        QPushButton#logout:hover:enabled {
            background: rgba(255, 90, 90, 30%);
            border: 1px solid rgba(255, 150, 150, 75%);
            color: white;
        }
        """)
        sombra_suave(self, desenfoque=50, opacidad=110, desplazamiento=14)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(4)

        for text in ("Tu perfil", "Estadísticas", "Privacidad y seguridad", "Ayuda"):
            b = QPushButton(text)
            b.setEnabled(False)
            lay.addWidget(b)

        linea = QFrame()
        linea.setObjectName("menuLine")
        linea.setFixedHeight(1)
        lay.addWidget(linea)

        self.logout = QPushButton("Cerrar sesión")
        self.logout.setObjectName("logout")
        estilizar_boton(self.logout, "logout", brillo=False)
        if on_logout:
            self.logout.clicked.connect(on_logout)
        lay.addWidget(self.logout)

        self.hide()
