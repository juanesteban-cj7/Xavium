"""
chat_client.py
Cliente de sockets para conectarse a chat_server.py (capa opcional de
tiempo real — ver docstring de chat_server.py sobre por qué es
opcional dado el presupuesto $0 del proyecto).

Uso típico desde la GUI:
    cliente = ChatClient(on_mensaje_nuevo=callback)
    conectado = cliente.conectar(host, puerto, token_sesion)
    if conectado:
        cliente.enviar_mensaje(destinatario_id, "hola")
    ...
    cliente.desconectar()

Si `conectar()` devuelve False (servidor no disponible), la GUI debe
seguir funcionando en modo "solo BD" (polling con QTimer sobre
chat/message_store.py) sin considerarlo un error fatal.
"""

import json
import socket
import threading
from typing import Callable, Optional


class ChatClient:
    def __init__(self, on_mensaje_nuevo: Optional[Callable[[dict], None]] = None):
        """
        on_mensaje_nuevo: callback(payload) que se invoca en un hilo de
        fondo cuando llega una notificación de mensaje nuevo. Debe ser
        una función segura de llamar desde otro hilo (en PyQt, usar
        señales en vez de tocar la UI directamente aquí).
        """
        self.on_mensaje_nuevo = on_mensaje_nuevo
        self._socket_cliente: Optional[socket.socket] = None
        self._conectado = False
        self._hilo_escucha: Optional[threading.Thread] = None

    def conectar(self, host: str, puerto: int, token_sesion: str, timeout: float = 3.0) -> bool:
        """
        Intenta conectarse y autenticarse contra chat_server.py.
        Devuelve True si la conexión y autenticación fueron exitosas,
        False en cualquier otro caso (sin lanzar excepción — se espera
        que el servidor pueda no estar disponible).
        """
        try:
            self._socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket_cliente.settimeout(timeout)
            self._socket_cliente.connect((host, puerto))

            self._enviar_payload({"tipo": "auth", "token_sesion": token_sesion})

            respuesta = self._leer_una_linea()
            if respuesta is None or respuesta.get("tipo") != "auth_ok":
                self._cerrar_socket()
                return False

            self._socket_cliente.settimeout(None)  # vuelve a modo bloqueante para escuchar
            self._conectado = True

            self._hilo_escucha = threading.Thread(target=self._escuchar, daemon=True)
            self._hilo_escucha.start()

            return True
        except (OSError, socket.timeout):
            self._cerrar_socket()
            return False

    def enviar_mensaje(self, destinatario_id: str, texto: str) -> bool:
        """
        Envía un mensaje vía el servidor en tiempo real, si está
        conectado. La persistencia real ocurre en el servidor
        (chat/message_store.py); esto es solo la notificación rápida.
        Devuelve False si no hay conexión activa (la GUI debe entonces
        guardar el mensaje directamente vía message_store.py).
        """
        if not self._conectado:
            return False
        try:
            self._enviar_payload(
                {"tipo": "mensaje", "destinatario_id": destinatario_id, "texto": texto}
            )
            return True
        except OSError:
            self._conectado = False
            return False

    def desconectar(self):
        self._conectado = False
        self._cerrar_socket()

    @property
    def esta_conectado(self) -> bool:
        return self._conectado

    def _escuchar(self):
        buffer = ""
        try:
            while self._conectado:
                datos = self._socket_cliente.recv(4096)
                if not datos:
                    break
                buffer += datos.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if not linea.strip():
                        continue
                    try:
                        payload = json.loads(linea)
                    except json.JSONDecodeError:
                        continue
                    if payload.get("tipo") == "mensaje_nuevo" and self.on_mensaje_nuevo:
                        self.on_mensaje_nuevo(payload)
        except OSError:
            pass
        finally:
            self._conectado = False

    def _enviar_payload(self, payload: dict):
        self._socket_cliente.sendall((json.dumps(payload) + "\n").encode("utf-8"))

    def _leer_una_linea(self) -> Optional[dict]:
        buffer = ""
        while "\n" not in buffer:
            datos = self._socket_cliente.recv(4096)
            if not datos:
                return None
            buffer += datos.decode("utf-8")
        linea = buffer.split("\n", 1)[0]
        try:
            return json.loads(linea)
        except json.JSONDecodeError:
            return None

    def _cerrar_socket(self):
        if self._socket_cliente:
            try:
                self._socket_cliente.close()
            except OSError:
                pass
        self._socket_cliente = None