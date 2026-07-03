import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Final

VALID_LOG_LEVELS: Final[frozenset[str]] = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
)

DEFAULT_LOG_LEVEL: Final[str] = "INFO"


class SafeRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler que maneja errores de permisos en Windows.
    Si la rotación falla (archivo en uso), simplemente continúa sin rotar.
    """

    def doRollover(self):
        try:
            super().doRollover()
        except (OSError, PermissionError) as e:
            if sys.platform == "win32":
                try:
                    if self.stream is not None:
                        self.stream.write(f"Warning: Could not rotate log file: {e}\n")
                        self.stream.flush()
                except (AttributeError, OSError):
                    pass
            else:
                raise


def normalize_log_level(level: str | None, *, default: str = DEFAULT_LOG_LEVEL) -> str:
    """
    Normaliza un nombre de nivel de logging Python.

    Acepta DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive).
    Valores inválidos → ``default`` (INFO).
    """
    if not level or not str(level).strip():
        return default
    normalized = str(level).strip().upper()
    if normalized not in VALID_LOG_LEVELS:
        return default
    return normalized


def resolve_log_level_numeric(level: str | None = None) -> int:
    """Resuelve el entero de logging stdlib para el nivel indicado o LOG_LEVEL env."""
    name = normalize_log_level(level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL))
    return getattr(logging, name)


def get_uvicorn_log_level(level: str | None = None) -> str:
    """
    Nivel para ``uvicorn --log-level`` (minúsculas).

    Usa la misma fuente que la app: argumento explícito o LOG_LEVEL env.
    """
    return normalize_log_level(level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)).lower()


def setup_logging(log_level: str | None = None, *, force: bool = False) -> str:
    """
    Configura el logging global de la aplicación con soporte UTF-8.

    Args:
        log_level: Nivel explícito; si es None usa LOG_LEVEL de entorno (default INFO).
        force: Si True, reconfigura handlers existentes (Python 3.8+).

    Returns:
        Nombre del nivel aplicado (ej. ``INFO``).
    """
    level_name = normalize_log_level(log_level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL))
    numeric_level = getattr(logging, level_name)

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    file_handler = SafeRotatingFileHandler(
        "logs/app.log",
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding="utf-8",
        errors="replace",
    )
    file_handler.setLevel(numeric_level)

    console_handler = logging.StreamHandler(sys.stdout)
    if hasattr(console_handler.stream, "reconfigure"):
        console_handler.stream.reconfigure(encoding="utf-8", errors="replace")
    console_handler.setLevel(numeric_level)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    basic_config_kwargs: dict = {
        "level": numeric_level,
        "format": log_format,
        "handlers": [file_handler, console_handler],
    }
    if force:
        basic_config_kwargs["force"] = True

    logging.basicConfig(**basic_config_kwargs)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    return level_name


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado para el módulo especificado."""
    return logging.getLogger(name)
