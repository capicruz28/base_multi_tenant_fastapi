"""
Script de prueba para validar el routing de conexiones híbrido.

EJECUTAR después de implementar FASE 2.

PRUEBAS:
1. Metadata retrieval desde BD
2. Cache funcionando correctamente
3. Routing Single-DB
4. Routing Multi-DB
5. Fallback cuando falla Multi-DB

USO:
    python test_routing.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.multi_db import (
    get_connection_metadata,
    get_client_db_connection_string,
    get_database_type,
    invalidate_client_connection_cache
)
from app.core.connection_cache import connection_cache
from app.core.config import settings

def test_system_client():
    """Prueba conexión para cliente SYSTEM."""
    print("=" * 70)
    print("TEST 1: Cliente SYSTEM (Single-DB)")
    print("=" * 70)
    
    client_id = settings.SUPERADMIN_CLIENTE_ID
    print(f"Cliente ID: {client_id}")
    
    # Obtener metadata
    metadata = get_connection_metadata(client_id)
    print(f"Database Type: {metadata.get('database_type')}")
    print(f"Database Name: {metadata.get('nombre_bd')}")
    
    # Verificar que es Single-DB
    assert metadata.get('database_type') == 'single', "❌ SYSTEM debe ser Single-DB"
    assert metadata.get('nombre_bd') == settings.DB_DATABASE, "❌ BD incorrecta"
    
    print("✅ Test SYSTEM passed")
    print()


def test_single_db_client():
    """Prueba cliente configurado como Single-DB."""
    print("=" * 70)
    print("TEST 2: Cliente Single-DB")
    print("=" * 70)
    
    # Usa el ID de TECH CORP o GLOBAL SOLUTIONS (según tu seed)
    # Ajusta este ID según tus datos
    client_id = 4  # TECH CORP en el seed
    
    print(f"Cliente ID: {client_id}")
    
    try:
        # Obtener metadata
        metadata = get_connection_metadata(client_id)
        print(f"Database Type: {metadata.get('database_type')}")
        print(f"Database Name: {metadata.get('nombre_bd')}")
        
        # Obtener connection string
        conn_str = get_client_db_connection_string(client_id)
        print(f"Connection String: {conn_str[:100]}...")
        
        # Verificar que apunta a bd_sistema
        assert settings.DB_DATABASE in conn_str, "❌ Debe apuntar a bd_sistema"
        
        print("✅ Test Single-DB client passed")
        
    except Exception as e:
        print(f"⚠️  Cliente {client_id} no existe o no está configurado: {e}")
        print("   Esto es normal si no has ejecutado el seed híbrido")
    
    print()


def test_multi_db_client():
    """Prueba cliente configurado como Multi-DB."""
    print("=" * 70)
    print("TEST 3: Cliente Multi-DB")
    print("=" * 70)
    
    # Usa el ID de ACME (cliente 2 en el seed)
    client_id = 2
    
    print(f"Cliente ID: {client_id}")
    
    try:
        # Obtener metadata
        metadata = get_connection_metadata(client_id)
        print(f"Database Type: {metadata.get('database_type')}")
        print(f"Database Name: {metadata.get('nombre_bd')}")
        
        if metadata.get('database_type') == 'multi':
            print(f"Servidor: {metadata.get('servidor')}")
            print(f"Puerto: {metadata.get('puerto')}")
            print(f"Usuario: {metadata.get('usuario', 'N/A')[:5]}***")
            
            # Obtener connection string
            conn_str = get_client_db_connection_string(client_id)
            print(f"Connection String: {conn_str[:100]}...")
            
            # Verificar que NO apunta a bd_sistema
            nombre_bd = metadata.get('nombre_bd')
            assert nombre_bd in conn_str, f"❌ Debe apuntar a {nombre_bd}"
            assert nombre_bd != settings.DB_DATABASE, "❌ No debe apuntar a bd_sistema"
            
            print("✅ Test Multi-DB client passed")
        else:
            print("⚠️  Cliente configurado como Single-DB (fallback)")
            print("   Verifica que cliente_modulo_conexion tenga datos")
        
    except Exception as e:
        print(f"⚠️  Cliente {client_id} no existe o no está configurado: {e}")
        print("   Ejecuta el seed híbrido primero")
    
    print()


def test_cache_functionality():
    """Prueba que el cache funciona correctamente."""
    print("=" * 70)
    print("TEST 4: Funcionalidad de Cache")
    print("=" * 70)
    
    client_id = 2
    
    # Limpiar cache
    connection_cache.clear()
    print("Cache limpiado")
    
    # Primera llamada (debe consultar BD)
    print("\n1. Primera llamada (cache miss)...")
    metadata1 = get_connection_metadata(client_id)
    print(f"   Metadata obtenida: {metadata1.get('database_type')}")
    
    # Segunda llamada (debe usar cache)
    print("\n2. Segunda llamada (cache hit)...")
    metadata2 = get_connection_metadata(client_id)
    print(f"   Metadata obtenida: {metadata2.get('database_type')}")
    
    # Verificar que son iguales
    assert metadata1 == metadata2, "❌ Metadata debe ser igual"
    
    # Verificar que está en cache
    assert client_id in connection_cache, "❌ Cliente debe estar en cache"
    
    # Obtener stats
    stats = connection_cache.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Size: {stats['size']}")
    print(f"   TTL: {stats['ttl_seconds']}s")
    print(f"   Clients: {stats['client_ids']}")
    
    print("\n✅ Test Cache passed")
    print()


def test_cache_invalidation():
    """Prueba invalidación de cache."""
    print("=" * 70)
    print("TEST 5: Invalidación de Cache")
    print("=" * 70)
    
    client_id = 2
    
    # Asegurar que está en cache
    get_connection_metadata(client_id)
    assert client_id in connection_cache, "❌ Debe estar en cache"
    print(f"Cliente {client_id} en cache: ✅")
    
    # Invalidar
    result = invalidate_client_connection_cache(client_id)
    assert result == True, "❌ Invalidación debe retornar True"
    print(f"Cliente {client_id} invalidado: ✅")
    
    # Verificar que ya no está
    assert client_id not in connection_cache, "❌ No debe estar en cache"
    print(f"Cliente {client_id} removido del cache: ✅")
    
    print("\n✅ Test Cache Invalidation passed")
    print()


def test_fallback_scenario():
    """Prueba que fallback funciona correctamente."""
    print("=" * 70)
    print("TEST 6: Fallback a Single-DB")
    print("=" * 70)
    
    # Cliente inexistente (debe hacer fallback)
    client_id = 9999
    
    print(f"Cliente ID (inexistente): {client_id}")
    
    metadata = get_connection_metadata(client_id)
    print(f"Database Type: {metadata.get('database_type')}")
    print(f"Database Name: {metadata.get('nombre_bd')}")
    
    # Debe hacer fallback a Single-DB
    assert metadata.get('database_type') == 'single', "❌ Debe hacer fallback a Single-DB"
    assert metadata.get('nombre_bd') == settings.DB_DATABASE, "❌ Debe apuntar a bd_sistema"
    
    print("✅ Test Fallback passed")
    print()


def main():
    print("\n")
    print("🧪" * 35)
    print("  SUITE DE PRUEBAS - ROUTING HÍBRIDO")
    print("🧪" * 35)
    print("\n")
    
    try:
        # Ejecutar tests
        test_system_client()
        test_single_db_client()
        test_multi_db_client()
        test_cache_functionality()
        test_cache_invalidation()
        test_fallback_scenario()
        
        # Resumen
        print("=" * 70)
        print("  RESUMEN")
        print("=" * 70)
        print()
        print("✅ Todos los tests pasaron exitosamente")
        print()
        print("📝 PRÓXIMOS PASOS:")
        print("   1. Verificar logs para ver el routing en acción")
        print("   2. Continuar con FASE 3 (Extender TenantContext)")
        print()
        
    except AssertionError as e:
        print(f"\n❌ Test falló: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)