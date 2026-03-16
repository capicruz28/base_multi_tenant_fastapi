# Reporte final — Alineación RBAC completa

**Fecha:** 2026-02-18  
**Alcance:** Cierre definitivo de la alineación de endpoints con el catálogo RBAC.  
**Referencia:** `rbac_patterns_and_conventions.md`, `rbac_pending_endpoints_classification.md`.

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|--------|--------|
| **Total endpoints decorados con require_permission (o equivalente)** | **154** |
| **Endpoints excluidos (SISTEMA)** | auth, health, docs, openapi, `/` |
| **Endpoints híbridos (USERS)** | 2 (read_usuario, read_usuario_roles) |
| **Permisos candidatos [C] altados en script** | 9 (log.guia_remision_detalle.*, log.despacho_guia.*, fin.asiento_detalle.*) |
| **Alineación total RBAC** | **Sí** — Todos los endpoints de negocio/admin definidos en el plan están alineados. |

---

## 2. Total endpoints del sistema (referencia)

- **API v1** (rutas bajo `/api/v1`): se consideran todos los endpoints de módulos de negocio, admin, RBAC, menús y usuarios.
- **Excluidos por diseño (SISTEMA):** `/auth/*` (login, refresh, logout, sessions, SSO, me, permissions/me, menu), `/health`, `/docs`, `/redoc`, `/openapi.json`, `/`. No se decoran con `require_permission` ni se integran al catálogo RBAC de negocio.

No se cuenta un “total absoluto” único porque depende de si se incluyen o no rutas de otros módulos (PUR, SLS, etc.) aún no decorados en este ciclo. En este cierre se consideran **todos los endpoints listados en el plan de alineación (HCM, LOG, INV, FIN, SVC, TKT, USERS, RBAC, Menús, Áreas)**.

---

## 3. Total decorados

### 3.1 Por fases

| Fase | Módulos / Grupos | Endpoints decorados |
|------|-------------------|----------------------|
| FASE 3 (riesgo BAJO) | HCM, LOG, INV, FIN, SVC, TKT | 120 |
| Cierre final (MEDIO + híbrido) | LOG sub-recursos, INV stock contextual, FIN sub-recursos, RBAC, Menús, Áreas | 32 |
| Híbrido USERS | read_usuario, read_usuario_roles (validación en handler) | 2 |
| **Total** | | **154** |

### 3.2 Desglose del cierre final (32 + 2)

| Grupo | Archivo(s) | Endpoints | Permiso(s) aplicado(s) |
|-------|------------|-----------|--------------------------|
| LOG guía detalle | endpoints_guias_remision.py | 4 | log.guia_remision_detalle.leer/crear/actualizar |
| LOG despacho-guía | endpoints_despachos.py | 4 | log.despacho_guia.leer/crear/actualizar |
| INV stock contextual | endpoints_stock.py | 1 | inv.stock.leer |
| FIN asiento detalle | endpoints_asientos.py | 4 | fin.asiento_detalle.leer/crear/actualizar |
| RBAC rol-menú | endpoints_permisos.py | 4 | admin.rol.leer, admin.rol.actualizar |
| Menús (legacy) | endpoints.py (menus) | 8 | modulos.menu.leer, modulos.menu.administrar |
| Áreas | endpoints_areas.py | 7 | modulos.menu.leer, modulos.menu.administrar |
| USERS (híbrido) | endpoints.py (users) | 2 | admin.usuario.leer / admin.rol.leer (solo al acceder a *otros* usuarios) |

---

## 4. Endpoints excluidos (SISTEMA)

No integrados al catálogo RBAC de negocio; protegidos por autenticación o por diseño de infraestructura:

- **`/api/v1/auth/*`** — login, refresh, logout, sessions, SSO, me, permissions/me, menu.
- **`/health`**, **`/docs`**, **`/redoc`**, **`/openapi.json`**, **`/`**.

---

## 5. Endpoints híbridos (USERS)

| Endpoint | Comportamiento |
|----------|----------------|
| GET /api/v1/usuarios/{id}/ | Self-service: usuario puede ver su propio perfil sin permiso. Acceso a **otros** usuarios: requiere `admin.usuario.leer` (validación en handler con `has_permission`). |
| GET /api/v1/usuarios/{id}/roles/ | Self-service: usuario puede ver sus propios roles sin permiso. Acceso a roles de **otros** usuarios: requiere `admin.rol.leer` (validación en handler). |

No se usa `Depends(require_permission(...))` en la ruta para no bloquear el acceso a sí mismo; la restricción se aplica solo cuando `usuario_id != current_user.usuario_id`.

---

## 6. Lista final de permisos utilizados

Permisos referenciados en código (por módulo / espacio). Los que no están en el seed actual deben darse de alta vía `SEED_PERMISOS_RBAC.sql`, `SEED_PERMISOS_RBAC_FASE4_CANDIDATOS.sql` o auto-registro.

### 6.1 Admin

- admin.usuario.leer, admin.usuario.crear, admin.usuario.actualizar, admin.usuario.eliminar  
- admin.rol.leer, admin.rol.crear, admin.rol.actualizar, admin.rol.eliminar, admin.rol.asignar  

### 6.2 Modulos (menú y áreas)

- modulos.menu.leer  
- modulos.menu.administrar  

### 6.3 HCM

- hcm.empleado.*, hcm.contrato.*, hcm.concepto_planilla.*, hcm.planilla.*, hcm.planilla_empleado.*, hcm.planilla_detalle.*, hcm.asistencia.*, hcm.vacaciones.*, hcm.prestamo.*  

### 6.4 LOG

- log.transportista.*, log.vehiculo.*, log.ruta.*, log.guia_remision.*, log.guia_remision_detalle.*, log.despacho.*, log.despacho_guia.*  

### 6.5 INV

- inv.categoria.*, inv.unidad_medida.*, inv.producto.*, inv.almacen.*, inv.stock.*, inv.tipo_movimiento.*, inv.movimiento.*, inv.inventario_fisico.*  

### 6.6 FIN

- fin.plan_cuenta.*, fin.periodo.*, fin.asiento.*, fin.asiento_detalle.*  

### 6.7 SVC

- svc.orden_servicio.leer, svc.orden_servicio.crear, svc.orden_servicio.actualizar  

### 6.8 TKT

- tkt.ticket.leer, tkt.ticket.crear, tkt.ticket.actualizar  

*(Otros módulos ya documentados en seed o en `rbac_new_permissions_candidates.md` siguen la misma convención `<modulo>.<recurso>.<accion>`.)*

---

## 7. Alta de permisos candidatos [C]

- **Script creado:** `app/docs/database/SEED_PERMISOS_RBAC_FASE4_CANDIDATOS.sql`  
- **Permisos incluidos:**  
  - log.guia_remision_detalle.leer, .crear, .actualizar  
  - log.despacho_guia.leer, .crear, .actualizar  
  - fin.asiento_detalle.leer, .crear, .actualizar  

Ejecutar después de `SEED_PERMISOS_RBAC.sql` (y dependencias). Los permisos ya existentes en el seed (admin.*, modulos.menu.*, inv.stock.leer, etc.) no se repiten en este script.

---

## 8. Confirmación de alineación total RBAC

| Criterio | Estado |
|----------|--------|
| Patrón A (negocio) o B (admin) aplicado donde corresponde | **Sí** |
| Convención `<modulo>.<recurso>.<accion>` respetada | **Sí** |
| MODULE_CODE / RESOURCE_CODE usados en routers de negocio | **Sí** |
| Endpoints SISTEMA excluidos del catálogo | **Sí** |
| Modelo híbrido USERS (self sin permiso, otros con admin.usuario.leer / admin.rol.leer) | **Sí** |
| Permisos [C] de FASE 4 preparados para inserción en `permiso` | **Sí** (script SQL) |
| Compatibilidad con auto-registro (código de permiso extraíble) | **Sí** |

**El sistema queda con alineación RBAC completa para los módulos y endpoints definidos en el plan.** Catálogo listo para sincronización automática con la tabla `permiso` (seed o auto-registro).
