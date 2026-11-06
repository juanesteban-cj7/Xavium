# Xavium con Docker

## Requisitos

- Docker Engine o Docker Desktop.
- Un navegador moderno.

## Crear e iniciar la aplicación

```bash
docker compose up -d --build
```

Cuando el contenedor ya fue creado, puedes iniciarlo y reconstruirlo con:

```bash
docker compose up -d --build
```

Para ver si el contenedor está listo y consultar errores:

```bash
docker compose ps
docker compose logs --tail 100
```

Esperar a que el estado sea `Up` o `running` y abrir `http://localhost:6080/vnc.html`.
En la ventana de noVNC, hacer clic en **Connect**.

El puerto VNC adicional es `5900`. La carpeta Docker `xavium_database` conserva la base de datos SQLite entre reinicios.

## Detener

```bash
docker compose down
```

Para borrar también los datos persistidos:

```bash
docker compose down -v
```
