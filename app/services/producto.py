import uuid
import httpx
import os
from fastapi import BackgroundTasks
from sqlalchemy import text
from app.database.config import SessionLocal
from app.services.groq_service import consultar_modelo_groq


from dotenv import load_dotenv

# Carga las variables definidas en el archivo .env
load_dotenv()

# Lee las credenciales
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


def procesar_lote_en_segundo_plano(ticket_id: str, productos_info: list):
    db = SessionLocal()
    try:
        resultados_procesados = []

        for item in productos_info:
            prod_id = item["id"]
            nombre = item["nombre"]

            # Prompt estricto para limitar la longitud (máx. 50 palabras en total) y separar campos
            prompt = f"""Para el producto '{nombre}', genera:
1. Una descripción comercial atractiva (máximo 30 palabras).
2. Sus características principales (máximo 20 palabras).

Responde estrictamente con este formato, sin saludos ni texto adicional:
DESCRIPCION: [Tu descripción aquí]
CARACTERISTICAS: [Tus características aquí]"""

            # Llamada a Groq
            respuesta_ia = consultar_modelo_groq(prompt)

            # Parsear la respuesta para separar descripción y características
            descripcion_ia = ""
            caracteristicas_ia = ""

            for linea in respuesta_ia.split("\n"):
                if linea.startswith("DESCRIPCION:"):
                    descripcion_ia = linea.replace("DESCRIPCION:", "").strip()
                elif linea.startswith("CARACTERISTICAS:"):
                    caracteristicas_ia = linea.replace("CARACTERISTICAS:", "").strip()

            # Fallback por si la IA no sigue estrictamente el formato
            if not descripcion_ia:
                descripcion_ia = respuesta_ia

            # Actualizamos AMBAS columnas en la base de datos
            db.execute(
                text(
                    "UPDATE productos SET descripcion = :desc, caracteristicas = :carac, estado = 'completado' WHERE id = :id"
                ),
                {
                    "desc": descripcion_ia,
                    "carac": caracteristicas_ia,
                    "id": prod_id,
                },
            )

            resultados_procesados.append(
                {
                    "id": prod_id,
                    "nombre": nombre,
                    "descripcion": descripcion_ia,
                    "caracteristicas": caracteristicas_ia,
                }
            )

        # 1. Actualizamos la tarea a 'completado'
        db.execute(
            text(
                "UPDATE async_tasks SET estado = 'completado' WHERE ticket_id = :ticket"
            ),
            {"ticket": ticket_id},
        )

        # 2. Consultamos la webhook_url guardada en la base de datos para este ticket
        res_task = db.execute(
            text("SELECT webhook_url FROM async_tasks WHERE ticket_id = :ticket"),
            {"ticket": ticket_id},
        ).fetchone()

        db.commit()

        # 3. DISPARAR EL WEBHOOK REAL HACIA WEBHOOK.SITE
        if res_task and res_task[0]:
            webhook_url = res_task[0]
            payload = {
                "ticket_id": ticket_id,
                "estado": "completado",
                "productos": resultados_procesados,
            }
            try:
                with httpx.Client() as client:
                    client.post(webhook_url, json=payload, timeout=10.0)
            except Exception as webhook_error:
                print(f"Error al enviar el webhook: {webhook_error}")

    except Exception as e:
        db.rollback()
        db.execute(
            text(
                "UPDATE async_tasks SET estado = 'fallido', detalles = :detalles WHERE ticket_id = :ticket"
            ),
            {"detalles": str(e), "ticket": ticket_id},
        )
        db.commit()
    finally:
        db.close()

def registrar_y_procesar_lote(productos: list, background_tasks: BackgroundTasks, db):
    lote_id = str(uuid.uuid4())
    ticket_id = str(uuid.uuid4())

    # Colocar aquí tu URL única de Webhook.site
    url_webhook_prueba = WEBHOOK_URL

    db.execute(
        text(
            "INSERT INTO async_tasks (ticket_id, lote_id, webhook_url, estado) VALUES (:ticket, :lote, :webhook, 'procesando')"
        ),
        {"ticket": ticket_id, "lote": lote_id, "webhook": url_webhook_prueba},
    )

    productos_registrados = []

    for p in productos:
        resultado = db.execute(
            text(
                "INSERT INTO productos (nombre, estado) VALUES (:nombre, 'pendiente')"
            ),
            {"nombre": p.nombre},
        )
        producto_id = resultado.lastrowid
        productos_registrados.append({"id": producto_id, "nombre": p.nombre})

    db.commit()

    background_tasks.add_task(
        procesar_lote_en_segundo_plano, ticket_id, productos_registrados
    )

    return {
        "mensaje": "Lote de productos registrado exitosamente. La IA está procesando el contenido en segundo plano.",
        "lote_id": lote_id,
        "ticket_id": ticket_id,
        "total_productos": len(productos_registrados),
        "estado": "procesando",
    }