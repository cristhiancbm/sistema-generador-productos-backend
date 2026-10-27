CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    caracteristicas TEXT,
    descripcion TEXT,
    estado VARCHAR(50) DEFAULT 'pendiente', -- 'pendiente', 'completado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE async_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id VARCHAR(100) UNIQUE NOT NULL,
    lote_id VARCHAR(100),
    webhook_url TEXT NOT NULL,
    estado VARCHAR(50) DEFAULT 'procesando', -- 'procesando', 'completado', 'fallido'
    detalles TEXT, -- Opcional: para guardar metadatos o errores
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);