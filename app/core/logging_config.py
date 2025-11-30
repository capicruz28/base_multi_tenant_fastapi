import logging
import sys
from logging.handlers import RotatingFileHandler
import os
import io

def setup_logging():
    """Configura el logging global de la aplicación con soporte UTF-8"""
    # Crear el directorio logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configurar stdout para UTF-8 en Windows
    if sys.platform == 'win32':
        # Forzar UTF-8 en stdout/stderr para Windows
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    
    # Handler para archivo rotativo con UTF-8
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
        encoding='utf-8',  # ✅ UTF-8 para soportar emojis y caracteres Unicode
        errors='replace'  # Reemplazar caracteres problemáticos en lugar de fallar
    )
    
    # Handler para consola con UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    # Configurar el handler de consola para usar UTF-8
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8', errors='replace')

    # Configuración básica del logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            console_handler
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado

    Args:
        name: Nombre del módulo (generalmente __name__)

    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)