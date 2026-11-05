from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QPushButton,QTextEdit
from chat.message_store import enviar_mensaje,marcar_mensajes_como_leidos,obtener_mensajes,obtener_o_crear_conversacion
from database.db_connection import get_session
from gui.app_header import AppHeader
from gui.theme import estilizar_boton

class ChatView(QWidget):
    def __init__(self,on_menu=None,on_inicio=None,on_contactos=None,on_grupos=None,on_buscar=None):
        super().__init__()
        self.usuario_actual_id=None; self.otro_usuario_id=None; self.conversacion_id=None
        layout=QVBoxLayout(self); layout.setContentsMargins(16,16,16,16); layout.setSpacing(0)
        header=AppHeader(on_inicio=on_inicio,on_contactos=on_contactos,on_grupos=on_grupos,on_buscar=on_buscar)
        if on_menu: header.menu_clicked.connect(on_menu)
        layout.addWidget(header)
        self.titulo=QLabel("Chat")
        self.titulo.setObjectName("pageTitle")
        layout.addWidget(self.titulo)
        self.historial=QTextEdit(); self.historial.setReadOnly(True)
        layout.addWidget(self.historial,1)
        layout.addSpacing(12)
        row=QHBoxLayout()
        row.setSpacing(10)
        self.input_mensaje=QLineEdit(); self.input_mensaje.setPlaceholderText("Escribe un mensaje...")
        self.input_mensaje.setFixedHeight(48)
        self.input_mensaje.returnPressed.connect(self._enviar); row.addWidget(self.input_mensaje,1)
        b=QPushButton("Enviar"); b.setFixedHeight(48); b.setMinimumWidth(110); estilizar_boton(b,"primary"); b.clicked.connect(self._enviar); row.addWidget(b)
        layout.addLayout(row)
        self._timer=QTimer(self); self._timer.setInterval(1500); self._timer.timeout.connect(self._refrescar_mensajes)

    def preparar(self,usuario_actual_id,otro_usuario_id,nombre):
        self.usuario_actual_id=usuario_actual_id; self.otro_usuario_id=otro_usuario_id; self.conversacion_id=None
        self.titulo.setText(f"Chat con {nombre}"); self.historial.clear(); self.input_mensaje.clear()
        try:
            with get_session() as session:
                self.conversacion_id=obtener_o_crear_conversacion(session,usuario_actual_id,otro_usuario_id).id
                session.commit()
            self._refrescar_mensajes(); self._timer.start()
        except Exception as exc:
            self.conversacion_id=None
            self._timer.stop()
            QMessageBox.critical(self,"No se pudo abrir el chat",str(exc))

    def _refrescar_mensajes(self):
        if not self.conversacion_id or not self.usuario_actual_id:return
        try:
            with get_session() as session:
                mensajes=obtener_mensajes(session,self.conversacion_id,self.usuario_actual_id)
                marcar_mensajes_como_leidos(session,self.conversacion_id,self.usuario_actual_id)
        except Exception as exc: QMessageBox.warning(self,"Error",str(exc)); return
        self.historial.setPlainText("\n\n".join(("Tú" if m.es_propio else "Otro")+": "+m.contenido for m in mensajes))
        cursor=self.historial.textCursor(); cursor.movePosition(cursor.MoveOperation.End); self.historial.setTextCursor(cursor)

    def _enviar(self):
        text=self.input_mensaje.text().strip()
        if not text or not self.conversacion_id:return
        try:
            with get_session() as session:
                enviar_mensaje(session,self.conversacion_id,self.usuario_actual_id,text)
                session.commit()
        except Exception as exc: QMessageBox.warning(self,"Error",str(exc)); return
        self.input_mensaje.clear(); self._refrescar_mensajes()

    def closeEvent(self,event):
        self._timer.stop(); super().closeEvent(event)
