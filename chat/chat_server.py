"""
chat_server.py
Servidor de mensajería en tiempo real, vía sockets TCP.

IMPORTANTE — contexto de diseño (ver conversación de alcance y
limitaciones del proyecto): con presupuesto $0, no hay forma de tener
un servidor de este tipo corriendo 24/7 de forma confiable en la
nube. Por eso, este servidor es una CAPA OPCIONAL para:
  - Pruebas del equipo en la misma red local (LAN) o en una sola
    máquina (localhost).
  - Demostrar el concepto de mensajería en tiempo real vía sockets,
    como pedía el plan original ("primero simulado, luego con
    sockets reales").

La GUI (Fase 6) NO depende de este servidor para funcionar: usa
directamente chat/message_store.py con polling (QTimer), que es
robusto incluso sin este servidor corriendo. Si el servidor está
activo, la entrega de mensajes se siente más inmediata; si no lo
está, el chat sigue funcionando igual, solo con el pequeño retraso
del intervalo de polling.

Protocolo: mensajes JSON delimitados por salto de línea ("\n"),
sobre un socket TCP. Cada mensaje ya viene cifrado (el servidor nunca
ve el texto plano ni las claves de conversación — solo reenvía
bytes ya cifrados por el cliente emisor y los persiste tal cual).
"""

import json
import socket
import threading
from typing import Dict, Optional

from database.db_connection import get_session
from auth.session_manager import validate_session
from chat.message_store import enviar_mensaje, obtener_o_crear_conversacion

HOST_DEFECTO = "0.0.0.0"
PUERTO_DEFECTO = 5555


class ChatServer:
    def __init__(self, host: str = HOST_DEFECTO, puerto: int = PUERTO_DEFECTO):
        self.host = host
        self.puerto = puerto
        self._socket_servidor: Optional[socket.socket] = None
        self._clientes_conectados: Dict[str, socket.socket] = {}  # usuario_id -> socket
        self._lock = threading.Lock()
        self._activo = False

    def iniciar(self):
        self._socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket_servidor.bind((self.host, self.puerto))
        self._socket_servidor.listen()
        self._activo = True
        print(f"[chat_server] Escuchando en {self.host}:{self.puerto}")

        while self._activo:
            try:
                conexion, direccion = self._socket_servidor.accept()
            except OSError:
                break  # el socket se cerró (detener())
            hilo = threading.Thread(
                target=self._manejar_cliente, args=(conexion, direccion), daemon=True
            )
            hilo.start()

    def detener(self):
        self._activo = False
        if self._socket_servidor:
            self._socket_servidor.close()

    def _manejar_cliente(self, conexion: socket.socket, direccion):
        usuario_id_autenticado = None
        buffer = ""
        try:
            while True:
                datos = conexion.recv(4096)
                if not datos:
                    break
                buffer += datos.decode("utf-8")

                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if not linea.strip():
                        continue
                    respuesta = self._procesar_mensaje(
                        conexion, direccion, linea, usuario_id_autenticado
                    )
                    if respuesta and respuesta.get("tipo") == "auth_ok":
                        usuario_id_autenticado = respuesta["usuario_id"]
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            if usuario_id_autenticado:
                with self._lock:
                    self._clientes_conectados.pop(usuario_id_autenticado, None)
            conexion.close()

    def _procesar_mensaje(self, conexion, direccion, linea_json, usuario_id_actual):
        try:
            payload = json.loads(linea_json)
        except json.JSONDecodeError:
            return None

        tipo = payload.get("tipo")

        # 1. Autenticación: el cliente debe validar su token de sesión
        #    (el mismo que usa la GUI) antes de poder enviar mensajes.
        if tipo == "auth":
            token = payload.get("token_sesion", "")
            with get_session() as session_db:
                usuario_id = validate_session(session_db, token)

            if usuario_id is None:
                self._enviar(conexion, {"tipo": "auth_error"})
                return None

            with self._lock:
                self._clientes_conectados[usuario_id] = conexion
            self._enviar(conexion, {"tipo": "auth_ok", "usuario_id": usuario_id})
            return {"tipo": "auth_ok", "usuario_id": usuario_id}

        # 2. Envío de mensaje: requiere estar autenticado.
        if tipo == "mensaje":
            if usuario_id_actual is None:
                self._enviar(conexion, {"tipo": "error", "detalle": "No autenticado"})
                return None

            destinatario_id = payload.get("destinatario_id")
            texto = payload.get("texto", "")

            try:
                with get_session() as session_db:
                    conversacion = obtener_o_crear_conversacion(
                        session_db, usuario_id_actual, destinatario_id
                    )
                    mensaje = enviar_mensaje(
                        session_db, conversacion.id, usuario_id_actual, texto
                    )
                    conversacion_id = conversacion.id
                    mensaje_id = mensaje.id
            except Exception as error:
                self._enviar(conexion, {"tipo": "error", "detalle": str(error)})
                return None

            # Notificar en vivo al destinatario si está conectado ahora mismo
            with self._lock:
                socket_destinatario = self._clientes_conectados.get(destinatario_id)

            if socket_destinatario:
                self._enviar(
                    socket_destinatario,
                    {
                        "tipo": "mensaje_nuevo",
                        "conversacion_id": conversacion_id,
                        "emisor_id": usuario_id_actual,
                    },
                )

            self._enviar(
                conexion, {"tipo": "mensaje_enviado", "mensaje_id": mensaje_id}
            )
            return None

        return None

    @staticmethod
    def _enviar(conexion: socket.socket, payload: dict):
        try:
            conexion.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        except OSError:
            pass


def iniciar_servidor_bloqueante(host: str = HOST_DEFECTO, puerto: int = PUERTO_DEFECTO):
    """Punto de entrada simple para correr el servidor de forma manual:
    python -m chat.chat_server
    """
    servidor = ChatServer(host, puerto)
    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        servidor.detener()


if __name__ == "__main__":
    iniciar_servidor_bloqueante()