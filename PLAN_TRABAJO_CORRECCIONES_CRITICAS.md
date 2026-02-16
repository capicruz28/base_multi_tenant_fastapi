# 📋 PLAN DE TRABAJO - CORRECCIONES CRÍTICAS PARA READINESS ERP

**Objetivo:** Corregir riesgos críticos identificados en auditoría técnica para preparar el sistema para módulos ERP  
**Enfoque:** Incremental, seguro, con verificaciones y rollback en cada fase  
**Tiempo Estimado Total:** 2-3 días de trabajo

---

## 🎯 PRINCIPIOS DE TRABAJO

1. **Incremental:** Una fase a la vez, verificar antes de continuar
2. **Seguro:** Backup antes de cambios, tests después de cada fase
3. **Reversible:** Cada cambio debe poder revertirse fácilmente
4. **Verificable:** Tests y validaciones en cada paso
5. **Documentado:** Documentar cambios y decisiones

---

## 📦 PREPARACIÓN (ANTES DE COMENZAR)

### Checklist Pre-Trabajo

- [ ] **Backup completo de código**
  ```bash
  git checkout -b correcciones-criticas-readiness-erp
  git add .
  git commit -m "Backup antes de correcciones críticas"
  ```

- [ ] **Backup de base de datos**
  ```sql
  -- BD Central
  BACKUP DATABASE [bd_hybrid_sistema_central] 
  TO DISK = 'C:\Backups\backup_pre_correcciones_' + CONVERT(VARCHAR, GETDATE(), 112) + '.bak'
  WITH FORMAT, COMPRESSION;
  
  -- BD Dedicadas (si aplica)
  -- Repetir para cada BD dedicada de cliente
  ```

- [ ] **Verificar ambiente de desarrollo**
  - [ ] Servidor de desarrollo funcionando
  - [ ] Tests básicos pasando
  - [ ] Base de datos accesible
  - [ ] Redis accesible (si se usa)

- [ ] **Preparar ambiente de pruebas**
  - [ ] Crear tenant de prueba (shared)
  - [ ] Crear tenant de prueba (dedicated) si aplica
  - [ ] Usuarios de prueba con diferentes roles

---

## 🔴 FASE 1: CORRECCIÓN SSO - TOKENS CON `cliente_id`

**Prioridad:** 🔴 CRÍTICA  
**Tiempo Estimado:** 2-4 horas  
**Riesgo:** BAJO (solo afecta flujos SSO, no login password)

### Objetivo
Incluir `cliente_id`, `access_level`, `is_super_admin` y `user_type` en payload de tokens SSO para que la validación de tenant funcione correctamente.

### Archivos a Modificar

1. `app/modules/auth/presentation/endpoints.py`
   - Línea ~1107: `sso_azure_login`
   - Línea ~1230: `sso_google_login`

### Pasos Detallados

#### Paso 1.1: Crear función helper para payload de token SSO

**Archivo:** `app/core/security/jwt.py` (o crear nuevo helper)

```python
def build_token_payload_for_sso(
    user_full_data: Dict[str, Any],
    cliente_id: UUID,
    user_role_names: List[str]
) -> Dict[str, Any]:
    """
    Construye el payload del token JWT para flujos SSO.
    
    ✅ FASE 1: Incluye cliente_id y level_info igual que login password.
    
    Args:
        user_full_data: Datos completos del usuario
        cliente_id: ID del cliente/tenant
        user_role_names: Lista de nombres de roles del usuario
    
    Returns:
        Dict con payload completo para JWT
    """
    from app.modules.rbac.application.services.rol_service import RolService
    
    # Obtener access_level (igual que en login password)
    access_level = await RolService.get_user_max_access_level(
        cliente_id=cliente_id,
        usuario_id=user_full_data['usuario_id'],
        role_names=user_role_names
    )
    
    # Determinar user_type
    is_super_admin = user_full_data.get('is_super_admin', False)
    user_type = "super_admin" if is_super_admin else "user"
    
    payload = {
        "sub": user_full_data['nombre_usuario'],
        "cliente_id": str(cliente_id),  # ✅ NUEVO
        "access_level": access_level,    # ✅ NUEVO
        "is_super_admin": is_super_admin,  # ✅ NUEVO
        "user_type": user_type,          # ✅ NUEVO
        "type": "access"
    }
    
    return payload
```

#### Paso 1.2: Modificar endpoint SSO Azure

**Archivo:** `app/modules/auth/presentation/endpoints.py`

**Línea ~1107 - ANTES:**
```python
access_token, access_jti = create_access_token(data={"sub": user_full_data['nombre_usuario']})
```

**Línea ~1107 - DESPUÉS:**
```python
# ✅ FASE 1: Construir payload completo con cliente_id y level_info
token_payload = await build_token_payload_for_sso(
    user_full_data=user_full_data,
    cliente_id=cliente_id,
    user_role_names=user_role_names
)
access_token, access_jti = create_access_token(data=token_payload)
```

#### Paso 1.3: Modificar endpoint SSO Google

**Archivo:** `app/modules/auth/presentation/endpoints.py`

**Línea ~1230 - ANTES:**
```python
access_token, access_jti = create_access_token(data={"sub": user_full_data['nombre_usuario']})
```

**Línea ~1230 - DESPUÉS:**
```python
# ✅ FASE 1: Construir payload completo con cliente_id y level_info
token_payload = await build_token_payload_for_sso(
    user_full_data=user_full_data,
    cliente_id=cliente_id,
    user_role_names=user_role_names
)
access_token, access_jti = create_access_token(data=token_payload)
```

#### Paso 1.4: Verificar refresh token también

**Verificar que refresh token también incluya cliente_id si es necesario**

### Verificaciones Post-Fase 1

- [ ] **Test manual SSO Azure**
  1. Autenticar con Azure AD
  2. Verificar token JWT decodificado contiene `cliente_id`
  3. Verificar `access_level` presente
  4. Verificar validación de tenant funciona

- [ ] **Test manual SSO Google**
  1. Autenticar con Google
  2. Verificar token JWT decodificado contiene `cliente_id`
  3. Verificar `access_level` presente
  4. Verificar validación de tenant funciona

- [ ] **Test de seguridad**
  1. Intentar usar token SSO de tenant A en tenant B
  2. Debe rechazarse con 403

- [ ] **Test de regresión**
  1. Login password sigue funcionando
  2. Refresh token sigue funcionando
  3. Validación de tenant en login password sigue funcionando

### Rollback Fase 1

Si algo falla:
```bash
git checkout app/modules/auth/presentation/endpoints.py
git checkout app/core/security/jwt.py  # Si se modificó
```

### ✅ Criterio de Éxito Fase 1

- ✅ Tokens SSO incluyen `cliente_id`, `access_level`, `is_super_admin`, `user_type`
- ✅ Validación de tenant funciona para SSO
- ✅ Login password no se afecta
- ✅ Tests pasan

---

## 🔴 FASE 2: AUDITORÍA Y CORRECCIÓN DE QUERIES TEXTCLAUSE/STRING

**Prioridad:** 🔴 CRÍTICA  
**Tiempo Estimado:** 1-2 días  
**Riesgo:** MEDIO (afecta múltiples archivos, requiere revisión cuidadosa)

### Objetivo
Identificar y corregir todas las queries que usan `text()` o string SQL contra tablas con `cliente_id`, asegurando que siempre incluyan filtro de tenant.

### Archivos Identificados para Revisión

Basado en `grep`, estos archivos usan `text()` o `TextClause`:

1. `app/modules/auth/application/services/refresh_token_service.py`
2. `app/core/application/unit_of_work.py`
3. `app/infrastructure/database/queries_async.py`
4. `app/modules/users/application/services/user_service.py`
5. `app/modules/rbac/application/services/rol_service.py`
6. `app/modules/superadmin/application/services/audit_service.py`
7. Otros archivos según auditoría

### Pasos Detallados

#### Paso 2.1: Crear script de auditoría

**Archivo:** `scripts/audit_text_queries.py` (NUEVO)

```python
"""
Script para auditar queries que usan text() o string SQL.
Identifica queries que tocan tablas con cliente_id sin filtro explícito.
"""
import re
import ast
from pathlib import Path
from typing import List, Dict

TABLAS_CON_CLIENTE_ID = {
    'usuario', 'rol', 'usuario_rol', 'rol_menu_permiso',
    'refresh_tokens', 'auth_audit_log'
}

def audit_file(file_path: Path) -> List[Dict]:
    """Audita un archivo Python buscando queries problemáticas."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Buscar text() o TextClause
    for i, line in enumerate(lines, 1):
        if 'text(' in line.lower() or 'textclause' in line.lower():
            # Buscar contexto (próximas 10 líneas)
            context = '\n'.join(lines[i-1:min(i+10, len(lines))])
            
            # Verificar si toca tablas con cliente_id
            for tabla in TABLAS_CON_CLIENTE_ID:
                if tabla in context.lower():
                    # Verificar si tiene cliente_id en la query
                    if 'cliente_id' not in context.lower():
                        issues.append({
                            'file': str(file_path),
                            'line': i,
                            'issue': f'Query con text() toca tabla {tabla} sin cliente_id visible',
                            'context': context[:200]
                        })
    
    return issues

def main():
    """Ejecuta auditoría en todos los archivos Python."""
    app_dir = Path('app')
    all_issues = []
    
    for py_file in app_dir.rglob('*.py'):
        issues = audit_file(py_file)
        all_issues.extend(issues)
    
    # Reportar
    print(f"Total de issues encontrados: {len(all_issues)}")
    for issue in all_issues:
        print(f"\n{issue['file']}:{issue['line']}")
        print(f"  {issue['issue']}")
        print(f"  Contexto: {issue['context']}")
    
    return all_issues

if __name__ == '__main__':
    main()
```

#### Paso 2.2: Ejecutar auditoría

```bash
python scripts/audit_text_queries.py > reports/audit_text_queries_report.txt
```

#### Paso 2.3: Revisar y priorizar queries

**Prioridad ALTA (tablas críticas):**
- `refresh_tokens` - Seguridad crítica
- `usuario` - Datos sensibles
- `rol_menu_permiso` - Permisos críticos

**Prioridad MEDIA:**
- `rol`, `usuario_rol` - Importantes pero menos críticos
- `auth_audit_log` - Auditoría, menos crítico

#### Paso 2.4: Corregir queries una por una

**Estrategia por query:**

1. **Identificar tabla y operación**
2. **Verificar si ya tiene `cliente_id`** (puede estar en parámetros)
3. **Si NO tiene:**
   - Añadir `cliente_id` como parámetro
   - Modificar query para incluir `WHERE cliente_id = :cliente_id`
   - Pasar `cliente_id` desde contexto o parámetro
4. **Si SÍ tiene pero no se pasa:**
   - Asegurar que se pasa desde contexto
   - Añadir validación si falta

**Ejemplo de Corrección:**

**ANTES:**
```python
query = text("SELECT * FROM refresh_tokens WHERE token_hash = :hash")
result = await execute_query(query, {"hash": token_hash})
```

**DESPUÉS:**
```python
from app.core.tenant.context import get_current_client_id

cliente_id = get_current_client_id()
query = text("""
    SELECT * FROM refresh_tokens 
    WHERE token_hash = :hash 
    AND cliente_id = :cliente_id
""")
result = await execute_query(query, {
    "hash": token_hash,
    "cliente_id": cliente_id
})
```

#### Paso 2.5: Migrar a SQLAlchemy Core donde sea posible

**Priorizar migración para:**
- Queries frecuentes
- Queries complejas
- Queries críticas de seguridad

**Ejemplo de Migración:**

**ANTES (text):**
```python
query = text("SELECT * FROM usuario WHERE correo = :email")
```

**DESPUÉS (SQLAlchemy Core):**
```python
from sqlalchemy import select
from app.infrastructure.database.tables import UsuarioTable

query = select(UsuarioTable).where(
    UsuarioTable.c.correo == email,
    UsuarioTable.c.cliente_id == cliente_id  # ✅ Filtro automático
)
```

### Verificaciones Post-Fase 2

- [ ] **Test de aislamiento por query corregida**
  1. Crear datos en tenant A
  2. Intentar acceder desde tenant B
  3. Debe fallar o retornar vacío

- [ ] **Test de regresión**
  1. Funcionalidad básica sigue funcionando
  2. Login funciona
  3. Refresh token funciona
  4. Permisos funcionan

- [ ] **Test de performance**
  1. Queries corregidas no son más lentas
  2. Índices se usan correctamente

### Rollback Fase 2

Si algo falla:
```bash
# Revertir archivos modificados uno por uno
git checkout app/modules/auth/application/services/refresh_token_service.py
# ... etc
```

### ✅ Criterio de Éxito Fase 2

- ✅ Todas las queries TextClause/string contra tablas con `cliente_id` incluyen filtro
- ✅ Tests de aislamiento pasan
- ✅ No hay regresiones
- ✅ Documentación actualizada

---

## 🟡 FASE 3: VALIDACIÓN DE `menu_id` EN BD DEDICADA

**Prioridad:** 🟡 ALTA  
**Tiempo Estimado:** 4-8 horas  
**Riesgo:** BAJO (añade validación, no cambia lógica existente)

### Objetivo
Validar que `menu_id` existe en BD central antes de insertar/actualizar `rol_menu_permiso` en BD dedicada.

### Archivos a Modificar

1. `app/modules/rbac/application/services/permiso_service.py`
   - Función `_validar_rol_y_menu` (línea ~206)
   - Función `asignar_o_actualizar_permiso` (línea ~161)

2. `app/modules/rbac/application/services/rol_service.py`
   - Función `actualizar_permisos_rol` (línea ~1089)

### Pasos Detallados

#### Paso 3.1: Crear servicio de validación de menú

**Archivo:** `app/modules/rbac/application/services/menu_validation_service.py` (NUEVO)

```python
"""
Servicio para validar que menu_id existe en BD central.
Útil para BD dedicadas donde menu_id referencia modulo_menu en central.
"""
from uuid import UUID
from typing import Optional
from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.infrastructure.database.tables_modulos import ModuloMenuTable
from sqlalchemy import select
from app.core.exceptions import NotFoundError, ValidationError

class MenuValidationService:
    """Valida existencia de menús en BD central."""
    
    @staticmethod
    async def validate_menu_exists_in_central(
        menu_id: UUID,
        cliente_id: UUID,
        allow_global: bool = True
    ) -> bool:
        """
        Valida que menu_id existe en BD central.
        
        Args:
            menu_id: ID del menú a validar
            cliente_id: ID del cliente (para validar ownership si no es global)
            allow_global: Si True, permite menús globales (cliente_id=NULL)
        
        Returns:
            True si existe y es válido
        
        Raises:
            NotFoundError: Si el menú no existe
            ValidationError: Si el menú no pertenece al cliente
        """
        # Query en BD central (ADMIN connection)
        query = select(
            ModuloMenuTable.c.menu_id,
            ModuloMenuTable.c.cliente_id,
            ModuloMenuTable.c.es_activo
        ).where(
            ModuloMenuTable.c.menu_id == menu_id
        )
        
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await session.execute(query)
            menu = result.fetchone()
            
            if not menu:
                raise NotFoundError(
                    detail=f"Menú con ID {menu_id} no existe en catálogo central",
                    internal_code="MENU_NOT_FOUND_CENTRAL"
                )
            
            menu_cliente_id = menu['cliente_id']
            es_activo = menu['es_activo']
            
            if not es_activo:
                raise ValidationError(
                    detail=f"Menú con ID {menu_id} está inactivo",
                    internal_code="MENU_INACTIVE"
                )
            
            # Validar ownership
            if menu_cliente_id is None:
                # Menú global
                if not allow_global:
                    raise ValidationError(
                        detail=f"Menú global {menu_id} no permitido para este cliente",
                        internal_code="GLOBAL_MENU_NOT_ALLOWED"
                    )
                return True
            
            # Menú específico del cliente
            if menu_cliente_id != cliente_id:
                raise ValidationError(
                    detail=f"Menú {menu_id} no pertenece al cliente {cliente_id}",
                    internal_code="MENU_CLIENT_MISMATCH"
                )
            
            return True
    
    @staticmethod
    async def validate_multiple_menus(
        menu_ids: list[UUID],
        cliente_id: UUID,
        allow_global: bool = True
    ) -> dict[UUID, bool]:
        """
        Valida múltiples menús en batch.
        
        Returns:
            Dict con menu_id -> True si válido
        """
        # Query batch en BD central
        query = select(
            ModuloMenuTable.c.menu_id,
            ModuloMenuTable.c.cliente_id,
            ModuloMenuTable.c.es_activo
        ).where(
            ModuloMenuTable.c.menu_id.in_(menu_ids)
        )
        
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await session.execute(query)
            menus = result.fetchall()
            
            valid_menus = {}
            for menu in menus:
                menu_id = menu['menu_id']
                menu_cliente_id = menu['cliente_id']
                es_activo = menu['es_activo']
                
                if not es_activo:
                    continue  # Skip inactivos
                
                if menu_cliente_id is None:
                    # Menú global
                    if allow_global:
                        valid_menus[menu_id] = True
                elif menu_cliente_id == cliente_id:
                    # Menú del cliente
                    valid_menus[menu_id] = True
            
            # Verificar que todos los menu_ids fueron encontrados
            missing = set(menu_ids) - set(valid_menus.keys())
            if missing:
                raise NotFoundError(
                    detail=f"Menús no encontrados: {missing}",
                    internal_code="MENUS_NOT_FOUND"
                )
            
            return valid_menus
```

#### Paso 3.2: Integrar validación en PermisoService

**Archivo:** `app/modules/rbac/application/services/permiso_service.py`

**Modificar función `_validar_rol_y_menu` (línea ~206):**

```python
@staticmethod
async def _validar_rol_y_menu(
    cliente_id: UUID,
    rol_id: UUID,
    menu_id: UUID
) -> None:
    """
    Valida que el rol y menú existen y pertenecen al cliente.
    
    ✅ FASE 3: Añade validación de menu_id en BD central para BD dedicadas.
    """
    from app.core.tenant.context import get_tenant_context
    from app.modules.rbac.application.services.menu_validation_service import MenuValidationService
    
    # ... validación de rol existente ...
    
    # ✅ FASE 3: Validar menú en BD central (especialmente importante para BD dedicadas)
    tenant_context = get_tenant_context()
    
    if tenant_context.is_multi_db():
        # BD dedicada: menu_id debe existir en BD central
        await MenuValidationService.validate_menu_exists_in_central(
            menu_id=menu_id,
            cliente_id=cliente_id,
            allow_global=True  # Permitir menús globales
        )
    else:
        # BD central: validación local (ya existe)
        # ... validación local existente ...
```

#### Paso 3.3: Integrar validación en RolService

**Archivo:** `app/modules/rbac/application/services/rol_service.py`

**Modificar función `actualizar_permisos_rol` (línea ~1089):**

Ya existe validación batch (línea ~1124-1155), pero asegurar que funciona para BD dedicadas:

```python
# ✅ FASE 3: Validación mejorada para BD dedicadas
from app.core.tenant.context import get_tenant_context
from app.modules.rbac.application.services.menu_validation_service import MenuValidationService

tenant_context = get_tenant_context()

if tenant_context.is_multi_db():
    # BD dedicada: validar todos los menu_ids en batch contra BD central
    menu_ids_to_validate = [permiso.menu_id for permiso in nuevos_permisos]
    await MenuValidationService.validate_multiple_menus(
        menu_ids=menu_ids_to_validate,
        cliente_id=cliente_id,
        allow_global=True
    )
else:
    # BD central: validación local existente
    # ... código existente ...
```

### Verificaciones Post-Fase 3

- [ ] **Test en BD dedicada**
  1. Intentar crear permiso con `menu_id` inexistente
  2. Debe fallar con error claro

- [ ] **Test en BD central**
  1. Validación local sigue funcionando
  2. No hay regresiones

- [ ] **Test de menús globales**
  1. Crear permiso con menú global (cliente_id=NULL)
  2. Debe funcionar si `allow_global=True`

- [ ] **Test de performance**
  1. Validación batch no es lenta
  2. No hay queries N+1

### Rollback Fase 3

Si algo falla:
```bash
git checkout app/modules/rbac/application/services/permiso_service.py
git checkout app/modules/rbac/application/services/rol_service.py
rm app/modules/rbac/application/services/menu_validation_service.py
```

### ✅ Criterio de Éxito Fase 3

- ✅ Validación de `menu_id` funciona en BD dedicadas
- ✅ Validación batch eficiente
- ✅ No hay regresiones en BD central
- ✅ Errores claros cuando `menu_id` no existe

---

## 🟡 FASE 4: DEFINIR Y CORREGIR FLUJO DE `cleanup_expired_tokens`

**Prioridad:** 🟡 ALTA  
**Tiempo Estimado:** 2-4 horas  
**Riesgo:** BAJO (mejora funcionalidad existente)

### Objetivo
Definir y corregir el flujo de limpieza de tokens expirados para que funcione correctamente en arquitectura Multi-DB.

### Archivos a Modificar

1. `app/modules/auth/application/services/refresh_token_service.py`
   - Función `cleanup_expired_tokens` (línea ~374)

### Pasos Detallados

#### Paso 4.1: Analizar comportamiento actual

**Problema identificado:**
- `cleanup_expired_tokens` llama `execute_update(text(DELETE_EXPIRED_TOKENS))` sin `client_id`
- En Single-DB puede limpiar todos los tenants
- En Multi-DB, sin contexto no hay conexión tenant

#### Paso 4.2: Definir diseño

**Opción A: Cleanup por tenant con contexto (RECOMENDADO)**
- Job que itera todos los tenants activos
- Para cada tenant, establece contexto y ejecuta cleanup
- Permite cleanup independiente por tenant

**Opción B: Cleanup solo en BD central**
- Solo ejecutar cleanup en Single-DB
- Multi-DB requiere cleanup manual o job separado

**Decisión:** Opción A (más robusta y escalable)

#### Paso 4.3: Crear job de cleanup por tenant

**Archivo:** `app/modules/auth/application/services/refresh_token_cleanup_job.py` (NUEVO)

```python
"""
Job para limpiar tokens expirados en todos los tenants.
Funciona tanto para Single-DB como Multi-DB.
"""
import logging
from uuid import UUID
from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.infrastructure.database.tables import ClienteTable
from sqlalchemy import select
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context

logger = logging.getLogger(__name__)

class RefreshTokenCleanupJob:
    """Job para limpiar tokens expirados por tenant."""
    
    @staticmethod
    async def cleanup_all_tenants() -> dict:
        """
        Limpia tokens expirados en todos los tenants activos.
        
        Returns:
            Dict con estadísticas de cleanup por tenant
        """
        stats = {
            'tenants_processed': 0,
            'tokens_deleted': 0,
            'errors': []
        }
        
        # Obtener todos los tenants activos
        query = select(
            ClienteTable.c.cliente_id,
            ClienteTable.c.codigo_cliente
        ).where(
            ClienteTable.c.es_activo == True
        )
        
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await session.execute(query)
            tenants = result.fetchall()
        
        # Procesar cada tenant
        for tenant in tenants:
            cliente_id = tenant['cliente_id']
            codigo_cliente = tenant['codigo_cliente']
            
            try:
                # Establecer contexto del tenant
                tenant_context = TenantContext(
                    client_id=cliente_id,
                    codigo_cliente=codigo_cliente,
                    database_type="single"  # Se determinará automáticamente
                )
                
                tokens = set_tenant_context(tenant_context)
                
                try:
                    # Ejecutar cleanup para este tenant
                    deleted_count = await RefreshTokenService.cleanup_expired_tokens()
                    
                    stats['tenants_processed'] += 1
                    stats['tokens_deleted'] += deleted_count
                    
                    logger.info(
                        f"[CLEANUP] Tenant {codigo_cliente} ({cliente_id}): "
                        f"{deleted_count} tokens eliminados"
                    )
                finally:
                    # Limpiar contexto
                    reset_tenant_context(tokens)
                    
            except Exception as e:
                error_msg = f"Error en tenant {codigo_cliente} ({cliente_id}): {str(e)}"
                logger.error(f"[CLEANUP] {error_msg}", exc_info=True)
                stats['errors'].append(error_msg)
        
        logger.info(
            f"[CLEANUP] Completado: {stats['tenants_processed']} tenants, "
            f"{stats['tokens_deleted']} tokens eliminados, "
            f"{len(stats['errors'])} errores"
        )
        
        return stats
```

#### Paso 4.4: Modificar `cleanup_expired_tokens` para requerir contexto

**Archivo:** `app/modules/auth/application/services/refresh_token_service.py`

**Modificar función `cleanup_expired_tokens` (línea ~374):**

```python
@staticmethod
async def cleanup_expired_tokens() -> int:
    """
    Elimina tokens de refresh expirados.
    
    ✅ FASE 4: Requiere contexto de tenant para funcionar correctamente.
    Para limpiar todos los tenants, usar RefreshTokenCleanupJob.cleanup_all_tenants()
    
    Returns:
        Número de tokens eliminados
    """
    from app.core.tenant.context import get_current_client_id
    
    # ✅ FASE 4: Obtener cliente_id del contexto
    try:
        cliente_id = get_current_client_id()
    except RuntimeError:
        raise ValidationError(
            detail="cleanup_expired_tokens requiere contexto de tenant. "
                   "Use RefreshTokenCleanupJob.cleanup_all_tenants() para limpiar todos los tenants.",
            internal_code="TENANT_CONTEXT_REQUIRED"
        )
    
    # Query con filtro de tenant
    query = text("""
        DELETE FROM refresh_tokens
        WHERE expires_at < GETDATE()
        AND cliente_id = :cliente_id
        AND is_revoked = 0
    """)
    
    result = await execute_update(query, {"cliente_id": cliente_id})
    return result.rowcount if result else 0
```

#### Paso 4.5: Crear endpoint/admin para ejecutar cleanup (opcional)

**Archivo:** `app/modules/auth/presentation/endpoints.py` (o crear endpoints_admin.py)

```python
@router.post(
    "/admin/cleanup-expired-tokens/",
    summary="Limpiar tokens expirados en todos los tenants",
    dependencies=[Depends(super_admin_required)]
)
async def cleanup_expired_tokens_all_tenants():
    """
    Endpoint administrativo para limpiar tokens expirados en todos los tenants.
    Solo accesible para super admin.
    """
    from app.modules.auth.application.services.refresh_token_cleanup_job import RefreshTokenCleanupJob
    
    stats = await RefreshTokenCleanupJob.cleanup_all_tenants()
    
    return {
        "status": "completed",
        "stats": stats
    }
```

### Verificaciones Post-Fase 4

- [ ] **Test en Single-DB**
  1. Crear tokens expirados en tenant A
  2. Ejecutar cleanup con contexto de tenant A
  3. Solo tokens de tenant A deben eliminarse

- [ ] **Test en Multi-DB**
  1. Crear tokens expirados en tenant dedicado
  2. Ejecutar cleanup con contexto
  3. Tokens deben eliminarse correctamente

- [ ] **Test de job completo**
  1. Ejecutar `cleanup_all_tenants()`
  2. Verificar que procesa todos los tenants
  3. Verificar estadísticas correctas

- [ ] **Test sin contexto**
  1. Intentar `cleanup_expired_tokens()` sin contexto
  2. Debe fallar con error claro

### Rollback Fase 4

Si algo falla:
```bash
git checkout app/modules/auth/application/services/refresh_token_service.py
rm app/modules/auth/application/services/refresh_token_cleanup_job.py
```

### ✅ Criterio de Éxito Fase 4

- ✅ Cleanup funciona correctamente en Single-DB y Multi-DB
- ✅ Job de cleanup por tenant funciona
- ✅ Sin contexto, función falla con error claro
- ✅ No hay regresiones

---

## 🟢 FASE 5: MEJORAS ADICIONALES (OPCIONAL)

**Prioridad:** 🟢 MEDIA  
**Tiempo Estimado:** 4-8 horas  
**Riesgo:** BAJO

### Objetivo
Mejoras adicionales identificadas en auditoría para mayor robustez.

### Tareas Opcionales

1. **Añadir tablas globales de catálogo a GLOBAL_TABLES**
   - Añadir `modulo`, `modulo_seccion` a `GLOBAL_TABLES`
   - Documentar excepción para `modulo_menu`

2. **Corregir tipo de parámetro en `_get_pool_for_tenant`**
   - Cambiar `client_id: int` a `Union[int, UUID]`

3. **Documentar comportamiento fail-soft de Redis**
   - Añadir documentación explícita
   - Definir criterios de monitoreo

---

## 📊 RESUMEN DE FASES

| Fase | Prioridad | Tiempo | Riesgo | Estado |
|------|-----------|--------|--------|--------|
| **Fase 1: SSO con cliente_id** | 🔴 CRÍTICA | 2-4h | BAJO | ⬜ Pendiente |
| **Fase 2: Queries TextClause** | 🔴 CRÍTICA | 1-2d | MEDIO | ⬜ Pendiente |
| **Fase 3: Validar menu_id** | 🟡 ALTA | 4-8h | BAJO | ⬜ Pendiente |
| **Fase 4: Cleanup tokens** | 🟡 ALTA | 2-4h | BAJO | ⬜ Pendiente |
| **Fase 5: Mejoras adicionales** | 🟢 MEDIA | 4-8h | BAJO | ⬜ Opcional |

**Tiempo Total Estimado:** 2-3 días

---

## ✅ CHECKLIST FINAL DE READINESS

Después de completar todas las fases:

### Seguridad
- [ ] SSO incluye `cliente_id` en tokens
- [ ] Todas las queries TextClause/string tienen filtro de tenant
- [ ] `menu_id` se valida en BD dedicadas
- [ ] Cleanup de tokens funciona correctamente

### Testing
- [ ] Tests de aislamiento pasan
- [ ] Tests de SSO pasan
- [ ] Tests de validación de menú pasan
- [ ] Tests de cleanup pasan
- [ ] Tests de regresión pasan

### Documentación
- [ ] Cambios documentados
- [ ] Edge cases documentados
- [ ] Comportamiento de cleanup documentado

### Deployment
- [ ] Código revisado
- [ ] Tests pasando
- [ ] Backup realizado
- [ ] Listo para producción

---

## 🚨 PROCEDIMIENTO DE ROLLBACK COMPLETO

Si es necesario revertir todos los cambios:

```bash
# 1. Revertir todos los cambios
git checkout main
git branch -D correcciones-criticas-readiness-erp

# 2. Restaurar BD desde backup
# (Usar backups creados en preparación)

# 3. Verificar que todo funciona
python -m pytest tests/
```

---

## 📝 NOTAS IMPORTANTES

1. **No hacer cambios en producción directamente**
   - Siempre probar en desarrollo primero
   - Usar ambiente de staging si está disponible

2. **Comunicar cambios al equipo**
   - Documentar decisiones de diseño
   - Compartir cambios en código

3. **Monitorear después de deploy**
   - Verificar logs de errores
   - Monitorear performance
   - Verificar que validaciones funcionan

4. **Iterar si es necesario**
   - Si algo no funciona, revertir y corregir
   - No acumular deuda técnica

---

**Fin del Plan de Trabajo**

*Documento generado: Febrero 2025*  
*Versión: 1.0*
