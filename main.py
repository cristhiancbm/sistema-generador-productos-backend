from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.config import verificar_conexion_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    verificar_conexion_db()
    yield


# Instancia principal de la aplicación
app = FastAPI(
    title="API REST GENERADOR DE PROUCTOS",
    description="API para la generacion de productos",
    version="1.0.0",
    lifespan=lifespan,
)


# Endpoint GET raíz
@app.get("/")
def ruta_raiz():
    return {
        "estado": "exitoso",
        "mensaje": "Servidor activo y respondiendo correctamente.",
    }