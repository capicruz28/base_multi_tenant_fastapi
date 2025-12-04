"""
Script temporal para generar credenciales encriptadas con Fernet.

Este script genera las credenciales encriptadas correctamente para
actualizar en la tabla cliente_conexion.

USO:
    python scripts/generate_encrypted_credentials.py
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security.encryption import encrypt_credential
from app.core.config import settings

def main():
    """Genera credenciales encriptadas para usuario y password."""
    
    # Verificar que ENCRYPTION_KEY esté configurada
    if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
        print("ERROR: ENCRYPTION_KEY no esta configurada en .env")
        print("   Por favor, configura ENCRYPTION_KEY en tu archivo .env")
        return
    
    # Credenciales a encriptar
    usuario = "soporte"
    password = "rrhh03"
    
    try:
        print("Generando credenciales encriptadas...")
        print(f"   Usuario: {usuario}")
        print(f"   Password: {password}")
        print()
        
        # Encriptar credenciales
        usuario_encriptado = encrypt_credential(usuario)
        password_encriptado = encrypt_credential(password)
        
        print("Credenciales encriptadas correctamente:")
        print()
        print("=" * 80)
        print("SQL para actualizar en cliente_conexion:")
        print("=" * 80)
        print()
        print(f"UPDATE cliente_conexion")
        print(f"SET usuario_encriptado = '{usuario_encriptado}',")
        print(f"    password_encriptado = '{password_encriptado}'")
        print(f"WHERE cliente_id = 'ee7bfc14-995f-4209-b4b9-99c307534a43'")
        print(f"  AND es_conexion_principal = 1")
        print(f"  AND es_activo = 1;")
        print()
        print("=" * 80)
        print("Valores individuales:")
        print("=" * 80)
        print(f"usuario_encriptado: {usuario_encriptado}")
        print(f"password_encriptado: {password_encriptado}")
        print()
        print("=" * 80)
        print("IMPORTANTE:")
        print("   1. Copia los valores encriptados")
        print("   2. Ejecuta el SQL en tu base de datos")
        print("   3. Asegurate de que ENCRYPTION_KEY en .env sea la misma")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR al encriptar credenciales: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

