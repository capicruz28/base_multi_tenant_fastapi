# Runtime Snapshot — Contrato de integración Frontend

**Tipo:** Contrato público Backend → Frontend  
**Estado:** Oficial — Backend implementado y validado  
**Versión del contrato de datos:** `1.0` (`schema_version`)  
**Fecha:** 2026-07-20  
**Audiencia:** Proyecto Frontend (consumidores ERP)  
**Autoridad:** Este documento es la **única referencia funcional** para consumir el Runtime Snapshot. No sustituye los contratos CREATE de ORG/INV; los complementa.

---

## 1. Objetivo

El **Runtime Snapshot** es la proyección de solo lectura que el Backend expone para que el Frontend conozca, por tenant:

- qué secuencias de código están **disponibles**;
- cuál es la **`generation_policy` efectiva**;
- cuál es el **formato efectivo** (prefijo, separador, longitud);
- si la secuencia está **activa**;
- capacidades estáticas útiles para UX (`supports_preview`, `allow_manual`, etc.).

Sustituye el uso del Manifest Frontend como fuente de `generation_policy` (y de formato tenant-specific).

**No asigna códigos.** La asignación real ocurre en el CREATE del módulo ERP (ORG, INV, …) en el Backend.

---

## 2. Endpoint oficial

```http
GET /api/v1/cfg/runtime/snapshot
```

| Atributo | Valor |
|----------|--------|
| Método | `GET` |
| Query params | Ninguno (v1.0) |
| Body | Ninguno |
| Respuesta éxito | `200` + documento Snapshot completo del tenant |

Este endpoint **no** es la API de administración CFG (`/api/v1/cfg/secuencias`).

---

## 3. Autenticación

| Requisito | Detalle |
|-----------|---------|
| Autenticación | Sesión ERP estándar (JWT + sesión completa), igual que el resto de APIs ERP |
| Tenant | `cliente_id` operativo de la sesión (incluye impersonación) |
| Permisos CFG Admin | **No** se exige `cfg.secuencias.consultar` ni `cfg.secuencias.actualizar` |

Cualquier usuario ERP autenticado con sesión de tenant válida puede leer el Snapshot. La autorización de **crear** entidades sigue en los permisos del módulo (`org.*.crear`, `inv.*.crear`, etc.).

---

## 4. Estructura del Response

### 4.1 Documento raíz

| Campo | Tipo | Significado funcional |
|-------|------|------------------------|
| `schema_version` | string | Versión del contrato de datos (hoy `"1.0"`). El Frontend debe leerla para evoluciones futuras. |
| `generated_at` | datetime (ISO-8601) | Instantánea en que Backend construyó esta proyección. Solo informativo. |
| `content_revision` | string (hex) | Huella del contenido. Útil para detectar si el Snapshot cambió respecto a una copia previa. |
| `items` | array | Lista de secuencias disponibles para el tenant. Puede ser `[]`. |

### 4.2 Cada elemento de `items`

| Campo | Tipo | Significado funcional |
|-------|------|------------------------|
| `sequence_key` | string | Identidad canónica de la secuencia (ej. `org_sucursal`, `inv_categoria_producto`). |
| `modulo_codigo` | string | Módulo ERP dueño (ej. `ORG`, `INV`). |
| `scope_type` | string | Ámbito de la fila: `TENANT` \| `EMPRESA` \| `ALMACEN` \| `PUNTO_VENTA`. |
| `empresa_id` | uuid \| null | Binding de empresa cuando aplica; `null` en scope `TENANT`. |
| `almacen_id` | uuid \| null | Binding de almacén cuando aplica. |
| `punto_venta_id` | uuid \| null | Binding de punto de venta cuando aplica. |
| `generation_policy` | string | Política efectiva del tenant (ver §5). |
| `es_activo` | boolean | Si la secuencia está operativa (ver §6). |
| `prefijo` | string | Prefijo efectivo configurado para el tenant/scope. |
| `separador` | string | Separador efectivo (`""` o `"-"` típicamente). |
| `longitud_numero` | integer | Padding / longitud de la parte numérica efectiva. |
| `supports_preview` | boolean | Si el sistema permite previsualizar el próximo código (capacidad). |
| `allow_manual` | boolean | Si el tipo de secuencia admite código manual a nivel de diseño (capacidad). **No** reemplaza `generation_policy`. |
| `normalize_case` | string | Normalización esperada del código (`UPPER` \| `AS_IS`). |
| `max_output_length` | integer | Longitud máxima permitida del código generado o manual. |

Campos administrativos (`ultimo_numero`, auditoría, `policy_drift`, `config_locked`, etc.) **no** forman parte de este contrato.

---

## 5. `generation_policy` (vista consumidor)

Fuente de verdad: configuración efectiva del tenant en Backend. El Frontend **no** debe tomar la policy del Manifest.

| Valor | Comportamiento UX esperado en CREATE |
|-------|--------------------------------------|
| `AUTO_REQUIRED` | El código se genera en Backend. El Frontend **no** debe ofrecer override manual en operación normal. Omitir el campo código (o no enviarlo). |
| `AUTO_DEFAULT` | Backend genera si el Frontend **omite** el código. El usuario **puede** enviar un código manual opcional (si la UX lo habilita). |
| `MANUAL_ONLY` | El usuario **debe** proporcionar el código. No omitir el campo. |

**Regla:** la decisión final de aceptar/rechazar manual la aplica el Backend en el CREATE. El Snapshot solo orienta la UI.

Relación con `allow_manual`:

- `allow_manual=false` → la secuencia no está diseñada para manual; no forzar UX de override aunque la policy diga otra cosa (caso excepcional / soporte).
- En operación normal, priorizar `generation_policy` para mostrar/ocultar/requerir el campo.

---

## 6. `es_activo`

| Valor | Interpretación Frontend |
|-------|-------------------------|
| `true` | Secuencia usable para flujos de alta que dependan de ella. |
| `false` | Secuencia existe pero está **desactivada**. No ofrecer creación que dependa de esa secuencia; mostrar mensaje de configuración / contactar admin. |

Una secuencia inactiva **sí puede aparecer** en el Snapshot. No confundir con “no contratada” (§8).

---

## 7. Resolución por scope

El Snapshot puede contener **varios ítems** con el mismo `sequence_key` (p. ej. una fila por empresa).

### Algoritmo de resolución (Frontend)

1. Identificar la `sequence_key` de la entidad del formulario (contrato del módulo, ej. cargo → `org_cargo`).
2. Leer `scope_type` de los candidatos con esa key (todos comparten el mismo tipo de scope).
3. Filtrar según el contexto de sesión / formulario:

| `scope_type` | Criterio de match |
|--------------|-------------------|
| `TENANT` | Único ítem; `empresa_id` / `almacen_id` / `punto_venta_id` son `null`. |
| `EMPRESA` | Ítem cuyo `empresa_id` = empresa activa de sesión (o la del formulario). |
| `ALMACEN` | Ítem cuyo `almacen_id` (y empresa si aplica) coincide con el contexto. |
| `PUNTO_VENTA` | Ítem cuyo `punto_venta_id` coincide con el contexto. |

4. Si no hay match para el contexto actual → tratar como **no disponible** en ese scope (equivalente práctico a §8 para esa operación).

**No** usar el primer ítem de la lista sin filtrar por scope.

---

## 8. `sequence_key` ausente en el Snapshot

Si la key esperada **no** está en `items` (tras filtrar por scope):

| Causa típica | Interpretación |
|--------------|----------------|
| Módulo no contratado o inactivo | El tenant no tiene derecho operativo a esas secuencias. |
| Secuencia no provisionada | No hay configuración Runtime para esa key. |

**El Frontend no debe:**

- inventar defaults desde Manifest;
- asumir `AUTO_DEFAULT`;
- fabricar prefijo/formato.

**Debe:** bloquear o degradar el flujo con mensaje claro (“módulo/secuencia no disponible”) y no enviar CREATE que dependa de esa generación.

---

## 9. Qué garantiza Backend

1. El Snapshot refleja solo secuencias de **módulos contratados y activos** del tenant.
2. `generation_policy`, `prefijo`, `separador`, `longitud_numero` y `es_activo` son la configuración **efectiva** del tenant/scope.
3. Shared y Dedicated usan el **mismo** contrato HTTP y el mismo shape de response.
4. Multiempresa: un ítem por binding de scope cuando existan varias filas.
5. El CREATE de ORG/INV/… aplica la policy y asigna el código de forma autoritativa.
6. Este endpoint es de **solo lectura** y no muta contadores ni configuración.

---

## 10. Qué NO debe asumir el Frontend

1. Que el Manifest sea dueño de `generation_policy` o del formato tenant.
2. Que todas las `sequence_key` del catálogo estático existan en el Snapshot.
3. Que `items` vacíos sea error HTTP (es `200` con `items: []`).
4. Que pueda calcular el próximo código correlativo (el Snapshot no expone contador).
5. Que `allow_manual` sustituya a `generation_policy`.
6. Que este endpoint reemplace el CREATE del módulo ERP.
7. Que existan query params (`empresa_id`, `sequence_key`, …) en v1.0 — el documento es **completo**; el filtrado es local.
8. Que campos admin (`ultimo_numero`, drift, locks) vayan a aparecer aquí.

---

## 11. Responsabilidades de Backend

| Responsabilidad | Detalle |
|-----------------|---------|
| Exponer Snapshot | `GET /api/v1/cfg/runtime/snapshot` |
| Filtrar por contratación | Solo módulos activos del tenant |
| Publicar policy/formato efectivos | Por cada secuencia/scope provisionado |
| Asignar códigos | En CREATE de dominio (ORG/INV/…), no en este GET |
| Administrar secuencias | API Admin CFG (fuera de este contrato) |

---

## 12. Responsabilidades de Frontend

| Responsabilidad | Detalle |
|-----------------|---------|
| Obtener Snapshot | Llamar el endpoint con sesión ERP |
| Resolver ítem | Por `sequence_key` + scope de sesión/formulario |
| Adaptar UX | Según `generation_policy`, `es_activo`, capacidades |
| Enviar CREATE | Al módulo ERP; omitir o enviar código según policy |
| No usar Manifest como SSOT de policy | Tras adoptar este contrato |
| Tratar ausencia | Key no presente → no disponible |

---

## 13. Ejemplos de respuesta JSON

### 13.1 Tenant con ORG (multiempresa) e ítem TENANT

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-20T23:15:00.123456",
  "content_revision": "9ce3ac6c5e76a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234",
  "items": [
    {
      "sequence_key": "org_empresa",
      "modulo_codigo": "ORG",
      "scope_type": "TENANT",
      "empresa_id": null,
      "almacen_id": null,
      "punto_venta_id": null,
      "generation_policy": "AUTO_DEFAULT",
      "es_activo": true,
      "prefijo": "EMP",
      "separador": "",
      "longitud_numero": 3,
      "supports_preview": true,
      "allow_manual": true,
      "normalize_case": "UPPER",
      "max_output_length": 20
    },
    {
      "sequence_key": "org_sucursal",
      "modulo_codigo": "ORG",
      "scope_type": "EMPRESA",
      "empresa_id": "11111111-1111-1111-1111-111111111111",
      "almacen_id": null,
      "punto_venta_id": null,
      "generation_policy": "AUTO_DEFAULT",
      "es_activo": true,
      "prefijo": "SUC",
      "separador": "",
      "longitud_numero": 3,
      "supports_preview": true,
      "allow_manual": true,
      "normalize_case": "UPPER",
      "max_output_length": 20
    },
    {
      "sequence_key": "org_sucursal",
      "modulo_codigo": "ORG",
      "scope_type": "EMPRESA",
      "empresa_id": "22222222-2222-2222-2222-222222222222",
      "almacen_id": null,
      "punto_venta_id": null,
      "generation_policy": "MANUAL_ONLY",
      "es_activo": true,
      "prefijo": "SUX",
      "separador": "-",
      "longitud_numero": 4,
      "supports_preview": true,
      "allow_manual": true,
      "normalize_case": "UPPER",
      "max_output_length": 20
    }
  ]
}
```

**Uso:** con empresa activa `11111111-…`, el formulario de sucursal usa el ítem con `prefijo: "SUC"` y `AUTO_DEFAULT`, no el de la otra empresa.

### 13.2 Secuencia inactiva

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-20T23:16:00.000000",
  "content_revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "items": [
    {
      "sequence_key": "org_departamento",
      "modulo_codigo": "ORG",
      "scope_type": "EMPRESA",
      "empresa_id": "11111111-1111-1111-1111-111111111111",
      "almacen_id": null,
      "punto_venta_id": null,
      "generation_policy": "AUTO_DEFAULT",
      "es_activo": false,
      "prefijo": "DEP",
      "separador": "",
      "longitud_numero": 3,
      "supports_preview": true,
      "allow_manual": true,
      "normalize_case": "UPPER",
      "max_output_length": 20
    }
  ]
}
```

### 13.3 Snapshot vacío

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-07-20T23:17:00.000000",
  "content_revision": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "items": []
}
```

HTTP sigue siendo **200**. Significa: no hay secuencias Runtime disponibles para ese tenant (p. ej. sin módulos ERP activos).

---

## 14. Versionado del contrato

| Campo / mecanismo | Uso |
|-------------------|-----|
| `schema_version` | Versión del **shape** de datos. Hoy `"1.0"`. |
| `content_revision` | Versión del **contenido** de esta proyección (cambia si cambian ítems/policy/formato). |
| URI | Estable: `GET /api/v1/cfg/runtime/snapshot` (sin query en v1.0). |

**Compatibilidad:**

- Cambios aditivos de campos → nuevo `schema_version` menor (p. ej. `1.1`) documentado en este mismo paquete.
- Cambios incompatibles → nuevo major y guía de migración Frontend.
- El Frontend debe tolerar campos desconocidos adicionales si aparecen en minors compatibles, y debe validar `schema_version` conocida.

---

## Referencia rápida

| Pregunta | Respuesta |
|----------|-----------|
| ¿De dónde sale la policy? | Runtime Snapshot (`generation_policy`), no Manifest |
| ¿Quién genera el código? | Backend en CREATE del módulo ERP |
| ¿Qué hago si falta la key? | Tratar como no disponible; no inventar defaults |
| ¿Admin CFG? | Otro path (`/cfg/secuencias`); fuera de este contrato |

---

*Documento oficial de integración Backend → Frontend. Pendiente de validación explícita antes de iniciar trabajo en el proyecto Frontend.*
