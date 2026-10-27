# Sistema Generador de Productos con IA

Este proyecto es una solución backend construida con **FastAPI** y **MySQL** para el procesamiento masivo y asíncrono de catálogos de productos. Utiliza la API de **Groq AI** para generar descripciones comerciales persuasivas y listados de características técnicas optimizadas, permitiendo procesar lotes mediante tareas en segundo plano (`BackgroundTasks`) y notificaciones mediante Webhooks.

---

## Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Framework Web:** FastAPI
- **Base de Datos:** MySQL
- **ORM / SQL:** SQLAlchemy (Raw SQL execution via `text()`)
- **Cliente HTTP:** HTTPX
- **Integración IA:** Groq SDK
- **Gestión de Entorno:** python-dotenv

---

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:

- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/)
- Servidor de [MySQL](https://www.mysql.com/) en ejecución (o contenedor de Docker con MySQL)
- Una API Key activa de [Groq AI](https://console.groq.com/)

---

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/cristhiancbm/sistema-generador-productos-backend.git
cd sistema-generador-productos-backend
```

### 2. Crear y Activar el Entorno Virtual

En Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto basándote en el siguiente modelo:

```bash
# Configuración Base de Datos MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_NAME=sistema_generador_productos_db

# Configuración API Groq
GROQ_API_KEY=tu_api_key_de_groq

# Webhook URL para Pruebas (Webhook.site u otro)
WEBHOOK_URL=https://webhook.site/tu-id-unico
```

---

## Base de Datos

En tu servidor mysql crea una base de datos indicando el nombre descrito en la variable de entorno `DB_NAME`

```sql
CREATE DATABASE sistema_generador_productos_db;
```

---

## Ejecución del Servidor

Inicia el servidor de desarrollo de FastAPI utilizando `uvicorn`:

```bash
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://localhost:8000`.

---

## Documentación Interactiva (Swagger)

Puedes acceder a la interfaz interactiva de OpenAPI para probar los endpoints en:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Flujo de Trabajo (Endpoints Principales)

1. **`POST /productos/`**:
   - Recibe un listado de nombres de productos.
   - Crea los productos en estado `pendiente` y la tarea en `procesando`.
   - Lanza la tarea asíncrona en segundo plano y responde de inmediato con el `ticket_id` y `lote_id`.

2. **`GET /productos/estado/{ticket_id}`**:
   - Permite consultar el estado actual del procesamiento de un ticket (`procesando`, `completado` o `fallido`).

3. **Notificación Webhook**:
   - Una vez finalizado el procesamiento por la IA, el servidor envía un `POST` HTTP automático a la `WEBHOOK_URL` configurada con la estructura JSON completa de los productos generados.
