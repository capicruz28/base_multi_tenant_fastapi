# Prompt para Corrección del Stored Procedure

## 📋 CONTEXTO

He confirmado la arquitectura:

### ✅ **BD CENTRAL** (Administración)
- `modulo`, `modulo_seccion`, `modulo_menu`, `modulo_rol_plantilla`, `cliente_modulo`
- Conexión: `DatabaseConnection.ADMIN`
- **Nombre de BD**: Necesito confirmar (¿`DB_DATABASE` o `DB_ADMIN_DATABASE`?)

### ✅ **BD del CLIENTE** (Permisos)
- `rol_menu_permiso`, `usuario_rol`, `rol`, `usuario`
- Conexión: `DatabaseConnection.DEFAULT`
- **Nombre de BD**: Variable según cliente (shared = BD central, dedicated = BD del cliente)

## ⚠️ PROBLEMA

El SP `sp_obtener_menu_usuario` necesita hacer JOIN entre tablas de BD central y BD del cliente.

## 🔧 SOLUCIÓN REQUERIDA

Necesito que me proporciones:

1. **Nombre exacto de la BD central**:
   - Valor de la variable de entorno `DB_DATABASE` o `DB_ADMIN_DATABASE`
   - O el nombre real de la BD central en tu servidor SQL

2. **Confirmación de cross-database queries**:
   - ¿Están habilitadas en tu SQL Server?
   - ¿Prefieres usar nombres completos de BD o linked servers?

3. **Preferencia de implementación**:
   - **Opción A**: SP en BD del cliente con cross-database query a BD central
   - **Opción B**: SP en BD central con cross-database query a BD del cliente
   - **Opción C**: Backend hace queries separadas y combina resultados

## 📝 CON ESTA INFORMACIÓN PODRÉ:

1. Crear el SP corregido con la sintaxis correcta
2. Asegurar que funcione en tu arquitectura específica
3. Documentar la solución final

**Por favor, proporciona el nombre de la BD central y tu preferencia de solución.**

