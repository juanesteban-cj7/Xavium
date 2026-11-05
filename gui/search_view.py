from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from database.db_connection import get_session
from matching.search_engine import buscar_estudiantes, obtener_facultades_disponibles
from gui.app_header import AppHeader
from gui.theme import estilizar_boton, pulir_lista

TEXTO_TODAS_FACULTADES = "Todas las facultades"

class SearchView(QWidget):
    def __init__(self, on_abrir_chat=None, on_menu=None, on_inicio=None,
                 on_contactos=None, on_grupos=None, on_buscar=None):
        super().__init__()
        self.on_abrir_chat = on_abrir_chat
        self.usuario_actual_id = None
        self._resultados_actuales = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,16,16,16)
        layout.setSpacing(0)
        header=AppHeader(on_inicio=on_inicio,on_contactos=on_contactos,on_grupos=on_grupos,on_buscar=on_buscar)
        if on_menu: header.menu_clicked.connect(on_menu)
        layout.addWidget(header)

        title=QLabel("Buscar estudiantes")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        filters=QHBoxLayout()
        filters.setSpacing(10)
        self.input_texto=QLineEdit()
        self.input_texto.setPlaceholderText("Buscar por nombre...")
        self.input_texto.setFixedHeight(46)
        self.input_texto.returnPressed.connect(self.ejecutar_busqueda)
        filters.addWidget(self.input_texto,2)

        self.combo_facultad=QComboBox()
        self.combo_facultad.setFixedHeight(46)
        self.combo_facultad.setCursor(Qt.CursorShape.PointingHandCursor)
        filters.addWidget(self.combo_facultad,2)

        self.boton_buscar=QPushButton("Buscar")
        self.boton_buscar.setFixedHeight(46)
        self.boton_buscar.setMinimumWidth(130)
        estilizar_boton(self.boton_buscar,"primary")
        self.boton_buscar.clicked.connect(self.ejecutar_busqueda)
        filters.addWidget(self.boton_buscar)
        layout.addLayout(filters)
        layout.addSpacing(14)

        self.lista_resultados=QListWidget()
        self.lista_resultados.itemDoubleClicked.connect(self._abrir_chat_seleccionado)
        pulir_lista(self.lista_resultados)
        layout.addWidget(self.lista_resultados,1)

    def preparar(self, usuario_id):
        self.usuario_actual_id=usuario_id
        self._cargar_facultades()
        self.input_texto.clear()
        self.ejecutar_busqueda()

    def _cargar_facultades(self):
        self.combo_facultad.clear()
        self.combo_facultad.addItem(TEXTO_TODAS_FACULTADES)
        try:
            with get_session() as session:
                self.combo_facultad.addItems(obtener_facultades_disponibles(session))
        except Exception as exc:
            QMessageBox.warning(self,"Error",f"No se pudo cargar facultades:\n{exc}")

    def ejecutar_busqueda(self):
        if not self.usuario_actual_id:return
        facultad=self.combo_facultad.currentText()
        try:
            with get_session() as session:
                resultados=buscar_estudiantes(session,self.usuario_actual_id,
                    facultad_filtro=None if facultad==TEXTO_TODAS_FACULTADES else facultad,
                    texto_busqueda=self.input_texto.text().strip() or None)
        except Exception as exc:
            QMessageBox.critical(self,"Error",f"No se pudo realizar la búsqueda:\n{exc}"); return
        self._resultados_actuales=resultados
        self.lista_resultados.clear()
        if not resultados:
            self.lista_resultados.addItem("No se encontraron estudiantes con esos filtros."); return
        for r in resultados:
            comunes=", ".join(r.intereses_comunes[:4]) if r.intereses_comunes else "Sin intereses en común declarados"
            item=QListWidgetItem(f"{r.nombre}  ·  {r.facultad}\nIntereses en común: {comunes}")
            item.setData(Qt.ItemDataRole.UserRole,r.usuario_id)
            self.lista_resultados.addItem(item)

    def _abrir_chat_seleccionado(self,item):
        uid=item.data(Qt.ItemDataRole.UserRole)
        if uid is None:return
        nombre=next((r.nombre for r in self._resultados_actuales if r.usuario_id==uid),"")
        if self.on_abrir_chat:self.on_abrir_chat(uid,nombre)
