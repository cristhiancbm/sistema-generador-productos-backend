import uuid
import httpx
import os
from fastapi import BackgroundTasks
from sqlalchemy import text
from app.database.config import SessionLocal
from app.services.groq_service import consultar_modelo_groq

from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


def _consultar_y_parsear_ia(nombre: str) -> tuple[str, str]:
    """Genera el prompt, consulta a Groq y extrae descripción y características."""
    prompt = f"""Para el producto '{nombre}', genera:
1. Una descripción comercial atractiva (máximo 30 palabras).
2. Sus características principales (máximo 20 palabras).

Responde estrictamente con este formato, sin saludos ni texto adicional:
DESCRIPCION: [Tu descripción aquí]
CARACTERISTICAS: [Tus características aquí]"""

    respuesta_ia = consultar_modelo_groq(prompt)

    descripcion_ia = ""
    caracteristicas_ia = ""

    for linea in respuesta_ia.split("\n"):
        if linea.startswith("DESCRIPCION:"):
            descripcion_ia = linea.replace("DESCRIPCION:", "").strip()
        elif linea.startswith("CARACTERISTICAS:"):
            caracteristicas_ia = linea.replace("CARACTERISTICAS:", "").strip()

    if not descripcion_ia and not caracteristicas_ia:
        descripcion_ia = respuesta_ia

    return descripcion_ia, caracteristicas_ia


def _actualizar_producto_en_db(db, prod_id: int, desc: str, carac: str):
    """Actualiza las columnas del producto en MySQL y lo marca como completado."""
    db.execute(
        text(
            "UPDATE productos SET descripcion = :desc, caracteristicas = :carac, estado = 'completado' WHERE id = :id"
        ),
        {"desc": desc, "carac": carac, "id": prod_id},
    )
def _disparar_webhook(webhook_url: str, ticket_id: str, resultados: list):
    """Envía la notificación HTTP POST con los resultados procesados."""
    payload = {
        "ticket_id": ticket_id,
        "estado": "completado",
        "productos": resultados,
    }
    try:
        with httpx.Client() as client:
            client.post(webhook_url, json=payload, timeout=10.0)
    except Exception as webhook_error:
        print(f"Error al enviar el webhook: {webhook_error}")


def procesar_lote_en_segundo_plano(ticket_id: str, productos_info: list):
    db = SessionLocal()
    try:
        resultados_procesados = []

        for item in productos_info:
            prod_id = item["id"]
            nombre = item["nombre"]

            # 1. Obtener datos limpios de la IA
            descripcion_ia, caracteristicas_ia = _consultar_y_parsear_ia(nombre)

            # 2. Actualizar base de datos
            _actualizar_producto_en_db(db, prod_id, descripcion_ia, caracteristicas_ia)

            resultados_procesados.append(
                {
                    "id": prod_id,
                    "nombre": nombre,
                    "descripcion": descripcion_ia,
                    "caracteristicas": caracteristicas_ia,
                }
            )

        # 3. Actualizar la tarea del ticket a completado
        db.execute(
            text(
                "UPDATE async_tasks SET estado = 'completado' WHERE ticket_id = :ticket"
            ),
            {"ticket": ticket_id},
        )

        # 4. Obtener URL del webhook
        res_task = db.execute(
            text("SELECT webhook_url FROM async_tasks WHERE ticket_id = :ticket"),
            {"ticket": ticket_id},
        ).fetchone()

        db.commit()

        # 5. Notificar por webhook si existe la URL
        if res_task and res_task[0]:
            _disparar_webhook(res_task[0], ticket_id, resultados_procesados)

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