from fastapi import FastAPI

# Instancia principal de la aplicación
app = FastAPI(
    title="API REST GENERADOR DE PROUCTOS",
    description="API para la generacion de productos",
    version="1.0.0",
)


# Endpoint GET raíz
@app.get("/")
def ruta_raiz():
    return {
        "estado": "exitoso",
        "mensaje": "Servidor activo y respondiendo correctamente.",
    }