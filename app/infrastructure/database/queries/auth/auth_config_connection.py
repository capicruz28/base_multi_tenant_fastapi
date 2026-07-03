"""ADR-012 — conexión normativa de cliente_auth_config (Control Plane SSOT)."""
from app.infrastructure.database.connection_async import DatabaseConnection

AUTH_CONFIG_STORE_CONNECTION = DatabaseConnection.ADMIN

__all__ = ["AUTH_CONFIG_STORE_CONNECTION"]
