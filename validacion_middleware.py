# Simular lo que hace el middleware
from app.core.multi_db import get_connection_metadata
from app.core.tenant_context import TenantContext, set_tenant_context

# Obtener metadata para ACME
metadata = get_connection_metadata(2)

# Crear contexto como lo haría el middleware
ctx = TenantContext(
    client_id=2,
    subdominio="acme",
    codigo_cliente="ACME001",
    database_type=metadata.get("database_type"),
    nombre_bd=metadata.get("nombre_bd"),
    connection_metadata=metadata
)

print(f"Contexto creado: {ctx}")
print(f"Dict completo: {ctx.to_dict()}")