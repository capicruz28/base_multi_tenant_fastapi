"""ADR-002-A — conexión normativa del IAM Session Store (Control Plane)."""
from app.infrastructure.database.connection_async import DatabaseConnection

SESSION_STORE_CONNECTION = DatabaseConnection.ADMIN

__all__ = ["SESSION_STORE_CONNECTION"]
