# ✅ FASE 3 COMPLETADA: Validación de `menu_id` en BD Dedicada

**Fecha:** 16 de Febrero, 2026  
**Objetivo:** Prevenir datos huérfanos en BD dedicadas donde `menu_id` referencia `modulo_menu` en BD central.

---

## 📋 Resumen de Cambios

### 1. Nuevo Servicio: `MenuValidationService`

**Archivo:** `app/modules/rbac/application/services/menu_validation_service.py`

**Funcionalidad:**
- ✅ Valida que `menu_id` existe en BD central usando conexión ADMIN
- ✅ Verifica que el menú esté activo (`es_activo = 1`)
- ✅ Valida ownership del menú (pertenece al cliente o es global)
- ✅ Soporta validación individual y en batch (múltiples `menu_id`)

**Métodos principales:**
- `validate_menu_exists_in_central()`: Valida un solo menú
- `validate_multiple_menus()`: Valida múltiples menús en batch (eficiente)

**Características:**
- Usa `DatabaseConnection.ADMIN` para consultar BD central
- Manejo robusto de errores (`NotFoundError`, `ValidationError`)
- Logging detallado para auditoría
- Soporte para menús globales (`cliente_id = NULL`)

---

### 2. Integración en `PermisoService._validar_rol_y_menu()`

**Archivo:** `app/modules/rbac/application/services/permiso_service.py`

**Cambios:**
- ✅ Detecta tipo de BD usando `get_tenant_context().is_multi_db()`
- ✅ **BD Dedicada:** Usa `MenuValidationService` para validar en BD central
- ✅ **BD Central:** Mantiene validación local usando `ModuloMenuService`

**Código modificado:**
```python
# ✅ FASE 3: Validación mejorada para BD dedicadas
from app.core.tenant.context import get_tenant_context
from app.modules.rbac.application.services.menu_validation_service import MenuValidationService

tenant_context = get_tenant_context()

if tenant_context.is_multi_db():
    # BD dedicada: menu_id debe existir en BD central
    await MenuValidationService.validate_menu_exists_in_central(
        menu_id=menu_id,
        cliente_id=cliente_id,
        allow_global=True
    )
else:
    # BD central: validación local usando ModuloMenuService
    menu = await ModuloMenuService.obtener_menu_por_id(menu_id)
    # ... validación local ...
```

**Líneas afectadas:** ~122-137

---

### 3. Integración en `RolService.actualizar_permisos_rol()`

**Archivo:** `app/modules/rbac/application/services/rol_service.py`

**Cambios:**
- ✅ Reemplaza query local que consultaba `ModuloMenuTable` con `client_id=cliente_id` (incorrecto para BD dedicadas)
- ✅ **BD Dedicada:** Usa `MenuValidationService.validate_multiple_menus()` para validación en batch
- ✅ **BD Central:** Mantiene validación local pero usa `DatabaseConnection.ADMIN` explícitamente

**Problema corregido:**
- **ANTES:** Query consultaba `ModuloMenuTable` con `client_id=cliente_id`, lo cual fallaría en BD dedicadas porque `ModuloMenuTable` está en BD central.
- **DESPUÉS:** Detecta tipo de BD y usa validación apropiada (central para dedicadas, local para central).

**Código modificado:**
```python
# ✅ FASE 3: Detectar tipo de BD y usar validación apropiada
tenant_context = get_tenant_context()

if tenant_context.is_multi_db():
    # BD dedicada: validar en batch en BD central
    valid_menus = await MenuValidationService.validate_multiple_menus(
        menu_ids=menu_ids,
        cliente_id=cliente_id,
        allow_global=True
    )
else:
    # BD central: validación local con conexión ADMIN explícita
    menus_query = select(ModuloMenuTable.c.menu_id, ModuloMenuTable.c.cliente_id)
    menus_result = await execute_query(
        menus_query, 
        connection_type=DatabaseConnection.ADMIN,
        client_id=None
    )
    # ... validación local ...
```

**Líneas afectadas:** ~1120-1155

---

## 🔍 Verificaciones Realizadas

### ✅ Linter
- Sin errores de sintaxis
- Imports correctos
- Tipos correctos

### ✅ Arquitectura
- Detección correcta de tipo de BD (`is_multi_db()`)
- Uso correcto de `DatabaseConnection.ADMIN` para BD central
- Validación cross-database implementada correctamente

### ✅ Manejo de Errores
- `NotFoundError` cuando menú no existe
- `ValidationError` cuando menú no pertenece al cliente o está inactivo
- Logging detallado para debugging

---

## 🎯 Beneficios

1. **Prevención de Datos Huérfanos:**
   - En BD dedicadas, `menu_id` en `rol_menu_permiso` ahora se valida contra BD central
   - Previene referencias a menús inexistentes o de otros clientes

2. **Validación Eficiente:**
   - Validación en batch para múltiples menús (evita N+1 queries)
   - Reutilización de conexión ADMIN para BD central

3. **Compatibilidad:**
   - Funciona tanto para BD central como BD dedicadas
   - Mantiene comportamiento existente para BD central
   - No rompe código existente

4. **Auditoría:**
   - Logging detallado de todas las validaciones
   - Errores claros y específicos

---

## 📝 Próximos Pasos

### Testing Recomendado

1. **BD Central:**
   - ✅ Verificar que validación local sigue funcionando
   - ✅ Probar asignación de permisos con menús válidos
   - ✅ Probar rechazo de menús inexistentes o de otro cliente

2. **BD Dedicada:**
   - ✅ Verificar que validación consulta BD central correctamente
   - ✅ Probar asignación de permisos con menús válidos (globales y específicos)
   - ✅ Probar rechazo de menús inexistentes o de otro cliente
   - ✅ Probar rechazo de menús inactivos

3. **Validación en Batch:**
   - ✅ Probar `actualizar_permisos_rol()` con múltiples permisos
   - ✅ Verificar que todos los menús se validan correctamente
   - ✅ Verificar que errores se reportan claramente

### Casos de Prueba Sugeridos

```python
# Test 1: BD Dedicada - Menú válido del cliente
# Test 2: BD Dedicada - Menú global válido
# Test 3: BD Dedicada - Menú inexistente (debe fallar)
# Test 4: BD Dedicada - Menú de otro cliente (debe fallar)
# Test 5: BD Dedicada - Menú inactivo (debe fallar)
# Test 6: BD Central - Validación local sigue funcionando
# Test 7: Batch - Múltiples menús válidos
# Test 8: Batch - Uno inválido entre varios válidos (debe fallar)
```

---

## 📚 Archivos Modificados

1. ✅ `app/modules/rbac/application/services/menu_validation_service.py` (NUEVO)
2. ✅ `app/modules/rbac/application/services/permiso_service.py` (MODIFICADO)
3. ✅ `app/modules/rbac/application/services/rol_service.py` (MODIFICADO)

---

## ✅ Estado de la Fase 3

- [x] Crear servicio `MenuValidationService`
- [x] Integrar validación en `PermisoService._validar_rol_y_menu`
- [x] Integrar validación en `RolService.actualizar_permisos_rol`
- [x] Verificar código (linter, imports, tipos)
- [ ] **Pendiente:** Testing manual/integration tests

---

## 🔗 Referencias

- **Plan de Trabajo:** `PLAN_TRABAJO_CORRECCIONES_CRITICAS.md` - Fase 3
- **Auditoría Original:** `AUDITORIA_TECNICA_COMPLETA_2025.md` - Riesgo: "Validación de `menu_id` en BD Dedicada"
- **Fase 1:** `FASE1_COMPLETADA.md`
- **Fase 2:** `FASE2_COMPLETADA.md`

---

**Fase 3 completada exitosamente.** ✅  
**Lista para testing y validación en entorno de desarrollo.**
