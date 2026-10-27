import os
from sqlalchemy import text
from app.database.config import engine


def ejecutar_migraciones():
    with engine.begin() as connection:
        # 1. Crear la tabla de control de migraciones si no existe
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        # 2. Obtener las migraciones que ya fueron aplicadas
        result = connection.execute(text("SELECT version FROM schema_migrations"))
        migraciones_aplicadas = {row[0] for row in result}

        # 3. Leer los archivos de la carpeta migrations/
        carpeta_migrations = "migrations"
        if not os.path.exists(carpeta_migrations):
            os.makedirs(carpeta_migrations)
            return

        archivos = sorted(os.listdir(carpeta_migrations))

        # 4. Iterar y ejecutar los archivos pendientes
        for archivo in archivos:
            if archivo.endswith(".sql") and archivo not in migraciones_aplicadas:
                ruta_archivo = os.path.join(carpeta_migrations, archivo)
                print(f"Aplicando migración: {archivo}...")

                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                # Ejecutar el script SQL del archivo
                for sentencia in sql_script.split(";"):
                    if sentencia.strip():
                        connection.execute(text(sentencia))

                # Registrar la migración como aplicada
                connection.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                    {"version": archivo},
                )
                print(f"Migración {archivo} aplicada exitosamente.")