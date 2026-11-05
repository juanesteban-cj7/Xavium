"""
theme.py
Tema visual de Xavium: glassmorfismo sobre una paleta azul.

Este módulo SOLO contiene presentación (colores, fuentes, efectos hover).
No importa ni toca base de datos, autenticación, chat ni ninguna lógica.

Piezas:
- GLOBAL_QSS        : hoja de estilos única que se aplica a toda la ventana.
- GradientStack     : QStackedWidget que pinta el fondo degradado con "orbes"
                      de luz (lo que da el efecto cristal a los paneles).
- aplicar_tema()    : aplica fuente + hoja de estilos a la ventana principal.
- estilizar_boton() : variante de botón + cursor + brillo animado al hover.
- sombra_suave()    : sombra difusa estática para tarjetas y cabecera.
- espaciar_letras() : espaciado de letras para títulos.
"""

import os
import tempfile

from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPointF,
    QVariantAnimation,
    Qt,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QStackedWidget,
)

# ----------------------------------------------------------------------
# Paleta (azul predominante)
# ----------------------------------------------------------------------
AZUL_PROFUNDO = "#061a3f"
AZUL_MEDIO = "#0d3b86"
AZUL_XAVIUM = "#1e5aa8"
AZUL_CLARO = "#2f9bff"
CIAN_LUZ = "#5cc8ff"

FUENTES = [
    "Segoe UI Variable Display",
    "Segoe UI",
    "Inter",
    "SF Pro Display",
    "Helvetica Neue",
    "Arial",
]


# ----------------------------------------------------------------------
# Hoja de estilos global
# ----------------------------------------------------------------------
GLOBAL_QSS = """
/* ---------- Base ---------- */
QMainWindow { background: #061a3f; }

QToolTip {
    background: #0b2a5e;
    color: white;
    border: 1px solid rgba(255, 255, 255, 40%);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
}

QLabel {
    color: white;
    background: transparent;
    font-size: 14px;
}
QLabel#brand {
    font-size: 38px;
    font-weight: 800;
    color: white;
}
QLabel#brandSmall {
    font-size: 30px;
    font-weight: 800;
    color: white;
}
QLabel#subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 82%);
}
QLabel#muted {
    font-size: 13px;
    color: rgba(255, 255, 255, 78%);
}
QLabel#info {
    font-size: 14px;
    color: rgba(255, 255, 255, 80%);
    padding: 4px 0;
}
QLabel#pageTitle {
    font-size: 26px;
    font-weight: 800;
    color: white;
    padding: 16px 4px 10px 4px;
}
QLabel#sectionTitle {
    font-size: 24px;
    font-weight: 800;
    color: white;
}
QLabel#panelTitle {
    font-size: 16px;
    font-weight: 700;
    color: white;
    padding: 16px 18px 12px 18px;
}
QLabel#logo {
    color: white;
    font-size: 34px;
    font-weight: 800;
    border: 1px solid rgba(255, 255, 255, 60%);
    border-radius: 22px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5cc8ff, stop:1 #2557e8);
}
QLabel#placeholderPanel {
    background: rgba(255, 255, 255, 9%);
    border: 1px dashed rgba(255, 255, 255, 38%);
    border-radius: 22px;
    color: rgba(255, 255, 255, 82%);
    font-size: 20px;
    font-weight: 600;
    padding: 30px;
}

/* ---------- Superficies de cristal ---------- */
QFrame#card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 255, 255, 26%), stop:1 rgba(255, 255, 255, 10%));
    border: 1px solid rgba(255, 255, 255, 48%);
    border-radius: 28px;
}
QFrame#card:hover {
    border: 1px solid rgba(255, 255, 255, 70%);
}

QFrame#panel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 255, 255, 18%), stop:1 rgba(255, 255, 255, 8%));
    border: 1px solid rgba(255, 255, 255, 34%);
    border-radius: 22px;
}
QFrame#panel:hover {
    border: 1px solid rgba(255, 255, 255, 52%);
}
QFrame#hline {
    background: rgba(255, 255, 255, 26%);
    border: none;
    min-height: 1px;
    max-height: 1px;
}

/* ---------- Campos de texto ---------- */
QLineEdit, QComboBox {
    background: rgba(255, 255, 255, 15%);
    border: 1px solid rgba(255, 255, 255, 38%);
    border-radius: 14px;
    padding: 9px 14px;
    color: white;
    font-size: 14px;
    selection-background-color: #2f9bff;
    selection-color: white;
    placeholder-text-color: rgba(255, 255, 255, 62%);
}
QLineEdit:hover, QComboBox:hover {
    background: rgba(255, 255, 255, 22%);
    border: 1px solid rgba(255, 255, 255, 68%);
}
QLineEdit:focus, QComboBox:focus, QComboBox:on {
    background: rgba(255, 255, 255, 27%);
    border: 1px solid #8fdcff;
}
QLineEdit:read-only {
    background: rgba(255, 255, 255, 10%);
}
QLineEdit#codeField {
    font-size: 20px;
    font-weight: 700;
    padding: 12px 14px;
}

QComboBox::drop-down {
    border: none;
    width: 34px;
}
QComboBox::down-arrow {
    image: url("__FLECHA__");
    width: 12px;
    height: 12px;
    margin-right: 14px;
}
QComboBox QAbstractItemView {
    background: #0c2f68;
    color: white;
    border: 1px solid rgba(255, 255, 255, 38%);
    border-radius: 12px;
    padding: 6px;
    outline: 0;
    selection-background-color: rgba(47, 155, 255, 55%);
    selection-color: white;
}

/* ---------- Área de chat ---------- */
QTextEdit {
    background: rgba(5, 22, 56, 38%);
    border: 1px solid rgba(255, 255, 255, 28%);
    border-radius: 18px;
    padding: 12px;
    color: white;
    font-size: 15px;
    selection-background-color: #2f9bff;
}
QTextEdit:hover {
    border: 1px solid rgba(255, 255, 255, 45%);
}

/* ---------- Listas ---------- */
QListWidget {
    background: rgba(255, 255, 255, 8%);
    border: 1px solid rgba(255, 255, 255, 26%);
    border-radius: 16px;
    padding: 6px;
    color: white;
    font-size: 14px;
    outline: 0;
}
QListWidget#flatList {
    background: transparent;
    border: none;
    padding: 2px 8px 10px 8px;
}
QListWidget#categoryList {
    background: transparent;
    border: none;
    padding: 2px 4px 8px 4px;
}
QListWidget#categoryList::item {
    padding: 0px;
    margin: 2px 0px;
    border-radius: 12px;
}
QListWidget::item {
    padding: 12px 14px;
    margin: 3px 2px;
    border-radius: 12px;
    border: 1px solid transparent;
    color: white;
}
QListWidget::item:hover {
    background: rgba(255, 255, 255, 17%);
    border: 1px solid rgba(255, 255, 255, 30%);
}
QListWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(47, 155, 255, 62%), stop:1 rgba(47, 155, 255, 28%));
    border: 1px solid rgba(143, 220, 255, 75%);
    color: white;
}
QListWidget::item:selected:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(70, 175, 255, 72%), stop:1 rgba(47, 155, 255, 38%));
}

/* ---------- Botones ---------- */
QPushButton {
    background: rgba(255, 255, 255, 16%);
    color: white;
    border: 1px solid rgba(255, 255, 255, 40%);
    border-radius: 13px;
    padding: 9px 18px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: rgba(255, 255, 255, 29%);
    border: 1px solid rgba(255, 255, 255, 78%);
}
QPushButton:pressed {
    background: rgba(255, 255, 255, 11%);
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton:disabled {
    color: rgba(255, 255, 255, 45%);
    background: rgba(255, 255, 255, 6%);
    border: 1px solid rgba(255, 255, 255, 14%);
}

QPushButton#primary, QPushButton#roundAdd, QDialogButtonBox QPushButton:default {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2f9bff, stop:1 #1f4fd8);
    border: 1px solid rgba(255, 255, 255, 58%);
    color: white;
    font-size: 15px;
    font-weight: 700;
}
QPushButton#primary:hover, QPushButton#roundAdd:hover, QDialogButtonBox QPushButton:default:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #55b2ff, stop:1 #2f66f0);
    border: 1px solid white;
}
QPushButton#primary:pressed, QPushButton#roundAdd:pressed, QDialogButtonBox QPushButton:default:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1f86e6, stop:1 #173fb5);
}
QPushButton#primary:disabled {
    background: rgba(255, 255, 255, 8%);
    color: rgba(255, 255, 255, 45%);
    border: 1px solid rgba(255, 255, 255, 14%);
}

QPushButton#link {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    color: #cfe8ff;
    font-size: 13px;
    font-weight: 600;
    text-decoration: underline;
    padding: 5px 10px;
}
QPushButton#link:hover {
    background: rgba(255, 255, 255, 13%);
    color: white;
}
QPushButton#link:pressed {
    background: rgba(255, 255, 255, 8%);
    padding-top: 5px;
    padding-bottom: 5px;
}

QPushButton#dots {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 0px;
    font-size: 22px;
    font-weight: 700;
}
QPushButton#dots:hover {
    background: rgba(255, 255, 255, 24%);
    border: 1px solid rgba(255, 255, 255, 45%);
}
QPushButton#dots:pressed {
    padding-top: 0px;
    padding-bottom: 0px;
}

QPushButton#roundAdd {
    border-radius: 14px;
    padding: 0px 0px 3px 0px;
    font-size: 24px;
    font-weight: 700;
}
QPushButton#roundAdd:pressed {
    padding: 2px 0px 0px 0px;
}

/* ---------- Casillas ---------- */
QCheckBox {
    color: white;
    font-size: 14px;
    spacing: 10px;
    padding: 4px 2px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 65%);
    background: rgba(255, 255, 255, 12%);
}
QCheckBox::indicator:hover {
    background: rgba(255, 255, 255, 25%);
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #5cc8ff, stop:1 #2f66f0);
    border: 1px solid white;
}

/* ---------- Barras de desplazamiento ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 6px 2px 6px 2px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 34%);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 62%);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px 6px 2px 6px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 34%);
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(255, 255, 255, 62%);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ---------- Diálogos y mensajes (ventanas hijas) ---------- */
QDialog, QMessageBox, QInputDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #09285c, stop:0.6 #12449a, stop:1 #1e5aa8);
}
QDialog QPushButton, QMessageBox QPushButton {
    min-width: 92px;
}
QMessageBox QLabel {
    color: white;
    font-size: 14px;
    min-width: 280px;
}
"""


# ----------------------------------------------------------------------
# Aplicación del tema
# ----------------------------------------------------------------------
def fuente_app() -> QFont:
    """Fuente moderna con cadena de respaldo (Segoe UI en Windows)."""
    fuente = QFont()
    fuente.setFamilies(FUENTES)
    fuente.setPixelSize(14)
    fuente.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return fuente


def _crear_flecha() -> str:
    """Genera (una vez) el icono de flecha blanca de los desplegables."""
    ruta = os.path.join(tempfile.gettempdir(), "xavium_flecha.png")
    imagen = QImage(24, 24, QImage.Format.Format_ARGB32)
    imagen.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagen)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    lapiz = QPen(QColor("white"))
    lapiz.setWidthF(2.8)
    lapiz.setCapStyle(Qt.PenCapStyle.RoundCap)
    lapiz.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pintor.setPen(lapiz)
    pintor.drawPolyline([QPointF(5.5, 9), QPointF(12, 15.5), QPointF(18.5, 9)])
    pintor.end()
    imagen.save(ruta)
    return ruta.replace("\\", "/")


def aplicar_tema(ventana) -> None:
    """Aplica fuente y hoja de estilos global a la ventana principal."""
    app = QApplication.instance()
    if app is not None:
        app.setFont(fuente_app())
    ventana.setStyleSheet(GLOBAL_QSS.replace("__FLECHA__", _crear_flecha()))


def pulir_lista(lista):
    """
    Ajustes visuales de una QListWidget: sin barra horizontal, texto
    largo recortado con "…" y desplazamiento suave. No toca datos ni señales.
    """
    lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    lista.setTextElideMode(Qt.TextElideMode.ElideRight)
    lista.setVerticalScrollMode(lista.ScrollMode.ScrollPerPixel)
    lista.setCursor(Qt.CursorShape.PointingHandCursor)
    return lista


# ----------------------------------------------------------------------
# Fondo degradado con orbes de luz
# ----------------------------------------------------------------------
class GradientStack(QStackedWidget):
    """
    QStackedWidget idéntico al original en comportamiento; solo pinta
    un fondo azul degradado con orbes luminosos difusos. Los paneles
    translúcidos que se colocan encima producen el efecto "cristal".
    """

    # (x relativa, y relativa, radio relativo, color, opacidad)
    _ORBES = (
        (0.10, 0.12, 0.46, "#37b6ff", 150),
        (0.92, 0.18, 0.40, "#4f6bff", 120),
        (0.78, 0.95, 0.52, "#22c7ff", 125),
        (0.12, 0.92, 0.38, "#2f7bff", 130),
        (0.50, 0.50, 0.30, "#1f6fe0", 90),
    )

    def paintEvent(self, event):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.rect()
        ancho, alto = area.width(), area.height()

        base = QLinearGradient(0, 0, ancho, alto)
        base.setColorAt(0.0, QColor(AZUL_PROFUNDO))
        base.setColorAt(0.5, QColor(AZUL_MEDIO))
        base.setColorAt(1.0, QColor(AZUL_XAVIUM))
        pintor.fillRect(area, base)

        pintor.setPen(Qt.PenStyle.NoPen)
        escala = max(ancho, alto)
        for fx, fy, fr, color, opacidad in self._ORBES:
            centro = QPointF(ancho * fx, alto * fy)
            radio = escala * fr
            gradiente = QRadialGradient(centro, radio)
            centro_color = QColor(color)
            centro_color.setAlpha(opacidad)
            borde_color = QColor(color)
            borde_color.setAlpha(0)
            gradiente.setColorAt(0.0, centro_color)
            gradiente.setColorAt(1.0, borde_color)
            pintor.setBrush(gradiente)
            pintor.drawEllipse(centro, radio, radio)
        pintor.end()


# ----------------------------------------------------------------------
# Efectos
# ----------------------------------------------------------------------
class _BrilloHover(QObject):
    """
    Anima el halo (sombra de color) de un widget al pasar el cursor:
    el desenfoque y la opacidad crecen suavemente al entrar y vuelven
    al reposo al salir. Es un filtro de eventos que nunca consume
    eventos, así que clicked y demás señales funcionan igual.
    """

    def __init__(self, widget, rgb, reposo, activo, desplazamiento: int):
        """reposo / activo: tuplas (desenfoque, opacidad 0-255)."""
        super().__init__(widget)
        self._rgb = rgb
        self._reposo = reposo
        self._activo = activo
        self._t = 0.0

        self._efecto = QGraphicsDropShadowEffect(widget)
        self._efecto.setOffset(0, desplazamiento)
        self._aplicar(0.0)
        widget.setGraphicsEffect(self._efecto)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(190)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._aplicar)
        widget.installEventFilter(self)

    def _aplicar(self, t):
        self._t = float(t)
        desenfoque = self._reposo[0] + (self._activo[0] - self._reposo[0]) * self._t
        opacidad = self._reposo[1] + (self._activo[1] - self._reposo[1]) * self._t
        self._efecto.setBlurRadius(desenfoque)
        self._efecto.setColor(QColor(self._rgb[0], self._rgb[1], self._rgb[2], int(opacidad)))

    def _animar_a(self, destino: float):
        self._anim.stop()
        self._anim.setStartValue(self._t)
        self._anim.setEndValue(destino)
        self._anim.start()

    def eventFilter(self, objeto, evento):
        tipo = evento.type()
        if tipo == QEvent.Type.Enter:
            self._animar_a(1.0)
        elif tipo in (QEvent.Type.Leave, QEvent.Type.Hide):
            self._animar_a(0.0)
        return False


def estilizar_boton(boton, variante: str = "glass", brillo: bool = True):
    """
    Configura la apariencia de un QPushButton:
    - variante: "glass" (por defecto), "primary", "link", "dots", etc.
      Se traduce en objectName para que la hoja de estilos lo reconozca.
    - cursor de mano y halo animado al pasar el mouse.
    No cambia señales ni comportamiento del botón.
    """
    if variante != "glass" and not boton.objectName():
        boton.setObjectName(variante)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    if brillo and variante in ("primary", "roundAdd"):
        _BrilloHover(boton, (47, 155, 255), (12, 90), (36, 215), 4)
    elif brillo and variante == "glass":
        _BrilloHover(boton, (120, 200, 255), (6, 0), (24, 135), 2)
    return boton


def sombra_suave(widget, desenfoque: int = 46, opacidad: int = 95, desplazamiento: int = 12):
    """Sombra difusa azul oscura para dar profundidad a tarjetas flotantes."""
    efecto = QGraphicsDropShadowEffect(widget)
    efecto.setBlurRadius(desenfoque)
    efecto.setOffset(0, desplazamiento)
    efecto.setColor(QColor(2, 12, 40, opacidad))
    widget.setGraphicsEffect(efecto)
    return efecto


def espaciar_letras(etiqueta, pixeles: float = 1.5):
    """Separa levemente las letras de un título (look de marca)."""
    fuente = etiqueta.font()
    fuente.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, pixeles)
    etiqueta.setFont(fuente)
    return etiqueta
