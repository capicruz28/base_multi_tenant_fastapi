# 📋 PLAN DE REFACTORIZACIÓN: Sistema de Módulos y Menús

## 📊 RESUMEN EJECUTIVO

Este documento detalla el plan completo para refactorizar el sistema de gestión de módulos y menús, migrando de la estructura antigua a la nueva arquitectura basada en la estructura de BD definida en `estructura_bd.sql`.

**Alcance**: Refactorización completa del módulo de menús y módulos ERP, manteniendo compatibilidad con la arquitectura multi-tenant híbrida.

**Estado**: ⏳ PENDIENTE DE APROBACIÓN

---

## 🔍 ANÁLISIS DE LA ESTRUCTURA ACTUAL VS NUEVA

### **Mapeo de Tablas**

| ❌ Tabla Antigua | ✅ Tabla Nueva | 📝 Cambios Principales |
|-----------------|---------------|----------------------|
| `cliente_modulo` (catálogo) | `modulo` | **Renombrada** - Ahora es catálogo global de módulos ERP. Campos nuevos: `categoria`, `precio_mensual`, `modulos_requeridos` (JSON), `configuracion_defecto` (JSON) |
| `cliente_modulo_activo` | `cliente_modulo` | **Renombrada** - Representa módulos contratados por cliente. Campos nuevos: `modo_prueba`, `fecha_fin_prueba`, `limite_transacciones_mes`, `activado_por_usuario_id` |
| `area_menu` | `modulo_seccion` | **Reemplazada** - Secciones pertenecen directamente a módulos. Campos nuevos: `modulo_id` (FK obligatoria), `codigo` (único por módulo), `es_seccion_sistema` |
| `menu` | `modulo_menu` | **Renombrada** - Menús pertenecen a módulos (FK obligatoria). Campos nuevos: `modulo_id` (FK obligatoria), `seccion_id` (FK opcional), `codigo`, `nivel`, `tipo_menu`, `es_visible`, `configuracion_json` |
| N/A | `modulo_rol_plantilla` | **NUEVA** - Plantillas de roles que se aplican al activar módulo. Campos: `modulo_id`, `nombre_rol`, `descripcion`, `nivel_acceso`, `permisos_json` |

### **Relaciones Clave (Nueva Estructura)**

```
modulo (1) ──→ (N) modulo_seccion
modulo (1) ──→ (N) modulo_menu
modulo (1) ──→ (N) modulo_rol_plantilla
modulo (1) ──→ (N) cliente_modulo (contrataciones)

modulo_seccion (1) ──→ (N) modulo_menu

cliente (1) ──→ (N) cliente_modulo
modulo (1) ──→ (N) cliente_modulo

modulo_menu (1) ──→ (N) rol_menu_permiso
```

---

## 📁 ARCHIVOS A CREAR/MODIFICAR/ELIMINAR

### ✅ **ARCHIVOS A CREAR**

#### **1. Tablas SQLAlchemy Core (Nuevas)**
- `app/infrastructure/database/tables_modulos.py` - Tablas nuevas:
  - `ModuloTable` (reemplaza `ClienteModuloTable`)
  - `ModuloSeccionTable` (reemplaza `AreaMenuTable`)
  - `ModuloMenuTable` (reemplaza `MenuTable`)
  - `ModuloRolPlantillaTable` (nueva)

#### **2. Schemas Pydantic (Nuevos)**
- `app/modules/modulos/presentation/schemas.py` - Schemas para:
  - `ModuloCreate`, `ModuloUpdate`, `ModuloRead`
  - `ModuloSeccionCreate`, `ModuloSeccionUpdate`, `ModuloSeccionRead`
  - `ModuloMenuCreate`, `ModuloMenuUpdate`, `ModuloMenuRead`
  - `ModuloRolPlantillaCreate`, `ModuloRolPlantillaUpdate`, `ModuloRolPlantillaRead`
  - `ClienteModuloCreate`, `ClienteModuloUpdate`, `ClienteModuloRead`

#### **3. Servicios (Nuevos)**
- `app/modules/modulos/application/services/modulo_service.py` - CRUD completo de módulos
- `app/modules/modulos/application/services/modulo_seccion_service.py` - CRUD completo de secciones
- `app/modules/modulos/application/services/modulo_menu_service.py` - CRUD completo de menús
- `app/modules/modulos/application/services/cliente_modulo_service.py` - Gestión de activación de módulos
- `app/modules/modulos/application/services/modulo_rol_plantilla_service.py` - Gestión de plantillas de roles

#### **4. Endpoints (Nuevos)**
- `app/modules/modulos/presentation/endpoints_modulos.py` - Endpoints CRUD módulos
- `app/modules/modulos/presentation/endpoints_secciones.py` - Endpoints CRUD secciones
- `app/modules/modulos/presentation/endpoints_menus.py` - Endpoints CRUD menús
- `app/modules/modulos/presentation/endpoints_cliente_modulo.py` - Endpoints activación/desactivación
- `app/modules/modulos/presentation/endpoints_rol_plantilla.py` - Endpoints plantillas de roles
- `app/modules/modulos/presentation/endpoints_menu_usuario.py` - Endpoint para obtener menú del usuario (usa SP)

#### **5. Helpers/Utils (Nuevos)**
- `app/modules/modulos/application/helpers/menu_transformer.py` - Transformar resultado SP a JSON jerárquico
- `app/modules/modulos/application/helpers/rol_plantilla_applier.py` - Aplicar plantillas de roles al activar módulo

#### **6. Dependencies (Nuevos)**
- `app/modules/modulos/presentation/dependencies.py` - Dependencies específicas:
  - `validar_acceso_menu_dep` - Usa `sp_validar_acceso_menu`

---

### 🔄 **ARCHIVOS A MODIFICAR**

#### **1. Tablas SQLAlchemy Core**
- `app/infrastructure/database/tables.py`:
  - ❌ Eliminar: `ClienteModuloTable`, `ClienteModuloActivoTable`, `AreaMenuTable`, `MenuTable`
  - ✅ Agregar imports de nuevas tablas desde `tables_modulos.py`
  - ✅ Actualizar `RolMenuPermisoTable`: Cambiar FK de `menu.menu_id` a `modulo_menu.menu_id`

#### **2. Servicios Existentes**
- `app/modules/tenant/application/services/modulo_service.py`:
  - ✅ Actualizar queries para usar tabla `modulo` (antes `cliente_modulo`)
  - ✅ Agregar validación de dependencias entre módulos
  - ✅ Agregar métodos para validar JSON de `modulos_requeridos` y `configuracion_defecto`

- `app/modules/tenant/application/services/modulo_activo_service.py`:
  - ✅ Renombrar a `cliente_modulo_service.py`
  - ✅ Actualizar queries para usar tabla `cliente_modulo` (antes `cliente_modulo_activo`)
  - ✅ **CRÍTICO**: Agregar lógica de aplicación automática de plantillas de roles al activar módulo

- `app/modules/rbac/application/services/permiso_service.py`:
  - ✅ Actualizar queries para usar `modulo_menu` (antes `menu`)
  - ✅ Actualizar validaciones de existencia de menú

- `app/modules/rbac/application/services/rol_service.py`:
  - ✅ Actualizar queries que referencian `menu` a `modulo_menu`

#### **3. Endpoints Existentes**
- `app/modules/tenant/presentation/endpoints_modulos.py`:
  - ✅ Actualizar para usar nuevos servicios
  - ✅ Agregar endpoints faltantes según especificación

- `app/modules/menus/presentation/endpoints.py`:
  - ❌ **ELIMINAR** - Reemplazado por nuevos endpoints en módulo `modulos`

- `app/modules/menus/presentation/endpoints_areas.py`:
  - ❌ **ELIMINAR** - Reemplazado por endpoints de secciones

#### **4. Schemas Existentes**
- `app/modules/tenant/presentation/schemas.py`:
  - ✅ Actualizar schemas de módulos para nueva estructura
  - ✅ Agregar schemas para secciones, menús y plantillas

- `app/modules/menus/presentation/schemas.py`:
  - ❌ **ELIMINAR** - Reemplazado por schemas en módulo `modulos`

#### **5. API Router**
- `app/api/v1/api.py`:
  - ✅ Agregar routers de nuevos endpoints
  - ❌ Eliminar routers de menús antiguos

#### **6. Queries SQL**
- `app/infrastructure/database/queries.py`:
  - ✅ Actualizar queries que usan tablas antiguas
  - ✅ Agregar queries para nuevas tablas

---

### ❌ **ARCHIVOS A ELIMINAR**

1. `app/modules/menus/` - **Módulo completo** (reemplazado por `modulos`)
2. `app/modules/tenant/application/services/modulo_activo_service.py` - Renombrado a `cliente_modulo_service.py`

---

## 🔗 MAPA DE DEPENDENCIAS

### **Flujo de Datos (Nuevo)**

```
Frontend Request
    ↓
Endpoints (presentation/)
    ↓
Services (application/services/)
    ↓
SQLAlchemy Core Tables (infrastructure/database/)
    ↓
Database (SQL Server)
```

### **Dependencias entre Módulos**

```
modulos/
├── presentation/
│   ├── endpoints_modulos.py → modulo_service.py
│   ├── endpoints_secciones.py → modulo_seccion_service.py
│   ├── endpoints_menus.py → modulo_menu_service.py
│   ├── endpoints_cliente_modulo.py → cliente_modulo_service.py
│   ├── endpoints_rol_plantilla.py → modulo_rol_plantilla_service.py
│   └── endpoints_menu_usuario.py → modulo_menu_service.py (usa SP)
│
├── application/
│   ├── services/
│   │   ├── modulo_service.py → tables_modulos.py
│   │   ├── modulo_seccion_service.py → tables_modulos.py, modulo_service.py
│   │   ├── modulo_menu_service.py → tables_modulos.py, modulo_seccion_service.py
│   │   ├── cliente_modulo_service.py → tables_modulos.py, modulo_service.py, modulo_rol_plantilla_service.py
│   │   └── modulo_rol_plantilla_service.py → tables_modulos.py, modulo_menu_service.py
│   │
│   └── helpers/
│       ├── menu_transformer.py → (transforma resultado SP)
│       └── rol_plantilla_applier.py → modulo_rol_plantilla_service.py, rol_service.py
│
└── infrastructure/
    └── (no repositories, usa SQLAlchemy Core directamente)

rbac/
└── application/services/
    ├── permiso_service.py → modulo_menu_service.py (validaciones)
    └── rol_service.py → modulo_menu_service.py (validaciones)
```

---

## 🚀 PLAN DE EJECUCIÓN PASO A PASO

### **FASE 1: Preparación y Estructura Base** ⏱️ ~2-3 horas

#### **1.1 Crear Nuevas Tablas SQLAlchemy Core**
- [ ] Crear `app/infrastructure/database/tables_modulos.py`
- [ ] Definir `ModuloTable` (mapeo completo de tabla `modulo`)
- [ ] Definir `ModuloSeccionTable` (mapeo completo de tabla `modulo_seccion`)
- [ ] Definir `ModuloMenuTable` (mapeo completo de tabla `modulo_menu`)
- [ ] Definir `ModuloRolPlantillaTable` (mapeo completo de tabla `modulo_rol_plantilla`)
- [ ] Actualizar `ClienteModuloTable` en `tables.py` (renombrar de `ClienteModuloActivoTable`)
- [ ] Actualizar `RolMenuPermisoTable`: Cambiar FK a `modulo_menu.menu_id`

#### **1.2 Crear Estructura de Módulo `modulos`**
- [ ] Crear directorio `app/modules/modulos/`
- [ ] Crear subdirectorios: `presentation/`, `application/services/`, `application/helpers/`
- [ ] Crear `__init__.py` en cada directorio

---

### **FASE 2: Schemas y Validaciones** ⏱️ ~2-3 horas

#### **2.1 Crear Schemas Pydantic**
- [ ] Crear `app/modules/modulos/presentation/schemas.py`
- [ ] Definir schemas para `Modulo` (Create, Update, Read)
- [ ] Definir schemas para `ModuloSeccion` (Create, Update, Read)
- [ ] Definir schemas para `ModuloMenu` (Create, Update, Read)
- [ ] Definir schemas para `ModuloRolPlantilla` (Create, Update, Read)
- [ ] Definir schemas para `ClienteModulo` (Create, Update, Read)
- [ ] Agregar validadores para JSON (modulos_requeridos, permisos_json, configuracion_defecto)
- [ ] Agregar validadores para códigos únicos

---

### **FASE 3: Servicios Core** ⏱️ ~6-8 horas

#### **3.1 Servicio de Módulos**
- [ ] Crear `modulo_service.py`
- [ ] Implementar `crear_modulo()` - Con validación de código único
- [ ] Implementar `obtener_modulos()` - Con filtros y paginación
- [ ] Implementar `obtener_modulo_por_id()`
- [ ] Implementar `obtener_modulo_por_codigo()`
- [ ] Implementar `actualizar_modulo()` - Con validación de dependencias
- [ ] Implementar `eliminar_modulo()` - Con validación de uso
- [ ] Implementar `activar_modulo()` / `desactivar_modulo()`
- [ ] Implementar `validar_dependencias()` - Validar JSON de modulos_requeridos
- [ ] Implementar `obtener_modulos_disponibles_cliente()` - Con SQLAlchemy Core

#### **3.2 Servicio de Secciones**
- [ ] Crear `modulo_seccion_service.py`
- [ ] Implementar `crear_seccion()` - Con validación de código único por módulo
- [ ] Implementar `obtener_secciones_modulo()` - Con filtros
- [ ] Implementar `obtener_seccion_por_id()`
- [ ] Implementar `actualizar_seccion()`
- [ ] Implementar `eliminar_seccion()` - Con validación de menús asociados
- [ ] Implementar `reordenar_secciones()` - Actualizar campo `orden`
- [ ] Implementar `activar_seccion()` / `desactivar_seccion()`

#### **3.3 Servicio de Menús**
- [ ] Crear `modulo_menu_service.py`
- [ ] Implementar `crear_menu()` - Con validación de módulo_id obligatorio
- [ ] Implementar `obtener_menus_modulo()` - Con estructura jerárquica
- [ ] Implementar `obtener_menu_por_id()`
- [ ] Implementar `obtener_submenus()` - Menús hijos de un padre
- [ ] Implementar `actualizar_menu()` - Con validación de jerarquía
- [ ] Implementar `eliminar_menu()` - Con validación de submenús y permisos
- [ ] Implementar `reordenar_menus()` - Dentro de una sección
- [ ] Implementar `duplicar_menu()` - Para personalización por cliente
- [ ] Implementar `obtener_menu_usuario()` - **Usa `sp_obtener_menu_usuario`**
- [ ] Crear helper `menu_transformer.py` - Transformar resultado SP a JSON jerárquico

#### **3.4 Servicio de Cliente-Módulo (Activación)**
- [ ] Renombrar `modulo_activo_service.py` → `cliente_modulo_service.py`
- [ ] Actualizar queries para usar tabla `cliente_modulo`
- [ ] Implementar `activar_modulo_cliente()` - **CRÍTICO**: Aplicar plantillas de roles automáticamente
- [ ] Implementar `desactivar_modulo_cliente()`
- [ ] Implementar `obtener_modulos_activos_cliente()`
- [ ] Implementar `actualizar_configuracion()` - Configuración personalizada
- [ ] Implementar `actualizar_limites()` - Límites de uso
- [ ] Implementar `extender_vencimiento()` - Agregar días
- [ ] Implementar `validar_licencia()` - Verificar activo + no vencido
- [ ] Crear helper `rol_plantilla_applier.py` - Aplicar plantillas al activar

#### **3.5 Servicio de Plantillas de Roles**
- [ ] Crear `modulo_rol_plantilla_service.py`
- [ ] Implementar `crear_plantilla()` - Solo SUPER ADMIN
- [ ] Implementar `obtener_plantillas_modulo()`
- [ ] Implementar `obtener_plantilla_por_id()`
- [ ] Implementar `actualizar_plantilla()` - Solo SUPER ADMIN
- [ ] Implementar `eliminar_plantilla()`
- [ ] Implementar `validar_json_permisos()` - Validar estructura JSON
- [ ] Implementar `preview_aplicacion()` - Mostrar qué se creará sin ejecutar
- [ ] Implementar `aplicar_plantilla()` - Usado por `cliente_modulo_service` al activar

---

### **FASE 4: Endpoints API** ⏱️ ~4-5 horas

#### **4.1 Endpoints de Módulos**
- [ ] Crear `endpoints_modulos.py`
- [ ] `POST /api/v1/modulos` - Crear módulo (SUPER ADMIN)
- [ ] `GET /api/v1/modulos` - Listar módulos (con filtros)
- [ ] `GET /api/v1/modulos/{modulo_id}` - Obtener módulo
- [ ] `GET /api/v1/modulos/codigo/{codigo}` - Obtener por código
- [ ] `PUT /api/v1/modulos/{modulo_id}` - Actualizar módulo (SUPER ADMIN)
- [ ] `DELETE /api/v1/modulos/{modulo_id}` - Eliminar módulo (SUPER ADMIN)
- [ ] `PATCH /api/v1/modulos/{modulo_id}/activar` - Activar módulo
- [ ] `PATCH /api/v1/modulos/{modulo_id}/desactivar` - Desactivar módulo
- [ ] `GET /api/v1/modulos/{modulo_id}/dependencias` - Validar dependencias
- [ ] `GET /api/v1/modulos/disponibles/{cliente_id}` - Módulos disponibles para cliente

#### **4.2 Endpoints de Secciones**
- [ ] Crear `endpoints_secciones.py`
- [ ] `POST /api/v1/modulos/{modulo_id}/secciones` - Crear sección
- [ ] `GET /api/v1/modulos/{modulo_id}/secciones` - Listar secciones
- [ ] `GET /api/v1/secciones/{seccion_id}` - Obtener sección
- [ ] `PUT /api/v1/secciones/{seccion_id}` - Actualizar sección
- [ ] `DELETE /api/v1/secciones/{seccion_id}` - Eliminar sección
- [ ] `PATCH /api/v1/secciones/{seccion_id}/activar` - Activar sección
- [ ] `PATCH /api/v1/secciones/{seccion_id}/desactivar` - Desactivar sección
- [ ] `PUT /api/v1/modulos/{modulo_id}/secciones/reordenar` - Reordenar secciones

#### **4.3 Endpoints de Menús**
- [ ] Crear `endpoints_menus.py`
- [ ] `POST /api/v1/modulos/{modulo_id}/menus` - Crear menú
- [ ] `GET /api/v1/modulos/{modulo_id}/menus` - Listar menús (jerárquico)
- [ ] `GET /api/v1/secciones/{seccion_id}/menus` - Menús de sección
- [ ] `GET /api/v1/menus/{menu_id}` - Obtener menú
- [ ] `GET /api/v1/menus/{menu_id}/submenus` - Obtener submenús
- [ ] `PUT /api/v1/menus/{menu_id}` - Actualizar menú
- [ ] `DELETE /api/v1/menus/{menu_id}` - Eliminar menú
- [ ] `PATCH /api/v1/menus/{menu_id}/activar` - Activar menú
- [ ] `PATCH /api/v1/menus/{menu_id}/desactivar` - Desactivar menú
- [ ] `PUT /api/v1/secciones/{seccion_id}/menus/reordenar` - Reordenar menús
- [ ] `POST /api/v1/menus/{menu_id}/duplicar` - Duplicar menú

#### **4.4 Endpoints de Cliente-Módulo**
- [ ] Crear `endpoints_cliente_modulo.py`
- [ ] `POST /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/activar` - Activar módulo (SUPER ADMIN)
- [ ] `DELETE /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/desactivar` - Desactivar módulo
- [ ] `GET /api/v1/clientes/{cliente_id}/modulos` - Listar módulos activos
- [ ] `GET /api/v1/clientes/{cliente_id}/modulos/{modulo_id}` - Obtener detalle
- [ ] `PUT /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/configuracion` - Actualizar configuración
- [ ] `PUT /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/limites` - Actualizar límites
- [ ] `PATCH /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/extender-vencimiento` - Extender vencimiento
- [ ] `GET /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/validar-licencia` - Validar licencia

#### **4.5 Endpoints de Plantillas de Roles**
- [ ] Crear `endpoints_rol_plantilla.py`
- [ ] `POST /api/v1/modulos/{modulo_id}/roles-plantilla` - Crear plantilla (SUPER ADMIN)
- [ ] `GET /api/v1/modulos/{modulo_id}/roles-plantilla` - Listar plantillas
- [ ] `GET /api/v1/roles-plantilla/{plantilla_id}` - Obtener plantilla
- [ ] `PUT /api/v1/roles-plantilla/{plantilla_id}` - Actualizar plantilla (SUPER ADMIN)
- [ ] `DELETE /api/v1/roles-plantilla/{plantilla_id}` - Eliminar plantilla
- [ ] `PATCH /api/v1/roles-plantilla/{plantilla_id}/activar` - Activar plantilla
- [ ] `PATCH /api/v1/roles-plantilla/{plantilla_id}/desactivar` - Desactivar plantilla
- [ ] `PUT /api/v1/modulos/{modulo_id}/roles-plantilla/reordenar` - Reordenar plantillas
- [ ] `POST /api/v1/roles-plantilla/validar-json` - Validar JSON de permisos
- [ ] `GET /api/v1/roles-plantilla/{plantilla_id}/preview` - Preview de aplicación

#### **4.6 Endpoint de Menú de Usuario**
- [ ] Crear `endpoints_menu_usuario.py`
- [ ] `GET /api/v1/usuarios/{usuario_id}/menu?cliente_id={cliente_id}` - Obtener menú completo del usuario
  - Usa `sp_obtener_menu_usuario`
  - Transforma resultado a JSON jerárquico
  - Respuesta según estructura especificada en prompt.md

---

### **FASE 5: Dependencies y Middleware** ⏱️ ~1-2 horas

#### **5.1 Dependency de Validación de Acceso**
- [ ] Crear `app/modules/modulos/presentation/dependencies.py`
- [ ] Implementar `validar_acceso_menu_dep()` - Usa `sp_validar_acceso_menu`
- [ ] Retorna permisos del usuario sobre el menú
- [ ] Lanza HTTPException 403 si no tiene acceso

---

### **FASE 6: Actualización de Referencias** ⏱️ ~3-4 horas

#### **6.1 Actualizar Servicios RBAC**
- [ ] Actualizar `permiso_service.py`: Cambiar referencias de `menu` a `modulo_menu`
- [ ] Actualizar `rol_service.py`: Cambiar referencias de `menu` a `modulo_menu`
- [ ] Actualizar validaciones de existencia de menú

#### **6.2 Actualizar Queries SQL**
- [ ] Actualizar `queries.py`: Cambiar queries que usan tablas antiguas
- [ ] Agregar queries para nuevas tablas si es necesario

#### **6.3 Actualizar API Router**
- [ ] Actualizar `app/api/v1/api.py`:
  - Agregar routers de nuevos endpoints
  - Eliminar routers de menús antiguos

---

### **FASE 7: Testing y Validación** ⏱️ ~4-6 horas

#### **7.1 Testing Manual**
- [ ] Probar CRUD completo de módulos
- [ ] Probar CRUD completo de secciones
- [ ] Probar CRUD completo de menús
- [ ] Probar activación de módulo (verificar aplicación de plantillas)
- [ ] Probar endpoint de menú de usuario (verificar transformación SP)
- [ ] Probar validación de acceso a menú (dependency)
- [ ] Probar validación de dependencias entre módulos
- [ ] Probar reordenamiento de secciones y menús

#### **7.2 Validación de Integridad**
- [ ] Verificar que no se pueden eliminar módulos en uso
- [ ] Verificar que no se pueden eliminar secciones con menús
- [ ] Verificar que no se pueden eliminar menús con submenús o permisos
- [ ] Verificar que las plantillas se aplican correctamente al activar módulo

---

### **FASE 8: Limpieza y Documentación** ⏱️ ~1-2 horas

#### **8.1 Eliminar Código Obsoleto**
- [ ] Eliminar módulo `app/modules/menus/` completo
- [ ] Eliminar referencias a tablas antiguas en `tables.py`
- [ ] Limpiar imports no utilizados

#### **8.2 Documentación**
- [ ] Actualizar README con nueva estructura
- [ ] Documentar endpoints nuevos
- [ ] Documentar uso de stored procedures

---

## ⚠️ CONSIDERACIONES TÉCNICAS Y RIESGOS

### **Riesgos Identificados**

1. **Transformación de SP a JSON Jerárquico**
   - **Riesgo**: Complejidad en la transformación del resultado plano del SP a estructura jerárquica
   - **Mitigación**: Crear helper dedicado `menu_transformer.py` con tests unitarios

2. **Aplicación Automática de Plantillas**
   - **Riesgo**: Lógica compleja al activar módulo (crear roles desde plantillas)
   - **Mitigación**: Separar en helper `rol_plantilla_applier.py` con validaciones exhaustivas

3. **Migración de Datos Existentes**
   - **Riesgo**: Si hay datos en producción, necesitar script de migración
   - **Mitigación**: El prompt indica que la BD ya fue recreada, pero verificar

4. **Performance de Queries**
   - **Riesgo**: Queries complejas con múltiples JOINs pueden ser lentas
   - **Mitigación**: Usar índices definidos en `estructura_bd.sql`, considerar cacheo

5. **Validación de JSON**
   - **Riesgo**: Errores en validación de JSON de permisos y configuraciones
   - **Mitigación**: Validadores Pydantic robustos, tests de casos edge

### **Optimizaciones Recomendadas**

1. **Cacheo**:
   - Cachear catálogo de módulos (cambian poco)
   - Cachear menús globales
   - Cachear resultado de `sp_obtener_menu_usuario` por usuario (TTL corto)

2. **Índices**:
   - Verificar que todos los índices de `estructura_bd.sql` estén creados
   - Considerar índices adicionales si hay queries lentas

3. **Transacciones**:
   - Usar transacciones para operaciones complejas (activar módulo + aplicar plantillas)

---

## 📊 ESTIMACIÓN TOTAL

| Fase | Tiempo Estimado | Complejidad |
|------|----------------|-------------|
| FASE 1: Preparación | 2-3 horas | Media |
| FASE 2: Schemas | 2-3 horas | Baja |
| FASE 3: Servicios | 6-8 horas | Alta |
| FASE 4: Endpoints | 4-5 horas | Media |
| FASE 5: Dependencies | 1-2 horas | Baja |
| FASE 6: Actualización | 3-4 horas | Media |
| FASE 7: Testing | 4-6 horas | Media |
| FASE 8: Limpieza | 1-2 horas | Baja |
| **TOTAL** | **23-33 horas** | **Media-Alta** |

---

## ✅ CHECKLIST DE APROBACIÓN

Antes de iniciar la refactorización, verificar:

- [ ] Estructura de BD en `estructura_bd.sql` está completa y correcta
- [ ] Stored procedures `sp_obtener_menu_usuario` y `sp_validar_acceso_menu` existen y funcionan
- [ ] No hay datos en producción que requieran migración (o se tiene script de migración)
- [ ] Se entiende completamente la lógica de aplicación de plantillas de roles
- [ ] Se tiene acceso a la BD para testing
- [ ] Se tiene plan de rollback si algo falla

---

## 📝 NOTAS FINALES

1. **Orden de Ejecución**: Seguir el orden de las fases, especialmente FASE 3 (Servicios) antes de FASE 4 (Endpoints)

2. **Testing Continuo**: Probar cada servicio inmediatamente después de crearlo, no esperar al final

3. **Commits Incrementales**: Hacer commits pequeños y frecuentes, uno por cada funcionalidad completada

4. **Documentación en Código**: Agregar docstrings completos en todos los servicios y endpoints

5. **Manejo de Errores**: Usar el sistema de excepciones existente (`BaseService`, `CustomException`)

---

**Estado del Plan**: ⏳ PENDIENTE DE APROBACIÓN

**Última Actualización**: 2024-12-19

