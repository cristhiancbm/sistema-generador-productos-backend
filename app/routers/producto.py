from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.config import get_db
from app.schemas.producto import ProductoCreate, LoteProductosCreate
from app.services.producto import (
    registrar_y_procesar_lote,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/")
def registrar_lote_productos(
    lote: LoteProductosCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        return registrar_y_procesar_lote(lote.productos, background_tasks, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estado/{ticket_id}")
def consultar_estado_ticket(ticket_id: str, db: Session = Depends(get_db)):
    try:
        resultado = db.execute(
            text("SELECT estado, detalles FROM async_tasks WHERE ticket_id = :ticket"),
            {"ticket": ticket_id},
        ).fetchone()

        if not resultado:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")

        return {
            "ticket_id": ticket_id,
            "estado": resultado[0],
            "detalles": resultado[1],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))