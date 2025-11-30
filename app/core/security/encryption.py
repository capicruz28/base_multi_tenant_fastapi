# app/core/encryption.py
"""
Sistema de encriptación/desencriptación de credenciales para arquitectura híbrida.

SEGURIDAD CRÍTICA:
- Usa Fernet (AES-128 en modo CBC con HMAC para autenticidad)
- La clave DEBE ser de 32 bytes URL-safe base64-encoded
- NUNCA commitear ENCRYPTION_KEY al repositorio
- Rotar la clave periódicamente (implementar rotación en producción)

USO:
    from app.core.encryption import encrypt_credential, decrypt_credential
    
    encrypted = encrypt_credential("mi_password")
    decrypted = decrypt_credential(encrypted)
"""

import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
import base64
import os

from app.core.config import settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Gestor centralizado de encriptación/desencriptación.
    Singleton para evitar múltiples instancias de Fernet.
    """
    
    _instance: Optional['EncryptionManager'] = None
    _fernet: Optional[Fernet] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa Fernet con la clave de configuración.
        
        IMPORTANTE: Si ENCRYPTION_KEY no está configurada, lanza error
        para prevenir operaciones sin encriptación.
        """
        if self._fernet is None:
            if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
                raise ValueError(
                    "ENCRYPTION_KEY no está configurada en .env. "
                    "Ejecuta generate_encryption_key() para crear una."
                )
            
            try:
                # Validar que la clave sea válida para Fernet
                key_bytes = settings.ENCRYPTION_KEY.encode('utf-8')
                self._fernet = Fernet(key_bytes)
                logger.info("EncryptionManager inicializado correctamente")
            except Exception as e:
                logger.critical(f"Error al inicializar Fernet: {e}")
                raise ValueError(
                    f"ENCRYPTION_KEY inválida. Debe ser base64 de 32 bytes. Error: {e}"
                )
    
    @property
    def fernet(self) -> Fernet:
        """Retorna la instancia de Fernet."""
        if self._fernet is None:
            raise RuntimeError("EncryptionManager no inicializado")
        return self._fernet


# ============================================
# FUNCIONES PÚBLICAS
# ============================================

def encrypt_credential(plain_text: str) -> str:
    """
    Encripta una credencial (usuario, password, API key, etc.).
    
    Args:
        plain_text: Texto en claro a encriptar
    
    Returns:
        String encriptado en base64 (safe para almacenar en BD)
    
    Raises:
        ServiceError: Si falla la encriptación
    
    Ejemplo:
        >>> encrypted = encrypt_credential("my_password123")
        >>> print(encrypted)
        'gAAAAABl...' (string largo en base64)
    """
    if not plain_text:
        raise ValueError("No se puede encriptar un string vacío")
    
    try:
        manager = EncryptionManager()
        encrypted_bytes = manager.fernet.encrypt(plain_text.encode('utf-8'))
        encrypted_str = encrypted_bytes.decode('utf-8')
        
        logger.debug(f"Credencial encriptada exitosamente (longitud: {len(encrypted_str)})")
        return encrypted_str
        
    except Exception as e:
        logger.error(f"Error al encriptar credencial: {e}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail="Error al encriptar credencial",
            internal_code="ENCRYPTION_ERROR"
        )


def decrypt_credential(encrypted_text: str) -> str:
    """
    Desencripta una credencial previamente encriptada.
    
    Args:
        encrypted_text: String encriptado (output de encrypt_credential)
    
    Returns:
        Texto original en claro
    
    Raises:
        ServiceError: Si falla la desencriptación o el token es inválido
    
    Ejemplo:
        >>> decrypted = decrypt_credential('gAAAAABl...')
        >>> print(decrypted)
        'my_password123'
    """
    if not encrypted_text:
        raise ValueError("No se puede desencriptar un string vacío")
    
    try:
        manager = EncryptionManager()
        decrypted_bytes = manager.fernet.decrypt(encrypted_text.encode('utf-8'))
        decrypted_str = decrypted_bytes.decode('utf-8')
        
        logger.debug("Credencial desencriptada exitosamente")
        return decrypted_str
        
    except InvalidToken:
        logger.error("Token de encriptación inválido. Posibles causas: clave incorrecta o datos corruptos")
        raise ServiceError(
            status_code=500,
            detail="Credencial corrupta o clave de encriptación incorrecta",
            internal_code="DECRYPTION_INVALID_TOKEN"
        )
    except Exception as e:
        logger.error(f"Error al desencriptar credencial: {e}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail="Error al desencriptar credencial",
            internal_code="DECRYPTION_ERROR"
        )


def generate_encryption_key() -> str:
    """
    Genera una nueva clave de encriptación válida para Fernet.
    
    IMPORTANTE: Ejecutar UNA SOLA VEZ durante setup inicial.
    Guardar el resultado en .env como ENCRYPTION_KEY.
    
    Returns:
        String base64 de 32 bytes (URL-safe)
    
    Ejemplo:
        >>> key = generate_encryption_key()
        >>> print(f"ENCRYPTION_KEY={key}")
        ENCRYPTION_KEY=xQzF8j9K...
    """
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')
    
    logger.info("Nueva clave de encriptación generada")
    logger.warning("CRÍTICO: Guarda esta clave de forma segura y NO la commitees a Git")
    
    return key_str


def validate_encryption_key(key: str) -> bool:
    """
    Valida si una clave es válida para Fernet.
    
    Args:
        key: Clave a validar
    
    Returns:
        True si es válida, False si no
    
    Ejemplo:
        >>> is_valid = validate_encryption_key("mi_clave_invalida")
        >>> print(is_valid)
        False
    """
    try:
        Fernet(key.encode('utf-8'))
        return True
    except Exception:
        return False


def rotate_credentials(old_encrypted: str, old_key: str, new_key: str) -> str:
    """
    Rota credenciales de una clave vieja a una nueva.
    
    USAR SOLO DURANTE ROTACIÓN DE CLAVES EN PRODUCCIÓN.
    
    Args:
        old_encrypted: Credencial encriptada con clave vieja
        old_key: Clave de encriptación vieja
        new_key: Clave de encriptación nueva
    
    Returns:
        Credencial re-encriptada con la nueva clave
    
    Proceso:
        1. Desencriptar con clave vieja
        2. Encriptar con clave nueva
        3. Retornar nuevo valor encriptado
    
    Ejemplo:
        >>> new_encrypted = rotate_credentials(
        ...     old_encrypted="gAAAAABl...",
        ...     old_key="OLD_KEY_BASE64",
        ...     new_key="NEW_KEY_BASE64"
        ... )
    """
    try:
        # Desencriptar con clave vieja
        old_fernet = Fernet(old_key.encode('utf-8'))
        plain_text = old_fernet.decrypt(old_encrypted.encode('utf-8')).decode('utf-8')
        
        # Encriptar con clave nueva
        new_fernet = Fernet(new_key.encode('utf-8'))
        new_encrypted = new_fernet.encrypt(plain_text.encode('utf-8')).decode('utf-8')
        
        logger.info("Credencial rotada exitosamente")
        return new_encrypted
        
    except Exception as e:
        logger.error(f"Error al rotar credencial: {e}", exc_info=True)
        raise ServiceError(
            status_code=500,
            detail="Error al rotar credencial",
            internal_code="ROTATION_ERROR"
        )


# ============================================
# UTILIDADES PARA TESTING
# ============================================

def test_encryption_roundtrip(test_value: str = "test_password_123") -> bool:
    """
    Prueba de round-trip para validar que encriptación/desencriptación funciona.
    
    Args:
        test_value: Valor de prueba
    
    Returns:
        True si el round-trip es exitoso, False si falla
    
    Ejemplo:
        >>> success = test_encryption_roundtrip()
        >>> print(f"Encriptación funcional: {success}")
        Encriptación funcional: True
    """
    try:
        encrypted = encrypt_credential(test_value)
        decrypted = decrypt_credential(encrypted)
        
        success = (decrypted == test_value)
        
        if success:
            logger.info("Test de encriptación round-trip exitoso")
        else:
            logger.error(f"Test de encriptación falló. Original: '{test_value}', Recuperado: '{decrypted}'")
        
        return success
        
    except Exception as e:
        logger.error(f"Test de encriptación falló con excepción: {e}")
        return False


# ============================================
# INICIALIZACIÓN AL IMPORTAR
# ============================================

# Validar que la clave existe al importar el módulo
try:
    if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
        # Intentar inicializar para validar la clave
        _test_manager = EncryptionManager()
        logger.info("Módulo de encriptación cargado correctamente")
    else:
        logger.warning(
            "ENCRYPTION_KEY no configurada. "
            "El módulo se cargó pero las funciones fallarán hasta configurar la clave."
        )
except Exception as e:
    logger.error(f"Error al inicializar módulo de encriptación: {e}")
    # No lanzar excepción aquí para permitir que la app inicie
    # Las funciones fallarán cuando se intenten usar