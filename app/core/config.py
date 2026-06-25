# app/core/config.py (MODIFICADO)
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List, Literal
import os
from dotenv import load_dotenv
import secrets
from typing import Optional

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Service API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API FastAPI para Service"

    # Database Principal (Base de datos centralizada Multi-Tenant)
    DB_SERVER: str = os.getenv("DB_SERVER", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "1433"))
    DB_DRIVER: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server") # Driver por defecto, puede ser sobrescrito por variable de entorno

    # Database Administración (Mantenido por si se usa para tareas específicas de admin, 
    # aunque en multi-tenant el admin DB suele ser la misma que la principal)
    DB_ADMIN_SERVER: str = os.getenv("DB_ADMIN_SERVER", "")
    DB_ADMIN_USER: str = os.getenv("DB_ADMIN_USER", "")
    DB_ADMIN_PASSWORD: str = os.getenv("DB_ADMIN_PASSWORD", "")
    DB_ADMIN_DATABASE: str = os.getenv("DB_ADMIN_DATABASE", "")
    DB_ADMIN_PORT: int = int(os.getenv("DB_ADMIN_PORT", "1433"))
    
    # --- NUEVAS VARIABLES MULTI-TENANT (CRÍTICO) ---
    BASE_DOMAIN: str = os.getenv("BASE_DOMAIN", "localhost")  # Ej: "tudominio.com"
    SUPERADMIN_CLIENTE_ID: str = os.getenv("SUPERADMIN_CLIENTE_ID", "")  # UUID como string
    SUPERADMIN_CLIENTE_CODIGO: str = os.getenv("SUPERADMIN_CLIENTE_CODIGO", "SYSTEM")
    SUPERADMIN_SUBDOMINIO: str = os.getenv("SUPERADMIN_SUBDOMINIO", "platform")
    # ✅ CORRECCIÓN: Agregar el nombre de usuario del Super Admin
    SUPERADMIN_USERNAME: str = os.getenv("SUPERADMIN_USERNAME", "superadmin")
    # Bootstrap plataforma (scripts/bootstrap_platform.py)
    PLATFORM_BOOTSTRAP_INITIAL_PASSWORD: str = os.getenv("PLATFORM_BOOTSTRAP_INITIAL_PASSWORD", "")
    PLATFORM_BOOTSTRAP_CONTACT_EMAIL: str = os.getenv("PLATFORM_BOOTSTRAP_CONTACT_EMAIL", "")
    PLATFORM_BOOTSTRAP_RAZON_SOCIAL: str = os.getenv("PLATFORM_BOOTSTRAP_RAZON_SOCIAL", "")
    # -----------------------------------------------

    # ✅ MEJORA: Security - Tokens con configuración robusta
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # ============================================
    # ENCRYPTION CONFIGURATION (NUEVO)
    # ============================================
    ENCRYPTION_KEY: str = ""  # Se carga desde .env

    # Environment
    ENVIRONMENT: Literal["development", "production"] = os.getenv("ENVIRONMENT", "development")

    # CORS - sin "*" cuando allow_credentials=True
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "http://acme.midominio.com:5173",
        "http://innova.midominio.com:5173",
        "http://techcorp.midominio.com:5173",
        "http://global.midominio.com:5173",
        "https://api-service-cunb.onrender.com",
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ============================================
    # FEATURE FLAGS - FASE 1: SEGURIDAD (ACTIVADO POR DEFECTO)
    # ============================================
    # ✅ ACTIVADO: Las funcionalidades de seguridad están activas por defecto
    # Para desactivar, establecer variable de entorno a "false"
    # Ejemplo: ENABLE_TENANT_TOKEN_VALIDATION=false
    # ⚠️ CORRECCIÓN RIESGO #2: En producción, ENABLE_TENANT_TOKEN_VALIDATION siempre es True
    # Leer valor raw desde variable de entorno
    _enable_tenant_token_validation_raw: str = os.getenv("ENABLE_TENANT_TOKEN_VALIDATION", "true")
    
    @model_validator(mode='after')
    def _validate_tenant_token_validation(self):
        """
        Valida y fuerza ENABLE_TENANT_TOKEN_VALIDATION en producción.
        
        ✅ CORRECCIÓN RIESGO #2: En producción, siempre fuerza validación de tenant en tokens.
        """
        # ✅ CORRECCIÓN RIESGO #2: En producción, forzar validación de tenant en tokens
        if self.ENVIRONMENT == "production":
            if self._enable_tenant_token_validation_raw.lower() == "false":
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "[SECURITY] ENABLE_TENANT_TOKEN_VALIDATION=false ignorado en producción. "
                    "La validación de tenant en tokens es obligatoria en producción por seguridad."
                )
            # Forzar a True en producción
            self._enable_tenant_token_validation_raw = "true"
            if self._iam_session_management_v2_enabled_raw.lower() == "true":
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "[IAM-SESSION-V2] IAM_SESSION_MANAGEMENT_V2_ENABLED=true en producción. "
                    "Solo debe activarse tras cutover F14."
                )
        return self

    @property
    def IAM_SESSION_MANAGEMENT_V2_ENABLED(self) -> bool:
        """Session Management V2 — desactivado por defecto hasta cutover F14."""
        return self._iam_session_management_v2_enabled_raw.lower() == "true"
    
    @property
    def ENABLE_TENANT_TOKEN_VALIDATION(self) -> bool:
        """
        Validación de tenant en tokens.
        
        ✅ CORRECCIÓN RIESGO #2: En producción, siempre es True (no puede desactivarse).
        En desarrollo, puede desactivarse estableciendo ENABLE_TENANT_TOKEN_VALIDATION=false.
        """
        # En producción, siempre True (ya fue forzado en model_validator)
        if self.ENVIRONMENT == "production":
            return True
        # En desarrollo, permitir desactivar para testing
        return self._enable_tenant_token_validation_raw.lower() == "true"
    
    ENABLE_QUERY_TENANT_VALIDATION: bool = os.getenv("ENABLE_QUERY_TENANT_VALIDATION", "true").lower() == "true"
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    
    # ✅ CORRECCIÓN AUDITORÍA: Filtro obligatorio de cliente_id
    # Por defecto, el filtro de tenant es OBLIGATORIO en BaseRepository
    # Para permitir bypass (solo en casos especiales), establecer a "true"
    # ⚠️ ADVERTENCIA: Permitir bypass reduce la seguridad multi-tenant
    ALLOW_TENANT_FILTER_BYPASS: bool = os.getenv("ALLOW_TENANT_FILTER_BYPASS", "false").lower() == "true"
    
    # Configuración de rate limiting
    # Límites generosos para no afectar uso normal, pero proteger contra ataques
    RATE_LIMIT_LOGIN: str = os.getenv("RATE_LIMIT_LOGIN", "10/minute")  # 10 intentos de login por minuto (generoso)
    RATE_LIMIT_API: str = os.getenv("RATE_LIMIT_API", "200/minute")  # 200 requests API por minuto (generoso)

    # ============================================
    # FEATURE FLAGS - FASE 2: PERFORMANCE (ACTIVADO POR DEFECTO)
    # ============================================
    # ✅ ACTIVADO: Mejoras de performance están activas por defecto
    # Para desactivar, establecer variable de entorno a "false"
    ENABLE_CONNECTION_POOLING: bool = os.getenv("ENABLE_CONNECTION_POOLING", "true").lower() == "true"
    ENABLE_REDIS_CACHE: bool = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"
    
    # ✅ FASE 1: Unit of Work Pattern (ACTIVADO POR DEFECTO)
    # Para desactivar temporalmente, establecer ENABLE_UNIT_OF_WORK=false
    ENABLE_UNIT_OF_WORK: bool = os.getenv("ENABLE_UNIT_OF_WORK", "true").lower() == "true"
    
    # ============================================
    # PERMISSION RESOLVER (Stage 1 - Fase A)
    # ============================================
    USE_PERMISSION_RESOLVER: bool = os.getenv("USE_PERMISSION_RESOLVER", "false").lower() == "true"
    PERMISSION_RESOLVER_CACHE_ENABLED: bool = os.getenv("PERMISSION_RESOLVER_CACHE_ENABLED", "false").lower() == "true"
    PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION: bool = os.getenv("PERMISSION_RESOLVER_FILTER_BY_SUBSCRIPTION", "false").lower() == "true"
    PERMISSION_RESOLVER_CACHE_TTL: int = int(os.getenv("PERMISSION_RESOLVER_CACHE_TTL", "300"))
    
    # Code-first RBAC: sincronizar permisos declarados en código con tabla permiso al startup.
    RBAC_PERMISSION_SYNC_ENABLED: bool = os.getenv("RBAC_PERMISSION_SYNC_ENABLED", "true").lower() == "true"

    # INV-P0-002: escritura directa POST/PUT /inv/stock (tabla derivada). Default false = bloqueado.
    INV_ALLOW_STOCK_DIRECT_WRITE: bool = os.getenv("INV_ALLOW_STOCK_DIRECT_WRITE", "false").lower() == "true"

    # ============================================
    # IAM SESSION MANAGEMENT V2 (F0 — gobernanza)
    # ============================================
    # Default false en todos los entornos. Activar solo en dev/staging o F14 producción.
    _iam_session_management_v2_enabled_raw: str = os.getenv(
        "IAM_SESSION_MANAGEMENT_V2_ENABLED", "false"
    )
    IAM_SESSION_V2_TENANT_ALLOWLIST: str = os.getenv("IAM_SESSION_V2_TENANT_ALLOWLIST", "")
    
    # Stage 2: Menú puede recibir permisos efectivos ya calculados (evita lógica duplicada).
    # Por defecto False; cuando True, el endpoint /modulos-menus/me/ pasa user.permisos al servicio.
    USE_MENU_EFFECTIVE_PERMISSIONS: bool = os.getenv("USE_MENU_EFFECTIVE_PERMISSIONS", "false").lower() == "true"
    
    # ✅ CORRECCIÓN AUDITORÍA: Conexiones async (desactivado por defecto hasta migración completa)
    # Para activar, instalar dependencias: pip install 'sqlalchemy[asyncio]' aioodbc
    # Luego establecer: ENABLE_ASYNC_CONNECTIONS=true
    ENABLE_ASYNC_CONNECTIONS: bool = os.getenv("ENABLE_ASYNC_CONNECTIONS", "false").lower() == "true"
    
    # Configuración de Connection Pooling
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))  # Tamaño del pool (conexiones simultáneas)
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "5"))  # Conexiones adicionales permitidas
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # Reciclar conexiones cada hora (segundos)
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # Timeout para obtener conexión (segundos)
    
    # Configuración de Redis Cache (opcional)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))  # Timeout en segundos
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "300"))  # TTL por defecto: 5 minutos

    # ✅ MEJORA: Cookies - Configuración segura y dinámica
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_MAX_AGE: int = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # segundos

    @property
    def COOKIE_SECURE(self) -> bool:
        """
        ✅ MEJORA: Secure=True solo en producción (HTTPS)
        """
        return self.ENVIRONMENT == "production"
    
    @property
    def COOKIE_SAMESITE(self) -> Literal["lax", "none", "strict"]:
        """
        ✅ MEJORA: SameSite dinámico según entorno
        """
        if self.ENVIRONMENT == "production":
            return "none"
        return "lax"

    @property
    def COOKIE_DOMAIN(self) -> str | None:
        """
        ✅ NUEVO: Dominio de la cookie (None en desarrollo, dominio específico en producción)
        """
        # Leer desde variable de entorno (añadida en .env)
        cookie_domain = os.getenv("COOKIE_DOMAIN", None)

        if cookie_domain:
            return cookie_domain  # Ej: ".app.local" o ".tudominio.com"
        
        # Fallback: Si no está configurado, usar BASE_DOMAIN con punto
        if self.BASE_DOMAIN and self.BASE_DOMAIN != "localhost":
            return f".{self.BASE_DOMAIN}"
        #if self.ENVIRONMENT == "production":
        #    return os.getenv("COOKIE_DOMAIN", None)  # Ej: ".tudominio.com"

        return None

    def get_database_url(self, is_admin: bool = False) -> str:
        """
        [DEPRECADO PARA MULTI-TENANT] Esta función se mantiene por compatibilidad 
        pero la lógica de conexión principal debe usar get_db_connection 
        (que es tenant-aware).
        """
        if is_admin:
            return (
                f"DRIVER={{{self.DB_DRIVER}}};"
                f"SERVER={self.DB_ADMIN_SERVER},{self.DB_ADMIN_PORT};"
                f"DATABASE={self.DB_ADMIN_DATABASE};"
                f"UID={self.DB_ADMIN_USER};"
                f"PWD={self.DB_ADMIN_PASSWORD};"
                "TrustServerCertificate=yes;"
            )
        # Retorna la conexión principal (la usará multi_db para todos los tenants por defecto)
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_SERVER},{self.DB_PORT};"
            f"DATABASE={self.DB_DATABASE};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )

    class Config:
        case_sensitive = True

    def validate_security_settings(self):
        """✅ MEJORA: Validación robusta de configuraciones de seguridad"""
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY no está configurada en las variables de entorno")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        
        if not self.REFRESH_SECRET_KEY:
            raise ValueError("REFRESH_SECRET_KEY no está configurada en las variables de entorno")
        if len(self.REFRESH_SECRET_KEY) < 32:
            raise ValueError("REFRESH_SECRET_KEY debe tener al menos 32 caracteres")
        if self.REFRESH_SECRET_KEY == self.SECRET_KEY:
            raise ValueError("REFRESH_SECRET_KEY debe ser diferente de SECRET_KEY")
        
        if not self.ALGORITHM:
            raise ValueError("ALGORITHM no está configurado")
        
        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 5:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser al menos 5 minutos")
        if self.REFRESH_TOKEN_EXPIRE_DAYS < 1:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS debe ser al menos 1 día")

    @staticmethod
    def generate_secret_key() -> str:
        """
        ✅ NUEVO: Genera una clave secreta segura
        """
        return secrets.token_urlsafe(32)

# Instancia de configuración
settings = Settings()

# Validación al iniciar
try:
    settings.validate_security_settings()
except ValueError as e:
    import logging
    logging.error(f"Error de configuración: {e}")
    raise