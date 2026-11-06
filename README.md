# Xavium

**Xavium** es una aplicación de escritorio para estudiantes de la Pontificia Universidad Javeriana: te permite registrarte con tu correo institucional, encontrar compañeros con intereses parecidos a los tuyos, organizar tus contactos y conversar por chat privado o en grupos.

> Versión: **BETA 0.2** · Proyecto de Introducción a la Ingeniería, PUJ.

**Contenido**

1. [¿Cómo quieres instalarla?](#1-cómo-quieres-instalarla)
2. [Instalación con Docker (la más fácil)](#2-instalación-con-docker-la-más-fácil)
3. [Instalación con Python](#3-instalación-con-python)
4. [Ejecutable para Windows](#4-ejecutable-para-windows)
5. [Guía de uso](#5-guía-de-uso)
6. [Problemas frecuentes](#6-problemas-frecuentes)
7. [Qué todavía no está disponible](#7-qué-todavía-no-está-disponible)
8. [Para desarrolladores](#8-para-desarrolladores)

---

## 1. ¿Cómo quieres instalarla?

| Opción | Ideal si… | Necesitas | Dificultad |
|---|---|---|---|
| [**Docker**](#2-instalación-con-docker-la-más-fácil) | Quieres que funcione sin instalar Python ni dependencias. Funciona en Windows, macOS y Linux. | Docker y un navegador | Fácil |
| [**Python**](#3-instalación-con-python) | Quieres usar la ventana nativa de la app, o vas a modificar el código. | Python 3.12 y Git | Media |
| [**Ejecutable (.exe)**](#4-ejecutable-para-windows) | Usas Windows y solo quieres abrirla. | Solo Windows | Fácil |

> Con **Docker** la app se muestra dentro de una pestaña del navegador. Con **Python** y con el **.exe** se abre como una ventana normal de tu computador.

---

## 2. Instalación con Docker (la más fácil)

No necesitas instalar Python ni configurar nada: Docker prepara todo, incluidas las claves de seguridad.

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows o macOS) o Docker Engine (Linux).
- Un navegador moderno (Chrome, Edge, Firefox…).
- Unos minutos y conexión a internet la primera vez (se descarga y construye la imagen).

### Pasos

1. **Abre Docker Desktop** y espera a que indique que está en ejecución.
2. **Descarga el proyecto.** Con Git:

   ```bash
   git clone https://github.com/juanesteban-cj7/Xavium.git
   cd Xavium
   ```

   (Si no usas Git, en la página del repositorio pulsa **Code → Download ZIP**, descomprime y abre una terminal dentro de la carpeta.)

3. **Crea e inicia la aplicación:**

   ```bash
   docker compose up -d --build
   ```

   La primera vez puede tardar varios minutos.

4. **Comprueba que está lista:**

   ```bash
   docker compose ps
   ```

   Espera a que el estado sea `Up` o `running`.

5. **Ábrela en el navegador:** entra a <http://localhost:6080/vnc.html> y haz clic en **Connect**. Verás la ventana de Xavium.

### Uso diario

| Quiero… | Comando |
|---|---|
| Iniciarla de nuevo (o reconstruirla tras actualizar) | `docker compose up -d --build` |
| Ver si hay errores | `docker compose logs --tail 100` |
| Detenerla (conserva tus datos) | `docker compose down` |
| Detenerla **y borrar todos los datos** | `docker compose down -v` |

### Datos y configuración

- La base de datos y las claves de cifrado se guardan en volúmenes de Docker, por lo que **tus cuentas y chats se conservan** aunque reinicies. Solo se pierden con `docker compose down -v`.
- Si el puerto 6080 ya está ocupado, puedes cambiarlo creando un archivo `.env` junto a `docker-compose.yml` con, por ejemplo, `XVNC_PORT=6090` y luego entrar a `http://localhost:6090/vnc.html`.
- Opcional: para que los códigos de verificación se envíen por correo real, define en ese mismo `.env` las variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM`. Si no lo haces, la propia app te muestra el código en pantalla (ver [Verificar tu correo](#verificar-tu-correo)).

> ⚠️ **Seguridad:** el acceso por VNC (puerto `5900`) no tiene contraseña. Úsalo en tu computador personal y no expongas esos puertos a internet ni a una red que no sea de confianza.

---

## 3. Instalación con Python

### Requisitos

- **Python 3.12** (recomendado; la app se desarrolló y probó con esta versión).
- **Git** (o descarga el ZIP desde GitHub).
- Linux: algunas librerías del sistema para Qt (ver [Problemas frecuentes](#6-problemas-frecuentes)).

Comprueba tu versión de Python:

```bash
python --version
```

(En Windows, si `python` no funciona, prueba con `py --version`.)

### Pasos

**1. Descarga el proyecto**

```bash
git clone https://github.com/juanesteban-cj7/Xavium.git
cd Xavium
```

**2. Crea un entorno virtual** (mantiene las librerías de Xavium separadas del resto de tu sistema)

```bash
python -m venv .venv
```

Actívalo:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Si PowerShell bloquea el script, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo.

Sabrás que está activo porque la terminal mostrará `(.venv)` al inicio.

**3. Instala las dependencias**

```bash
pip install -r requirements.txt
```

**4. Crea el archivo de claves `config/.env`** ⚠️ *Este paso es obligatorio*

Xavium cifra los correos y los mensajes, y para eso necesita tres claves propias. Ese archivo **no viene en el repositorio** (por seguridad), así que debes generarlo una sola vez con este comando (es el mismo en todos los sistemas):

```bash
python -c "from cryptography.fernet import Fernet; import secrets; open('config/.env','w').write(f'FERNET_KEY={Fernet.generate_key().decode()}\nHMAC_SECRET={secrets.token_hex(32)}\nSESSION_SECRET={secrets.token_hex(32)}\n')"
```

Esto crea `config/.env` con claves aleatorias. No necesitas editarlo para empezar.

> ⚠️ **Guarda ese archivo y no lo cambies ni lo compartas.** Si lo borras o generas claves nuevas, los correos y chats que ya estaban guardados dejarán de poder leerse. Tampoco lo subas a GitHub (ya está excluido en `.gitignore`).

**5. Ejecuta la aplicación**

```bash
python main.py
```

Se abrirá la ventana de inicio de sesión. La primera vez, la app crea sola la base de datos y el catálogo de facultades e intereses.

### Dónde se guardan tus datos

En `database/database/xavium.db` (dentro de la carpeta del proyecto). Para empezar desde cero, cierra la app y borra ese archivo.

### Actualizar a una versión nueva

```bash
git pull
pip install -r requirements.txt
```

Tus datos y tu `config/.env` se conservan.

---

## 4. Ejecutable para Windows

Si el repositorio incluye el ejecutable en la carpeta **`dist/`**, no necesitas instalar nada más:

1. Descarga `Xavium.exe` (en GitHub: abre `dist/Xavium.exe` y pulsa el botón de descarga), o clona el repositorio.
2. Haz doble clic en `Xavium.exe`.
3. Si Windows muestra el aviso *"Windows protegió su PC"* (SmartScreen), pulsa **Más información → Ejecutar de todas formas**. Aparece porque la app no está firmada digitalmente.

Tus datos se guardan en una carpeta `database` **junto al `.exe`**. Si cambias el `.exe` de carpeta y quieres conservar tu cuenta, mueve también esa carpeta `database`.

---

## 5. Guía de uso

### Crear tu cuenta

1. En la pantalla de inicio de sesión pulsa **Regístrate**.
2. Completa el formulario:

   | Campo | Qué debes escribir |
   |---|---|
   | Nombre completo | Solo letras, espacios y los signos `'` `.` `-` (mínimo 2 caracteres). |
   | Edad | Un número entre **16 y 100**. |
   | Correo institucional | Debe terminar en **`@javeriana.edu.co`**. |
   | Facultad | Elige una de la lista. |
   | Contraseña | Mínimo **8 caracteres**, con al menos **una letra y un número**. |
   | Confirmar contraseña | Igual a la anterior. |

3. Pulsa **Registrarse**.

### Verificar tu correo

Tu cuenta queda pendiente hasta que confirmes tu correo con un código. Lo que verás depende de cómo esté instalada la app:

- **Sin correo configurado (lo normal al instalarla tú mismo):** aparece una ventana con tu código. Pulsa **Copiar código** si lo quieres guardar y luego **Verificar**. Listo, tu cuenta queda activa.
- **Con correo configurado:** recibirás un correo con el código. Escríbelo en la ventana que aparece; tienes **3 intentos**.

Si cierras la ventana sin verificar, tu cuenta queda pendiente y no podrás iniciar sesión todavía. Para terminar el proceso: en la pantalla de inicio de sesión escribe tu correo y pulsa **Reenviar código de verificación**. Los códigos duran **24 horas**.

### Iniciar sesión

1. Escribe tu correo institucional y tu contraseña, y pulsa **Iniciar sesión** (o la tecla Enter).
2. La app pasa a pantalla completa.

Cosas que conviene saber:

- Si te equivocas **5 veces** seguidas, la cuenta se bloquea **15 minutos** por seguridad.
- Si cierras la app sin cerrar sesión, al volver a abrirla entrarás directo durante unas **12 horas**. Para salir de verdad usa **☰ → Cerrar sesión**.
- Para cerrar la ventana en pantalla completa usa `Alt + F4` (Windows/Linux) o `Cmd + Q` (macOS).

### Moverte por la aplicación

La barra superior está siempre visible:

| Botón | Qué hace |
|---|---|
| **☰** (menú) | Abre el menú. Hoy solo funciona **Cerrar sesión**; las demás opciones llegarán más adelante. |
| **Inicio** | Tus chats recientes. |
| **Contactos** | Tus contactos y tus categorías. |
| **Grupos** | Tus grupos y sus chats. |
| **Buscar** | Encontrar a otros estudiantes. |

### Inicio: tus chats recientes

A la izquierda aparece la lista de tus conversaciones con el último mensaje. Haz clic en una para abrir el chat.

### Buscar estudiantes

1. Pulsa **Buscar** en la barra superior.
2. Escribe un nombre (o parte de él) y/o elige una **facultad** en el desplegable. Pulsa **Buscar** o Enter.
3. Los resultados salen **ordenados por compatibilidad** (intereses en común) y muestran nombre, facultad e intereses compartidos. Se muestran hasta 30 resultados y solo estudiantes con cuenta verificada.
4. **Haz doble clic** sobre alguien para abrir un chat con esa persona.

### Chatear

- Escribe tu mensaje abajo y pulsa **Enviar** o Enter.
- Los mensajes nuevos aparecen solos (la pantalla se actualiza cada par de segundos), así que no necesitas recargar.
- Verás **"Tú"** para tus mensajes y **"Otro"** para los de la otra persona.
- Tus mensajes se guardan cifrados en la base de datos.

### Contactos y categorías

**Agregar un contacto**

1. Entra a **Contactos** y pulsa **+ Agregar contacto**.
2. Elige a un estudiante de la lista y confirma con **OK**.

**Organizar contactos en categorías** (por ejemplo "Compañeros de clase" o "Amigos")

1. Pulsa **＋ Añadir clasificación**, escribe el nombre y elige un color.
2. Haz clic en la categoría para verla. Para cambiarla, usa los tres puntos **⋮** a su lado:
   - **Editar contactos:** marca quiénes pertenecen a esa categoría y guarda.
   - **Cambiar nombre**
   - **Cambiar color**
   - **Eliminar**
3. Con una categoría abierta, **haz doble clic** en un contacto para abrir el chat con esa persona.

### Grupos

1. Entra a **Grupos** y pulsa **+** (junto a "Lista de grupos") para crear uno; ponle un nombre.
2. Haz clic en el grupo para abrir su chat. A la derecha verás la **lista de miembros**.
3. Pulsa **+ Agregar miembro** para sumar a otros estudiantes.
4. Escribe en la parte de abajo y pulsa **Enviar**. Los mensajes del grupo también se actualizan solos.

### Cerrar sesión

Pulsa **☰ → Cerrar sesión**. La ventana vuelve a su tamaño normal y se muestra el inicio de sesión.

### Tu privacidad

- Las contraseñas **nunca se guardan tal cual**: se almacenan protegidas con bcrypt.
- Los correos y los mensajes se guardan **cifrados** en tu base de datos local.
- Importante: es cifrado "en reposo", **no** cifrado de extremo a extremo; protege la base de datos si alguien la obtiene, pero la aplicación sí puede leer los mensajes mientras funciona.
- Toda la información queda en **tu propia instalación** (tu computador o tu contenedor Docker); no se envía a ningún servidor externo.

---

## 6. Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| `Falta la variable de entorno obligatoria 'FERNET_KEY'` | No existe `config/.env`. Genera el archivo con el comando del [paso 4](#3-instalación-con-python). |
| `ModuleNotFoundError: No module named 'PyQt6'` (o `sqlalchemy`, `bcrypt`…) | Activa el entorno virtual (`(.venv)` debe verse en la terminal) y ejecuta `pip install -r requirements.txt`. |
| `python` no se reconoce (Windows) | Prueba con `py` en lugar de `python`, o reinstala Python marcando **"Add Python to PATH"**. |
| En Linux: `Could not load the Qt platform plugin "xcb"` | Instala las librerías de Qt: `sudo apt install libxcb-cursor0 libegl1 libgl1 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0` |
| Docker: la página `localhost:6080` no carga | Espera un momento tras `docker compose up`. Revisa `docker compose ps` y `docker compose logs --tail 100`. Verifica que Docker Desktop esté en ejecución. |
| Docker: *"port is already allocated"* | Otro programa usa el puerto. Cambia `XVNC_PORT` / `VNC_PORT` como se explica en la [sección de Docker](#datos-y-configuración). |
| "El formato del correo no es válido" / "Debes usar tu correo institucional" | El correo debe terminar en `@javeriana.edu.co`. |
| "Debes verificar tu correo institucional antes de iniciar sesión" | Pulsa **Reenviar código de verificación** en la pantalla de inicio y completa la verificación. |
| "El código de verificación expiró" | Pide uno nuevo con **Reenviar código de verificación**. |
| "Cuenta bloqueada temporalmente" | Espera el tiempo indicado (15 minutos) e inténtalo de nuevo. |
| No me llega el correo con el código | Si la instalación no tiene correo configurado, la app muestra el código en una ventana en vez de enviarlo. |
| Quiero empezar de cero | Cierra la app y borra `database/database/xavium.db` (Python) o ejecuta `docker compose down -v` (Docker). |

---

## 7. Qué todavía no está disponible

Xavium está en **beta**, así que algunas partes aún están en construcción:

- Las opciones **Tu perfil, Estadísticas, Privacidad y seguridad** y **Ayuda** del menú ☰ aparecen desactivadas.
- Todavía **no hay pantalla para elegir tus intereses** dentro de la app; por eso en los resultados de búsqueda puede aparecer *"Sin intereses en común declarados"*.
- El chat funciona por actualización automática periódica, no en tiempo real instantáneo.

---

## 8. Para desarrolladores

**Tecnologías:** Python · PyQt6 (interfaz) · SQLAlchemy + SQLite (datos) · bcrypt (contraseñas) · Fernet/AES y HMAC-SHA256 (cifrado e índices) · Docker + noVNC (despliegue).

**Estructura**

```
main.py          Punto de entrada
auth/            Registro, login, sesiones
chat/            Mensajes y cifrado de conversaciones
config/          Configuración (.env.example → .env)
contacts/        Contactos y categorías
database/        Modelos y conexión
groups/          Grupos
gui/             Pantallas de la interfaz
matching/        Búsqueda y algoritmo de compatibilidad
profile/         Perfil, facultades e intereses
security/        Cifrado, validaciones y auditoría
tests/           Pruebas automáticas
```

**Pruebas**

```bash
pip install pytest
python -m pytest tests
```

**Cómo se calcula la compatibilidad:** se usa el **índice de Jaccard** (coeficiente de similitud) entre los conjuntos de intereses de dos estudiantes. Más información: [Jaccard index](https://www.statisticshowto.com/jaccard-index/).

**Metodología de desarrollo (por fases)**

1. Núcleo de datos y seguridad: modelos de BD, hashing, cifrado base.
2. Autenticación: registro/login con validaciones y verificación de correo.
3. Perfil y catálogo de intereses y facultades.
4. Motor de búsqueda y *matching*.
5. Chat (primero local, luego con sockets reales).
6. Integración completa de la interfaz.
7. Pruebas de seguridad (básicas y unitarias).

**Generar el `.exe`:** con PyInstaller y el archivo `Xavium.spec` incluido (`pyinstaller Xavium.spec`). El `.spec` empaqueta también `config/.env`, así que genera ese archivo antes de compilar.

---

## Licencia

Este proyecto se distribuye bajo la licencia **GNU GPL v3**. Consulta el archivo [`LICENSE`](LICENSE).