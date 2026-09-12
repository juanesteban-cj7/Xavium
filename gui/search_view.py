"""
search_view.py
Vista de búsqueda de estudiantes: filtra por facultad y texto, y
muestra los resultados ordenados por compatibilidad (matching/
search_engine.py). Al seleccionar un resultado, abre el chat con
esa persona.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from database.db_connection import get_session
from matching.search_engine import buscar_estudiantes, obtener_facultades_disponibles

INPUT_STYLE = """
QLineEdit, QComboBox {
    background-color: white;
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
    color: #1E1E1E;
}
"""

PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: white;
    color: #1E5AA8;
    font-size: 13px;
    font-weight: bold;
    border-radius: 8px;
    padding: 8px 14px;
}
QPushButton:hover {
    background-color: #E6EEF8;
}
"""

LINK_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    color: white;
    font-size: 13px;
    text-decoration: underline;
    border: none;
}
QPushButton:hover {
    color: #D6E4F5;
}
"""

LIST_STYLE = """
QListWidget {
    background-color: white;
    border-radius: 8px;
    padding: 4px;
    font-size: 13px;
    color: #1E1E1E;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #E0E0E0;
}
QListWidget::item:selected {
    background-color: #E6EEF8;
    color: #1E1E1E;
}
"""

TEXTO_TODAS_FACULTADES = "Todas las facultades"


class SearchView(QWidget):
    def __init__(self, on_abrir_chat=None, on_volver=None):
        """
        on_abrir_chat: callback(otro_usuario_id, otro_usuario_nombre)
        que se ejecuta al hacer doble clic en un resultado.
        on_volver: callback para volver a la pantalla de inicio.
        """
        super().__init__()
        self.on_abrir_chat = on_abrir_chat
        self.on_volver = on_volver
        self.usuario_actual_id = None

        # Guarda los resultados actuales para poder mapear el ítem
        # seleccionado en la lista de vuelta a su usuario_id
        self._resultados_actuales = []

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(10)
        self.setLayout(layout)

        fila_superior = QHBoxLayout()
        self.boton_volver = QPushButton("← Volver")
        self.boton_volver.setStyleSheet(LINK_BUTTON_STYLE)
        self.boton_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_volver.clicked.connect(self._volver)
        fila_superior.addWidget(self.boton_volver)
        fila_superior.addStretch()
        layout.addLayout(fila_superior)

        titulo = QLabel("Encuentra estudiantes afines")
        titulo.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        layout.addWidget(titulo)

        # Fila de filtros
        fila_filtros = QHBoxLayout()

        self.input_texto = QLineEdit()
        self.input_texto.setPlaceholderText("Buscar por nombre...")
        self.input_texto.setStyleSheet(INPUT_STYLE)
        self.input_texto.returnPressed.connect(self.ejecutar_busqueda)
        fila_filtros.addWidget(self.input_texto, stretch=2)

        self.combo_facultad = QComboBox()
        self.combo_facultad.setStyleSheet(INPUT_STYLE)
        fila_filtros.addWidget(self.combo_facultad, stretch=2)

        self.boton_buscar = QPushButton("Buscar")
        self.boton_buscar.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.boton_buscar.clicked.connect(self.ejecutar_busqueda)
        fila_filtros.addWidget(self.boton_buscar, stretch=1)

        layout.addLayout(fila_filtros)

        # Lista de resultados
        self.lista_resultados = QListWidget()
        self.lista_resultados.setStyleSheet(LIST_STYLE)
        self.lista_resultados.itemDoubleClicked.connect(self._abrir_chat_seleccionado)
        layout.addWidget(self.lista_resultados, stretch=1)

        ayuda = QLabel("Doble clic sobre un estudiante para abrir el chat.")
        ayuda.setStyleSheet("color: #D6E4F5; font-size: 11px;")
        layout.addWidget(ayuda)

    def preparar(self, usuario_id: str):
        """Se llama cada vez que se entra a esta vista, para refrescar datos."""
        self.usuario_actual_id = usuario_id
        self._cargar_facultades()
        self.input_texto.clear()
        self.ejecutar_busqueda()

    def _cargar_facultades(self):
        self.combo_facultad.clear()
        self.combo_facultad.addItem(TEXTO_TODAS_FACULTADES)
        try:
            with get_session() as session:
                nombres = obtener_facultades_disponibles(session)
            self.combo_facultad.addItems(nombres)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"No se pudo cargar facultades:\n{exc}")

    def ejecutar_busqueda(self):
        if not self.usuario_actual_id:
            return

        texto = self.input_texto.text().strip() or None
        facultad = self.combo_facultad.currentText()
        facultad_filtro = None if facultad == TEXTO_TODAS_FACULTADES else facultad

        try:
            with get_session() as session:
                resultados = buscar_estudiantes(
                    session,
                    self.usuario_actual_id,
                    facultad_filtro=facultad_filtro,
                    texto_busqueda=texto,
                )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo realizar la búsqueda:\n{exc}")
            return

        self._resultados_actuales = resultados
        self._renderizar_resultados(resultados)

    def _renderizar_resultados(self, resultados):
        self.lista_resultados.clear()

        if not resultados:
            item = QListWidgetItem("No se encontraron estudiantes con esos filtros.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_resultados.addItem(item)
            return

        for resultado in resultados:
            if resultado.intereses_comunes:
                intereses_texto = ", ".join(resultado.intereses_comunes[:4])
                linea_intereses = f"Intereses en común: {intereses_texto}"
            else:
                linea_intereses = "Sin intereses en común declarados"

            texto_item = (
                f"{resultado.nombre}  ·  {resultado.facultad}\n{linea_intereses}"
            )
            item = QListWidgetItem(texto_item)
            item.setData(Qt.ItemDataRole.UserRole, resultado.usuario_id)
            self.lista_resultados.addItem(item)

    def _abrir_chat_seleccionado(self, item: QListWidgetItem):
        usuario_id = item.data(Qt.ItemDataRole.UserRole)
        if usuario_id is None:
            return

        nombre = next(
            (r.nombre for r in self._resultados_actuales if r.usuario_id == usuario_id),
            "",
        )

        if self.on_abrir_chat:
            self.on_abrir_chat(usuario_id, nombre)

    def _volver(self):
        if self.on_volver:
            self.on_volver()