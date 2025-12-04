import logging
import sys
from logging.handlers import RotatingFileHandler
import os
import io

class SafeRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler que maneja errores de permisos en Windows.
    Si la rotación falla (archivo en uso), simplemente continúa sin rotar.
    """
    def doRollover(self):
        """
        Sobrescribe doRollover para manejar errores de permisos en Windows.
        """
        try:
            super().doRollover()
        except (OSError, PermissionError) as e:
            # En Windows, si el archivo está en uso, simplemente continuar sin rotar
            # Esto es mejor que fallar completamente
            if sys.platform == 'win32':
                # Intentar log el error solo si el stream está disponible
                # Si no está disponible, simplemente ignorar el error silenciosamente
                try:
                    if self.stream is not None:
                        self.stream.write(f"Warning: Could not rotate log file: {e}\n")
                        self.stream.flush()
                except (AttributeError, OSError):
                    # Si no se puede escribir, simplemente ignorar
                    pass
            else:
                # En otros sistemas, re-lanzar el error
                raise

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
    # ✅ Usar SafeRotatingFileHandler para manejar errores de permisos en Windows
    file_handler = SafeRotatingFileHandler(
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