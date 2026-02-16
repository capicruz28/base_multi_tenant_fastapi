# 📦 GUÍA DE SEED DATA - Base de Datos

**Propósito:** Scripts para poblar las bases de datos con datos iniciales para pruebas

---

## 📋 ESTRUCTURA DE SEED DATA

### ✅ **BD CENTRAL** (`SEED_BD_CENTRAL.sql`)

**Contenido:**
- ✅ 5 Clientes:
  - `SUPERADMIN` (platform) - tipo: `shared`
  - `ACME` (acme) - tipo: `shared`
  - `INNOVA` (innova) - tipo: `shared`
  - `TECHCORP` (techcorp) - tipo: `dedicated`
  - `GLOBALLOG` (globallog) - tipo: `dedicated`

- ✅ 3 Módulos:
  - `ALMACEN` - Control de Almacén
  - `LOGISTICA` - Gestión Logística (requiere ALMACEN)
  - `PLANILLAS` - Gestión de Planillas

- ✅ Secciones por módulo:
  - **ALMACEN:** Productos, Movimientos, Reportes
  - **LOGISTICA:** Rutas, Vehículos, Conductores
  - **PLANILLAS:** Empleados, Planillas, Reportes

- ✅ Menús básicos por módulo (14 menús totales)

- ✅ Activación de módulos por cliente

- ✅ Usuarios y roles para clientes `shared`:
  - SUPERADMIN: `admin` (ADMIN), `user` (USER)
  - ACME: `admin` (ADMIN), `user` (USER)
  - INNOVA: `admin` (ADMIN), `user` (USER)

- ✅ Permisos básicos configurados

---

### ✅ **BD DEDICADA - TECHCORP** (`SEED_BD_DEDICADA_TECHCORP.sql`)

**Contenido:**
- ✅ Usuarios:
  - `admin` (rol ADMIN)
  - `user` (rol USER)

- ✅ Permisos para módulos activos:
  - ALMACEN (todos los menús)
  - LOGISTICA (todos los menús)
  - PLANILLAS (todos los menús)

---

### ✅ **BD DEDICADA - GLOBALLOG** (`SEED_BD_DEDICADA_GLOBALLOG.sql`)

**Contenido:**
- ✅ Usuarios:
  - `admin` (rol ADMIN)
  - `user` (rol USER)

- ✅ Permisos para módulos activos:
  - ALMACEN (todos los menús)
  - LOGISTICA (todos los menús)
  - **NO PLANILLAS** (módulo no activado)

---

## 🚀 ORDEN DE EJECUCIÓN

### Paso 1: Crear Estructura de Tablas

```sql
-- BD CENTRAL
USE bd_hybrid_sistema_central;
GO
-- Ejecutar: TABLAS_BD_CENTRAL.sql
```

```sql
-- BD DEDICADA TECHCORP
USE bd_cliente_techcorp;
GO
-- Ejecutar: TABLAS_BD_DEDICADA.sql
```

```sql
-- BD DEDICADA GLOBALLOG
USE bd_cliente_globallog;
GO
-- Ejecutar: TABLAS_BD_DEDICADA.sql
```

### Paso 2: Poblar con Seed Data

```sql
-- BD CENTRAL
USE bd_hybrid_sistema_central;
GO
-- Ejecutar: SEED_BD_CENTRAL.sql
```

```sql
-- BD DEDICADA TECHCORP
USE bd_cliente_techcorp;
GO
-- Ejecutar: SEED_BD_DEDICADA_TECHCORP.sql
```

```sql
-- BD DEDICADA GLOBALLOG
USE bd_cliente_globallog;
GO
-- Ejecutar: SEED_BD_DEDICADA_GLOBALLOG.sql
```

---

## 🔑 CREDENCIALES DE PRUEBA

### Clientes con BD Compartida (`shared`)

#### SUPERADMIN (platform.app.local)
- **admin** / `admin123` → Rol: ADMIN
- **user** / `user123` → Rol: USER

#### ACME (acme.app.local)
- **admin** / `admin123` → Rol: ADMIN
- **user** / `user123` → Rol: USER

#### INNOVA (innova.app.local)
- **admin** / `admin123` → Rol: ADMIN
- **user** / `user123` → Rol: USER

### Clientes con BD Dedicada (`dedicated`)

#### TECHCORP (techcorp.app.local)
- **admin** / `admin123` → Rol: ADMIN
- **user** / `user123` → Rol: USER

#### GLOBALLOG (globallog.app.local)
- **admin** / `admin123` → Rol: ADMIN
- **user** / `user123` → Rol: USER

---

## 📊 RESUMEN DE MÓDULOS ACTIVADOS

| Cliente | ALMACEN | LOGISTICA | PLANILLAS |
|---------|---------|-----------|-----------|
| SUPERADMIN | ✅ | ✅ | ✅ |
| ACME | ✅ | ✅ | ✅ |
| INNOVA | ✅ | ❌ | ✅ |
| TECHCORP | ✅ | ✅ | ✅ |
| GLOBALLOG | ✅ | ✅ | ❌ |

---

## 📝 MENÚS CREADOS POR MÓDULO

### ALMACEN (6 menús)
- Productos: Listar, Crear, Categorías
- Movimientos: Listar, Entrada, Salida

### LOGISTICA (4 menús)
- Rutas: Listar, Crear
- Vehículos: Listar, Crear

### PLANILLAS (4 menús)
- Empleados: Listar, Crear
- Planillas: Listar, Procesar

**Total:** 14 menús globales

---

## ⚠️ NOTAS IMPORTANTES

1. **UUIDs Fijos:** Los scripts usan UUIDs fijos para mantener coherencia entre BD central y dedicadas
2. **Passwords:** Todos los usuarios tienen password `admin123` o `user123` (hash bcrypt)
3. **Permisos:** 
   - ADMIN: Acceso completo (ver, crear, editar, eliminar, exportar, imprimir)
   - USER: Solo lectura (ver)
4. **Cross-Database:** Los permisos en BD dedicada referencian `menu_id` de BD central
5. **Módulos Requeridos:** LOGISTICA requiere ALMACEN activo (validado en código)

---

## ✅ VALIDACIÓN POST-SEED

### Verificar en BD CENTRAL:

```sql
-- Verificar clientes
SELECT cliente_id, codigo_cliente, subdominio, tipo_instalacion 
FROM cliente;

-- Verificar módulos
SELECT modulo_id, codigo, nombre, es_activo 
FROM modulo;

-- Verificar activaciones
SELECT c.codigo_cliente, m.codigo, cm.esta_activo
FROM cliente_modulo cm
JOIN cliente c ON cm.cliente_id = c.cliente_id
JOIN modulo m ON cm.modulo_id = m.modulo_id;

-- Verificar usuarios (clientes shared)
SELECT c.codigo_cliente, u.nombre_usuario, u.correo
FROM usuario u
JOIN cliente c ON u.cliente_id = c.cliente_id
WHERE c.tipo_instalacion = 'shared';
```

### Verificar en BD DEDICADA:

```sql
-- Verificar usuarios
SELECT nombre_usuario, correo, es_activo 
FROM usuario;

-- Verificar roles
SELECT nombre, codigo_rol, nivel_acceso 
FROM rol;

-- Verificar permisos
SELECT COUNT(*) as total_permisos 
FROM rol_menu_permiso;
```

---

**Última actualización:** Diciembre 2024  
**Mantenido por:** Arquitectura del Sistema
