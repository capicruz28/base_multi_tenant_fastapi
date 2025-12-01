# Análisis de Seguridad - Evaluación de Tercero

**Fecha:** $(date)  
**Evaluador:** Tercero Externo  
**Calificación:** 5.5 / 10  
**Veredicto:** Riesgo Alto

---

## 📋 Resumen Ejecutivo

Este documento analiza los comentarios de seguridad de un tercero y evalúa su validez, impacto y posibles soluciones para el proyecto multi-tenant FastAPI.

---

## 🔍 Análisis de los Comentarios del Tercero

### 1. ✅ **Tenant Spoofing - CONFIRMADO (Crítico)**

**Comentario del Tercero:**
> "El middleware confía en headers Origin y Referer para determinar el tenant si el host no coincide. Esto es falsificable por un atacante para acceder a datos de otro cliente."

**Ubicación del Código:**
- `app/core/tenant/middleware.py` líneas 63-130, método `_get_host_from_request()`

**Análisis:**
✅ **EL COMENTARIO ES CORRECTO Y CRÍTICO**

**Problema Identificado:**
```python
# Líneas 94-122: Fallback a Origin/Referer
if should_extract_from_origin:
    origin = request.headers.get("origin", "")
    if origin:
        parsed = urlparse(origin)
        if parsed.netloc and not parsed.netloc.startswith(("localhost", "127.0.0.1")):
            host = parsed.netloc  # ⚠️ VULNERABLE: Header falsificable
```

**Riesgo:**
- Un atacante puede enviar un header `Origin: https://victima.midominio.com` para acceder a datos de otro tenant
- El middleware confía en este header cuando el `Host` es localhost o un subdominio excluido
- **Severidad: CRÍTICA** - Permite acceso no autorizado a datos de otros clientes

**Evidencia:**
- El código usa `Origin` y `Referer` como fuente de verdad para determinar el tenant
- Estos headers son completamente controlables por el cliente
- No hay validación adicional (whitelist, verificación DNS, etc.)

---

### 2. ⚠️ **SQL Injection (Riesgo Latente) - PARCIALMENTE CORRECTO**

**Comentario del Tercero:**
> "Aunque usas parámetros ? en la mayoría de queries, la construcción dinámica de strings SQL en los servicios (ej: where_clause += ...) es propensa a errores humanos graves si un desarrollador concatena variables directamente."

**Ubicación del Código:**
- `app/infrastructure/database/repositories/base_repository.py` líneas 162-177, 388-401
- `app/modules/tenant/application/services/cliente_service.py` líneas 502-544
- `app/modules/superadmin/application/services/superadmin_auditoria_service.py` líneas 490-521

**Análisis:**
⚠️ **EL COMENTARIO ES PARCIALMENTE CORRECTO - RIESGO LATENTE**

**Estado Actual:**
✅ **Buenas Prácticas Encontradas:**
- Uso consistente de parámetros `?` en queries
- Construcción de `where_clause` con listas y join seguro
- Valores pasados como tuplas separadas

**Ejemplo Seguro (base_repository.py):**
```python
where_clauses = []
params = []
if filters:
    for field, value in filters.items():
        if value is not None:
            where_clauses.append(f"{field} = ?")  # ✅ Campo hardcodeado
            params.append(value)  # ✅ Valor como parámetro
where_clause = " AND ".join(where_clauses)
query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
# ✅ Parámetros pasados separadamente
```

**Riesgo Latente:**
⚠️ **Patrones Peligrosos Detectados:**
1. **Construcción dinámica de queries con f-strings:**
   ```python
   # cliente_service.py línea 522
   count_query = f"SELECT COUNT(*) as total FROM cliente {where_clause}"
   ```
   - Si `where_clause` contiene valores en lugar de parámetros, es vulnerable
   - Depende de que todos los desarrolladores sigan las prácticas

2. **Ordenamiento dinámico:**
   ```python
   # superadmin_auditoria_service.py línea 486
   order_field = valid_order_fields.get(ordenar_por, "l.fecha_sincronizacion")
   query = f"... ORDER BY {order_field} {order_dir}"
   ```
   - ✅ **Bien implementado:** Usa whitelist de campos válidos
   - ⚠️ **Riesgo:** Si alguien olvida la whitelist, es vulnerable

**Conclusión:**
- El código actual es **relativamente seguro** porque usa parámetros
- El riesgo es **latente** porque la arquitectura permite errores humanos
- Un desarrollador nuevo podría fácilmente hacer: `query = f"SELECT * FROM tabla WHERE campo = '{valor}'"` (vulnerable)

---

### 3. ⚠️ **Validación de Tenant - PARCIALMENTE CORRECTO**

**Comentario del Tercero:**
> "La función get_current_active_user confía en que el token_cliente_id coincide con el request_cliente_id pero la lógica tiene excepciones para SuperAdmin que podrían explotarse."

**Ubicación del Código:**
- `app/api/deps.py` líneas 182-196, función `get_current_active_user()`
- `app/core/auth.py` líneas 301-320, función `get_current_user()`

**Análisis:**
⚠️ **EL COMENTARIO ES PARCIALMENTE CORRECTO - RIESGO MODERADO**

**Estado Actual:**

**1. Validación en `get_current_active_user()` (deps.py):**
```python
# Línea 183-196
token_cliente_id = user_dict.get('cliente_id')
request_cliente_id = getattr(request.state, 'cliente_id', None)

if token_cliente_id is not None and request_cliente_id is not None and token_cliente_id != request_cliente_id:
    logger.warning(f"Acceso denegado...")
    raise credentials_exception
```

**Problemas Identificados:**
1. ⚠️ **Validación incompleta:** Solo valida si ambos IDs son `not None`
   - Si `token_cliente_id` es `None` (SuperAdmin), la validación se omite
   - Si `request_cliente_id` es `None`, la validación se omite
   - **Riesgo:** Un usuario regular con `cliente_id` podría acceder si `request.state.cliente_id` no está establecido

2. ⚠️ **Falta validación explícita de SuperAdmin:**
   - No verifica si el usuario realmente es SuperAdmin antes de permitir acceso cross-tenant
   - Depende de que `cliente_id` sea `None` en la BD, lo cual es frágil

**2. Validación en `get_current_user()` (auth.py):**
```python
# Línea 301-320
if settings.ENABLE_TENANT_TOKEN_VALIDATION:
    if not es_superadmin and token_cliente_id is not None:
        if token_cliente_id != current_cliente_id:
            raise HTTPException(...)
```

**Problemas Identificados:**
1. ✅ **Bien:** Usa feature flag (activado por defecto)
2. ✅ **Bien:** Valida explícitamente que no sea SuperAdmin
3. ⚠️ **Riesgo:** Si `ENABLE_TENANT_TOKEN_VALIDATION` está desactivado, no hay validación

**Riesgo de Explotación:**
- Un atacante podría intentar:
  1. Obtener un token de un usuario regular del tenant A
  2. Enviar request con headers manipulados para parecer tenant B
  3. Si la validación falla o está desactivada, podría acceder a datos del tenant B

**Conclusión:**
- La validación existe pero tiene **gaps** que podrían ser explotados
- La excepción para SuperAdmin es necesaria pero debe ser más robusta
- **Severidad: MODERADA** - Requiere condiciones específicas para explotarse

---

## 🎯 Recomendaciones y Soluciones

### 🔴 **PRIORIDAD ALTA - Tenant Spoofing**

**Solución 1: Eliminar dependencia de Origin/Referer en producción**
```python
def _get_host_from_request(self, request: Request) -> str:
    host = request.headers.get("host", "")
    
    # ✅ SOLUCIÓN: Solo usar Origin/Referer en desarrollo
    if settings.ENVIRONMENT == "development":
        # Lógica actual para desarrollo...
    else:
        # ✅ PRODUCCIÓN: Solo confiar en Host header
        if not host or host.startswith(("localhost", "127.0.0.1")):
            logger.error("[SECURITY] Host inválido en producción")
            raise HTTPException(status_code=400, detail="Host header requerido")
    
    return host
```

**Solución 2: Validar subdominio contra whitelist en BD**
```python
def _get_host_from_request(self, request: Request) -> str:
    host = request.headers.get("host", "")
    
    # Extraer subdominio
    subdomain = self._extract_subdomain(host)
    
    # ✅ VALIDAR: Verificar que el subdominio existe en BD antes de confiar
    if subdomain:
        client_data = self._get_client_data_by_subdomain(subdomain)
        if not client_data:
            raise ClientNotFoundException(f"Subdominio '{subdomain}' no válido")
    
    return host
```

**Solución 3: Usar header personalizado con firma (Recomendado para producción)**
```python
# Agregar header X-Tenant-ID con firma HMAC
# El frontend debe incluir este header firmado
# El backend valida la firma antes de confiar
```

---

### 🟡 **PRIORIDAD MEDIA - SQL Injection (Prevención)**

**Solución 1: Crear helper para construcción segura de queries**
```python
# app/infrastructure/database/query_builder.py
class SafeQueryBuilder:
    ALLOWED_OPERATORS = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
    ALLOWED_FUNCTIONS = ["LOWER", "UPPER", "COUNT", "MAX", "MIN"]
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> tuple:
        """Construye WHERE clause de forma segura"""
        where_clauses = []
        params = []
        
        for field, value in filters.items():
            # ✅ Validar nombre de campo (solo alfanumérico y _)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
                raise ValueError(f"Campo inválido: {field}")
            
            where_clauses.append(f"{field} = ?")
            params.append(value)
        
        return " AND ".join(where_clauses), tuple(params)
```

**Solución 2: Linter/Pre-commit hook para detectar SQL vulnerable**
```python
# .pre-commit-hooks.yaml
- id: detect-sql-injection
  name: Detect SQL Injection
  entry: python scripts/check_sql_injection.py
  language: python
```

**Solución 3: Tests automatizados para queries**
```python
# tests/security/test_sql_injection.py
def test_no_sql_injection_in_repositories():
    """Verifica que todos los repositorios usen parámetros"""
    # Escanear código para patrones peligrosos
```

---

### 🟡 **PRIORIDAD MEDIA - Validación de Tenant**

**Solución 1: Validación más robusta en `get_current_active_user()`**
```python
async def get_current_active_user(...):
    # ... código existente ...
    
    token_cliente_id = user_dict.get('cliente_id')
    request_cliente_id = get_current_client_id()  # ✅ Siempre obtener del contexto
    
    # ✅ VALIDACIÓN MEJORADA
    is_super_admin = user_dict.get('is_super_admin', False)
    
    if is_super_admin:
        # SuperAdmin puede acceder a cualquier tenant
        # Pero validar que el token tenga flag correcto
        if not user_dict.get('is_super_admin'):
            raise HTTPException(403, "Token no válido para SuperAdmin")
    else:
        # Usuario regular: DEBE coincidir
        if token_cliente_id is None:
            raise HTTPException(403, "Token inválido: falta cliente_id")
        
        if request_cliente_id is None:
            raise HTTPException(500, "Error interno: contexto de tenant no disponible")
        
        if token_cliente_id != request_cliente_id:
            logger.warning(f"Tenant mismatch: token={token_cliente_id}, request={request_cliente_id}")
            raise HTTPException(403, "Acceso denegado: token no válido para este tenant")
```

**Solución 2: Validación en middleware (Defensa en profundidad)**
```python
# En TenantMiddleware, después de establecer contexto
if request.user and not request.user.is_super_admin:
    if request.user.cliente_id != client_id:
        raise HTTPException(403, "Tenant mismatch")
```

**Solución 3: Auditoría de accesos cross-tenant**
```python
# Registrar todos los accesos cross-tenant para auditoría
if token_cliente_id != request_cliente_id:
    await AuditService.registrar_tenant_access(
        usuario_id=user_dict['usuario_id'],
        token_cliente_id=token_cliente_id,
        request_cliente_id=request_cliente_id
    )
```

---

## 📊 Matriz de Riesgo y Priorización

| Vulnerabilidad | Severidad | Probabilidad | Impacto | Prioridad |
|---------------|-----------|--------------|---------|-----------|
| Tenant Spoofing | 🔴 Crítica | Alta | Acceso no autorizado a datos | **P0 - Inmediata** |
| SQL Injection | 🟡 Media | Baja* | Pérdida de datos, acceso no autorizado | **P1 - Próxima sprint** |
| Validación Tenant | 🟡 Media | Media | Acceso no autorizado limitado | **P1 - Próxima sprint** |

\* Baja probabilidad porque el código actual es seguro, pero alta si un desarrollador comete error

---

## ✅ Conclusión

**Validez de los Comentarios del Tercero:**
1. ✅ **Tenant Spoofing:** **100% CORRECTO** - Vulnerabilidad crítica confirmada
2. ⚠️ **SQL Injection:** **PARCIALMENTE CORRECTO** - Riesgo latente, código actual seguro
3. ⚠️ **Validación Tenant:** **PARCIALMENTE CORRECTO** - Gaps identificados, no crítico

**Impacto en el Proyecto:**
- Las correcciones **NO dañarán** el proyecto
- Son **mejoras de seguridad** que fortalecen el sistema
- Algunas requieren cambios arquitectónicos menores
- Todas son **compatibles** con el código existente

**Recomendación Final:**
✅ **IMPLEMENTAR TODAS LAS CORRECCIONES** siguiendo el orden de prioridad:
1. **P0:** Corregir Tenant Spoofing (crítico)
2. **P1:** Mejorar validación de tenant y prevenir SQL injection

---

## 🔧 Plan de Implementación Sugerido

### Fase 1: Corrección Crítica (1-2 días)
- [ ] Eliminar dependencia de Origin/Referer en producción
- [ ] Agregar validación de subdominio contra BD
- [ ] Tests de seguridad para tenant spoofing

### Fase 2: Mejoras de Seguridad (3-5 días)
- [ ] Mejorar validación de tenant en `get_current_active_user()`
- [ ] Crear `SafeQueryBuilder` para prevenir SQL injection
- [ ] Agregar auditoría de accesos cross-tenant
- [ ] Tests de seguridad para validación de tenant

### Fase 3: Prevención a Futuro (1 semana)
- [ ] Linter para detectar SQL vulnerable
- [ ] Documentación de mejores prácticas
- [ ] Code review checklist de seguridad

---

**Documento generado automáticamente - Revisar y ajustar según necesidades del proyecto**


