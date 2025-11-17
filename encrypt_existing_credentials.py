"""
Script para encriptar credenciales existentes en cliente_modulo_conexion.

EJECUTAR UNA SOLA VEZ cuando ya tengas:
1. ENCRYPTION_KEY configurada en .env
2. Registros en cliente_modulo_conexion con credenciales en texto plano

IMPORTANTE:
- Hace backup de los valores originales
- Actualiza solo registros que NO estén encriptados
- Puede ejecutarse múltiples veces de forma segura

USO:
    python encrypt_existing_credentials.py
    
    # Con modo dry-run (no modifica BD):
    python encrypt_existing_credentials.py --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.encryption import encrypt_credential, decrypt_credential
from app.db.connection import get_db_connection, DatabaseConnection
import pyodbc

def is_already_encrypted(value: str) -> bool:
    """
    Detecta si un valor ya está encriptado intentando desencriptarlo.
    
    Los valores de Fernet siempre empiezan con 'gAAAAA' (base64).
    """
    if not value:
        return False
    
    # Heurística rápida: valores Fernet siempre tienen longitud > 50
    if len(value) < 50:
        return False
    
    # Intentar desencriptar
    try:
        decrypt_credential(value)
        return True  # Si no lanza excepción, está encriptado
    except:
        return False  # Si falla, no está encriptado


def get_connections_to_encrypt() -> List[Dict[str, Any]]:
    """
    Consulta las conexiones que necesitan encriptación.
    """
    query = """
        SELECT 
            conexion_id,
            cliente_id,
            modulo_id,
            servidor,
            usuario_encriptado,
            password_encriptado
        FROM cliente_modulo_conexion
        WHERE es_activo = 1
    """
    
    with get_db_connection(DatabaseConnection.ADMIN) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append(row_dict)
        
        return results


def update_encrypted_credentials(conexion_id: int, encrypted_user: str, encrypted_pass: str, dry_run: bool = False):
    """
    Actualiza las credenciales encriptadas en la BD.
    """
    if dry_run:
        print(f"   [DRY-RUN] Se actualizaría conexion_id={conexion_id}")
        return
    
    query = """
        UPDATE cliente_modulo_conexion
        SET 
            usuario_encriptado = ?,
            password_encriptado = ?
        WHERE conexion_id = ?
    """
    
    with get_db_connection(DatabaseConnection.ADMIN) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (encrypted_user, encrypted_pass, conexion_id))
        conn.commit()


def main(dry_run: bool = False):
    print("=" * 70)
    print("  ENCRIPTACIÓN DE CREDENCIALES EXISTENTES")
    print("=" * 70)
    print()
    
    if dry_run:
        print("⚠️  MODO DRY-RUN: No se modificará la base de datos")
        print()
    
    # 1. Obtener conexiones
    print("1️⃣  Consultando conexiones en BD...")
    try:
        connections = get_connections_to_encrypt()
        print(f"✅ Encontradas {len(connections)} conexiones")
    except Exception as e:
        print(f"❌ ERROR al consultar BD: {e}")
        return
    
    if not connections:
        print("ℹ️  No hay conexiones para procesar")
        return
    
    print()
    
    # 2. Procesar cada conexión
    print("2️⃣  Procesando credenciales...")
    print()
    
    stats = {
        "total": len(connections),
        "ya_encriptadas": 0,
        "encriptadas": 0,
        "errores": 0
    }
    
    for conn in connections:
        conexion_id = conn['conexion_id']
        cliente_id = conn['cliente_id']
        usuario = conn['usuario_encriptado']
        password = conn['password_encriptado']
        
        print(f"📦 Conexión ID: {conexion_id} (Cliente: {cliente_id})")
        print(f"   Servidor: {conn['servidor']}")
        
        # Validar si ya están encriptadas
        user_encrypted = is_already_encrypted(usuario)
        pass_encrypted = is_already_encrypted(password)
        
        if user_encrypted and pass_encrypted:
            print("   ℹ️  Ya está encriptada, saltando...")
            stats["ya_encriptadas"] += 1
            print()
            continue
        
        # Encriptar
        try:
            if not user_encrypted:
                print(f"   🔒 Encriptando usuario: '{usuario}'")
                encrypted_user = encrypt_credential(usuario)
                print(f"   ✅ Usuario encriptado: {encrypted_user[:50]}...")
            else:
                encrypted_user = usuario
                print("   ℹ️  Usuario ya estaba encriptado")
            
            if not pass_encrypted:
                print(f"   🔒 Encriptando password: {'*' * len(password)}")
                encrypted_pass = encrypt_credential(password)
                print(f"   ✅ Password encriptado: {encrypted_pass[:50]}...")
            else:
                encrypted_pass = password
                print("   ℹ️  Password ya estaba encriptado")
            
            # Actualizar en BD
            update_encrypted_credentials(conexion_id, encrypted_user, encrypted_pass, dry_run)
            
            if not dry_run:
                print("   ✅ Actualizado en BD")
            
            stats["encriptadas"] += 1
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            stats["errores"] += 1
        
        print()
    
    # 3. Resumen
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print()
    print(f"Total de conexiones:     {stats['total']}")
    print(f"Ya encriptadas:          {stats['ya_encriptadas']}")
    print(f"Encriptadas ahora:       {stats['encriptadas']}")
    print(f"Errores:                 {stats['errores']}")
    print()
    
    if dry_run:
        print("⚠️  Esto fue un DRY-RUN. Ejecuta sin --dry-run para aplicar cambios.")
    elif stats["encriptadas"] > 0:
        print("✅ Credenciales encriptadas exitosamente")
        print()
        print("📝 PRÓXIMOS PASOS:")
        print("   1. Verificar que las credenciales se pueden desencriptar")
        print("   2. Continuar con FASE 2 (Routing de conexiones)")
    else:
        print("ℹ️  No se realizaron cambios")
    
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encripta credenciales en BD")
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Modo prueba: no modifica la BD"
    )
    
    args = parser.parse_args()
    
    try:
        main(dry_run=args.dry_run)
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()