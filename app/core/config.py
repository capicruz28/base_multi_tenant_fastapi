# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Literal
import os
from dotenv import load_dotenv
import secrets

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Service API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API FastAPI para Service"

    # Database Principal
    DB_SERVER: str = os.getenv("DB_SERVER", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "1433"))

    # Database Administración
    DB_ADMIN_SERVER: str = os.getenv("DB_ADMIN_SERVER", "")
    DB_ADMIN_USER: str = os.getenv("DB_ADMIN_USER", "")
    DB_ADMIN_PASSWORD: str = os.getenv("DB_ADMIN_PASSWORD", "")
    DB_ADMIN_DATABASE: str = os.getenv("DB_ADMIN_DATABASE", "")
    DB_ADMIN_PORT: int = int(os.getenv("DB_ADMIN_PORT", "1433"))

    # ✅ MEJORA: Security - Tokens con configuración robusta
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "")  # ✅ NUEVO: Clave separada para refresh tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # ✅ REDUCIDO: De 30 a 15 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Environment
    ENVIRONMENT: Literal["development", "production"] = os.getenv("ENVIRONMENT", "development")

    # CORS - sin "*" cuando allow_credentials=True
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5173",
        "https://api-service-cunb.onrender.com",
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ✅ MEJORA: Cookies - Configuración segura y dinámica
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_MAX_AGE: int = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # segundos

    @property
    def COOKIE_SECURE(self) -> bool:
        """
        ✅ MEJORA: Secure=True solo en producción (HTTPS)
        En desarrollo (HTTP) debe ser False para permitir cookies
        """
        return self.ENVIRONMENT == "production"
    
    @property
    def COOKIE_SAMESITE(self) -> Literal["lax", "none", "strict"]:
        """
        ✅ MEJORA: SameSite dinámico según entorno
        - 'lax' en desarrollo (mismo dominio, diferentes puertos)
        - 'strict' en producción (máxima seguridad)
        """
        if self.ENVIRONMENT == "production":
            return "strict"
        return "lax"

    @property
    def COOKIE_DOMAIN(self) -> str | None:
        """
        ✅ NUEVO: Dominio de la cookie (None en desarrollo, dominio específico en producción)
        """
        if self.ENVIRONMENT == "production":
            return os.getenv("COOKIE_DOMAIN", None)  # Ej: ".tudominio.com"
        return None

    def get_database_url(self, is_admin: bool = False) -> str:
        """
        Construye y retorna la URL de conexión a la base de datos
        Args:
            is_admin: Si es True, devuelve la conexión de administración
        """
        if is_admin:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.DB_ADMIN_SERVER},{self.DB_ADMIN_PORT};"
                f"DATABASE={self.DB_ADMIN_DATABASE};"
                f"UID={self.DB_ADMIN_USER};"
                f"PWD={self.DB_ADMIN_PASSWORD};"
                "TrustServerCertificate=yes;"
            )
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
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
        
        # ✅ NUEVO: Validar REFRESH_SECRET_KEY
        if not self.REFRESH_SECRET_KEY:
            raise ValueError("REFRESH_SECRET_KEY no está configurada en las variables de entorno")
        if len(self.REFRESH_SECRET_KEY) < 32:
            raise ValueError("REFRESH_SECRET_KEY debe tener al menos 32 caracteres")
        if self.REFRESH_SECRET_KEY == self.SECRET_KEY:
            raise ValueError("REFRESH_SECRET_KEY debe ser diferente de SECRET_KEY")
        
        if not self.ALGORITHM:
            raise ValueError("ALGORITHM no está configurado")
        
        # ✅ NUEVO: Validar tiempos de expiración
        if self.ACCESS_TOKEN_EXPIRE_MINUTES < 5:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser al menos 5 minutos")
        if self.REFRESH_TOKEN_EXPIRE_DAYS < 1:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS debe ser al menos 1 día")

    @staticmethod
    def generate_secret_key() -> str:
        """
        ✅ NUEVO: Genera una clave secreta segura
        Útil para generar SECRET_KEY y REFRESH_SECRET_KEY
        """
        return secrets.token_urlsafe(32)

# Instancia de configuración
settings = Settings()

# Validación al iniciar
try:
    settings.validate_security_settings()
except ValueError as e:
    import logging
    logging.error(f"❌ Error de configuración: {e}")
    raise