from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMainWindow,QStackedWidget
from database.db_connection import get_session
from auth.login import logout_user
from auth.session_manager import validate_session
from database.models import Usuario
from security.encryption_utils import decrypt_text,encrypt_text
from gui.login_view import LoginView
from gui.register_view import RegisterView
from gui.home_view import HomeView
from gui.search_view import SearchView
from gui.chat_view import ChatView
from gui.contacts_view import ContactsView
from gui.groups_view import GroupsView
from gui.menu_overlay import MenuOverlay

class MainWindow(QMainWindow):
    SESSION_KEY="sesion/token"; SETTINGS=("Xavium","Xavium")
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xavium"); self.setMinimumSize(500,560); self.setStyleSheet("background-color: #1E5AA8;")
        self.usuario_id=None; self.usuario_nombre=None; self.token_sesion=None
        self.stack=QStackedWidget(); self.setCentralWidget(self.stack)

        self.login_view=LoginView(on_ir_a_registro=self.mostrar_registro,on_login_exitoso=self.manejar_login_exitoso)
        self.register_view=RegisterView(on_ir_a_login=self.mostrar_login)
        self.home_view=HomeView(on_logout=self.manejar_logout,on_menu=self.toggle_menu,
            on_inicio=self.mostrar_home,on_contactos=self.mostrar_contactos,on_grupos=self.mostrar_grupos,
            on_buscar=self.mostrar_busqueda,on_abrir_chat=self.mostrar_chat)
        self.contacts_view=ContactsView(on_menu=self.toggle_menu,on_inicio=self.mostrar_home,
            on_contactos=self.mostrar_contactos,on_grupos=self.mostrar_grupos,on_buscar=self.mostrar_busqueda,
            on_abrir_chat=self.mostrar_chat)
        self.groups_view=GroupsView(on_menu=self.toggle_menu,on_inicio=self.mostrar_home,
            on_contactos=self.mostrar_contactos,on_grupos=self.mostrar_grupos,on_buscar=self.mostrar_busqueda)
        self.search_view=SearchView(on_abrir_chat=self.mostrar_chat,on_menu=self.toggle_menu,
            on_inicio=self.mostrar_home,on_contactos=self.mostrar_contactos,on_grupos=self.mostrar_grupos,on_buscar=self.mostrar_busqueda)
        self.chat_view=ChatView(on_menu=self.toggle_menu,on_inicio=self.mostrar_home,
            on_contactos=self.mostrar_contactos,on_grupos=self.mostrar_grupos,on_buscar=self.mostrar_busqueda)
        for w in (self.login_view,self.register_view,self.home_view,self.contacts_view,self.groups_view,self.search_view,self.chat_view):
            self.stack.addWidget(w)

        self.menu_overlay=MenuOverlay(on_logout=self.manejar_logout); self.menu_overlay.setParent(self); self.menu_overlay.hide()
        if not self._restaurar_sesion(): self.mostrar_login()

    def mostrar_login(self):
        self.menu_overlay.hide(); self.stack.setCurrentWidget(self.login_view)
    def mostrar_registro(self):
        self.register_view._cargar_facultades(); self.stack.setCurrentWidget(self.register_view)
    def mostrar_home(self):
        if self.usuario_id is None:return
        self.menu_overlay.hide(); self.home_view.set_usuario(self.usuario_id); self.stack.setCurrentWidget(self.home_view)
    def mostrar_contactos(self):
        if self.usuario_id is None:return
        self.menu_overlay.hide(); self.contacts_view.set_usuario(self.usuario_id); self.stack.setCurrentWidget(self.contacts_view)
    def mostrar_grupos(self):
        if self.usuario_id is None:return
        self.menu_overlay.hide(); self.groups_view.set_usuario(self.usuario_id); self.stack.setCurrentWidget(self.groups_view)
    def mostrar_busqueda(self):
        if self.usuario_id is None:return
        self.menu_overlay.hide(); self.search_view.preparar(self.usuario_id); self.stack.setCurrentWidget(self.search_view)
    def mostrar_chat(self,uid,nombre):
        if self.usuario_id is None:return
        self.menu_overlay.hide(); self.chat_view.preparar(self.usuario_id,uid,nombre); self.stack.setCurrentWidget(self.chat_view)

    def manejar_login_exitoso(self,usuario_id,nombre,token_sesion):
        self.usuario_id=usuario_id; self.usuario_nombre=nombre; self.token_sesion=token_sesion
        QSettings(*self.SETTINGS).setValue(self.SESSION_KEY,encrypt_text(token_sesion))
        self.showFullScreen(); self.mostrar_home()

    def manejar_logout(self):
        if self.token_sesion:
            with get_session() as session:
                logout_user(session,self.token_sesion,usuario_id=self.usuario_id); session.commit()
        QSettings(*self.SETTINGS).remove(self.SESSION_KEY)
        self.usuario_id=self.usuario_nombre=self.token_sesion=None
        self.menu_overlay.hide(); self.showNormal(); self.mostrar_login()

    def toggle_menu(self):
        if self.usuario_id is None:return
        if self.menu_overlay.isVisible(): self.menu_overlay.hide()
        else:
            self.menu_overlay.adjustSize()
            self.menu_overlay.move(16+12, 16+72)
            self.menu_overlay.raise_(); self.menu_overlay.show()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.menu_overlay.isVisible():
            self.menu_overlay.move(28,88)

    def _restaurar_sesion(self):
        token_cifrado=QSettings(*self.SETTINGS).value(self.SESSION_KEY,"")
        if not token_cifrado:return False
        try:
            token=decrypt_text(token_cifrado)
            with get_session() as session:
                uid=validate_session(session,token)
                usuario=session.query(Usuario).filter(Usuario.id==uid).first() if uid else None
        except Exception: usuario=None; token=None
        if usuario is None:
            QSettings(*self.SETTINGS).remove(self.SESSION_KEY); return False
        self.usuario_id=usuario.id; self.usuario_nombre=usuario.nombre; self.token_sesion=token
        self.showFullScreen(); self.mostrar_home(); return True
