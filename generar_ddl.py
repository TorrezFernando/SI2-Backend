"""
Genera el script SQL (DDL) completo de la base de datos a partir de los
modelos SQLAlchemy del proyecto, respetando el orden de dependencias
(FK) entre tablas.

Uso:
    python generar_ddl.py > esquema.sql

Requiere que el proyecto (y sus modelos) sean importables desde donde
se ejecute este script, es decir, debe correrse desde la raiz del
proyecto (SI2-Backend), con el entorno virtual activado.
"""

import sys
from datetime import datetime

from sqlalchemy.schema import CreateTable

from database.database import Base, engine
import database.models  # noqa: F401  (registra todos los modelos modulares)


def generar_ddl():
    encabezado = f"""-- ============================================================================
-- SCRIPT DDL GENERADO AUTOMATICAMENTE
-- Proyecto: Inmobiliaria Raices (Multi-Tenant)
-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================================================
-- Este archivo se genera a partir de los modelos SQLAlchemy del proyecto.
-- No editar manualmente: modificar los modelos en su lugar y volver a
-- generar este script con: python generar_ddl.py > esquema.sql
-- ============================================================================

"""
    salida = [encabezado]

    tablas = Base.metadata.sorted_tables  # ya vienen ordenadas segun dependencias FK

    # Sentencias DROP en orden inverso, por si se quiere dejar la base limpia
    # antes de recrear el esquema.
    salida.append("-- 1. Eliminacion de tablas en orden inverso a sus dependencias\n")
    for tabla in reversed(tablas):
        salida.append(f"DROP TABLE IF EXISTS {tabla.name} CASCADE;\n")
    salida.append("\n")

    # Sentencias CREATE TABLE en el orden correcto
    salida.append("-- 2. Creacion de tablas\n\n")
    for tabla in tablas:
        ddl = str(CreateTable(tabla).compile(engine)).strip()
        salida.append(f"-- Tabla: {tabla.name}\n")
        salida.append(ddl + ";\n\n")

    return "".join(salida)


if __name__ == "__main__":
    contenido = generar_ddl()
    # Se imprime a stdout para poder redirigir con > esquema.sql
    sys.stdout.write(contenido)