# 🔄 REFACTORIZACIÓN: Sistema de Módulos y Menús - Multi-tenant Híbrido

## 📋 CONTEXTO DEL PROYECTO

Eres un arquitecto de software senior especializado en sistemas multi-tenant. El proyecto es un **ERP SaaS modular con arquitectura híbrida** construido con:

- **Backend**: FastAPI (Python)
- **Base de datos**: SQL Server
- **Arquitectura**: Multi-tenant híbrida (Single-DB + Multi-DB)

El sistema soporta:
- **Clientes Single-DB**: Todos los datos en BD central
- **Clientes Multi-DB**: BD dedicada por cliente
- **Módulos ERP**: Planillas, Logística, Almacén (activación por contratación)

---

## 🎯 OBJETIVO DE LA REFACTORIZACIÓN

**REFACTORIZAR ÚNICAMENTE** el sistema de gestión de módulos y menús, creando una **ADMINISTRACIÓN COMPLETA** desde el frontend que permita:

### ✅ 1. Gestión de Módulos (CRUD Completo):
- Crear, listar, actualizar, eliminar módulos
- Activar/desactivar módulos
- Configurar precios, dependencias y configuraciones
- Validar dependencias entre módulos
- Obtener módulos disponibles para un cliente

### ✅ 2. Gestión de Cliente-Módulo (Activación/Contratación):
- Activar módulos para clientes específicos (ejecutado por SUPER ADMIN)
- Desactivar módulos contratados
- Configurar límites (usuarios, registros, transacciones)
- Gestionar licencias y vencimientos
- Modo prueba (trial) con días configurables
- Extender vencimientos
- **CRÍTICO**: Al activar, crear roles automáticamente desde plantillas

### ✅ 3. Gestión de Secciones (CRUD Completo):
- Crear, listar, actualizar, eliminar secciones por módulo
- Reordenar secciones
- Asignar iconos y descripciones
- Activar/desactivar secciones

### ✅ 4. Gestión de Menús (CRUD Completo):
- Crear, listar, actualizar, eliminar menús
- Asignar menús a módulos y secciones
- Crear jerarquías (menús padre-hijo)
- Reordenar menús
- Menús globales vs menús personalizados por cliente
- Configurar rutas, iconos, tipo de menú
- Duplicar menús para personalización

### ✅ 5. Gestión de Plantillas de Roles (CRUD Completo):
- Crear, listar, actualizar, eliminar plantillas
- Configurar permisos en formato JSON
- Validar estructura de JSON de permisos
- Activar/desactivar plantillas
- Reordenar plantillas
- Preview de aplicación de plantilla
- **Aplicación automática** al activar módulo para un cliente

### ✅ 6. Consulta de Menús con Permisos:
- Obtener menú completo del usuario con sus permisos (usando SP)
- Filtrar por módulos activos del cliente
- Respetar jerarquías y orden
- Agregar permisos de múltiples roles
- Transformar resultado del SP a JSON jerárquico

---

## ⚠️ RESTRICCIONES CRÍTICAS

1. **NO TOCAR** autenticación, usuarios, roles base (solo actualizar referencias a menús en permisos)
2. **NO MODIFICAR** lógica de clientes, conexiones, refresh tokens
3. **SOLO REFACTORIZAR** módulos, secciones, menús y plantillas de roles
4. **MANTENER** compatibilidad con clientes Single-DB y Multi-DB
5. **NO PROPORCIONAR CÓDIGO** - Generar todo basándose en el conocimiento del proyecto
6. **NO CREAR MIGRACIONES** - La BD ya fue recreada con la nueva estructura
7. **REVISAR** archivo `estructura_bd.sql` para conocer la estructura completa
9. **SOLO 2 STORED PROCEDURES**: `sp_obtener_menu_usuario` y `sp_validar_acceso_menu`

---

## 📊 CAMBIOS DE ESTRUCTURA DE BASE DE DATOS

### **⚠️ IMPORTANTE: Revisar archivo `estructura_bd.sql`**
El archivo `estructura_bd.sql` contiene la estructura completa y actualizada de todas las tablas. Cursor debe leerlo y analizarlo antes de proceder.

### **MAPEO DE REFACTORIZACIÓN (Tablas antiguas → Tablas nuevas)**

| ❌ Tabla Antigua | ✅ Tabla Nueva | 📝 Cambio Principal |
|-----------------|---------------|----------|
| `cliente_modulo` (catálogo) | `modulo` | Renombrada - Ahora es el catálogo global de módulos ERP |
| `cliente_modulo_activo` | `cliente_modulo` | Renombrada - Representa módulos contratados por cliente |
| `area_menu` | `modulo_seccion` | Reemplazada - Secciones pertenecen directamente a módulos |
| `menu` | `modulo_menu` | Renombrada - Menús pertenecen a módulos (FK obligatoria) |
| N/A | `modulo_rol_plantilla` | **NUEVA** - Plantillas de roles que se aplican al activar módulo |

### **Relaciones clave**:
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

## 🔍 ANÁLISIS PREVIO REQUERIDO

**ANTES DE REFACTORIZAR**, Cursor debe realizar un análisis exhaustivo:

### 1️⃣ **Leer archivo `estructura_bd.sql`**
- Analizar estructura completa de tablas nuevas
- Identificar campos, tipos de datos, constraints
- Comprender relaciones entre tablas (FKs)
- Identificar índices y validaciones

### 2️⃣ **Escanear proyecto FastAPI completo**

Identificar TODOS los archivos que:
- Consultan o manipulan las tablas antiguas (`cliente_modulo`, `cliente_modulo_activo`, `area_menu`, `menu`)
- Contienen lógica de módulos/menús
- Generan menús para el frontend
- Validan permisos sobre menús
- Usan SQLAlchemy Core (Table definitions)
- Routers/endpoints relacionados
- Schemas/Pydantic models
- CRUD operations
- Services/Business logic
- Dependencies/Utils

### 3️⃣ **Clasificar archivos por categoría**

Organizar por:
- **Routers** (endpoints API)
- **Schemas** (Pydantic models para request/response)
- **Tables** (SQLAlchemy Core Table definitions)
- **CRUD** (operaciones de base de datos con SQLAlchemy Core)
- **Services** (lógica de negocio)
- **Dependencies** (validadores, permisos)
- **Utils** (helpers)

### 4️⃣ **Generar mapa de dependencias completo**

Mostrar relaciones entre:
- Routers → Services → CRUD → Tables
- Identificar interdependencias
- Detectar código acoplado que necesita refactorización

### 5️⃣ **Listar archivos a crear/modificar/eliminar**

Clasificar en:
- ✅ **CREAR**: Nuevos archivos necesarios
- 🔄 **MODIFICAR**: Archivos existentes que cambiarán
- ❌ **ELIMINAR**: Archivos obsoletos

### 6️⃣ **Presentar plan de refactorización detallado**

Con:
- Orden de ejecución (paso a paso)
- Estimación de complejidad
- Riesgos identificados
- Plan de testing

---

## 🛠️ OPERACIONES CRUD REQUERIDAS

El backend debe implementar **administración completa** 

### **Gestión de Módulos**

**Operaciones requeridas**:
- ✅ Crear módulo
- ✅ Listar módulos (con filtros: activos, categoría, requiere_licencia)
- ✅ Obtener módulo por ID
- ✅ Obtener módulo por código
- ✅ Actualizar módulo
- ✅ Eliminar módulo (validar que no esté en uso)
- ✅ Activar/desactivar módulo
- ✅ Validar dependencias entre módulos
- ✅ Obtener módulos disponibles para un cliente (con SQLAlchemy, no SP)

**Validaciones críticas**:
- No permitir eliminar si está activo en algún cliente
- Validar formato de JSON en `modulos_requeridos`
- Validar formato de JSON en `configuracion_defecto`
- Código único y en mayúsculas

---

### **Gestión de Cliente-Módulo (Contratación)**

**Operaciones requeridas**:
- ✅ Activar módulo para cliente (ejecutado por SUPER ADMIN)
- ✅ Desactivar módulo para cliente
- ✅ Listar módulos activos de un cliente
- ✅ Obtener detalle de activación
- ✅ Actualizar configuración personalizada
- ✅ Actualizar límites (usuarios, registros, transacciones)
- ✅ Extender vencimiento (agregar días)
- ✅ Cambiar de modo prueba a modo licenciado
- ✅ Validar licencia (está activo + no vencido)

**Validaciones críticas al activar**:
- Módulo debe existir y estar activo
- Validar dependencias (módulos requeridos ya activos)
- No permitir duplicados (cliente ya tiene el módulo)
- Validar límites antes de permitir operaciones

**⚠️ LÓGICA ESPECIAL AL ACTIVAR MÓDULO (CRÍTICO)**:

Cuando el SUPER ADMIN activa un módulo

**Resultado**: Admin del cliente encuentra roles creados automáticamente

---

### **Gestión de Secciones**

**Operaciones requeridas**:
- ✅ Crear sección en un módulo
- ✅ Listar secciones de un módulo
- ✅ Obtener sección por ID
- ✅ Actualizar sección
- ✅ Eliminar sección (validar que no tenga menús)
- ✅ Reordenar secciones de un módulo
- ✅ Activar/desactivar sección

**Validaciones críticas**:
- Código único dentro del módulo
- No eliminar si tiene menús asociados

---

### **Gestión de Menús**

**Operaciones requeridas**:
- ✅ Crear menú (global o personalizado)
- ✅ Listar menús (con filtros: módulo, sección, cliente, tipo)
- ✅ Obtener menú por ID
- ✅ Actualizar menú
- ✅ Eliminar menú (validar que no tenga submenús)
- ✅ Activar/desactivar menú
- ✅ Mostrar/ocultar menú (es_visible)
- ✅ Listar menús de un módulo (estructura jerárquica)
- ✅ Obtener submenús de un menú padre
- ✅ Reordenar menús dentro de una sección
- ✅ Duplicar menú (para crear versión personalizada)
- ✅ **CRÍTICO**: Obtener menú completo del usuario con permisos

**Validaciones críticas**:
- `modulo_id` es obligatorio
- Validar que `menu_padre_id` pertenezca al mismo módulo
- No permitir niveles > 3
- Validar que ruta sea única dentro del módulo
- No eliminar si tiene submenús o permisos asignados

---

### **Gestión de Plantillas de Roles**

**Operaciones requeridas**:
- ✅ Crear plantilla de rol para un módulo (solo SUPER ADMIN)
- ✅ Listar plantillas de un módulo
- ✅ Obtener plantilla por ID
- ✅ Actualizar plantilla
- ✅ Eliminar plantilla
- ✅ Activar/desactivar plantilla
- ✅ Reordenar plantillas de un módulo
- ✅ Validar estructura de JSON de permisos
- ✅ Preview de aplicación (mostrar qué se creará sin ejecutar)

**Validaciones críticas**:
- Solo SUPER ADMIN puede crear/editar plantillas globales
- Validar formato JSON de `permisos_json`
- Validar que códigos de menú en JSON existan en el módulo
- No eliminar si se está usando en algún proceso activo
- Estructura esperada del JSON:
```json
{
  "MENU_CODIGO_1": {
    "ver": true,
    "crear": true,
    "editar": false,
    "eliminar": false,
    "exportar": true,
    "imprimir": false,
    "aprobar": false
  },
  "MENU_CODIGO_2": {
    "ver": true,
    "crear": false
  }
}
```

**Uso de las plantillas**:
- Se aplican AUTOMÁTICAMENTE cuando el SUPER ADMIN activa un módulo
- La lógica de aplicación está en el service de activación de módulos
- Los roles creados son editables por el admin del cliente después

---

## 🗄️ STORED PROCEDURES DISPONIBLES

### **⚠️ IMPORTANTE: Solo usar estos 2 SPs**

Todo lo demás debe hacerse con SQLAlchemy Core.

#### **SP1: `sp_obtener_menu_usuario`** (PRINCIPAL)

**Propósito**: Obtener el menú completo de un usuario con todos sus permisos

**Parámetros**:
```sql
@usuario_id UNIQUEIDENTIFIER,
@cliente_id UNIQUEIDENTIFIER
```

**Uso en FastAPI**:
```python
# Llamar SP con SQLAlchemy Core
from sqlalchemy import text

async def obtener_menu_usuario(usuario_id: str, cliente_id: str):
    query = text("""
        EXEC sp_obtener_menu_usuario 
        @usuario_id = :usuario_id,
        @cliente_id = :cliente_id
    """)
    
    result = await db.execute(
        query,
        {"usuario_id": usuario_id, "cliente_id": cliente_id}
    )
    
    rows = result.fetchall()
    
    # Transformar resultado plano a estructura jerárquica
    menu_jerarquico = construir_estructura_jerarquica(rows)
    
    return menu_jerarquico
```

**Lógica**:
- Filtra por módulos activos del cliente
- Valida vencimiento de licencias
- Agrupa permisos de múltiples roles (MAX)
- Retorna dataset plano que debe transformarse a JSON jerárquico

---

#### **SP2: `sp_validar_acceso_menu`** (MIDDLEWARE)

**Propósito**: Validar si un usuario tiene acceso a un menú específico

**Parámetros**:
```sql
@usuario_id UNIQUEIDENTIFIER,
@cliente_id UNIQUEIDENTIFIER,
@menu_id UNIQUEIDENTIFIER = NULL,
@ruta NVARCHAR(255) = NULL
```

**Uso en FastAPI** (Dependency):
```python
async def validar_acceso_menu_dep(
    menu_id: str = None,
    ruta: str = None,
    usuario_id: str = Depends(get_current_user),
    cliente_id: str = Depends(get_current_cliente)
):
    query = text("""
        EXEC sp_validar_acceso_menu
        @usuario_id = :usuario_id,
        @cliente_id = :cliente_id,
        @menu_id = :menu_id,
        @ruta = :ruta
    """)
    
    result = await db.execute(query, {...})
    row = result.fetchone()
    
    if not row.tiene_acceso:
        raise HTTPException(403, "Sin acceso al menú")
    
    return row  # Devuelve permisos
```

---

## 👥 LÓGICA DE PERMISOS POR TIPO DE USUARIO

### **Super Admin (cliente_id = SYSTEM)**:
- ✅ Acceso TOTAL a TODOS los módulos
- ✅ Acceso a TODOS los menús (globales y custom)
- ✅ Todos los permisos en TRUE
- ✅ No validar vencimiento de licencias

### **Admin de Tenant**:
- ✅ Acceso TOTAL a módulos contratados por su cliente
- ✅ Acceso a menús globales + menús custom de su cliente
- ✅ Todos los permisos en TRUE dentro de sus módulos
- ✅ Validar vencimiento de licencias

### **Usuario estándar**:
- ⚠️ Acceso según permisos configurados en `rol_menu_permiso`
- ⚠️ Solo módulos contratados por su cliente
- ⚠️ Permisos pueden ser limitados (solo ver, solo exportar, etc.)

---

## 📁 ESTRUCTURA DE RESPUESTA API (Frontend)

### **Endpoint principal**: 
```
GET /api/v1/usuarios/{usuario_id}/menu?cliente_id={cliente_id}
```

### **Respuesta JSON esperada** (estructura jerárquica):

```json
{
  "modulos": [
    {
      "modulo_id": "uuid",
      "codigo": "LOGISTICA",
      "nombre": "Logística y Distribución",
      "icono": "local_shipping",
      "color": "#FF9800",
      "categoria": "operaciones",
      "orden": 2,
      "secciones": [
        {
          "seccion_id": "uuid",
          "codigo": "RUTAS",
          "nombre": "Gestión de Rutas",
          "icono": "route",
          "orden": 1,
          "menus": [
            {
              "menu_id": "uuid",
              "codigo": "LOGISTICA_RUTAS_LISTA",
              "nombre": "Lista de Rutas",
              "icono": "route",
              "ruta": "/logistica/rutas",
              "nivel": 1,
              "tipo_menu": "pantalla",
              "orden": 1,
              "permisos": {
                "ver": true,
                "crear": true,
                "editar": true,
                "eliminar": false,
                "exportar": true,
                "imprimir": true,
                "aprobar": false
              },
              "submenus": [
                {
                  "menu_id": "uuid",
                  "codigo": "LOGISTICA_RUTAS_NUEVA",
                  "nombre": "Nueva Ruta",
                  "icono": "add_road",
                  "ruta": "/logistica/rutas/nueva",
                  "nivel": 2,
                  "tipo_menu": "pantalla",
                  "orden": 1,
                  "permisos": {
                    "ver": true,
                    "crear": true
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 📊 ENDPOINTS API MÍNIMOS REQUERIDOS

### **Módulos**:
```
POST   /api/v1/modulos
GET    /api/v1/modulos
GET    /api/v1/modulos/{modulo_id}
GET    /api/v1/modulos/codigo/{codigo}
PUT    /api/v1/modulos/{modulo_id}
DELETE /api/v1/modulos/{modulo_id}
PATCH  /api/v1/modulos/{modulo_id}/activar
PATCH  /api/v1/modulos/{modulo_id}/desactivar
GET    /api/v1/modulos/{modulo_id}/dependencias
GET    /api/v1/modulos/disponibles/{cliente_id}
```

### **Cliente-Módulo**:
```
POST   /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/activar
DELETE /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/desactivar
GET    /api/v1/clientes/{cliente_id}/modulos
GET    /api/v1/clientes/{cliente_id}/modulos/{modulo_id}
PUT    /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/configuracion
PUT    /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/limites
PATCH  /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/extender-vencimiento
GET    /api/v1/clientes/{cliente_id}/modulos/{modulo_id}/validar-licencia
```

### **Secciones**:
```
POST   /api/v1/modulos/{modulo_id}/secciones
GET    /api/v1/modulos/{modulo_id}/secciones
GET    /api/v1/secciones/{seccion_id}
PUT    /api/v1/secciones/{seccion_id}
DELETE /api/v1/secciones/{seccion_id}
PATCH  /api/v1/secciones/{seccion_id}/activar
PATCH  /api/v1/secciones/{seccion_id}/desactivar
PUT    /api/v1/modulos/{modulo_id}/secciones/reordenar
```

### **Menús**:
```
POST   /api/v1/modulos/{modulo_id}/menus
GET    /api/v1/modulos/{modulo_id}/menus
GET    /api/v1/secciones/{seccion_id}/menus
GET    /api/v1/menus/{menu_id}
GET    /api/v1/menus/{menu_id}/submenus
PUT    /api/v1/menus/{menu_id}
DELETE /api/v1/menus/{menu_id}
PATCH  /api/v1/menus/{menu_id}/activar
PATCH  /api/v1/menus/{menu_id}/desactivar
PUT    /api/v1/secciones/{seccion_id}/menus/reordenar
POST   /api/v1/menus/{menu_id}/duplicar
GET    /api/v1/usuarios/{usuario_id}/menu
```

### **Plantillas de Roles**:
```
POST   /api/v1/modulos/{modulo_id}/roles-plantilla
GET    /api/v1/modulos/{modulo_id}/roles-plantilla
GET    /api/v1/roles-plantilla/{plantilla_id}
PUT    /api/v1/roles-plantilla/{plantilla_id}
DELETE /api/v1/roles-plantilla/{plantilla_id}
PATCH  /api/v1/roles-plantilla/{plantilla_id}/activar
PATCH  /api/v1/roles-plantilla/{plantilla_id}/desactivar
PUT    /api/v1/modulos/{modulo_id}/roles-plantilla/reordenar
POST   /api/v1/roles-plantilla/validar-json
GET    /api/v1/roles-plantilla/{plantilla_id}/preview
```

---

## 🚨 CONSIDERACIONES ESPECIALES

### **Arquitectura Multi-DB**:
- Menús SIEMPRE en BD central (tabla `modulo_menu`)
- `rol_menu_permiso` se replica en BD del cliente
- Al consultar menús: JOIN entre BD central + BD cliente
- Usar stored procedures para queries complejas

### **Performance**:
- Cachear catálogo de módulos (cambian poco)
- Cachear menús globales
- Optimizar transformación de resultado SP a JSON
- Usar índices: `modulo_id`, `cliente_id`, `es_activo`, `orden`

### **Seguridad**:
- Validar siempre que cliente tenga módulo activo
- Validar fecha vencimiento antes de permitir operaciones
- Logs de auditoría en activaciones/desactivaciones
- Solo super admin puede crear/editar módulos globales y plantillas
- Clientes solo pueden crear menús personalizados

---

## 🤔 EVALUACIÓN Y VALIDACIÓN DEL PLAN

**Cursor, antes de presentar el plan de refactorización:**

### 1️⃣ **Analiza la factibilidad completa**:
- ¿La estructura de tablas en `estructura_bd.sql` soporta todas las operaciones?
- ¿Los 2 stored procedures son suficientes o necesitas más?
- ¿Hay alguna operación CRUD que falte?
- ¿La lógica de activación con SQLAlchemy Core es clara?
- ¿El proyecto actual usa SQLAlchemy Core correctamente?

### 2️⃣ **Identifica mejoras o optimizaciones**:
- ¿Hay oportunidades de cacheo adicional?
- ¿Endpoints que podrían simplificarse o agruparse?
- ¿Validaciones adicionales necesarias?
- ¿Estructura de transformación de datos del SP óptima?

### 3️⃣ **Detecta posibles riesgos técnicos**:
- ¿Complejidad en la transformación de datos del SP a JSON jerárquico?
- ¿Problemas de performance esperados?
- ¿Dependencias circulares en el código?
- ¿Transacciones complejas con múltiples inserts?

### 4️⃣ **Propón mejoras arquitectónicas** (si aplican):
- ¿Separación de concerns más clara?
- ¿Middlewares o dependencies específicos?
- ¿Estructura de carpetas óptima?
- ¿Helpers para trabajar con Table definitions?

---

✅ APROBACIÓN REQUERIDA
NO INICIAR LA REFACTORIZACIÓN hasta que yo confirme el plan.
Una vez aprobado, proceder fase por fase, notificando progresos.