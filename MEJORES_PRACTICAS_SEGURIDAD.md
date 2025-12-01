# Mejores Prácticas de Seguridad

## 📋 Guía para Desarrolladores

Este documento describe las mejores prácticas de seguridad que deben seguirse al desarrollar en este proyecto multi-tenant.

---

## 🔒 1. Construcción de Queries SQL

### ❌ **NUNCA HAGAS ESTO:**

```python
# ❌ VULNERABLE: Concatenación directa de valores
user_input = request.json.get("nombre")
query = f"SELECT * FROM usuarios WHERE nombre = '{user_input}'"
```

### ✅ **SIEMPRE USA PARÁMETROS:**

```python
# ✅ SEGURO: Usar parámetros
user_input = request.json.get("nombre")
query = "SELECT * FROM usuarios WHERE nombre = ?"
results = execute_query(query, (user_input,))
```

### ✅ **USA SafeQueryBuilder PARA QUERIES DINÁMICAS:**

```python
from app.infrastructure.database.query_builder import SafeQueryBuilder

# Construir WHERE clause de forma segura
filters = {"nombre": "Juan", "edad": 25}
where_clause, params = SafeQueryBuilder.build_where_clause(filters)
query = f"SELECT * FROM usuarios WHERE {where_clause}"
results = execute_query(query, params)
```

### ✅ **VALIDACIÓN DE CAMPOS EN ORDER BY:**

```python
# ✅ SEGURO: Usar whitelist para ORDER BY
valid_fields = ["nombre", "edad", "fecha_creacion"]
order_by = SafeQueryBuilder.build_order_by(
    ["nombre", "edad DESC"],
    valid_fields=valid_fields
)
query = f"SELECT * FROM usuarios ORDER BY {order_by}"
```

---

## 🏢 2. Aislamiento Multi-Tenant

### ✅ **SIEMPRE FILTRA POR cliente_id:**

```python
# ✅ CORRECTO: Usar BaseRepository que filtra automáticamente
from app.infrastructure.database.repositories.base_repository import BaseRepository

class UsuarioRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            table_name="usuario",
            id_column="usuario_id",
            tenant_column="cliente_id"  # ✅ Filtra automáticamente
        )

# Al usar find_all, automáticamente filtra por cliente_id del contexto
usuarios = repository.find_all()
```

### ✅ **VALIDAR TENANT EN ENDPOINTS:**

```python
from app.api.deps import get_current_active_user
from fastapi import Depends

@router.get("/usuarios/")
async def listar_usuarios(
    current_user = Depends(get_current_active_user)
):
    # ✅ current_user ya tiene validación de tenant
    # No necesitas validar manualmente
    usuarios = await UsuarioService.listar_usuarios()
    return usuarios
```

### ❌ **NUNCA HAGAS QUERIES SIN FILTRO DE TENANT:**

```python
# ❌ PELIGROSO: Query sin filtro de tenant
query = "SELECT * FROM usuarios WHERE nombre = ?"
results = execute_query(query, (nombre,))
# ⚠️ Esto puede retornar usuarios de otros tenants!
```

---

## 🔐 3. Validación de Headers y Request

### ✅ **EN PRODUCCIÓN, SOLO CONFÍA EN HOST:**

El middleware ya maneja esto automáticamente:
- **Producción:** Solo usa header `Host` (no falsificable)
- **Desarrollo:** Permite fallback a `Origin`/`Referer` (con validación)

### ❌ **NUNCA CONFÍES EN ORIGIN/REFERER EN PRODUCCIÓN:**

```python
# ❌ NUNCA HAGAS ESTO EN PRODUCCIÓN
origin = request.headers.get("origin")
tenant = extract_tenant_from_origin(origin)  # ⚠️ Falsificable!
```

---

## 👤 4. Manejo de SuperAdmin

### ✅ **VALIDAR EXPLÍCITAMENTE SI ES SUPERADMIN:**

```python
# ✅ CORRECTO: Validar flag is_super_admin
if current_user.is_super_admin:
    # Permitir acceso cross-tenant
    pass
else:
    # Validar que token_cliente_id == request_cliente_id
    if token_cliente_id != request_cliente_id:
        raise HTTPException(403, "Acceso denegado")
```

### ✅ **AUDITAR ACCESOS CROSS-TENANT:**

```python
from app.modules.superadmin.application.services.audit_service import AuditService

# Registrar acceso cross-tenant
if is_super_admin and token_cliente_id != request_cliente_id:
    await AuditService.registrar_tenant_access(
        usuario_id=current_user.usuario_id,
        token_cliente_id=token_cliente_id,
        request_cliente_id=request_cliente_id,
        tipo_acceso="superadmin_cross_tenant",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
```

---

## 🛡️ 5. Prevención de SQL Injection

### ✅ **CHECKLIST ANTES DE ESCRIBIR QUERIES:**

- [ ] ¿Uso parámetros `?` para todos los valores?
- [ ] ¿Validé nombres de campos contra whitelist?
- [ ] ¿Uso `SafeQueryBuilder` para queries dinámicas?
- [ ] ¿Evité concatenación directa de strings en queries?
- [ ] ¿Validé que ORDER BY use campos permitidos?

### ✅ **EJEMPLO COMPLETO SEGURO:**

```python
from app.infrastructure.database.query_builder import SafeQueryBuilder
from app.infrastructure.database.queries import execute_query

def buscar_usuarios(filtros: dict, ordenar_por: str = "nombre"):
    # 1. Construir WHERE clause de forma segura
    where_clause, params = SafeQueryBuilder.build_where_clause(filtros)
    
    # 2. Validar ORDER BY contra whitelist
    valid_order_fields = ["nombre", "edad", "fecha_creacion"]
    order_by = SafeQueryBuilder.build_order_by(
        [ordenar_por],
        valid_fields=valid_order_fields
    )
    
    # 3. Construir query final
    query = f"""
        SELECT * FROM usuarios
        WHERE {where_clause}
        ORDER BY {order_by}
    """
    
    # 4. Ejecutar con parámetros
    return execute_query(query, params)
```

---

## 📝 6. Logging y Auditoría

### ✅ **REGISTRAR EVENTOS DE SEGURIDAD:**

```python
from app.modules.superadmin.application.services.audit_service import AuditService

# Registrar intento de acceso no autorizado
await AuditService.registrar_auth_event(
    cliente_id=cliente_id,
    usuario_id=usuario_id,
    evento="access_denied",
    exito=False,
    descripcion="Intento de acceso a tenant no autorizado",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

### ✅ **LOGS INFORMATIVOS:**

```python
import logging

logger = logging.getLogger(__name__)

# ✅ BUEN LOG: Incluye contexto de seguridad
logger.warning(
    f"[SECURITY] Acceso denegado: usuario '{username}' "
    f"(cliente {token_cliente_id}) intentó acceder a cliente {request_cliente_id}"
)

# ❌ MAL LOG: No incluye contexto
logger.warning("Acceso denegado")
```

---

## 🧪 7. Testing de Seguridad

### ✅ **ESCRIBIR TESTS PARA:**

1. **Prevención de SQL Injection:**
   ```python
   def test_query_builder_rejects_dangerous_input():
       # Test que SafeQueryBuilder rechaza campos peligrosos
   ```

2. **Aislamiento de Tenant:**
   ```python
   def test_user_cannot_access_other_tenant():
       # Test que usuario regular no puede acceder a otro tenant
   ```

3. **Prevención de Tenant Spoofing:**
   ```python
   def test_production_rejects_fake_origin():
       # Test que producción rechaza Origin falsificado
   ```

---

## 📚 8. Recursos Adicionales

### Documentación:
- `ANALISIS_SEGURIDAD_EVALUACION_TERCERO.md` - Análisis detallado
- `SOLUCIONES_IMPLEMENTADAS_SEGURIDAD.md` - Soluciones implementadas
- `RESUMEN_EVALUACION_SEGURIDAD.md` - Resumen ejecutivo

### Código de Referencia:
- `app/infrastructure/database/query_builder.py` - SafeQueryBuilder
- `app/core/tenant/middleware.py` - Prevención de Tenant Spoofing
- `app/api/deps.py` - Validación de tenant

### Tests:
- `tests/security/test_tenant_spoofing_prevention.py` - Tests de seguridad

---

## ⚠️ 9. Red Flags - Señales de Alerta

Si ves alguno de estos patrones, **DETENTE Y REVISA**:

1. ❌ `f"SELECT * FROM tabla WHERE campo = '{variable}'"`
2. ❌ `query += f" AND campo = {valor}"`
3. ❌ `execute_query(f"SELECT * FROM {tabla}")` (tabla dinámica sin validar)
4. ❌ `ORDER BY {user_input}` (sin whitelist)
5. ❌ `tenant = request.headers.get("origin")` (en producción)
6. ❌ Query sin filtro de `cliente_id`

---

## ✅ 10. Checklist de Code Review

Antes de hacer merge, verifica:

- [ ] Todas las queries usan parámetros `?`
- [ ] Queries dinámicas usan `SafeQueryBuilder`
- [ ] ORDER BY valida contra whitelist
- [ ] No hay concatenación de strings en queries
- [ ] Validación de tenant en endpoints sensibles
- [ ] Logs incluyen contexto de seguridad
- [ ] Tests de seguridad escritos y pasando
- [ ] No se confía en headers falsificables en producción

---

**Última actualización:** $(date)  
**Versión:** 1.0


