# Revisión Completa de Arquitectura - Módulos y Menús

## ✅ CONFIRMACIÓN DE ARQUITECTURA

### **Tablas en BD CENTRAL** (Administración Global)
Todas las operaciones de administración de módulos, secciones, menús y plantillas se realizan en la **BD CENTRAL**:

- ✅ `modulo` - Catálogo de módulos ERP
- ✅ `modulo_seccion` - Secciones dentro de módulos  
- ✅ `modulo_menu` - Menús jerárquicos
- ✅ `modulo_rol_plantilla` - Plantillas de roles
- ✅ `cliente_modulo` - Activación de módulos por cliente
- ✅ `cliente` - Información de clientes
- ✅ `cliente_conexion` - Metadata de conexiones

**Conexión en código**: `DatabaseConnection.ADMIN` ✅

### **Tablas en BD del CLIENTE** (Datos del Tenant)
Los permisos se guardan en la BD del cliente según su tipo:

- ✅ `rol_menu_permiso` - Permisos de roles sobre menús
  - **Shared (single)**: Se guarda en BD central
  - **Dedicated (multi)**: Se guarda en BD del cliente
- ✅ `rol` - Roles del cliente
- ✅ `usuario_rol` - Asignación de roles a usuarios
- ✅ `usuario` - Usuarios del cliente

**Conexión en código**: `DatabaseConnection.DEFAULT` (rutea según tipo de cliente)

## ✅ VERIFICACIÓN DE SERVICIOS

### Servicios que usan BD CENTRAL (correcto):
- ✅ `ModuloService` → `DatabaseConnection.ADMIN`
- ✅ `ModuloSeccionService` → `DatabaseConnection.ADMIN`
- ✅ `ModuloMenuService` (CRUD) → `DatabaseConnection.ADMIN`
- ✅ `ModuloRolPlantillaService` → `DatabaseConnection.ADMIN`
- ✅ `ClienteModuloService` → `DatabaseConnection.ADMIN`

### Servicio que usa BD del Cliente (correcto):
- ✅ `ModuloMenuService.obtener_menu_usuario()` → `DatabaseConnection.DEFAULT`
  - **Razón**: El SP se ejecuta en la BD del cliente porque necesita acceder a `rol_menu_permiso` y `usuario_rol`

## ⚠️ PROBLEMA IDENTIFICADO

El stored procedure `sp_obtener_menu_usuario` necesita hacer JOIN entre:
- **BD CENTRAL**: `modulo`, `modulo_seccion`, `modulo_menu`, `cliente_modulo`
- **BD CLIENTE**: `rol_menu_permiso`, `usuario_rol`, `rol`, `usuario`

### Solución: SP con Cross-Database Query

El SP debe:
1. **Crearse en la BD del cliente** (donde están los permisos)
2. **Hacer referencia a tablas de BD central** usando nombres completos

## 🔧 CORRECCIONES NECESARIAS

### 1. SP Corregido con Cross-Database Query

El SP debe usar nombres completos para tablas de BD central. Necesito confirmar:
- **Nombre exacto de la BD central**: ¿Es `DB_DATABASE` o `DB_ADMIN_DATABASE`?
- **Variable de entorno**: ¿Cuál es el valor de `DB_DATABASE` o `DB_ADMIN_DATABASE`?

### 2. Alternativa: SP Dinámico

Si no se pueden hacer cross-database queries, el backend puede:
1. Obtener módulos/menús desde BD central
2. Obtener permisos desde BD del cliente
3. Combinar resultados en el backend

## 📋 INFORMACIÓN REQUERIDA

Para proceder, necesito que confirmes:

1. **Nombre exacto de la BD central**:
   - ¿Es el valor de `DB_DATABASE`?
   - ¿O es el valor de `DB_ADMIN_DATABASE`?
   - ¿O es otro nombre específico?

2. **Cross-database queries**:
   - ¿Están habilitadas en tu SQL Server?
   - ¿Hay linked servers configurados?

3. **Preferencia de solución**:
   - ¿SP con cross-database query? (más eficiente)
   - ¿O queries separadas en backend? (más flexible)

## 🎯 ESTADO ACTUAL

- ✅ Servicios usando conexiones correctas
- ✅ Estructura de tablas correcta
- ⚠️ SP necesita corrección para cross-database queries
- ⚠️ Nombre de BD central necesita confirmación

