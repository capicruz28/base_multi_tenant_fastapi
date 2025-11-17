"""
Script para generar la clave de encriptación inicial.

EJECUTAR UNA SOLA VEZ durante setup del proyecto.

USO:
    python generate_encryption_key.py
    
SALIDA:
    Imprime la clave que debes copiar a tu .env
"""

from cryptography.fernet import Fernet

def main():
    print("=" * 70)
    print("  GENERADOR DE CLAVE DE ENCRIPTACIÓN")
    print("=" * 70)
    print()
    
    # Generar clave
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')
    
    print("✅ Clave generada exitosamente:")
    print()
    print(f"ENCRYPTION_KEY={key_str}")
    print()
    print("=" * 70)
    print("  INSTRUCCIONES:")
    print("=" * 70)
    print()
    print("1. Copia la línea completa de arriba")
    print("2. Pégala en tu archivo .env")
    print("3. NUNCA commitees esta clave a Git")
    print("4. Guarda una copia segura en tu gestor de passwords")
    print("5. Reinicia tu aplicación")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Si pierdes esta clave, NO podrás desencriptar credenciales")
    print("   - Deberás re-encriptar todas las credenciales con una nueva clave")
    print()
    
    # Validar que la clave funciona
    print("🧪 Validando clave generada...")
    try:
        fernet = Fernet(key)
        test_msg = b"test_encryption"
        encrypted = fernet.encrypt(test_msg)
        decrypted = fernet.decrypt(encrypted)
        
        if decrypted == test_msg:
            print("✅ Validación exitosa: La clave funciona correctamente")
        else:
            print("❌ Error: Validación falló")
            return
    except Exception as e:
        print(f"❌ Error al validar clave: {e}")
        return
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()