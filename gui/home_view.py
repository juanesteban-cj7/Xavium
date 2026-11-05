from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame

from database.db_connection import get_session
from chat.message_store import listar_conversaciones_usuario
from gui.app_header import AppHeader
from gui.theme import pulir_lista


class HomeView(QWidget):
    def __init__(self, on_logout=None, on_menu=None, on_inicio=None,
                 on_contactos=None, on_grupos=None, on_buscar=None, on_abrir_chat=None):
        super().__init__()
        self.usuario_id = None
        self.on_abrir_chat = on_abrir_chat

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        self.header = AppHeader(on_inicio=on_inicio, on_contactos=on_contactos,
                                on_grupos=on_grupos, on_buscar=on_buscar)
        if on_menu:
            self.header.menu_clicked.connect(on_menu)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(14)

        left = QFrame()
        left.setObjectName("panel")
        left.setFixedWidth(270)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        title = QLabel("chats recientes")
        title.setObjectName("panelTitle")
        left_lay.addWidget(title)

        linea = QFrame()
        linea.setObjectName("hline")
        linea.setFixedHeight(1)
        left_lay.addWidget(linea)

        self.chats = QListWidget()
        self.chats.setObjectName("flatList")
        self.chats.itemClicked.connect(self._abrir_chat)
        pulir_lista(self.chats)
        left_lay.addWidget(self.chats)
        body.addWidget(left)

        self.chat_placeholder = QLabel("(AQUÍ APARECE EL CHAT UNA VEZ SE HAGA CLICK EN EL)")
        self.chat_placeholder.setObjectName("placeholderPanel")
        self.chat_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_placeholder.setWordWrap(True)
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
