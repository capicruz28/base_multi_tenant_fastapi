# Validación alineación RBAC — Módulo SLS (Ventas)

**Fecha:** 2026-02-18  
**Estado:** Completado

---

## 1. Endpoints encontrados

| Archivo | Router prefix | Recurso RBAC | Endpoints |
|---------|----------------|--------------|-----------|
| endpoints_clientes.py | /clientes | cliente | GET "", GET /{id}, POST, PUT |
| endpoints_contactos.py | /contactos | contacto | GET "", GET /{id}, POST, PUT |
| endpoints_direcciones.py | /direcciones | direccion | GET "", GET /{id}, POST, PUT |
| endpoints_cotizaciones.py | /cotizaciones | cotizacion | GET "", GET /{id}, POST, PUT |
| endpoints_pedidos.py | /pedidos | pedido | GET "", GET /{id}, POST, PUT |

**Total endpoints SLS:** 20

---

## 2. Endpoints decorados

Todos decorados con Patrón A (MODULE_CODE = "sls", RESOURCE_CODE por recurso).

**Endpoints decorados:** 20/20 (100 %)

---

## 3. Permisos generados

sls.cliente.leer, .crear, .actualizar; sls.contacto.*; sls.direccion.*; sls.cotizacion.*; sls.pedido.* → **15 permisos únicos**.

---

## 4–5. Inconsistencias / Introspección

Ninguna. Permisos detectables por auto-registro.
