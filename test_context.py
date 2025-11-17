"""
Script de prueba para validar el TenantContext híbrido.

EJECUTAR después de implementar FASE 3.

PRUEBAS:
1. Creación de contexto con campos híbridos
2. Métodos helper (is_single_db, is_multi_db, etc.)
3. Conversión a dict
4. Representación string
5. Validaciones

USO:
    python test_context.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.tenant_context import (
    TenantContext,
    set_tenant_context,
    reset_tenant_context,
    get_current_client_id,
    get_tenant_context,
    try_get_current_client_id,
    try_get_tenant_context,
    get_database_type,
    get_database_name
)


def test_tenant_context_creation():
    """Prueba creación de TenantContext."""
    print("=" * 70)
    print("TEST 1: Creación de TenantContext")
    print("=" * 70)
    
    # Contexto Single-DB
    ctx_single = TenantContext(
        client_id=1,
        subdominio="platform",
        codigo_cliente="SYSTEM",
        database_type="single",
        nombre_bd="bd_sistema"
    )
    
    print(f"Contexto Single-DB creado: {ctx_single}")
    assert ctx_single.client_id == 1
    assert ctx_single.database_type == "single"
    assert ctx_single.nombre_bd == "bd_sistema"
    print("✅ Contexto Single-DB OK")
    
    # Contexto Multi-DB
    ctx_multi = TenantContext(
        client_id=2,
        subdominio="acme",
        codigo_cliente="ACME001",
        database_type="multi",
        nombre_bd="bd_cliente_acme",
        servidor="localhost",
        puerto=1433
    )
    
    print(f"Contexto Multi-DB creado: {ctx_multi}")
    assert ctx_multi.client_id == 2
    assert ctx_multi.database_type == "multi"
    assert ctx_multi.nombre_bd == "bd_cliente_acme"
    assert ctx_multi.servidor == "localhost"
    print("✅ Contexto Multi-DB OK")
    
    print()


def test_context_methods():
    """Prueba métodos del contexto."""
    print("=" * 70)
    print("TEST 2: Métodos de TenantContext")
    print("=" * 70)
    
    # Contexto Single-DB
    ctx_single = TenantContext(
        client_id=1,
        database_type="single",
        nombre_bd="bd_sistema"
    )
    
    assert ctx_single.is_single_db() == True
    assert ctx_single.is_multi_db() == False
    assert ctx_single.get_database_name() == "bd_sistema"
    print("✅ Métodos Single-DB OK")
    
    # Contexto Multi-DB
    ctx_multi = TenantContext(
        client_id=2,
        database_type="multi",
        nombre_bd="bd_cliente_acme"
    )
    
    assert ctx_multi.is_single_db() == False
    assert ctx_multi.is_multi_db() == True
    assert ctx_multi.get_database_name() == "bd_cliente_acme"
    print("✅ Métodos Multi-DB OK")
    
    print()


def test_context_to_dict():
    """Prueba conversión a dict."""
    print("=" * 70)
    print("TEST 3: Conversión a Dict")
    print("=" * 70)
    
    ctx = TenantContext(
        client_id=2,
        subdominio="acme",
        codigo_cliente="ACME001",
        database_type="multi",
        nombre_bd="bd_cliente_acme",
        servidor="localhost",
        puerto=1433,
        tipo_instalacion="cloud"
    )
    
    ctx_dict = ctx.to_dict()
    
    print(f"Dict: {ctx_dict}")
    
    assert ctx_dict["client_id"] == 2
    assert ctx_dict["database_type"] == "multi"
    assert ctx_dict["nombre_bd"] == "bd_cliente_acme"
    assert ctx_dict["servidor"] == "localhost"
    
    print("✅ Conversión a dict OK")
    print()


def test_context_setting_and_getting():
    """Prueba establecer y obtener contexto."""
    print("=" * 70)
    print("TEST 4: Set/Get de Contexto")
    print("=" * 70)
    
    # Verificar que no hay contexto al inicio
    client_id = try_get_current_client_id()
    assert client_id is None
    print("✅ Sin contexto inicial: OK")
    
    # Crear y establecer contexto
    ctx = TenantContext(
        client_id=2,
        subdominio="acme",
        codigo_cliente="ACME001",
        database_type="multi",
        nombre_bd="bd_cliente_acme"
    )
    
    tokens = set_tenant_context(ctx)
    print("Contexto establecido")
    
    try:
        # Obtener client_id
        retrieved_id = get_current_client_id()
        assert retrieved_id == 2
        print(f"✅ get_current_client_id() → {retrieved_id}")
        
        # Obtener contexto completo
        retrieved_ctx = get_tenant_context()
        assert retrieved_ctx.client_id == 2
        assert retrieved_ctx.database_type == "multi"
        assert retrieved_ctx.nombre_bd == "bd_cliente_acme"
        print(f"✅ get_tenant_context() → {retrieved_ctx}")
        
        # Obtener database_type
        db_type = get_database_type()
        assert db_type == "multi"
        print(f"✅ get_database_type() → {db_type}")
        
        # Obtener database_name
        db_name = get_database_name()
        assert db_name == "bd_cliente_acme"
        print(f"✅ get_database_name() → {db_name}")
        
    finally:
        # Limpiar contexto
        reset_tenant_context(tokens)
        print("Contexto limpiado")
    
    # Verificar que se limpió
    client_id = try_get_current_client_id()
    assert client_id is None
    print("✅ Contexto limpiado correctamente")
    
    print()


def test_context_without_setting():
    """Prueba que lanza error si no hay contexto."""
    print("=" * 70)
    print("TEST 5: Error sin Contexto")
    print("=" * 70)
    
    try:
        get_current_client_id()
        print("❌ ERROR: Debió lanzar RuntimeError")
        assert False
    except RuntimeError as e:
        print(f"✅ RuntimeError esperado: {e}")
    
    try:
        get_tenant_context()
        print("❌ ERROR: Debió lanzar RuntimeError")
        assert False
    except RuntimeError as e:
        print(f"✅ RuntimeError esperado: {e}")
    
    # try_* no debe lanzar error
    client_id = try_get_current_client_id()
    assert client_id is None
    print("✅ try_get_current_client_id() → None (sin error)")
    
    ctx = try_get_tenant_context()
    assert ctx is None
    print("✅ try_get_tenant_context() → None (sin error)")
    
    print()


def test_context_validation():
    """Prueba validaciones del contexto."""
    print("=" * 70)
    print("TEST 6: Validaciones")
    print("=" * 70)
    
    # client_id es obligatorio
    try:
        TenantContext(client_id=None)
        print("❌ ERROR: Debió lanzar ValueError")
        assert False
    except ValueError as e:
        print(f"✅ ValueError esperado para client_id=None: {e}")
    
    # Inferir nombre_bd de connection_metadata
    ctx = TenantContext(
        client_id=2,
        connection_metadata={"nombre_bd": "bd_inferida"}
    )
    assert ctx.nombre_bd == "bd_inferida"
    print("✅ Inferencia de nombre_bd desde metadata OK")
    
    print()


def main():
    print("\n")
    print("🧪" * 35)
    print("  SUITE DE PRUEBAS - TENANT CONTEXT HÍBRIDO")
    print("🧪" * 35)
    print("\n")
    
    try:
        # Ejecutar tests
        test_tenant_context_creation()
        test_context_methods()
        test_context_to_dict()
        test_context_setting_and_getting()
        test_context_without_setting()
        test_context_validation()
        
        # Resumen
        print("=" * 70)
        print("  RESUMEN")
        print("=" * 70)
        print()
        print("✅ Todos los tests pasaron exitosamente")
        print()
        print("📝 PRÓXIMOS PASOS:")
        print("   1. Probar middleware completo con requests reales")
        print("   2. Verificar que servicios reciben contexto correctamente")
        print("   3. Continuar con FASE 4 (Testing integrado)")
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