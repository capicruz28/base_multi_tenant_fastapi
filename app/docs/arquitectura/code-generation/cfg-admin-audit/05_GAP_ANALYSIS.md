# Gap analysis — CFG Admin

**Paquete:** `cfg-admin-audit`  
**Fecha:** 2026-07-17

---

## 1. Matriz de cobertura (30 focos de auditoría)

| # | Foco | Estado | Notas |
|---|------|--------|-------|
| 1 | Estructura módulo CFG | ❌ Gap | Sin `app/modules/cfg/` |
| 2 | Entidad cfg_codigo_secuencia | ✅ | DDL + ORM |
| 3 | Modelos SQLAlchemy | ✅ | Table Core |
| 4 | Queries ERP | ❌ Gap | Sin `queries/cfg/` |
| 5 | Servicios admin | ❌ Gap | Solo seed onboarding |
| 6 | Endpoints | ❌ Gap | Cero rutas |
| 7 | OpenAPI | ❌ Gap | Recurso inexistente |
| 8 | Relación empresa | ✅ parcial | FK + scopes; sin API filtro admin |
| 9 | Relación cliente | ✅ | `cliente_id` obligatorio |
| 10 | Relación tenant | ✅ | Aislamiento Motor/Repo |
| 11 | Validaciones admin | ❌ Gap | Solo Motor |
| 12 | Policies Motor | ✅ | CodePolicy + PolicyResolver |
| 13 | SequenceCatalog | ✅ | Congelado Ola 1 |
| 14 | GenerationPolicy | ✅ | Read runtime; no admin |
| 15 | FormatStrategy | ⚠️ N/A | No hay clase; hay FormatterProfile |
| 16 | PrefixStrategy | ⚠️ N/A | Columna `prefijo` |
| 17 | SuffixStrategy | ❌ N/A | No modelado |
| 18 | NumberStrategy | ⚠️ N/A | padding + contador |
| 19 | Scope empresa | ✅ | ScopeType + fingerprint |
| 20 | Shared DB | ✅ | Patrón DEFAULT |
| 21 | Dedicated DB | ✅ | ADJ-03 session |
| 22 | Dep. ORG | ✅ consumidor | Admin no debe acoplarse a services ORG |
| 23 | Dep. INV | ✅ consumidor | Idem |
| 24 | Futuros ERP | ✅ diseño | Catalog + seed/lazy |
| 25 | Seguridad/permisos | ❌ Gap | Sin RBAC cfg |
| 26 | Auditoría admin | ⚠️ Gap parcial | Columnas existen; update no las setea |
| 27 | Riesgos arquitectónicos | Ver §2 | |
| 28 | Deuda técnica | Ver §3 | |
| 29 | Limitaciones actuales | Ver §4 | |
| 30 | Oportunidades simplificación | Ver §5 | |
| 31 | Reutilizables | Ver `02` | |
| 32 | Faltantes | Ver `02` / `06` | |

---

## 2. Riesgos arquitectónicos

| ID | Riesgo | Severidad | Observación |
|----|--------|-----------|-------------|
| R-01 | Implementar CRUD genérico sobre cfg incluyendo contador | Alta | Rompe SC-GOV-01 |
| R-02 | Permitir editar `generation_policy` en tenant | Alta | Divergencia Catalog/BR-UPD-02 |
| R-03 | Duplicar lógica de formato en admin | Media | Bypass Gateway |
| R-04 | Writes Dedicated sin session | Alta | ADJ-03 ya mitigado en Repo si se reusa |
| R-05 | Acoplar admin a ORG/INV services | Media | Rompe transversalidad |
| R-06 | Confundir “CFG store” con “módulo CFG” | Media | Documentación/comunicación |
| R-07 | Exponer filas lazy inexistentes como error 500 | Baja | Debe ser 404 o empty list |
| R-08 | Colisión de prefijos entre keys | Media | Requiere BR-CUST validator nuevo |

---

## 3. Deuda técnica relevante

| Deuda | Impacto admin |
|-------|---------------|
| `update_secuencia` sin `numero_inicial` | MVP B incompleto si no se extiende |
| `update_secuencia` sin audit columns | Gaps de trazabilidad |
| Sin queries paginadas | Listados grandes (~57+ eager + lazy) |
| Diseño admin desacoplado del código (julio 2026) | Riesgo de drift doc↔código si no se versiona decisión MVP |
| Nombres “Strategy” en docs históricos vs perfiles reales | Confusión de implementación |

---

## 4. Limitaciones actuales

1. Tenant Admin **no puede** inspeccionar secuencias vía API.
2. Cambios de prefijo solo vía SQL/manual/bootstrap — no hay canal oficial.
3. Preview/align existen en Gateway pero **no** están expuestos HTTP.
4. Diagnóstico drift Catalog↔cfg no automatizado.
5. Suffix no es configurable (no existe columna).
6. Fiscal fuera de alcance cfg (correcto, pero limita “un solo panel de códigos”).

---

## 5. Oportunidades de simplificación

| Oportunidad | Beneficio |
|-------------|-----------|
| MVP = solo GET + PATCH B + preview | Evita fase maintain/diagnóstico al inicio |
| Reusar Repo en lugar de Store para admin reads | Separación clara Motor vs Admin |
| Enricher Catalog único | Un solo join lógico metadatos |
| No introducir Strategy pattern | Alinear API a columnas reales |
| Reutilizar diseño `codigo-generation-admin` | Evitar re-especificar API |
| No tocar Motor/Gateway/Catalog en Ola CFG | Menor riesgo de regresión Ola 1 |

---

## 6. Componentes reutilizables (sin modificar Motor)

- `CfgCodigoSecuenciaTable`
- `CfgCodigoSecuenciaRepository` (lectura + update config)
- `CodigoGeneracionGateway.preview|align_counter|validate_manual`
- `SequenceCatalog` (read-only)
- `CodePolicy` / perfiles enums (exposición Read)
- Patrones session scope ORG/INV (`*_deps`, pagination shared)
- Docs `codigo-generation-admin/*`

---

## 7. Componentes faltantes (desarrollo nuevo)

- Módulo ERP completo `cfg`
- Queries + schemas + services + routers
- Validators admin (inmutables, anti-colisión, org_empresa)
- Catalog enricher
- Seed RBAC + menú
- Tests + OpenAPI
- Extensión menor repo: `numero_inicial` + audit fields (si MVP lo exige)
- Post-MVP: diagnóstico, align HTTP, audit log enriquecido

---

## 8. Porcentajes (reafirmación)

| Vista | Existe | Por construir |
|-------|--------|---------------|
| Fundación datos/runtime | ~90% | ~10% |
| Módulo admin ERP | ~0% | ~100% |
| Producto completo ponderado | **~30%** | **~70%** |
