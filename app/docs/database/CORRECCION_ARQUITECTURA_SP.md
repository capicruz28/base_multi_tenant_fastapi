# Corrección de Arquitectura - Stored Procedure sp_obtener_menu_usuario

## ✅ CONFIRMACIÓN DE ARQUITECTURA

### **Tablas en BD CENTRAL** (Administración Global)
- ✅ `modulo` - Catálogo de módulos ERP
- ✅ `modulo_seccion` - Secciones dentro de módulos  
- ✅ `modulo_menu` - Menús jerárquicos
- ✅ `modulo_rol_plantilla` - Plantillas de roles
- ✅ `cliente_modulo` - Activación de módulos por cliente
- ✅ `cliente` - Información de clientes
- ✅ `cliente_conexion` - Metadata de conexiones

**Conexión**: `DatabaseConnection.ADMIN` ✅ (Ya implementado correctamente)

### **Tablas en BD del CLIENTE** (Datos del Tenant)
- ✅ `rol_menu_permiso` - Permisos de roles sobre menús
- ✅ `rol` - Roles del cliente
- ✅ `usuario_rol` - Asignación de roles a usuarios
- ✅ `usuario` - Usuarios del cliente

**Conexión**: `DatabaseConnection.DEFAULT` (BD del cliente según tipo: shared/dedicated)

## ⚠️ PROBLEMA IDENTIFICADO

El stored procedure `sp_obtener_menu_usuario` necesita hacer JOIN entre:
- **BD CENTRAL**: `modulo`, `modulo_seccion`, `modulo_menu`, `cliente_modulo`
- **BD CLIENTE**: `rol_menu_permiso`, `usuario_rol`, `rol`, `usuario`

### El SP actual intenta hacer JOIN directo, pero las tablas están en diferentes BDs.

## 🔧 SOLUCIÓN REQUERIDA

### **Opción Recomendada: SP en BD del Cliente con Cross-Database Query**

El SP debe crearse en **cada BD de cliente** y hacer referencia a la BD central usando:
- Nombre completo de BD: `[bd_hybrid_sistema_central].[dbo].[modulo]`
- O linked server si está configurado

### **SP Corregido para Cross-Database Query**

El SP debe usar nombres completos para tablas de BD central:

```sql
FROM [bd_hybrid_sistema_central].[dbo].[modulo_menu] m
INNER JOIN [bd_hybrid_sistema_central].[dbo].[modulo] mod ON m.modulo_id = mod.modulo_id
LEFT JOIN [bd_hybrid_sistema_central].[dbo].[modulo_seccion] sec ON m.seccion_id = sec.seccion_id
INNER JOIN [bd_hybrid_sistema_central].[dbo].[cliente_modulo] cm ON mod.modulo_id = cm.modulo_id
-- Tablas de BD del cliente (sin prefijo)
INNER JOIN rol_menu_permiso p ON m.menu_id = p.menu_id
INNER JOIN usuario_rol ur ON p.rol_id = ur.rol_id
```

## 📋 REVISIÓN NECESARIA

Necesito que confirmes:

1. **Nombre exacto de la BD central**: ¿Es `bd_hybrid_sistema_central` o otro nombre?
2. **Cross-database queries**: ¿Están habilitadas en SQL Server?
3. **Linked servers**: ¿Hay linked servers configurados?
4. **Alternativa**: ¿Prefieres que el backend haga queries separadas y combine resultados?

## 🔍 VERIFICACIÓN DE SERVICIOS

### ✅ Servicios que usan BD CENTRAL (correcto):
- `ModuloService` → `DatabaseConnection.ADMIN` ✅
- `ModuloSeccionService` → `DatabaseConnection.ADMIN` ✅
- `ModuloMenuService` → `DatabaseConnection.ADMIN` ✅
- `ModuloRolPlantillaService` → `DatabaseConnection.ADMIN` ✅
- `ClienteModuloService` → `DatabaseConnection.ADMIN` ✅

### ⚠️ Servicio que necesita corrección:
- `ModuloMenuService.obtener_menu_usuario()` → Usa `DatabaseConnection.DEFAULT` (BD del cliente) ✅
  - Pero el SP debe hacer cross-database query a BD central

## 📝 PRÓXIMOS PASOS

1. **Confirmar nombre de BD central**
2. **Crear SP corregido con cross-database queries**
3. **Probar en BD de cliente**
4. **Documentar solución final**

