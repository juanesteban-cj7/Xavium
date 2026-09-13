from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFrame, QDialog, QLineEdit, QMessageBox, QColorDialog,
    QCheckBox, QDialogButtonBox
)
from sqlalchemy.orm import joinedload

from database.db_connection import get_session
from database.models import Usuario
from contacts.contact_manager import (
    listar_contactos, agregar_contacto, eliminar_contacto,
    listar_categorias, crear_categoria, cambiar_nombre_categoria,
    cambiar_color_categoria, eliminar_categoria, contactos_de_categoria,
    establecer_contactos_categoria
)
from gui.app_header import AppHeader


class ContactsView(QWidget):
    def __init__(self, on_menu=None, on_inicio=None, on_contactos=None,
                 on_grupos=None, on_buscar=None, on_abrir_chat=None):
        super().__init__()
        self.usuario_id = None
        self.selected_category = None
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

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setStyleSheet("QFrame { background:white; border:3px solid #111; border-top:none; }")
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(0, 0, 0, 0)

        add = QPushButton("＋  Añadir clasificación")
        add.setStyleSheet("QPushButton { padding:12px 8px; border:none; border-bottom:3px solid #111; font-size:14px; color:#111; background:#FFF; } QPushButton:hover{background:#EEE;}")
        add.clicked.connect(self._crear_categoria)
        sl.addWidget(add)

        self.category_list = QListWidget()
        self.category_list.setStyleSheet("""
        QListWidget { border:none; color:#111; background:white; }
        QListWidget::item { padding:10px 7px; border-bottom:2px solid #111; }
        QListWidget::item:selected { background:#EEE; }
        """)
        self.category_list.itemClicked.connect(self._seleccionar_categoria)
        sl.addWidget(self.category_list)
        body.addWidget(self.sidebar)

        right = QFrame()
        right.setStyleSheet("QFrame { background:white; border:3px solid #111; border-left:none; border-top:none; }")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(22, 18, 22, 18)

        top = QHBoxLayout()
        self.title = QLabel("Tus categorías")
        self.title.setStyleSheet("font-size:22px; color:#111; font-weight:bold;")
        top.addWidget(self.title)
        top.addStretch()
        self.add_contact_btn = QPushButton("+ Agregar contacto")
        self.add_contact_btn.setStyleSheet("""
            QPushButton { background:#35A853; color:white; border:none; border-radius:5px; padding:9px 14px; font-weight:bold; }
            QPushButton:hover { background:#2E9148; }
        """)
        self.add_contact_btn.clicked.connect(self._agregar_contacto_dialog)
        top.addWidget(self.add_contact_btn)
        rl.addLayout(top)

        self.info = QLabel("Crea una clasificación en el panel izquierdo. Después podrás agregar contactos a ella.")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color:#555; font-size:14px; padding:8px 0;")
        rl.addWidget(self.info)

        self.contacts = QListWidget()
        self.contacts.setStyleSheet("""
        QListWidget { border:1px solid #CCC; color:#111; background:white; }
        QListWidget::item { padding:13px; border-bottom:1px solid #DDD; }
        QListWidget::item:selected { background:#EEE; }
        """)
        self.contacts.itemDoubleClicked.connect(self._abrir_chat)
        rl.addWidget(self.contacts, 1)
        body.addWidget(right, 1)

        root.addLayout(body, 1)

    def set_usuario(self, usuario_id):
        self.usuario_id = usuario_id
        self._cargar_categorias()
        self._mostrar_sin_categoria()

    def _cargar_categorias(self):
        self.category_list.clear()
        with get_session() as session:
            cats = listar_categorias(session, self.usuario_id)
        for c in cats:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, c)
            item.setSizeHint(self._category_row_size())
            self.category_list.addItem(item)

            row = QWidget()
            row.setStyleSheet(f"QWidget{{background:white;border-left:6px solid {c['color']};}}")
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(8, 0, 4, 0)
            label = QLabel(c["nombre"])
            label.setStyleSheet("color:#111; font-size:14px;")
            row_lay.addWidget(label, 1)
            dots = QPushButton("⋮")
            dots.setFixedWidth(32)
            dots.setStyleSheet("""
                QPushButton { border:none; background:transparent; color:#111;
                              font-size:22px; padding:0; }
                QPushButton:hover { background:#DDD; }
            """)
            dots.clicked.connect(lambda checked=False, cat=c: self._category_options(cat))
            row_lay.addWidget(dots)
            self.category_list.setItemWidget(item, row)

    def _category_row_size(self):
        from PyQt6.QtCore import QSize
        return QSize(200, 44)

    def _mostrar_sin_categoria(self):
        self.selected_category = None
        self.title.setText("Tus categorías")
        self.info.setText("Crea una clasificación en el panel izquierdo. Después podrás agregar contactos a ella.")
        self.contacts.clear()
        with get_session() as session:
            contacts = listar_contactos(session, self.usuario_id)
        for c in contacts:
            self.contacts.addItem(QListWidgetItem(f"{c['nombre']}  ·  {c['facultad']}"))

    def _seleccionar_categoria(self, item):
        c = item.data(Qt.ItemDataRole.UserRole)
        self.selected_category = c
        self.title.setText(c["nombre"])
        self.info.setText("Usa los tres puntos (⋮) de la categoría para editarla, cambiar su nombre/color o eliminarla.")
        self._render_category(c["id"])

    def _render_category(self, category_id):
        self.contacts.clear()
        with get_session() as session:
            rows = contactos_de_categoria(session, self.usuario_id, category_id)
        for c in rows:
            item = QListWidgetItem(f"{c['nombre']}  ·  {c['facultad']}")
            item.setData(Qt.ItemDataRole.UserRole, (c["usuario_id"], c["nombre"]))
            self.contacts.addItem(item)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def _crear_categoria(self):
        nombre, ok = self._input("Nueva clasificación", "Nombre de la clasificación:")
        if not ok:
            return
        color = QColorDialog.getColor()
        if not color.isValid():
            color_name = "#1E5AA8"
        else:
            color_name = color.name()
        try:
            with get_session() as session:
                crear_categoria(session, self.usuario_id, nombre, color_name)
                session.commit()
            self._cargar_categorias()
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo crear", str(exc))

    def _input(self, title, label, default=""):
        d = QDialog(self)
        d.setWindowTitle(title)
        lay = QVBoxLayout(d)
        lay.addWidget(QLabel(label))
        e = QLineEdit(default)
        lay.addWidget(e)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(d.accept)
        buttons.rejected.connect(d.reject)
        lay.addWidget(buttons)
        accepted = d.exec() == QDialog.DialogCode.Accepted
        return (e.text().strip(), accepted)

    def _category_options(self, category):
        menu = QDialog(self)
        menu.setWindowTitle(f"Opciones: {category['nombre']}")
        lay = QVBoxLayout(menu)
        buttons = []
        for text in ("Editar contactos", "Cambiar nombre", "Cambiar color", "Eliminar"):
            b = QPushButton(text)
            lay.addWidget(b)
            buttons.append(b)
        buttons[0].clicked.connect(lambda: (menu.accept(), self._editar_contactos(category)))
        buttons[1].clicked.connect(lambda: (menu.accept(), self._cambiar_nombre(category)))
        buttons[2].clicked.connect(lambda: (menu.accept(), self._cambiar_color(category)))
        buttons[3].clicked.connect(lambda: (menu.accept(), self._eliminar_categoria(category)))
        menu.exec()

    def _editar_contactos(self, category):
        with get_session() as session:
            all_contacts = listar_contactos(session, self.usuario_id)
            current = {c["id"] for c in contactos_de_categoria(session, self.usuario_id, category["id"])}
        d = QDialog(self)
        d.setWindowTitle(f"Contactos de {category['nombre']}")
        lay = QVBoxLayout(d)
        checks = []
        for c in all_contacts:
            cb = QCheckBox(f"{c['nombre']} · {c['facultad']}")
            cb.setChecked(c["id"] in current)
            cb.setProperty("contact_id", c["id"])
            lay.addWidget(cb)
            checks.append(cb)
        if not checks:
            lay.addWidget(QLabel("Aún no tienes contactos. Agrega contactos primero."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(d.accept); buttons.rejected.connect(d.reject)
        lay.addWidget(buttons)
        if d.exec() == QDialog.DialogCode.Accepted:
            ids = [c.property("contact_id") for c in checks if c.isChecked()]
            with get_session() as session:
                establecer_contactos_categoria(session, self.usuario_id, category["id"], ids)
                session.commit()
            self._render_category(category["id"])

    def _cambiar_nombre(self, category):
        nombre, ok = self._input("Cambiar nombre", "Nuevo nombre:", category["nombre"])
        if not ok: return
        with get_session() as session:
            cambiar_nombre_categoria(session, self.usuario_id, category["id"], nombre)
            session.commit()
        self._cargar_categorias()
        self._render_category(category["id"])

    def _cambiar_color(self, category):
        color = QColorDialog.getColor()
        if not color.isValid(): return
        with get_session() as session:
            cambiar_color_categoria(session, self.usuario_id, category["id"], color.name())
            session.commit()
        self._cargar_categorias()

    def _eliminar_categoria(self, category):
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar '{category['nombre']}'?") != QMessageBox.StandardButton.Yes:
            return
        with get_session() as session:
            eliminar_categoria(session, self.usuario_id, category["id"])
            session.commit()
        self._cargar_categorias()
        self._mostrar_sin_categoria()

    def _agregar_contacto_dialog(self):
        d = QDialog(self)
        d.setWindowTitle("Agregar contacto")
        d.resize(420, 420)
        lay = QVBoxLayout(d)
        lay.addWidget(QLabel("Selecciona un estudiante para agregarlo a tus contactos."))
        lista = QListWidget()
        lay.addWidget(lista, 1)
        with get_session() as session:
            users = session.query(Usuario).options(joinedload(Usuario.facultad)).filter(Usuario.id != self.usuario_id).order_by(Usuario.nombre).all()
            existing = {x["usuario_id"] for x in listar_contactos(session, self.usuario_id)}
        for u in users:
            if u.id not in existing:
                item = QListWidgetItem(f"{u.nombre} · {u.facultad.nombre if u.facultad else ''}")
                item.setData(Qt.ItemDataRole.UserRole, u.id)
                lista.addItem(item)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(d.accept); buttons.rejected.connect(d.reject)
        lay.addWidget(buttons)
        if d.exec() == QDialog.DialogCode.Accepted and lista.currentItem():
            uid = lista.currentItem().data(Qt.ItemDataRole.UserRole)
            with get_session() as session:
                agregar_contacto(session, self.usuario_id, uid)
                session.commit()
            if self.selected_category:
                self._render_category(self.selected_category["id"])
            else:
                self._mostrar_sin_categoria()

    def _abrir_chat(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and self.on_abrir_chat:
            self.on_abrir_chat(*data)
