# 🏗️ PLAN DE REFACTORIZACIÓN POR FASES
## Corrección de 3 Problemas Bloqueantes del Core ERP

**Fecha:** Diciembre 2024  
**Arquitecto:** Senior Software Architect  
**Objetivo:** 9/10 en Mantenibilidad y Seguridad  
**Principio:** Zero-Breaking Changes + Enfoque Híbrido

---

## 📊 ANÁLISIS DE RIESGOS PREVIO

### 🚨 Riesgos Críticos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **1. Romper endpoints existentes** | ALTA | CRÍTICO | ✅ Tests de integración antes/después cada fase |
| **2. Pérdida de datos en migración** | MEDIA | CRÍTICO | ✅ Transacciones + Rollback automático |
| **3. Degradación de performance** | MEDIA | ALTO | ✅ Benchmarks antes/después + Monitoreo |
| **4. Conflictos de merge** | ALTA | MEDIO | ✅ Fases pequeñas + Feature flags |
| **5. Inconsistencias entre código nuevo/viejo** | MEDIA | ALTO | ✅ Adapters/Wrappers híbridos |
| **6. Pool exhaustion durante migración** | BAJA | ALTO | ✅ Aumentar límites ANTES de migrar |

### 🛡️ Estrategias de Safety Net

1. **Feature Flags por Fase**
   - Cada fase tiene un flag de configuración
   - Permite rollback inmediato sin deploy
   - Ejemplo: `ENABLE_UNIT_OF_WORK`, `ENABLE_MODULAR_QUERIES`

2. **Tests de Integración Automatizados**
   - Suite completa antes de iniciar
   - Re-ejecutar después de cada fase
   - Coverage mínimo: 80% de endpoints críticos

3. **Adapters/Wrappers Híbridos**
   - Código nuevo puede llamar código viejo
   - Código viejo puede usar código nuevo (opcional)
   - Eliminación gradual de adapters

4. **Monitoreo y Alertas**
   - Métricas de performance por endpoint
   - Alertas de errores en tiempo real
   - Dashboard de salud del sistema

5. **Rollback Plan por Fase**
   - Cada fase tiene plan de rollback documentado
   - Tiempo máximo de rollback: 15 minutos
   - Scripts automatizados de reversión

---

## 📋 FASES DE TRABAJO

### 🎯 ORDEN LÓGICO JUSTIFICADO

El orden está basado en **dependencias reales** del código:

1. **FASE 0: Preparación** (Sin dependencias)
   - Aumentar límites de pool (no afecta código existente)
   - Crear estructura de carpetas (solo creación, sin cambios)

2. **FASE 1: Unit of Work Pattern** (Base para todo)
   - Debe ir primero porque otros módulos lo necesitarán
   - Bajo riesgo: es código nuevo, no modifica existente

3. **FASE 2: Refactorizar SQL Constants** (Depende de FASE 1)
   - Necesita Unit of Work para transacciones en migración
   - Alto impacto pero bajo riesgo con adapters

4. **FASE 3: Optimizar Connection Pool** (Depende de FASE 1 y 2)
   - Necesita estructura modular para pools por módulo
   - Bajo riesgo: solo configuración

---

## 🔧 FASE 0: PREPARACIÓN Y FUNDACIÓN
**Duración:** 2 días  
**Riesgo:** ⚪ MUY BAJO  
**Breaking Changes:** ❌ NINGUNO

### Objetivo
Preparar infraestructura sin tocar código existente.

### Tareas

#### 0.1 Aumentar Límites de Connection Pool
**Archivos Afectados:**
- `app/infrastructure/database/connection_pool.py` (líneas 47-50)

**Cambios:**
```python
# ANTES:
MAX_TENANT_POOLS = int(os.getenv("MAX_TENANT_POOLS", "50"))
TENANT_POOL_SIZE = int(os.getenv("TENANT_POOL_SIZE", "3"))
TENANT_POOL_MAX_OVERFLOW = int(os.getenv("TENANT_POOL_MAX_OVERFLOW", "2"))

# DESPUÉS:
MAX_TENANT_POOLS = int(os.getenv("MAX_TENANT_POOLS", "200"))  # 50 → 200
TENANT_POOL_SIZE = int(os.getenv("TENANT_POOL_SIZE", "5"))  # 3 → 5
TENANT_POOL_MAX_OVERFLOW = int(os.getenv("TENANT_POOL_MAX_OVERFLOW", "3"))  # 2 → 3
INACTIVE_POOL_TIMEOUT = int(os.getenv("INACTIVE_POOL_TIMEOUT", "1800"))  # 30 min (nuevo)
```

**Safety Net:**
- ✅ Variable de entorno permite rollback inmediato
- ✅ No afecta código existente (solo configuración)
- ✅ Tests de carga para validar mejoras

**Validación:**
```bash
# Test de carga antes/después
pytest tests/performance/test_connection_pool.py --benchmark
```

---

#### 0.2 Crear Estructura de Carpetas para Queries Modulares
**Archivos Creados (NUEVOS, sin modificar existentes):**
```
app/infrastructure/database/queries/
├── __init__.py                    # Re-exporta todo para compatibilidad
├── base/
│   ├── __init__.py
│   └── common_queries.py          # Queries compartidas (usuarios, roles)
├── auth/
│   ├── __init__.py
│   └── auth_queries.py            # Queries de autenticación
├── menus/
│   ├── __init__.py
│   └── menu_queries.py            # Queries de menús
├── rbac/
│   ├── __init__.py
│   └── rbac_queries.py            # Queries de RBAC
└── audit/
    ├── __init__.py
    └── audit_queries.py           # Queries de auditoría
```

**Safety Net:**
- ✅ Solo creación de archivos vacíos
- ✅ `__init__.py` mantiene compatibilidad con imports existentes
- ✅ No se modifica `sql_constants.py` todavía

**Validación:**
```python
# Verificar que imports existentes siguen funcionando
from app.infrastructure.database.sql_constants import SELECT_USUARIOS_PAGINATED
assert SELECT_USUARIOS_PAGINATED is not None
```

---

#### 0.3 Crear Tests de Baseline
**Archivos Creados:**
- `tests/integration/test_baseline_endpoints.py`
- `tests/performance/test_baseline_performance.py`

**Contenido:**
- Tests de todos los endpoints críticos
- Benchmarks de performance actual
- Métricas de cobertura

**Safety Net:**
- ✅ Baseline para comparar después de cada fase
- ✅ CI/CD debe pasar 100% antes de continuar

---

### ✅ Criterios de Éxito FASE 0
- [ ] Límites de pool aumentados y validados
- [ ] Estructura de carpetas creada (vacía)
- [ ] Tests de baseline pasando 100%
- [ ] Performance igual o mejor que antes
- [ ] Zero breaking changes confirmado

---

## 🔧 FASE 1: IMPLEMENTAR UNIT OF WORK PATTERN
**Duración:** 4-5 días  
**Riesgo:** 🟡 BAJO (código nuevo, no modifica existente)  
**Breaking Changes:** ❌ NINGUNO (enfoque híbrido)

### Objetivo
Crear patrón Unit of Work que conviva con código existente.

### Tareas

#### 1.1 Crear UnitOfWork Base
**Archivos Creados:**
- `app/core/application/unit_of_work.py` (NUEVO)

**Implementación:**
```python
# app/core/application/unit_of_work.py
"""
Unit of Work Pattern para transacciones atómicas multi-operación.

✅ FASE 1: Implementación híbrida que convive con código existente.
- Código nuevo puede usar UnitOfWork
- Código viejo sigue usando execute_query() directamente
- Ambos funcionan simultáneamente
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, Select, Update, Delete, Insert
from sqlalchemy.sql import ClauseElement, TextClause

from app.infrastructure.database.connection_async import (
    get_db_connection, DatabaseConnection
)
from app.core.tenant.context import get_current_client_id
from app.core.exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)


class UnitOfWork:
    """
    Unit of Work Pattern para transacciones atómicas.
    
    ✅ HÍBRIDO: Puede usarse junto con execute_query() existente.
    - Código nuevo: Usa UnitOfWork para operaciones multi-paso
    - Código viejo: Sigue usando execute_query() (sin cambios)
    
    Ejemplo:
        async with UnitOfWork(client_id=current_client_id) as uow:
            await uow.execute(calcular_totales_query)
            await uow.execute(actualizar_estado_query)
            await uow.execute(crear_asientos_query)
            # Todo se commitea o rollback juntos
    """
    
    def __init__(
        self,
        client_id: Optional[UUID] = None,
        connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
    ):
        self.client_id = client_id or self._get_client_id()
        self.connection_type = connection_type
        self.session: Optional[AsyncSession] = None
        self._committed = False
        self._rolled_back = False
    
    def _get_client_id(self) -> UUID:
        """Obtiene client_id del contexto o lanza error."""
        try:
            return get_current_client_id()
        except RuntimeError:
            raise DatabaseError(
                detail="UnitOfWork requiere client_id o contexto de tenant",
                internal_code="UOW_CLIENT_ID_REQUIRED"
            )
    
    async def __aenter__(self):
        """Inicia la transacción."""
        self.session = await get_db_connection(
            connection_type=self.connection_type,
            client_id=self.client_id
        ).__aenter__()
        logger.debug(f"[UOW] Transacción iniciada para cliente {self.client_id}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra la transacción (commit o rollback)."""
        if exc_type:
            # Error ocurrió → Rollback
            if self.session:
                await self.session.rollback()
                self._rolled_back = True
                logger.warning(
                    f"[UOW] Rollback ejecutado para cliente {self.client_id}: {exc_val}"
                )
        else:
            # Sin errores → Commit
            if self.session:
                await self.session.commit()
                self._committed = True
                logger.debug(f"[UOW] Commit ejecutado para cliente {self.client_id}")
        
        # Cerrar sesión
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def execute(
        self,
        query: Union[str, ClauseElement, TextClause],
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Ejecuta una query dentro de la transacción.
        
        Args:
            query: Query SQL (string, SQLAlchemy Core, o TextClause)
            params: Parámetros opcionales (solo para strings)
        
        Returns:
            Resultado de la ejecución (rows para SELECT, rowcount para otros)
        """
        if not self.session:
            raise DatabaseError(
                detail="UnitOfWork no está activo. Usar dentro de 'async with'",
                internal_code="UOW_NOT_ACTIVE"
            )
        
        # Convertir string a TextClause si es necesario
        if isinstance(query, str):
            if params:
                query = text(query).bindparams(**params)
            else:
                query = text(query)
        
        try:
            result = await self.session.execute(query)
            
            # Si es SELECT, retornar resultados
            if isinstance(query, (Select, TextClause)) or isinstance(query, str):
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
            
            # Para UPDATE/DELETE/INSERT, retornar rowcount
            return {"rows_affected": result.rowcount}
            
        except Exception as e:
            logger.error(f"[UOW] Error ejecutando query: {e}")
            raise DatabaseError(
                detail=f"Error en UnitOfWork: {str(e)}",
                internal_code="UOW_EXECUTION_ERROR"
            )
    
    def is_committed(self) -> bool:
        """Verifica si la transacción fue commiteada."""
        return self._committed
    
    def is_rolled_back(self) -> bool:
        """Verifica si la transacción fue revertida."""
        return self._rolled_back
```

**Safety Net:**
- ✅ Código nuevo, no modifica existente
- ✅ Feature flag: `ENABLE_UNIT_OF_WORK` (default: True)
- ✅ Tests unitarios completos antes de usar en producción

**Validación:**
```python
# tests/unit/test_unit_of_work.py
async def test_uow_commit():
    async with UnitOfWork(client_id=test_client_id) as uow:
        result = await uow.execute("SELECT 1 as test")
        assert result[0]["test"] == 1
    assert uow.is_committed()

async def test_uow_rollback():
    try:
        async with UnitOfWork(client_id=test_client_id) as uow:
            await uow.execute("SELECT 1")
            raise ValueError("Test error")
    except ValueError:
        pass
    assert uow.is_rolled_back()
```

---

#### 1.2 Crear Adapter para Repositorios Existentes
**Archivos Creados:**
- `app/infrastructure/database/repositories/uow_adapter.py` (NUEVO)

**Propósito:**
Permite que repositorios existentes usen UnitOfWork opcionalmente sin romper código.

**Implementación:**
```python
# app/infrastructure/database/repositories/uow_adapter.py
"""
Adapter para permitir que BaseRepository use UnitOfWork opcionalmente.

✅ HÍBRIDO: Repositorios pueden usar UOW o seguir como antes.
"""

from typing import Optional
from uuid import UUID
from app.core.application.unit_of_work import UnitOfWork
from app.infrastructure.database.connection_async import DatabaseConnection

class RepositoryUOWAdapter:
    """
    Adapter que permite a repositorios usar UnitOfWork sin cambios.
    """
    
    @staticmethod
    async def execute_with_uow(
        query,
        client_id: Optional[UUID] = None,
        connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
        use_uow: bool = False
    ):
        """
        Ejecuta query con o sin UnitOfWork según flag.
        
        ✅ HÍBRIDO: Si use_uow=False, usa execute_query() normal (comportamiento actual)
        """
        if use_uow:
            async with UnitOfWork(client_id=client_id, connection_type=connection_type) as uow:
                return await uow.execute(query)
        else:
            # Comportamiento actual (sin cambios)
            from app.infrastructure.database.queries_async import execute_query
            return await execute_query(query, client_id=client_id, connection_type=connection_type)
```

**Safety Net:**
- ✅ Por defecto `use_uow=False` (comportamiento actual)
- ✅ Código existente no necesita cambios
- ✅ Migración gradual módulo por módulo

---

#### 1.3 Actualizar BaseRepository (Opcional, Híbrido)
**Archivos Modificados:**
- `app/infrastructure/database/repositories/base_repository.py`

**Cambios (HÍBRIDOS):**
```python
# Agregar método opcional que usa UOW
class BaseRepository(ABC, Generic[T]):
    # ... código existente sin cambios ...
    
    async def create_with_uow(
        self,
        data: Dict[str, Any],
        client_id: Optional[UUID] = None,
        uow: Optional[UnitOfWork] = None
    ) -> Dict[str, Any]:
        """
        ✅ NUEVO: Versión que acepta UnitOfWork externo.
        Si uow=None, usa comportamiento actual (sin cambios).
        """
        if uow:
            # Usar UOW proporcionado (nuevo código)
            query = insert(table).values(**data)
            return await uow.execute(query)
        else:
            # Comportamiento actual (sin cambios)
            return await self.create(data, client_id)
```

**Safety Net:**
- ✅ Método nuevo (`create_with_uow`), no modifica `create()` existente
- ✅ Código existente sigue funcionando igual
- ✅ Migración gradual

---

#### 1.4 Ejemplo de Uso en Servicio Nuevo
**Archivos Creados (EJEMPLO, no afecta producción):**
- `app/modules/planillas/application/services/planilla_service.py` (ejemplo)

**Implementación de Ejemplo:**
```python
# Ejemplo de cómo usar UnitOfWork en módulos nuevos
from app.core.application.unit_of_work import UnitOfWork

class PlanillaService(BaseService):
    @staticmethod
    @BaseService.handle_service_errors
    async def cerrar_planilla(planilla_id: UUID, client_id: UUID):
        """Ejemplo de uso de UnitOfWork para operación atómica."""
        async with UnitOfWork(client_id=client_id) as uow:
            # Paso 1: Calcular totales
            await uow.execute(calcular_totales_query, {"planilla_id": planilla_id})
            
            # Paso 2: Actualizar estado
            await uow.execute(actualizar_estado_query, {"planilla_id": planilla_id})
            
            # Paso 3: Generar asientos
            await uow.execute(crear_asientos_query, {"planilla_id": planilla_id})
            
            # Si cualquier paso falla, todo se revierte automáticamente
```

**Safety Net:**
- ✅ Solo ejemplo, no afecta código existente
- ✅ Documentación para desarrolladores

---

### ✅ Criterios de Éxito FASE 1
- [ ] UnitOfWork implementado y testeado
- [ ] Adapter creado (opcional)
- [ ] Tests unitarios pasando 100%
- [ ] Código existente sigue funcionando (zero breaking changes)
- [ ] Documentación completa
- [ ] Feature flag funcionando

---

## 🔧 FASE 2: REFACTORIZAR SQL CONSTANTS A ESTRUCTURA MODULAR
**Duración:** 5-6 días  
**Riesgo:** 🟡 MEDIO (migración de imports)  
**Breaking Changes:** ❌ NINGUNO (adapters de compatibilidad)

### Objetivo
Dividir `sql_constants.py` monolítico en módulos por dominio, manteniendo compatibilidad.

### Análisis de Dependencias

**Archivos que importan `sql_constants.py`:**
1. `app/modules/auth/application/services/auth_service.py`
2. `app/modules/auth/application/services/refresh_token_service.py`
3. `app/modules/users/application/services/user_service.py`
4. `app/modules/rbac/application/services/rol_service.py`
5. `app/modules/menus/application/services/area_service.py`
6. `app/modules/menus/application/services/menu_service.py`
7. `app/modules/superadmin/application/services/audit_service.py`
8. `app/infrastructure/database/query_helpers.py`
9. `app/api/deps_backup.py`

**Orden de Migración (basado en dependencias):**
1. **auth** (base, otros dependen de él)
2. **users** (depende de auth)
3. **rbac** (depende de users)
4. **menus** (independiente)
5. **audit** (depende de auth)
6. **query_helpers** (último, usa todo)

---

### Tareas

#### 2.1 Mover Queries de Auth a Módulo Dedicado
**Archivos Creados:**
- `app/infrastructure/database/queries/auth/auth_queries.py` (NUEVO)

**Archivos Modificados:**
- `app/infrastructure/database/sql_constants.py` (mantener como deprecado)

**Estrategia Híbrida:**
```python
# app/infrastructure/database/queries/auth/auth_queries.py
"""
Queries de autenticación y usuarios.

✅ FASE 2: Migrado desde sql_constants.py
"""

# Mover queries relacionadas con auth
GET_USER_ACCESS_LEVEL_INFO_COMPLETE = """
SELECT 
    ISNULL(MAX(r.nivel_acceso), 1) as max_level,
    ...
"""

# ... resto de queries de auth ...

# app/infrastructure/database/queries/__init__.py
"""
✅ HÍBRIDO: Re-exporta para compatibilidad con imports existentes.
"""

# Re-exportar desde módulos nuevos
from .auth.auth_queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    # ... resto ...
)

# También mantener compatibilidad con sql_constants.py
from app.infrastructure.database.sql_constants import (
    # Queries que aún no se migraron
    SELECT_ROLES_PAGINATED,
    # ...
)
```

**Migración Gradual:**
```python
# app/modules/auth/application/services/auth_service.py

# ANTES:
from app.infrastructure.database.sql_constants import GET_USER_ACCESS_LEVEL_INFO_COMPLETE

# DESPUÉS (HÍBRIDO - ambos funcionan):
from app.infrastructure.database.queries.auth.auth_queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE
)

# O mantener import antiguo temporalmente (compatibilidad)
# from app.infrastructure.database.sql_constants import GET_USER_ACCESS_LEVEL_INFO_COMPLETE
```

**Safety Net:**
- ✅ `sql_constants.py` mantiene re-exports durante migración
- ✅ Ambos imports funcionan simultáneamente
- ✅ Deprecation warnings en `sql_constants.py`
- ✅ Tests de integración validan que ambos funcionan

**Validación:**
```python
# tests/integration/test_query_imports.py
def test_old_import_still_works():
    """Verificar que imports antiguos siguen funcionando."""
    from app.infrastructure.database.sql_constants import GET_USER_ACCESS_LEVEL_INFO_COMPLETE
    assert GET_USER_ACCESS_LEVEL_INFO_COMPLETE is not None

def test_new_import_works():
    """Verificar que imports nuevos funcionan."""
    from app.infrastructure.database.queries.auth.auth_queries import (
        GET_USER_ACCESS_LEVEL_INFO_COMPLETE
    )
    assert GET_USER_ACCESS_LEVEL_INFO_COMPLETE is not None
```

---

#### 2.2 Migrar Módulo por Módulo (Mismo Patrón)

**Orden de Migración:**
1. ✅ **auth** (FASE 2.1)
2. ✅ **users** (depende de auth)
3. ✅ **rbac** (depende de users)
4. ✅ **menus** (independiente)
5. ✅ **audit** (depende de auth)
6. ✅ **query_helpers** (último)

**Patrón Repetitivo:**
```python
# Para cada módulo:
# 1. Crear archivo en queries/{modulo}/{modulo}_queries.py
# 2. Mover queries desde sql_constants.py
# 3. Actualizar __init__.py para re-exportar
# 4. Migrar imports en servicios (opcional, ambos funcionan)
# 5. Agregar deprecation warning en sql_constants.py
```

---

#### 2.3 Marcar sql_constants.py como Deprecated
**Archivos Modificados:**
- `app/infrastructure/database/sql_constants.py`

**Cambios:**
```python
# app/infrastructure/database/sql_constants.py
"""
⚠️ DEPRECATED: Este archivo está siendo refactorizado.

✅ FASE 2: Migrar a app/infrastructure/database/queries/{modulo}/{modulo}_queries.py

IMPORTS DEPRECADOS (mantener por compatibilidad):
- GET_USER_ACCESS_LEVEL_INFO_COMPLETE → queries.auth.auth_queries
- SELECT_USUARIOS_PAGINATED → queries.users.user_queries
- SELECT_ROLES_PAGINATED → queries.rbac.rbac_queries
- ...

Este archivo será eliminado en FASE 3.
"""

import warnings

# Re-exportar desde módulos nuevos (compatibilidad)
from app.infrastructure.database.queries.auth.auth_queries import (
    GET_USER_ACCESS_LEVEL_INFO_COMPLETE,
    # ...
)

# Deprecation warning
warnings.warn(
    "sql_constants.py está deprecated. "
    "Usar app.infrastructure.database.queries.{modulo}.{modulo}_queries en su lugar.",
    DeprecationWarning,
    stacklevel=2
)
```

**Safety Net:**
- ✅ Warnings no rompen código, solo alertan
- ✅ Re-exports mantienen compatibilidad
- ✅ Eliminación gradual en FASE 3

---

#### 2.4 Actualizar Documentación
**Archivos Creados:**
- `docs/MIGRACION_QUERIES.md`

**Contenido:**
- Guía de migración para desarrolladores
- Mapeo de queries antiguas → nuevas
- Ejemplos de uso

---

### ✅ Criterios de Éxito FASE 2
- [ ] Todos los módulos migrados a estructura modular
- [ ] Imports antiguos siguen funcionando (compatibilidad)
- [ ] Tests de integración pasando 100%
- [ ] Deprecation warnings activos
- [ ] Documentación actualizada
- [ ] Zero breaking changes confirmado

---

## 🔧 FASE 3: OPTIMIZAR CONNECTION POOL Y ELIMINAR CÓDIGO DEPRECADO
**Duración:** 3-4 días  
**Riesgo:** 🟡 BAJO (solo limpieza)  
**Breaking Changes:** ❌ NINGUNO (solo eliminar deprecated)

### Objetivo
Eliminar código deprecated y optimizar pools con estructura modular.

### Tareas

#### 3.1 Eliminar sql_constants.py (Después de Migración Completa)
**Archivos Eliminados:**
- `app/infrastructure/database/sql_constants.py`

**Pre-requisitos:**
- ✅ Todos los imports migrados a estructura modular
- ✅ Tests pasando 100%
- ✅ Deprecation warnings activos por 2 semanas mínimo

**Safety Net:**
- ✅ Verificar que ningún import use `sql_constants.py`
- ✅ Script de validación antes de eliminar:
```python
# scripts/validate_no_sql_constants_imports.py
import ast
import os

def find_sql_constants_imports():
    """Busca imports de sql_constants.py en todo el código."""
    imports_found = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path) as f:
                    content = f.read()
                    if "sql_constants" in content:
                        imports_found.append(path)
    return imports_found

if __name__ == "__main__":
    imports = find_sql_constants_imports()
    if imports:
        print("❌ Imports de sql_constants.py encontrados:")
        for imp in imports:
            print(f"  - {imp}")
        exit(1)
    else:
        print("✅ No se encontraron imports de sql_constants.py")
```

---

#### 3.2 Optimizar Connection Pool con Estructura Modular
**Archivos Modificados:**
- `app/infrastructure/database/connection_pool.py`

**Mejoras:**
```python
# Agregar pools por módulo (opcional, para optimización futura)
MODULE_POOLS = {
    "auth": {"size": 5, "max_overflow": 3},
    "planillas": {"size": 10, "max_overflow": 5},  # Más grande para módulo crítico
    "logistica": {"size": 8, "max_overflow": 4},
}

def _get_pool_for_module(module_name: str, client_id: int) -> Any:
    """
    ✅ NUEVO: Pool específico por módulo (optimización futura).
    Por ahora, usa pool general pero preparado para especialización.
    """
    # Por ahora, usar pool general
    # En el futuro, pools especializados por módulo
    return _get_pool_for_tenant(client_id, connection_string)
```

**Safety Net:**
- ✅ Cambios opcionales, no afectan comportamiento actual
- ✅ Feature flag para activar pools por módulo

---

#### 3.3 Limpiar Código Deprecated
**Archivos Modificados:**
- Eliminar adapters temporales si ya no se usan
- Limpiar comentarios de migración
- Actualizar documentación

---

### ✅ Criterios de Éxito FASE 3
- [ ] `sql_constants.py` eliminado (o marcado para eliminación)
- [ ] Todos los imports usan estructura modular
- [ ] Connection pool optimizado
- [ ] Código deprecated eliminado
- [ ] Tests pasando 100%
- [ ] Documentación final actualizada

---

## 📊 RESUMEN DE FASES

| Fase | Duración | Riesgo | Breaking Changes | Dependencias |
|------|----------|--------|------------------|--------------|
| **FASE 0** | 2 días | ⚪ MUY BAJO | ❌ NINGUNO | Ninguna |
| **FASE 1** | 4-5 días | 🟡 BAJO | ❌ NINGUNO | FASE 0 |
| **FASE 2** | 5-6 días | 🟡 MEDIO | ❌ NINGUNO | FASE 1 |
| **FASE 3** | 3-4 días | 🟡 BAJO | ❌ NINGUNO | FASE 2 |
| **TOTAL** | **14-17 días** | | | |

---

## 🎯 OBJETIVO FINAL: 9/10

### Métricas de Éxito

| Métrica | Antes | Después | Objetivo |
|---------|-------|---------|----------|
| **Mantenibilidad** | 3.0/10 | 9.0/10 | ✅ |
| **Seguridad** | 6.0/10 | 9.0/10 | ✅ |
| **Escalabilidad** | 4.0/10 | 9.0/10 | ✅ |
| **Robustez** | 4.5/10 | 9.0/10 | ✅ |

### Validación Final

1. **Tests de Integración:** 100% pasando
2. **Performance:** Igual o mejor que antes
3. **Breaking Changes:** Zero confirmado
4. **Documentación:** Completa y actualizada
5. **Code Review:** Aprobado por arquitecto

---

## 🚨 PLAN DE ROLLBACK POR FASE

### Rollback FASE 0
- **Tiempo:** < 5 minutos
- **Acción:** Revertir variables de entorno a valores anteriores
- **Script:** `scripts/rollback_phase0.sh`

### Rollback FASE 1
- **Tiempo:** < 10 minutos
- **Acción:** Desactivar feature flag `ENABLE_UNIT_OF_WORK=False`
- **Script:** `scripts/rollback_phase1.sh`

### Rollback FASE 2
- **Tiempo:** < 15 minutos
- **Acción:** Re-activar imports desde `sql_constants.py`
- **Script:** `scripts/rollback_phase2.sh`

### Rollback FASE 3
- **Tiempo:** < 10 minutos
- **Acción:** Re-crear `sql_constants.py` desde backup
- **Script:** `scripts/rollback_phase3.sh`

---

## 📝 CHECKLIST DE VALIDACIÓN POR FASE

### Antes de Iniciar Cualquier Fase
- [ ] Tests de baseline pasando 100%
- [ ] Backup de código y BD
- [ ] Feature flags configurados
- [ ] Plan de rollback documentado
- [ ] Equipo notificado

### Durante Cada Fase
- [ ] Tests pasando después de cada cambio
- [ ] Code review completado
- [ ] Documentación actualizada
- [ ] Monitoreo activo

### Después de Cada Fase
- [ ] Tests de integración pasando 100%
- [ ] Performance validada
- [ ] Zero breaking changes confirmado
- [ ] Documentación actualizada
- [ ] Retrospectiva realizada

---

**Firma del Arquitecto:**  
*Senior Software Architect*  
*Diciembre 2024*
