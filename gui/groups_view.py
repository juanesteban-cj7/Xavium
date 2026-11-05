from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QFrame, QDialog, QLineEdit, QDialogButtonBox, QMessageBox, QTextEdit
from sqlalchemy.orm import joinedload

from database.db_connection import get_session
from database.models import Usuario
from chat.message_store import enviar_mensaje_grupo, obtener_mensajes_grupo, obtener_o_crear_conversacion_grupo
from groups.group_manager import crear_grupo, listar_grupos, listar_miembros, agregar_miembro
from gui.app_header import AppHeader
from gui.theme import estilizar_boton, pulir_lista


class GroupsView(QWidget):
    def __init__(self, on_menu=None, on_inicio=None, on_contactos=None,
                 on_grupos=None, on_buscar=None):
        super().__init__()
        self.usuario_id = None
        self.selected_group = None
        self.group_conversation_id = None
        self.group_member_names = {}
        self._group_timer = QTimer(self)
        self._group_timer.setInterval(1500)
        self._group_timer.timeout.connect(self._refrescar_chat_grupo)

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
        left.setFixedWidth(250)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0,0,0,0)
        ll.setSpacing(0)
        top = QHBoxLayout()
        top.setContentsMargins(0,0,14,0)
        group_list_title = QLabel("Lista de grupos")
        group_list_title.setObjectName("panelTitle")
        top.addWidget(group_list_title)
        top.addStretch()
        add = QPushButton("+")
        add.setFixedSize(38,38)
        estilizar_boton(add, "roundAdd")
        add.clicked.connect(self._crear_grupo)
        top.addWidget(add)
        ll.addLayout(top)

        linea_izq = QFrame()
        linea_izq.setObjectName("hline")
        linea_izq.setFixedHeight(1)
        ll.addWidget(linea_izq)

        self.groups = QListWidget()
        self.groups.setObjectName("flatList")
        self.groups.itemClicked.connect(self._abrir_grupo)
        pulir_lista(self.groups)
        ll.addWidget(self.groups)
        body.addWidget(left)

        center = QFrame()
        center.setObjectName("panel")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(22,18,22,18)
        cl.setSpacing(12)
        title_row = QHBoxLayout()
        self.group_title = QLabel("Selecciona un grupo")
        self.group_title.setObjectName("sectionTitle")
        title_row.addWidget(self.group_title)
        title_row.addStretch()
        add_member = QPushButton("+ Agregar miembro")
        add_member.setVisible(False)
        add_member.setFixedHeight(40)
        estilizar_boton(add_member, "primary")
        add_member.clicked.connect(self._agregar_miembro)
        self.add_member = add_member
        title_row.addWidget(add_member)
        cl.addLayout(title_row)
        self.group_content = QTextEdit()
        self.group_content.setReadOnly(True)
        self.group_content.setPlaceholderText("Los mensajes del grupo aparecerán aquí.")
        cl.addWidget(self.group_content,1)
        message_row = QHBoxLayout()
        message_row.setSpacing(10)
        self.group_message_input = QLineEdit()
        self.group_message_input.setPlaceholderText("Escribe un mensaje para el grupo...")
        self.group_message_input.setFixedHeight(46)
        self.group_message_input.returnPressed.connect(self._enviar_mensaje_grupo)
        message_row.addWidget(self.group_message_input,1)
        self.group_send_button = QPushButton("Enviar")
        self.group_send_button.setFixedHeight(46)
        self.group_send_button.setMinimumWidth(110)
        estilizar_boton(self.group_send_button, "primary")
        self.group_send_button.clicked.connect(self._enviar_mensaje_grupo)
        message_row.addWidget(self.group_send_button)
        cl.addLayout(message_row)
        body.addWidget(center,1)

        right = QFrame()
        right.setObjectName("panel")
        right.setFixedWidth(230)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0,0,0,0)
        rl.setSpacing(0)
        titulo_miembros = QLabel("Lista de miembros")
        titulo_miembros.setObjectName("panelTitle")
        rl.addWidget(titulo_miembros)
        linea_der = QFrame()
        linea_der.setObjectName("hline")
        linea_der.setFixedHeight(1)
        rl.addWidget(linea_der)
        self.members = QListWidget()
        self.members.setObjectName("flatList")
        pulir_lista(self.members)
        rl.addWidget(self.members,1)
        body.addWidget(right)

        root.addLayout(body,1)

    def set_usuario(self, usuario_id):
        self._group_timer.stop()
        self.usuario_id = usuario_id
        self.selected_group = None
        self.group_conversation_id = None
        self.add_member.setVisible(False)
        self.group_content.clear()
        self.group_message_input.clear()
        self._cargar_grupos()

    def _cargar_grupos(self):
        self.groups.clear()
        with get_session() as session:
            groups = listar_grupos(session, self.usuario_id)
        for g in groups:
            item = QListWidgetItem(g.nombre)
            item.setData(Qt.ItemDataRole.UserRole, g.id)
            self.groups.addItem(item)

    def _abrir_grupo(self, item):
        gid = item.data(Qt.ItemDataRole.UserRole)
        self._group_timer.stop()
        self.selected_group = gid
        self.group_conversation_id = None
        self.group_member_names = {}
        self.group_title.setText(item.text())
        self.group_content.clear()
        self.group_message_input.setEnabled(True)
        self.group_send_button.setEnabled(True)
        self.add_member.setVisible(True)
        self.members.clear()
        try:
            with get_session() as session:
                members = listar_miembros(session, gid, self.usuario_id)
            for u in members:
                item = QListWidgetItem(f"{u.nombre} · {u.facultad.nombre if u.facultad else ''}")
                self.members.addItem(item)
                self.group_member_names[u.id] = u.nombre
            self._preparar_chat_grupo()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def _preparar_chat_grupo(self):
        with get_session() as session:
            conversacion = obtener_o_crear_conversacion_grupo(
                session, self.selected_group, self.usuario_id
            )
            self.group_conversation_id = conversacion.id
            session.commit()
        self._refrescar_chat_grupo()
        self._group_timer.start()

    def _refrescar_chat_grupo(self):
        if not self.selected_group or not self.usuario_id:
            return
        try:
            with get_session() as session:
                mensajes = obtener_mensajes_grupo(
                    session, self.selected_group, self.usuario_id
                )
            lineas = []
            for mensaje in mensajes:
                autor = "Tú" if mensaje.es_propio else self.group_member_names.get(
                    mensaje.emisor_id, "Miembro"
                )
                lineas.append(f"{autor}: {mensaje.contenido}")
            self.group_content.setPlainText("\n\n".join(lineas))
            cursor = self.group_content.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.group_content.setTextCursor(cursor)
        except Exception as exc:
            self._group_timer.stop()
            QMessageBox.warning(self, "Error", str(exc))

    def _enviar_mensaje_grupo(self):
        text = self.group_message_input.text().strip()
        if not text or not self.selected_group:
            return
        try:
            with get_session() as session:
                enviar_mensaje_grupo(
                    session, self.selected_group, self.usuario_id, text
                )
                session.commit()
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo enviar", str(exc))
            return
        self.group_message_input.clear()
        self._refrescar_chat_grupo()

    def _crear_grupo(self):
        d = QDialog(self)
        d.setWindowTitle("Crear grupo")
        lay = QVBoxLayout(d)
        lay.addWidget(QLabel("Nombre del grupo:"))
        e = QLineEdit()
        lay.addWidget(e)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(d.accept); buttons.rejected.connect(d.reject)
        lay.addWidget(buttons)
        if d.exec() == QDialog.DialogCode.Accepted:
            try:
                with get_session() as session:
                    crear_grupo(session, self.usuario_id, e.text())
                    session.commit()
                self._cargar_grupos()
            except Exception as exc:
                QMessageBox.warning(self, "No se pudo crear", str(exc))

    def _agregar_miembro(self):
        if not self.selected_group:
            return
        d = QDialog(self)
        d.setWindowTitle("Agregar miembro")
        lay = QVBoxLayout(d)
        lista = QListWidget()
        lay.addWidget(lista,1)
        with get_session() as session:
            current = {u.id for u in listar_miembros(session, self.selected_group, self.usuario_id)}
            users = session.query(Usuario).options(joinedload(Usuario.facultad)).filter(Usuario.id != self.usuario_id).order_by(Usuario.nombre).all()
        for u in users:
            if u.id not in current:
                item = QListWidgetItem(f"{u.nombre} · {u.facultad.nombre if u.facultad else ''}")
                item.setData(Qt.ItemDataRole.UserRole,u.id)
                lista.addItem(item)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(d.accept); buttons.rejected.connect(d.reject)
        lay.addWidget(buttons)
        if d.exec() == QDialog.DialogCode.Accepted and lista.currentItem():
            uid=lista.currentItem().data(Qt.ItemDataRole.UserRole)
            try:
                with get_session() as session:
                    agregar_miembro(session,self.selected_group,self.usuario_id,uid)
                    session.commit()
                self._abrir_grupo(self.groups.currentItem())
            except Exception as exc:
                QMessageBox.warning(self,"No se pudo agregar",str(exc))
