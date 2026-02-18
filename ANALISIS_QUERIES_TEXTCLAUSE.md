# 🔍 ANÁLISIS DETALLADO: Queries TextClause Sin Filtro Automático

## 📋 PROBLEMA IDENTIFICADO

Las queries que usan `text().bindparams()` (TextClause) **NO reciben filtro automático de tenant**, a diferencia de las queries SQLAlchemy Core que sí lo reciben automáticamente.

### Ubicación del Problema

**Archivo:** `app/infrastructure/database/queries_async.py:207-222`

```python
elif isinstance(query, TextClause):
    # ✅ Aceptar TextClause (resultado de text().bindparams())
    # ⚠️ PROBLEMA: NO se aplica apply_tenant_filter() aquí
    # Solo se ejecuta directamente sin validación automática
    async with _get_connection_context(connection_type, client_id) as session:
        try:
            result = await session.execute(query)
            # ...
```

**Comparación con SQLAlchemy Core:**

```python
if isinstance(query, (Select, Update, Delete, Insert)):
    # ✅ SÍ se aplica filtro automático
    query = apply_tenant_filter(query, client_id=client_id, table_name=table_name)
    # ...
```

---

## 🔴 EJEMPLOS DE QUERIES VULNERABLES

### Ejemplo 1: Query Correcta (Pero Depende del Desarrollador)

**Archivo:** `app/modules/auth/application/services/refresh_token_service.py:90`

```python
# ✅ CORRECTO: El desarrollador incluye cliente_id manualmente
existing = await execute_query(
    text(GET_REFRESH_TOKEN_BY_HASH).bindparams(
        token_hash=token_hash, 
        cliente_id=cliente_id  # ✅ Correcto: desarrollador incluye cliente_id
    )
)
```

**Query SQL:**
```sql
-- app/infrastructure/database/queries/auth/auth_queries.py:76-85
GET_REFRESH_TOKEN_BY_HASH = """
SELECT 
    token_id, usuario_id, token_hash, expires_at, 
    is_revoked, created_at, client_type, cliente_id
FROM refresh_tokens
WHERE token_hash = :token_hash
  AND cliente_id = :cliente_id  -- ✅ Correcto: incluye filtro de tenant
  AND is_revoked = 0
  AND expires_at > GETDATE();
"""
```

**Estado:** ✅ **SEGURO** - El desarrollador incluyó `cliente_id` manualmente

---

### Ejemplo 2: Query Potencialmente Vulnerable

**Archivo:** `app/modules/modulos/application/services/modulo_menu_service.py:187-199`

```python
# ⚠️ POTENCIALMENTE VULNERABLE: Query sobre modulo_menu (tabla global)
# Pero si se olvida cliente_id en el WHERE, podría acceder a menús de otros tenants
query_raw = text("""
    SELECT menu_id 
    FROM modulo_menu 
    WHERE modulo_id = :modulo_id 
      AND ruta = :ruta 
      AND cliente_id = :cliente_id  -- ✅ Correcto: incluye cliente_id
""").bindparams(
    modulo_id=str(modulo_id),
    ruta=ruta,
    cliente_id=str(cliente_id)  # ✅ Correcto: desarrollador incluye cliente_id
)
```

**Estado:** ✅ **SEGURO** - El desarrollador incluyó `cliente_id` manualmente

**PERO:** Si un desarrollador olvida incluir `cliente_id` en el bindparams, la query se ejecutaría sin filtro.

---

### Ejemplo 3: Query Realmente Vulnerable (Escenario Hipotético)

**Escenario:** Un desarrollador nuevo crea una query sin incluir `cliente_id`

```python
# ❌ VULNERABLE: Falta cliente_id en el WHERE y en bindparams
query = text("""
    SELECT usuario_id, nombre_usuario, correo
    FROM usuario
    WHERE es_activo = 1
      AND correo = :correo
""").bindparams(
    correo=correo  # ❌ Falta cliente_id
)

# Esta query se ejecutaría SIN filtro de tenant
results = await execute_query(query)
# ⚠️ PROBLEMA: Retornaría usuarios de TODOS los tenants
```

**Estado:** 🔴 **VULNERABLE** - No hay filtro automático que prevenga esto

---

## 🔍 ANÁLISIS DEL CÓDIGO ACTUAL

### Código Actual en `queries_async.py`

```python
# Línea 154-182: SQLAlchemy Core SÍ recibe filtro automático
if isinstance(query, (Select, Update, Delete, Insert)):
    # Obtener nombre de tabla para verificar si es global
    table_name = get_table_name_from_query(query)
    
    # ✅ Auditoría automática
    if not skip_tenant_validation and settings.ENABLE_QUERY_TENANT_VALIDATION:
        QueryAuditor.validate_tenant_filter(...)
    
    # ✅ Aplicar filtro automático
    if not skip_tenant_validation:
        query = apply_tenant_filter(query, client_id=client_id, table_name=table_name)

# Línea 207-222: TextClause NO recibe filtro automático
elif isinstance(query, TextClause):
    # ⚠️ PROBLEMA: Solo ejecuta, NO aplica filtro automático
    # Solo valida (si está habilitado) pero NO aplica
    async with _get_connection_context(connection_type, client_id) as session:
        result = await session.execute(query)
        # ...
```

**Problema:** `TextClause` solo se valida (si `ENABLE_QUERY_TENANT_VALIDATION=True`), pero **NO se aplica filtro automático**.

---

## 💡 SOLUCIONES PROPUESTAS

### Opción 1: Aplicar Filtro Automático a TextClause (RECOMENDADA)

**Ventajas:**
- ✅ Solución inmediata sin migrar código existente
- ✅ Protege automáticamente todas las queries TextClause
- ✅ Mantiene compatibilidad con código existente

**Desventajas:**
- ⚠️ Requiere parsear SQL string (complejo pero factible)
- ⚠️ Puede tener casos edge donde no funcione perfectamente

**Implementación:**

```python
# app/infrastructure/database/queries_async.py

elif isinstance(query, TextClause):
    # ✅ NUEVO: Aplicar filtro automático también a TextClause
    if not skip_tenant_validation:
        # Intentar aplicar filtro automático
        query = apply_tenant_filter_to_text_clause(query, client_id, table_name)
    
    # ✅ Auditoría automática (ya existe)
    if not skip_tenant_validation and settings.ENABLE_QUERY_TENANT_VALIDATION:
        try:
            table_name = extract_table_name_from_text_clause(query)
            QueryAuditor.validate_tenant_filter(
                query=query,
                table_name=table_name,
                client_id=client_id,
                skip_validation=False
            )
        except Exception as audit_error:
            logger.warning(f"[QUERY_AUDITOR] Error en auditoría TextClause: {audit_error}")
            if settings.ENVIRONMENT == "production":
                raise
    
    async with _get_connection_context(connection_type, client_id) as session:
        # ...
```

**Nueva función helper:**

```python
# app/infrastructure/database/query_helpers.py

def apply_tenant_filter_to_text_clause(
    query: TextClause,
    client_id: Optional[Union[int, UUID]] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id"
) -> TextClause:
    """
    Aplica filtro de tenant automáticamente a TextClause.
    
    Intenta parsear el SQL y agregar filtro de cliente_id si no existe.
    
    Args:
        query: TextClause a modificar
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        table_name: Nombre de la tabla (opcional, se infiere si es posible)
        tenant_column: Nombre de la columna de tenant (default: "cliente_id")
    
    Returns:
        TextClause modificado con filtro de tenant
    """
    from sqlalchemy import text
    import re
    
    # Obtener client_id si no se proporciona
    if client_id is None:
        client_id = try_get_current_client_id()
    
    if client_id is None:
        if not settings.ALLOW_TENANT_FILTER_BYPASS:
            raise ValidationError(
                detail="No se puede aplicar filtro de tenant: falta client_id y contexto",
                internal_code="MISSING_TENANT_CONTEXT"
            )
        return query
    
    # Convertir TextClause a string para análisis
    query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
    query_lower = query_str.lower()
    
    # Extraer nombre de tabla si no se proporciona
    if table_name is None:
        # Buscar patrones: "FROM tabla", "UPDATE tabla", "DELETE FROM tabla"
        for keyword in ["from", "update", "delete from"]:
            if keyword in query_lower:
                parts = query_lower.split(keyword, 1)
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0].strip(";").strip("(")
                    table_name = table_part
                    break
    
    # Si es tabla global, no aplicar filtro
    if table_name and table_name.lower() in GLOBAL_TABLES:
        logger.debug(f"[TENANT_FILTER] Tabla global '{table_name}' detectada, omitiendo filtro")
        return query
    
    # Verificar si ya tiene filtro de tenant
    if f"{tenant_column} = :{tenant_column}" in query_str or \
       f"{tenant_column} = :client_id" in query_str or \
       f"{tenant_column} = {client_id}" in query_str:
        logger.debug(f"[TENANT_FILTER] TextClause ya tiene filtro de tenant")
        return query
    
    # Agregar filtro de tenant al WHERE clause
    if "where" in query_lower:
        # Ya tiene WHERE, agregar AND cliente_id = :cliente_id
        # Buscar el último WHERE y agregar condición
        where_pos = query_str.lower().rfind("where")
        if where_pos != -1:
            # Insertar después del WHERE existente
            insert_pos = query_str.find(" ", where_pos + 5)
            if insert_pos == -1:
                insert_pos = len(query_str)
            
            # Construir nueva query con filtro agregado
            new_query_str = (
                query_str[:insert_pos] + 
                f" AND {tenant_column} = :{tenant_column}" +
                query_str[insert_pos:]
            )
            
            # Obtener parámetros existentes y agregar cliente_id
            existing_params = dict(query.bindparams) if hasattr(query, 'bindparams') else {}
            existing_params[tenant_column] = client_id
            
            return text(new_query_str).bindparams(**existing_params)
    else:
        # No tiene WHERE, agregar WHERE cliente_id = :cliente_id
        # Buscar FROM para determinar dónde insertar
        from_pos = query_lower.rfind("from")
        if from_pos != -1:
            # Encontrar el final de la tabla (puede tener JOIN, etc.)
            # Simplificado: buscar el siguiente espacio o punto y coma
            insert_pos = query_str.find(" ", from_pos + 4)
            if insert_pos == -1:
                insert_pos = len(query_str)
            
            # Construir nueva query con WHERE agregado
            new_query_str = (
                query_str[:insert_pos] + 
                f" WHERE {tenant_column} = :{tenant_column}" +
                query_str[insert_pos:]
            )
            
            # Obtener parámetros existentes y agregar cliente_id
            existing_params = dict(query.bindparams) if hasattr(query, 'bindparams') else {}
            existing_params[tenant_column] = client_id
            
            return text(new_query_str).bindparams(**existing_params)
    
    # Si no se pudo modificar, retornar original (con advertencia)
    logger.warning(
        f"[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause. "
        f"Query: {query_str[:200]}..."
    )
    return query
```

**Tiempo estimado:** 1-2 días (implementación + testing)

---

### Opción 2: Migrar a SQLAlchemy Core (MEJOR A LARGO PLAZO)

**Ventajas:**
- ✅ Máxima seguridad (filtro automático garantizado)
- ✅ Type safety y mejor mantenibilidad
- ✅ Mejor integración con SQLAlchemy

**Desventajas:**
- ⚠️ Requiere migrar todas las queries existentes
- ⚠️ Más tiempo de desarrollo
- ⚠️ Algunas queries complejas pueden ser difíciles de migrar

**Ejemplo de Migración:**

**ANTES (TextClause):**
```python
# app/modules/auth/application/services/refresh_token_service.py:90
existing = await execute_query(
    text(GET_REFRESH_TOKEN_BY_HASH).bindparams(
        token_hash=token_hash, 
        cliente_id=cliente_id
    )
)
```

**DESPUÉS (SQLAlchemy Core):**
```python
# app/modules/auth/application/services/refresh_token_service.py
from sqlalchemy import select
from app.infrastructure.database.tables import RefreshTokenTable

# Query migrada a SQLAlchemy Core
query = select(
    RefreshTokenTable.c.token_id,
    RefreshTokenTable.c.usuario_id,
    RefreshTokenTable.c.token_hash,
    RefreshTokenTable.c.expires_at,
    RefreshTokenTable.c.is_revoked,
    RefreshTokenTable.c.created_at,
    RefreshTokenTable.c.client_type,
    RefreshTokenTable.c.cliente_id
).where(
    RefreshTokenTable.c.token_hash == token_hash,
    RefreshTokenTable.c.cliente_id == cliente_id,  # ✅ Filtro explícito
    RefreshTokenTable.c.is_revoked == False,
    RefreshTokenTable.c.expires_at > func.getdate()
)

# ✅ Filtro automático se aplica además del filtro explícito
existing = await execute_query(query, client_id=cliente_id)
```

**Tiempo estimado:** 3-5 días (migración completa de todas las queries)

---

## 🎯 RECOMENDACIÓN FINAL

### Estrategia Híbrida (RECOMENDADA)

1. **Corto Plazo (1-2 días):**
   - Implementar `apply_tenant_filter_to_text_clause()` para proteger queries existentes
   - Aplicar filtro automático a todas las queries TextClause

2. **Mediano Plazo (3-5 días):**
   - Migrar queries críticas a SQLAlchemy Core (auth, tokens, usuarios)
   - Mantener TextClause para queries complejas que son difíciles de migrar

3. **Largo Plazo:**
   - Migrar gradualmente todas las queries a SQLAlchemy Core
   - Deprecar uso de TextClause para queries simples

### Prioridad de Migración

**🔴 ALTA PRIORIDAD (Migrar primero):**
- Queries de autenticación (`refresh_token_service.py`)
- Queries de usuarios (`user_service.py`)
- Queries de roles y permisos (`rol_service.py`, `permiso_service.py`)

**🟡 MEDIA PRIORIDAD:**
- Queries de menús (`modulo_menu_service.py`)
- Queries de auditoría (`audit_service.py`)

**🟢 BAJA PRIORIDAD:**
- Queries complejas con múltiples JOINs
- Queries de reportes

---

## 📝 EJEMPLO CONCRETO DE CORRECCIÓN

### Query Actual (Vulnerable si se olvida cliente_id)

```python
# app/modules/auth/application/services/refresh_token_service.py:90
existing = await execute_query(
    text(GET_REFRESH_TOKEN_BY_HASH).bindparams(
        token_hash=token_hash, 
        cliente_id=cliente_id  # ✅ Correcto: desarrollador incluye cliente_id
    )
)
```

### Con Opción 1 (Filtro Automático)

```python
# Mismo código, pero ahora con protección automática
existing = await execute_query(
    text(GET_REFRESH_TOKEN_BY_HASH).bindparams(
        token_hash=token_hash
        # ⚠️ Si se olvida cliente_id, el filtro automático lo agrega
    ),
    client_id=cliente_id  # ✅ Filtro automático lo usa
)
```

### Con Opción 2 (SQLAlchemy Core)

```python
# Migrado a SQLAlchemy Core
from sqlalchemy import select, func
from app.infrastructure.database.tables import RefreshTokenTable

query = select(RefreshTokenTable).where(
    RefreshTokenTable.c.token_hash == token_hash,
    RefreshTokenTable.c.is_revoked == False,
    RefreshTokenTable.c.expires_at > func.getdate()
    # ✅ cliente_id se agrega automáticamente por apply_tenant_filter()
)

existing = await execute_query(query, client_id=cliente_id)
```

---

## ✅ CONCLUSIÓN

**Recomendación:** Implementar **Opción 1** primero (filtro automático para TextClause) y luego migrar gradualmente a **Opción 2** (SQLAlchemy Core).

Esto proporciona:
- ✅ Protección inmediata para todas las queries existentes
- ✅ Flexibilidad para migrar gradualmente
- ✅ Máxima seguridad a largo plazo
