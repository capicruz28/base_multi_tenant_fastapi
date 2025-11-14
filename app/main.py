# app/main.py (MODIFICADO)
from typing import Any
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import configure_exception_handlers, CustomException 
from app.api.v1.api import api_router
from app.db.connection import get_db_connection
from app.core.logging_config import setup_logging

# CRÍTICO: Importar el nuevo middleware y el contexto
from app.middleware.tenant_middleware import TenantMiddleware
from app.core.tenant_context import get_current_client_id

# IMPORTA ESTO SI NO LO TIENES:
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    
    # 1. Definición explícita del esquema Bearer (JWT) para Swagger
    security_scheme_definition = {
        # CRÍTICO: El nombre de la clave es lo que referenciarás después
        "JWTBearerAuth": { 
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Pegue el Access Token (JWT) obtenido del /auth/login/.",
        }
    }

    app = FastAPI(
        title=settings.PROJECT_NAME,
        # ... otros parámetros
        redirect_slashes=False,
        
        # 2. Inyectar la definición de seguridad en el documento OpenAPI
        openapi_extra={
            "components": {
                "securitySchemes": security_scheme_definition
            },
            # IMPORTANTE: No definimos 'security' globalmente aquí,
            # lo aplicaremos en cada ruta protegida para evitar conflictos.
        }
    )

    # Manejadores de excepciones custom
    configure_exception_handlers(app)

    # --- MIDDLEWARES (CRÍTICO: ORDEN IMPORTA) ---

    # 1. Tenant Middleware: Debe ser el PRIMERO para establecer el contexto.
    app.add_middleware(
        TenantMiddleware
    )
    
    # 2. CORS Middleware: Después del tenant, usa las settings de Allowed_Origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Middleware de logging con timing
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any):
        start = time.perf_counter()
        # Intentamos obtener el ID del cliente para el log (puede fallar si la ruta está excluida)
        client_id_log = "SYSTEM" 
        try:
             client_id_log = get_current_client_id()
        except Exception:
             pass # Si no hay contexto, usamos el default
             
        logger.info(f"[{client_id_log}] {request.client.host} -> {request.method} {request.url.path}")
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(f"[{client_id_log}] {request.client.host} <- {request.method} {request.url.path} {response.status_code if 'response' in locals() else 'N/A'} {duration_ms:.1f}ms")
        return response

    # 4. Middleware para añadir headers de seguridad básicos
    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    # Rutas API v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

# Instancia de la aplicación
app = create_application()

# Rutas base
@app.get("/")
async def root():
    """
    Ruta raíz que muestra información básica de la API
    """
    return {
        "message": "Service API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de la aplicación y la conexión a la BD.
    Prueba la conexión utilizando el contexto del tenant (ID 1 si se accede por IP/localhost).
    """
    db_status = "error"
    client_id = "N/A (No Contexto)"
    
    try:
        # Se obtiene el ID del cliente del request (o el default si no hay subdominio)
        client_id = get_current_client_id() 
        with get_db_connection() as conn:
            # Esta conexión ahora es tenant-aware gracias a multi_db.py
            conn.cursor().execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        logger.error(f"Error en health check para Cliente ID {client_id}: {str(e)}")
        db_status = "error"

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": db_status,
        "tenant_id": client_id # CRÍTICO: Muestra el ID del cliente activo.
    }

# Compatibilidad con código existente
@app.get("/api/test")
async def test_db():
    try:
        # PRUEBA: Usará la conexión del tenant actual (SYSTEM si no hay subdominio)
        with get_db_connection() as conn: 
            if conn:
                return {"message": "Conexión exitosa al tenant actual"}
            else:
                return {"error": "Conexión fallida: objeto de conexión es None"}
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/drivers")
async def check_drivers():
    """Endpoint para verificar drivers ODBC disponibles"""
    # Asume que test_drivers está disponible en app.db.connection
    from app.db.connection import test_drivers
    drivers = test_drivers()
    return {
        "drivers_available": list(drivers),
        "odbc_17_found": 'ODBC Driver 17 for SQL Server' in drivers
    }

@app.get("/debug-env")
async def debug_env():
    """Endpoint para verificar variables de entorno (sin mostrar passwords)"""
    return {
        "db_server": settings.DB_SERVER,
        "db_user": settings.DB_USER,
        "db_database": settings.DB_DATABASE,
        "db_port": settings.DB_PORT,
        "base_domain": settings.BASE_DOMAIN,
        "superadmin_client_id": settings.SUPERADMIN_CLIENTE_ID,
        "superadmin_subdominio": settings.SUPERADMIN_SUBDOMINIO,
        "db_password_set": bool(settings.DB_PASSWORD),
        "secret_key_set": bool(settings.SECRET_KEY),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )