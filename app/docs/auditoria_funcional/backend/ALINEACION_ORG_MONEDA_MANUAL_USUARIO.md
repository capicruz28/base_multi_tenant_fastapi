# Alineación módulo ORG — Documentos oficiales vs implementación

Revisión tras la actualización de los documentos oficiales de funcionalidad: **CATALOGO_MODULOS.md**, **MENU_NAVEGACION.md** y **MANUAL_USUARIO.md**. Este documento contrasta lo que dichos documentos exigen con la implementación actual del backend (tablas, endpoints, schemas, seeds) para el módulo ORG, en especial **catálogo de monedas** y **multi-moneda**.

---

## 1. Lo que dicen los documentos oficiales (actualizados)

### 1.1 CATALOGO_MODULOS.md

- **ORG — Configuración Empresarial** incluye:
  - Estructura organizacional completa
  - Sucursales, departamentos, cargos
  - Centros de costo
  - **Catálogo de monedas y multi-moneda**

### 1.2 MENU_NAVEGACION.md (módulo ORG)

- **Monedas** (primera opción)
  - Catálogo de monedas (PEN, USD, EUR, BRL)
  - Configurar moneda base y decimales
- **Mi Empresa**
  - Ver y editar datos de la empresa (RUC, razón social, logo)
  - **Configurar moneda base y activar/desactivar multi-moneda**
- Sucursales, Departamentos, Cargos, Centros de Costo, Parámetros del Sistema

### 1.3 MANUAL_USUARIO.md (sección 2.1 ORG)

- **PASO 0: Configurar catálogo de monedas**
  - Navegar a **ORG > Monedas > [+ Nueva Moneda]**
  - Campos: Código, Nombre, Símbolo, Decimales, **Es moneda base** (solo una por empresa), Activo
  - Regla: **solo UNA moneda puede ser “moneda base”** por empresa
- **PASO 1: Configurar Mi Empresa**
  - **Moneda base:** “PEN - Sol Peruano (**seleccionar catálogo**)” → selección por referencia al catálogo
  - **Multi-moneda:** ☐ No / ◉ Sí (switch)
  - Comportamiento según switch: documentos con moneda/tipo de cambio o todo en moneda base

---

## 2. Lo que está alineado (implementado)

| Documento / funcionalidad | Implementación backend / docs | Estado |
|---------------------------|------------------------------|--------|
| CATALOGO: “Catálogo de monedas y multi-moneda” en ORG | Documento ya lo incluye | ✔ Docs alineados |
| MENU: opción “Monedas” en ORG | MENU_NAVEGACION.md incluye “Monedas” como primera opción | ✔ Docs alineados |
| MANUAL: PASO 0 — Catálogo de monedas (CRUD) | Tabla `org_moneda`, queries, servicio, endpoints `GET/POST/PUT/DELETE /api/v1/org/monedas` | ✔ Implementado |
| Campos: código, nombre, símbolo, decimales, es_moneda_base, activo | Schemas y tabla con esas columnas | ✔ Alineado |
| Filtro por empresa en listado | `GET /api/v1/org/monedas?empresa_id=...` | ✔ |
| Baja lógica de moneda | `DELETE /api/v1/org/monedas/{moneda_id}` | ✔ |
| Multi-tenant en monedas | Queries y servicios filtran por `client_id` | ✔ |
| Resto del módulo ORG (Empresa, Sucursales, Departamentos, Cargos, Centros de costo, Parámetros) | CRUD con DELETE y `buscar` según auditoría previa | ✔ (ya implementado) |

---

## 3. Faltantes para tener todo completamente alineado

### 3.1 Empresa: moneda base (catálogo) y switch multi-moneda

**Documentos:** En Mi Empresa debe poder **seleccionar la moneda base del catálogo** y **activar/desactivar multi-moneda**.

**Estado actual:**

- En el diseño de BD (Fase 4) existen `org_empresa.moneda_base_id` (FK a `org_moneda`) y `org_empresa.maneja_multimoneda` (BIT).
- En código:
  - `tables_org.py` (OrgEmpresaTable) solo tiene `moneda_base` (String(3)), **no** `moneda_base_id` ni `maneja_multimoneda`.
  - Schemas y endpoints de empresa **no** exponen `moneda_base_id` ni `maneja_multimoneda`.

**Faltante:**  
Implementar en modelo, schemas y endpoints de empresa:

- `moneda_base_id` (UUID, FK a `org_moneda`) para “seleccionar moneda base del catálogo”.
- `maneja_multimoneda` (bool) para el switch Sí/No.

(Opcional: mantener `moneda_base` como derivado/compatibilidad.)

---

### 3.2 Regla: “Solo una moneda base por empresa”

**Documentos:** “Solo UNA moneda puede marcarse como ‘moneda base’”.

**Estado actual:**  
Al marcar una moneda como `es_moneda_base = True` no se desmarca la anterior moneda base de esa empresa.

**Faltante:**  
En el servicio (o query) de creación/actualización de moneda: al poner `es_moneda_base = True` en una moneda de una empresa, desmarcar (`es_moneda_base = False`) cualquier otra moneda de esa misma empresa que estuviera marcada como base.

---

### 3.3 Permisos RBAC para monedas

**Estado actual:**  
Los endpoints de monedas exigen `org.moneda.leer`, `org.moneda.crear`, `org.moneda.actualizar`, `org.moneda.eliminar`. Esos códigos **no** están en `SEED_PERMISOS_RBAC.sql`. Sin ellos, los usuarios (salvo superadmin) reciben 403 en `/api/v1/org/monedas`.

**Faltante:**  
Añadir en el seed de permisos (p. ej. `SEED_PERMISOS_RBAC.sql`) los cuatro permisos anteriores para el módulo ORG (mismo `modulo_id` que el resto de ORG).

---

### 3.4 Menú “Monedas” en la base de datos (seed)

**Documentos:** MENU_NAVEGACION.md ya incluye la opción “Monedas” en ORG.

**Estado actual:**  
El seed de menú `4.- SEED_MODULO_MENU_COMPLETO.sql` define para ORG **6 ítems**: Mi Empresa, Sucursales, Departamentos, Cargos, Centros de Costo, Parámetros. **No** existe la entrada “Monedas”. El menú dinámico que consume el front no mostrará “Monedas” hasta que exista en `modulo_menu`.

**Faltante:**  
Añadir en el seed de menú una fila para **Monedas** (ORG), con ruta `/org/monedas`, orden antes de Mi Empresa (o según criterio de negocio), y vinculada al módulo ORG. Si el menú se filtra por permisos, asociar a permisos `org.moneda.*`.

---

### 3.5 Documentación frontend (DOC_FRONTEND_MODULO_ORG.md)

**Documentos:** El manual y el menú asumen pantalla Monedas y flujo PASO 0 → PASO 1.

**Estado actual:**  
En `DOC_FRONTEND_MODULO_ORG.md` no se documentan los endpoints de **Monedas** ni la ruta SPA para la pantalla Monedas, ni el flujo recomendado (primero monedas, luego Mi Empresa con moneda base y multi-moneda).

**Faltante:**  
En `DOC_FRONTEND_MODULO_ORG.md`:

- Añadir sección **Monedas** con tabla de métodos y rutas: `GET/POST/PUT/DELETE /api/v1/org/monedas` y query params (`empresa_id`, `solo_activos`, `es_moneda_base`).
- Añadir en la tabla de rutas del menú: **Monedas** → `/org/monedas`.
- En el flujo recomendado, incluir **PASO 0** (catálogo de monedas) y, cuando existan en la API, la configuración de moneda base y multi-moneda en Mi Empresa.

---

## 4. Resumen de alineación

| Área | Documentos oficiales | Backend / seeds | Estado |
|------|----------------------|-----------------|--------|
| CATALOGO / MENU / MANUAL (texto) | Incluyen monedas y multi-moneda | — | ✔ Alineados entre sí |
| Catálogo `org_moneda` (CRUD, API) | PASO 0, opción Monedas | Implementado | ✔ Alineado |
| Empresa: `moneda_base_id` y `maneja_multimoneda` | Mi Empresa: seleccionar catálogo + switch | No implementado en modelo/schemas/API | ✖ Faltante |
| Regla “solo una moneda base por empresa” | Manual | Sin validación en backend | ✖ Faltante |
| Permisos `org.moneda.*` | Necesarios para usar API monedas | No están en SEED_PERMISOS_RBAC.sql | ✖ Faltante |
| Entrada “Monedas” en menú (BD) | MENU_NAVEGACION la describe | No existe en seed modulo_menu | ✖ Faltante |
| DOC_FRONTEND: Monedas y flujo | Flujo PASO 0 y Mi Empresa | No documentado | ✖ Faltante |

**Conclusión:** Los tres documentos oficiales (CATALOGO_MODULOS, MENU_NAVEGACION, MANUAL_USUARIO) están alineados entre sí y con el flujo deseado (catálogo de monedas + Mi Empresa con moneda base y multi-moneda). Para que **todo** quede alineado con esos documentos faltan en backend y documentación técnica:

1. Exponer y persistir en empresa `moneda_base_id` y `maneja_multimoneda`.
2. Validación/lógica “solo una moneda base por empresa” en el servicio de monedas.
3. Incluir permisos `org.moneda.leer/crear/actualizar/eliminar` en el seed RBAC.
4. Añadir la opción “Monedas” en el seed de menú (modulo_menu).
5. Documentar en DOC_FRONTEND_MODULO_ORG los endpoints de Monedas, la ruta `/org/monedas` y el flujo (PASO 0 + Mi Empresa).

---

¿Deseas que proceda con la implementación de las mejoras recomendadas para el módulo ORG?
