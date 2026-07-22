# Revisión de arquitectura

**Paquete:** `cfg-backend-final-review`  
**Fecha:** 2026-07-17

---

## 1. Arquitectura interna del módulo

| Aspecto | Evaluación |
|---------|------------|
| Capas V4 (presentation → services → queries) | **Correcto** |
| Ausencia de `domain/` / infra por módulo | **Correcto** |
| Orquestación vs Motor | **Correcto** |
| 3 helpers separados (validator, enricher, context builder) | **Sobreingeniería leve** — ver opcional O-01 |
| Diagrama con `SVC → REPO` | **Inconsistente** con decisión “queries canónicas” — **G-06** |

**Veredicto arquitectura:** sólida; corregir ambigüedad Repo y opcionalmente colapsar helpers.

---

## 2. Dependencias (`cfg_deps`)

| Decisión | Evaluación |
|----------|------------|
| `get_cfg_session_client_id` vía `require_session_cliente_id` | Alineado ORG/INV |
| `require_cfg_tenant_erp_session` (sin empresa obligatoria) | **Correcto** para recurso TENANT transversal |
| Scope preview desde fila | **Correcto** — evita override body |

Sin hallazgos bloqueantes en deps.

---

## 3. Consistencia con STANDARDS V4

| Norma V4 | Blueprint | Hallazgo |
|----------|-----------|----------|
| Soft delete: `DELETE` + `POST .../reactivar` | `POST activar` + `POST desactivar` | **Divergencia — G-01 obligatorio** |
| RBAC `{modulo}.{recurso}.{accion}` | `cfg.secuencias.*` | OK |
| `cliente_id` sesión, no body | Cumple | OK |
| DEFAULT + tenant session | Cumple | OK |
| Paginación opt-in `page` | Cumple en intención | Roto si SQL page + filtro post-enrich — **G-04** |
| Orden schemas → queries → services → routers | Cumple en plan | OK |
| No ADMIN para datos ERP | Cumple | OK |

---

## 4. Consistencia con ORG / INV

| Patrón ORG/INV | Blueprint | Hallazgo |
|----------------|-----------|----------|
| Soft-disable DELETE/reactivar | activar/desactivar | **G-01** |
| UoW `get_connection_for_tenant` | Sí | OK |
| Funciones `*_servicio` | Sí | OK |
| Enrich/catalog propio | N/A (cfg específico) | OK |
| Permiso `actualizar` para reactivar | Blueprint usa `actualizar` en activar/desactivar | Se conserva con G-01 |

La divergencia soft-delete no está justificada por dominio: `es_activo` en cfg es el mismo concepto de soft-enable que en maestros. Mantener endpoints inventados aumenta superficie FE/BE sin beneficio.

---

## 5. Consistencia con el Motor

| Aspecto | Evaluación |
|---------|------------|
| `Gateway.preview` → PreviewReader | Correcto; **no** chequea `es_activo` |
| Ambigüedad blueprint sobre `SEQUENCE_INACTIVE` en preview | **G-05** — alinear con Motor AS-IS + diseño funcional (preview en inactiva permitido) |
| No usar allocate/align | Correcto |
| Catalog read-only | Correcto |
| Fórmula `numero_inicial` en PreviewReader | `max(ultimo, inicial-1)+1` — conflicto “absurdo” del blueprint **no está definido** frente al Motor — **G-03** |

---

## 6. Shared / Dedicated

| Aspecto | Evaluación |
|---------|------------|
| Session tenant obligatoria | Correcto y crítico |
| Prohibición Path A ADMIN | Correcto |
| Riesgo residual | Extender Repo “por comodidad” reintroduce Path A — **G-06** cierra la puerta en MVP |

---

## 7. Escalabilidad futura

| Tema | Evaluación |
|------|------------|
| Align / diagnóstico fuera de MVP | Correcto |
| Filtro `modulo_codigo` in-memory | Aceptable volumen bajo **si** no se pagina en SQL antes — **G-04** |
| Colisión formato global | Prematura y frágil — **G-02** defer |
| Helpers/files extra | Mantenimiento ↑ sin necesidad MVP — O-01 |

---

## 8. Auditoría

| Aspecto | Evaluación |
|---------|------------|
| `usuario_actualizacion_id` + `fecha_actualizacion` en mutaciones | Suficiente MVP |
| Historial dedicado | Correctamente post-MVP |
| Preview sin audit BD | Correcto |

Sin ajuste obligatorio.
