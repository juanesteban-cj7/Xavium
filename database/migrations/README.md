# Migraciones

Por ahora, la creación de tablas se maneja con
`Base.metadata.create_all()` en `database/db_connection.py::init_db()`,
suficiente para la etapa de prototipo.

Cuando el esquema empiece a cambiar en producción (con datos reales
que no se puedan simplemente recrear), se recomienda introducir
**Alembic** aquí para migraciones versionadas.
