# Flujos de datos (MVP)

**Paquete:** `cfg-backend-mvp-design`  
**Fecha:** 2026-07-17

---

## 1. Lectura — listado

```text
HTTP GET /cfg/secuencias
  → require_cfg_tenant_erp_session + consultar
  → get_cfg_session_client_id
  → list_codigo_secuencias_servicio(cliente_id, filters, pagination, sort)
       → get_connection_for_tenant(cliente_id)
       → list_codigo_secuencias(session, …)
       → [opcional count si page]
       → cfg_catalog_enricher.enrich_many(rows)
       → filter modulo_codigo in-memory
       → build list | PaginatedResponse
  ← 200
```

**Shared / Dedicated:** solo cambia el binding de `get_connection_for_tenant`; el flujo es idéntico.

---

## 2. Lectura — detalle

```text
HTTP GET /{secuencia_id}
  → get_codigo_secuencia_by_id(session, secuencia_id, cliente_id)
  → None? NotFoundError 404
  → enrich_one
  ← CodigoSecuenciaRead (config_locked, policy_drift)
```

---

## 3. Escritura — PATCH configuración

```text
HTTP PATCH /{secuencia_id}
  → get fila (session)
  → cfg_secuencia_validator.validate_update(row, payload, cliente_id, session)
       → org_empresa lock
       → extra forbid already in schema
       → prefijo/pad/separador/piso
       → colisión formato (query peer rows same cliente)
  → session.begin()
  → update_codigo_secuencia_config(..., usuario_actualizacion_id, fecha)
  → commit
  → re-read + enrich
  ← CodigoSecuenciaRead
```

**Integración Repo:** no requerida si queries canónicas implementan el UPDATE.  
**Integración Gateway:** ninguna en PATCH.  
**Integración Catalog:** solo enrich respuesta; no escribe Catalog.

---

## 4. Escritura — activar / desactivar

```text
HTTP POST .../activar|desactivar
  → get fila
  → desactivar + org_empresa? → ValidationError ORG_EMPRESA_CFG_LOCKED
  → begin → set_codigo_secuencia_activo(es_activo=…) + audit
  → enrich ← Read
```

---

## 5. Preview — integración Gateway

```text
HTTP POST .../preview
  → get fila (tenant session)
  → cfg_preview_context_builder.from_row(row, cliente_id)
       GenerationContext(
         client_id=cliente_id,
         operation=GenerationOperation.PREVIEW,
         empresa_id=row.empresa_id,
         almacen_id=row.almacen_id,
         punto_venta_id=row.punto_venta_id,
       )
  → CodigoGeneracionGateway.preview(row.sequence_key, context, session)
  → map PreviewResult + row.ultimo_numero → CodigoSecuenciaPreviewResponse
```

| Garantía | Cómo se asegura |
|----------|-----------------|
| No consume contador | PreviewReader AS-IS; test spy/assert ultimo_numero igual antes/después |
| Scope correcto | IDs desde fila, no body |
| Dedicated-safe | Misma session tenant |

Si la fila no existe en Store para el fingerprint (anomalía): Gateway `CFG_SEQUENCE_NOT_FOUND` → 404.

---

## 6. SequenceCatalog enrich

```text
row.sequence_key
  → if SequenceCatalog.contains(key):
       defn = SequenceCatalog.get(key)
       map fields → Read enrich
       policy_drift = (row.generation_policy != defn.policy.value)
    else:
       enrich nulls; policy_drift = false
config_locked = (sequence_key == "org_empresa")
```

Catalog **nunca** se muta.

---

## 7. Matriz de dependencias por operación

| Operación | Queries | Repo | Gateway | Catalog | UoW write |
|-----------|---------|------|---------|---------|-----------|
| List | ✅ | ❌ | ❌ | ✅ enrich | ❌ |
| Detail | ✅ | ❌ | ❌ | ✅ | ❌ |
| PATCH | ✅ | ❌ (opc.) | ❌ | ✅ post | ✅ |
| Activar/Desactivar | ✅ | ❌ | ❌ | ✅ post | ✅ |
| Preview | ✅ get | ❌ | ✅ | enrich opcional | ❌ (read session) |

---

## 8. Onboarding vs Admin (no mezclar)

```text
Platform onboarding
  → CfgCodigoSecuenciaRepository.insert_secuencia (session tenant)
  → NO pasa por /cfg HTTP

Admin HTTP /cfg
  → queries/cfg + Gateway.preview
  → NO inserta filas nuevas
```

---

## 9. Auditoría en el flujo de mutación

```text
antes: row
después: UPDATE SET ..., fecha_actualizacion=NOW, usuario_actualizacion_id=:uid
respuesta: Read con timestamps actualizados
```

No hay tabla de historial en MVP.
