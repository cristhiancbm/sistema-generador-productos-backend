from pydantic import BaseModel
from typing import List, Optional


# Lo que el cliente envía para registrar el producto (solo el nombre)
class ProductoCreate(BaseModel):
    nombre: str


class LoteProductosCreate(BaseModel):
    productos: List[ProductoCreate]


# Lo que la API devuelve al consultar el producto
class ProductoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    estado: str