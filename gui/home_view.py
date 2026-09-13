from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame

from database.db_connection import get_session
from chat.message_store import listar_conversaciones_usuario
from gui.app_header import AppHeader


class HomeView(QWidget):
    def __init__(self, on_logout=None, on_menu=None, on_inicio=None,
                 on_contactos=None, on_grupos=None, on_buscar=None, on_abrir_chat=None):
        super().__init__()
        self.usuario_id = None
        self.on_abrir_chat = on_abrir_chat

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        self.header = AppHeader(on_inicio=on_inicio, on_contactos=on_contactos,
                                on_grupos=on_grupos, on_buscar=on_buscar)
        if on_menu:
            self.header.menu_clicked.connect(on_menu)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(0)

        left = QFrame()
        left.setStyleSheet("QFrame { border: 3px solid #111; border-top: none; background: white; }")
        left.setFixedWidth(225)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("chats recientes")
        title.setStyleSheet("font-size: 17px; padding: 10px; border-bottom: 3px solid #111; color: #111;")
        left_lay.addWidget(title)

        self.chats = QListWidget()
        self.chats.setStyleSheet("""
        QListWidget { border: none; color: #111; font-size: 14px; background: white; }
        QListWidget::item { padding: 12px 8px; border-bottom: 1px solid #DDD; }
        QListWidget::item:selected { background: #EAEAEA; }
        """)
        self.chats.itemClicked.connect(self._abrir_chat)
        left_lay.addWidget(self.chats)
        body.addWidget(left)

        self.chat_placeholder = QLabel("(AQUÍ APARECE EL CHAT UNA VEZ SE HAGA CLICK EN EL)")
        self.chat_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_placeholder.setWordWrap(True)
        self.chat_placeholder.setStyleSheet("""
            QLabel { border: 3px solid #111; border-left: none; border-top: none;
            background: white; color: #111; font-size: 24px; padding: 30px; }
        """)
        body.addWidget(self.chat_placeholder, 1)

        root.addLayout(body, 1)

    def set_usuario(self, usuario_id):
        self.usuario_id = usuario_id
        self._cargar_chats()

    def set_nombre_usuario(self, nombre):
        self._cargar_chats()

    def _cargar_chats(self):
        self.chats.clear()
        if not self.usuario_id:
            return
        try:
            with get_session() as session:
                resumenes = listar_conversaciones_usuario(session, self.usuario_id)
            for r in resumenes:
                item = QListWidgetItem(f"{r.otro_usuario_nombre}\n{r.ultimo_mensaje or ''}")
                item.setData(Qt.ItemDataRole.UserRole, (r.otro_usuario_id, r.otro_usuario_nombre))
                self.chats.addItem(item)
        except Exception:
            pass

    def _abrir_chat(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and self.on_abrir_chat:
            self.on_abrir_chat(*data)
