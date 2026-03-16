# Validación alineación RBAC — Módulo WMS (Gestión de Almacenes)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Router prefix | Recurso RBAC | Endpoints |
|---------|----------------|--------------|-----------|
| endpoints_zonas.py | (según api) | zona | GET "", GET /{zona_id}, POST, PUT |
| endpoints_ubicaciones.py | (según api) | ubicacion | GET "", GET /{ubicacion_id}, POST, PUT |
| endpoints_tareas.py | (según api) | tarea | GET "", GET /{tarea_id}, POST, PUT |
| endpoints_stock.py | (según api) | stock_ubicacion | GET "", GET /{id}, POST, PUT |

**Total endpoints WMS:** 16

---

## 2. Endpoints decorados

Todos con Patrón A (MODULE_CODE = "wms", RESOURCE_CODE por archivo). **16/16 (100 %).**

---

## 3. Permisos generados

wms.zona.leer, .crear, .actualizar; wms.ubicacion.*; wms.tarea.*; wms.stock_ubicacion.* → **12 permisos únicos**.

---

## 4–5. Inconsistencias / Introspección

Ninguna. Detectables por auto-registro.
