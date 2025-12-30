# Análisis de Arquitectura de Base de Datos

## ✅ CONFIRMACIÓN DE ARQUITECTURA

### **Tablas en BD CENTRAL** (Administración Global)
- ✅ `modulo` - Catálogo de módulos ERP
- ✅ `modulo_seccion` - Secciones dentro de módulos
- ✅ `modulo_menu` - Menús jerárquicos
- ✅ `modulo_rol_plantilla` - Plantillas de roles
- ✅ `cliente_modulo` - Activación de módulos por cliente
- ✅ `cliente` - Información de clientes
- ✅ `cliente_conexion` - Metadata de conexiones

### **Tablas en BD del CLIENTE** (Datos del Tenant)
- ✅ `rol_menu_permiso` - Permisos de roles sobre menús
- ✅ `rol` - Roles del cliente
- ✅ `usuario_rol` - Asignación de roles a usuarios
- ✅ `usuario` - Usuarios del cliente

## ⚠️ PROBLEMA IDENTIFICADO

El stored procedure `sp_obtener_menu_usuario` necesita hacer JOIN entre:
- **BD CENTRAL**: `modulo`, `modulo_seccion`, `modulo_menu`, `cliente_modulo`
- **BD CLIENTE**: `rol_menu_permiso`, `usuario_rol`, `rol`, `usuario`

### Opciones de Solución:

#### **Opción 1: SP en BD Central con Cross-Database Query**
- SP se crea en BD central
- Hace referencia a BD del cliente usando nombre completo: `[bd_cliente_acme].[dbo].[rol_menu_permiso]`
- Requiere que el SP conozca el nombre de la BD del cliente

#### **Opción 2: SP en BD del Cliente con Cross-Database Query**
- SP se crea en cada BD de cliente
- Hace referencia a BD central usando nombre completo: `[bd_hybrid_sistema_central].[dbo].[modulo]`
- Requiere linked server o nombre completo de BD central

#### **Opción 3: SP Dinámico con Ejecución en BD Correcta**
- El backend ejecuta queries separadas y combina resultados
- No requiere cross-database queries

## 🔍 REVISIÓN NECESARIA

Necesito confirmar:
1. ¿Cómo se manejan las cross-database queries en tu sistema?
2. ¿Hay linked servers configurados?
3. ¿Cuál es el nombre exacto de la BD central?
4. ¿Prefieres SP en BD central o en BD del cliente?

