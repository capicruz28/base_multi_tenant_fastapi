"""
Script de prueba para validar el sistema de encriptación.

EJECUTAR después de configurar ENCRYPTION_KEY en .env

USO:
    python test_encryption.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from app.core.encryption import (
    encrypt_credential, 
    decrypt_credential, 
    test_encryption_roundtrip,
    validate_encryption_key
)
from app.core.config import settings

def main():
    print("=" * 70)
    print("  PRUEBA DEL SISTEMA DE ENCRIPTACIÓN")
    print("=" * 70)
    print()
    
    # 1. Validar que la clave existe
    print("1️⃣  Validando configuración...")
    if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
        print("❌ ERROR: ENCRYPTION_KEY no está configurada en .env")
        print("   Ejecuta generate_encryption_key.py primero")
        return
    
    print(f"✅ ENCRYPTION_KEY encontrada (longitud: {len(settings.ENCRYPTION_KEY)})")
    print()
    
    # 2. Validar que la clave es válida
    print("2️⃣  Validando formato de clave...")
    if validate_encryption_key(settings.ENCRYPTION_KEY):
        print("✅ Clave tiene formato válido")
    else:
        print("❌ ERROR: Clave inválida. Genera una nueva con generate_encryption_key.py")
        return
    print()
    
    # 3. Test de round-trip automático
    print("3️⃣  Ejecutando test de round-trip...")
    if test_encryption_roundtrip():
        print("✅ Round-trip exitoso")
    else:
        print("❌ ERROR: Round-trip falló")
        return
    print()
    
    # 4. Test con credenciales reales
    print("4️⃣  Probando con credenciales de ejemplo...")
    test_cases = [
        ("usuario_db", "Usuario de base de datos"),
        ("P@ssw0rd!123", "Password compleja"),
        ("API_KEY_xyz789", "API Key"),
        ("", "String vacío (debe fallar)")
    ]
    
    for test_value, description in test_cases:
        print(f"\n   Probando: {description}")
        print(f"   Valor: '{test_value}'")
        
        if not test_value:
            # Caso especial: debe fallar
            try:
                encrypt_credential(test_value)
                print("   ❌ ERROR: Debió fallar con string vacío")
            except ValueError as e:
                print(f"   ✅ Falló correctamente: {e}")
            continue
        
        try:
            # Encriptar
            encrypted = encrypt_credential(test_value)
            print(f"   Encriptado: {encrypted[:50]}... (truncado)")
            
            # Desencriptar
            decrypted = decrypt_credential(encrypted)
            
            # Validar
            if decrypted == test_value:
                print("   ✅ Encriptación/Desencriptación exitosa")
            else:
                print(f"   ❌ ERROR: Valor recuperado no coincide")
                print(f"      Original:  '{test_value}'")
                print(f"      Recuperado: '{decrypted}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print()
    print("✅ Sistema de encriptación funcionando correctamente")
    print()
    print("📝 PRÓXIMOS PASOS:")
    print("   1. Ejecutar script para encriptar credenciales en BD")
    print("   2. Continuar con FASE 2 (Routing de conexiones)")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()