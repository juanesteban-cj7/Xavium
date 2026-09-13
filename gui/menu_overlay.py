from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton


class MenuOverlay(QFrame):
    def __init__(self, on_logout=None):
        super().__init__()
        self.setObjectName("menuOverlay")
        self.setFixedWidth(250)
        self.setStyleSheet("""
        QFrame#menuOverlay {
            background: white;
            border: 3px solid #111;
        }
        QPushButton {
            background: white;
            border: none;
            text-align: left;
            padding: 14px 18px;
            font-size: 16px;
            color: #222;
        }
        QPushButton:disabled {
            color: #999;
            background: #F7F7F7;
        }
        QPushButton:hover:enabled { background: #EEEEEE; }
        QPushButton#logout { color: #C51F2A; font-weight: bold; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        for text in ("Tu perfil", "Estadísticas", "Privacidad y seguridad", "Ayuda"):
            b = QPushButton(text)
            b.setEnabled(False)
            lay.addWidget(b)

        self.logout = QPushButton("Cerrar sesión")
        self.logout.setObjectName("logout")
        if on_logout:
            self.logout.clicked.connect(on_logout)
        lay.addWidget(self.logout)

        self.hide()
