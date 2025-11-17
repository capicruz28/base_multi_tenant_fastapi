from app.core.tenant_context import (
    TenantContext, 
    set_tenant_context, 
    reset_tenant_context,
    get_tenant_context
)

# Crear contexto Multi-DB
ctx = TenantContext(
    client_id=2,
    subdominio="acme",
    codigo_cliente="ACME001",
    database_type="multi",
    nombre_bd="bd_cliente_acme",
    servidor="localhost"
)

# Establecer
tokens = set_tenant_context(ctx)

try:
    # Obtener y verificar
    current = get_tenant_context()
    print(f"Cliente: {current.client_id}")
    print(f"DB Type: {current.database_type}")
    print(f"BD: {current.nombre_bd}")
    print(f"Es Multi-DB: {current.is_multi_db()}")
finally:
    # Limpiar
    reset_tenant_context(tokens)
