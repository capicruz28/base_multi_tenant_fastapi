# Validación alineación RBAC — Módulo PUR (Compras)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Router prefix | Recursos | Métodos | Recurso RBAC |
|---------|----------------|----------|---------|---------------|
| endpoints_proveedores.py | /proveedores | proveedor | GET, GET /{id}, POST, PUT | proveedor |
| endpoints_contactos.py | /contactos | contacto | GET, GET /{id}, POST, PUT | contacto |
| endpoints_productos_proveedor.py | /productos-proveedor | producto_proveedor | GET, GET /{id}, POST, PUT | producto_proveedor |
| endpoints_solicitudes.py | /solicitudes | solicitud | GET, GET /{id}, POST, PUT | solicitud |
| endpoints_cotizaciones.py | /cotizaciones | cotizacion | GET, GET /{id}, POST, PUT | cotizacion |
| endpoints_ordenes_compra.py | /ordenes-compra | orden_compra | GET, GET /{id}, POST, PUT | orden_compra |
| endpoints_recepciones.py | /recepciones | recepcion | GET, GET /{id}, POST, PUT | recepcion |

**Total endpoints PUR:** 28

---

## 2. Endpoints decorados

Todos decorados con Patrón A: `MODULE_CODE = "pur"`, `RESOURCE_CODE` por archivo, `require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.<accion>")`.

**Endpoints decorados:** 28/28 (100 %)

---

## 3. Permisos generados (detectables por auto-registro)

| Código permiso | Recurso |
|----------------|---------|
| pur.proveedor.leer, .crear, .actualizar | proveedor |
| pur.orden_compra.leer, .crear, .actualizar | orden_compra |
| pur.cotizacion.leer, .crear, .actualizar | cotizacion |
| pur.solicitud.leer, .crear, .actualizar | solicitud |
| pur.recepcion.leer, .crear, .actualizar | recepcion |
| pur.contacto.leer, .crear, .actualizar | contacto |
| pur.producto_proveedor.leer, .crear, .actualizar | producto_proveedor |

**Total permisos únicos PUR:** 21

---

## 4. Inconsistencias detectadas

Ninguna.

---

## 5. Confirmación introspección para auto-registro

Todos los handlers usan f-string con constantes; los 21 permisos serán detectados en startup y sincronizados a `permiso`.
