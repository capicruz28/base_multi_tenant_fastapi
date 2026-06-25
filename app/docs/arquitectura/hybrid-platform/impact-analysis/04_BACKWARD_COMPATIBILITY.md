# 04 — Compatibilidad hacia Atrás

**Etapa:** 2 — Architectural Impact Assessment  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión  
**Principio:** Backward Compatibility First.

---

## 1. Propósito

Evaluar explícitamente si la evolución híbrida preserva el comportamiento actual para tenants Shared, Frontend, contratos API e IAM.

Respuesta por dimensión: **Sí | No | Parcialmente**, con justificación.

---

## 2. Resumen ejecutivo de compatibilidad

| Dimensión | Veredicto | Confianza |
|-----------|-----------|-----------|
| Tenants Shared existentes | **Sí** | Alta (con gate de regresión) |
| Frontend | **Sí** | Alta |
| OpenAPI | **Sí** | Alta |
| Endpoints REST | **Sí** | Alta |
| Contratos JWT | **Sí** | Alta |
| Contratos IAM / Session | **Sí** | Alta |
| Lógica ERP | **Sí** | Alta |
| Onboarding Shared | **Sí** (externamente) | Media (cambio interno posible) |
| Scripts / repair legacy | **Parcialmente** | Media |
| Performance Shared | **Sí** | Media (vigilar overhead routing) |

---

## 3. Tenants Shared existentes

### Veredicto: **Sí**

**Justificación:**

- Modo Shared permanece como **default** (`database_type = single`)
- Resolución de conexión para Shared debe producir **idéntico almacén y comportamiento** que hoy
- Filtro `cliente_id` continúa aplicándose — semántica de aislamiento unchanged
- Metadata `cliente_conexion` ausente implica fallback a Shared (comportamiento AS-IS)
- Ningún tenant Shared requiere migración de datos ni cambio de configuración

**Condiciones:**

1. Capa 1–2 no altera path single-DB existente
2. Tests de regresión Shared ejecutados en cada fase
3. Engine cache no introduce conexión cruzada

**Riesgo residual:** Regresión en refactor de `queries_async` — mitigable con tests.

---

## 4. Frontend

### Veredicto: **Sí**

**Justificación:**

- Frontend no conoce modo de instalación
- No consume metadata de almacén
- Depende de: subdominio, JWT, endpoints REST, cookies refresh
- Ninguno de estos elementos cambia en contrato
- Flujos multiempresa, impersonación, sesiones admin — preservados

**Excepciones (no breaking):**

- Platform Admin podría recibir **pantallas nuevas** para gestión dedicated (opt-in, rutas nuevas)
- Estados `Provisioning` podrían mostrar UX de espera — requiere FE solo si se expone estado en API existente

**Recomendación:** No añadir campos obligatorios a responses existentes. Estados de provisioning vía endpoint nuevo o campo opcional.

---

## 5. OpenAPI

### Veredicto: **Sí**

**Justificación:**

- Mismos paths, methods, tags
- Mismos `response_model`
- Mismos schemas Pydantic en endpoints existentes
- `operationId` estables

**Aditivo permitido:**

- Nuevos endpoints bajo `/conexiones` o `/clientes/{id}/provisioning-status`
- Nuevos campos **opcionales** en schemas Platform (ej. `tipo_instalacion` ya existe en ClienteRead)

**Prohibido:**

- Renombrar rutas
- Cambiar tipos de campos existentes
- Eliminar endpoints consumidos por FE

---

## 6. Endpoints REST

### Veredicto: **Sí**

**Desglose:**

| Grupo endpoints | Compatible |
|-----------------|------------|
| `/auth/*` | Sí |
| `/org/*`, `/inv/*`, … ERP | Sí |
| `/usuarios`, `/roles`, `/permisos` | Sí |
| `/clientes` POST/GET/PUT | Sí (response shape) |
| `/superadmin/*` | Sí |
| `/modulos-v2/*` | Sí |
| `/health` | Sí |

**Parcialmente:**

| Caso | Motivo |
|------|--------|
| `POST /clientes/` timing | Dedicated podría tardar más; mismo 200 final pero latencia distinta |
| Repair scripts vía API | No hay API pública hoy — N/A |

---

## 7. Contratos JWT

### Veredicto: **Sí**

**Justificación:**

- Claims set unchanged (certificación FE)
- `cliente_id` sigue siendo identificador de tenant lógico
- `empresa_id`, `sid`, impersonación flags — sin cambio
- TTL, algoritmo, refresh rotation — sin cambio
- Dedicated no añade claims de infraestructura al token (correcto — transparency)

**Riesgo:** Si sesiones dedicated fallan en refresh por routing, FE ve 401 — es bug de infra, no cambio de contrato.

---

## 8. Contratos IAM / Session

### Veredicto: **Sí**

**Justificación:**

- IAM V2 services operan sobre UoW + queries — conexión transparente
- Session probe `/auth/me` — mismo payload
- Logout idempotente — sin cambio
- Impersonación — mismo flujo; infra resuelve almacén target
- Redis keys patterns — sin cambio

**Parcialmente:**

| Aspecto | Nota |
|---------|------|
| Persistencia sesión en dedicated tenant | Misma API, posible latencia distinta si ADR-002 mantiene central |
| V1 refresh coexistence | Ya existe; sin cambio |

---

## 9. Lógica ERP

### Veredicto: **Sí**

**Justificación:**

- Cero modificaciones planificadas en services, queries, endpoints ERP
- Reglas de workflow, validaciones, paginación — intactas
- Scope `cliente_id` + `empresa_id` — intacto
- INV UoW transaccional — intacto

**Condición:** Infraestructura debe presentar al ERP el **mismo contrato de acceso a datos** que hoy (execute_* + UoW).

---

## 10. Onboarding (compatibilidad interna)

### Veredicto: **Parcialmente** (externo Sí, interno evoluciona)

| Aspecto | Compatible |
|---------|------------|
| Response `ClienteRead` + credenciales | Sí |
| Validaciones pre-alta | Sí |
| Tablas creadas (resultado final Shared) | Sí |
| Transacción única interna | **No** — evoluciona a saga |
| Tiempo de respuesta dedicated | Parcial — puede requerir async |

**Impacto FE:** Ninguno si response final idéntico. Dedicated async requeriría polling — endpoint nuevo, no breaking.

---

## 11. Scripts, bootstrap, operaciones

### Veredicto: **Parcialmente**

| Elemento | Compatible |
|----------|------------|
| `bootstrap_v2_sql_apply.ps1` Shared | Sí |
| Seeds S010/S020 | Sí |
| Repair scripts tenant | Parcial — pueden asumir BD única |
| CI pipeline | Parcial — extensión dedicated tests |

---

## 12. Matriz de compatibilidad detallada

| Consumidor | Expectativa | Preservada | Mecanismo |
|------------|-------------|------------|-----------|
| FE login | JWT + cookies | Sí | IAM intacto |
| FE ERP screens | REST + pagination | Sí | Endpoints intactos |
| FE tenant admin | Users/RBAC/ORG | Sí | Platform/Tenant intacto |
| FE superadmin | Clientes, módulos | Sí | Platform intacto |
| Mobile auth | Refresh en body | Sí | Auth endpoints |
| OpenAPI codegen | Schemas | Sí | Sin breaking changes |
| Integración staging | Shared tenants | Sí | Default path |
| pytest ERP unit | Mocks | Sí | Sin cambio |
| pytest integration | DB real | Parcial | Nuevos fixtures dedicated |

---

## 13. Escenarios de incompatibilidad a evitar

| Escenario | Impacto | Prevención |
|-----------|---------|------------|
| Cambiar claim JWT | FE auth roto | Protección absoluta |
| Eliminar filtro tenant Shared | Fuga datos | Test aislamiento |
| Cambiar envelope paginación | FE listados rotos | Protección schemas |
| Bifurcar endpoints ERP | Fork lógico | Prohibido |
| `database_type` en response ERP | FE acoplado a infra | Prohibido |
| Cambiar status codes auth | FE error handling | Protección contrato |

---

## 14. Gate de compatibilidad (criterios de aprobación etapa técnica)

Antes de considerar Dedicated MVP listo:

1. **100%** tests Shared existentes pasan sin modificación de tests ERP
2. Contrato auth certificado re-validado (checklist FE)
3. Smoke test FE en staging Shared post-cambio infra
4. OpenAPI diff sin breaking changes en endpoints existentes
5. Tenant Shared de staging idéntico en comportamiento (comparison audit)

---

## 15. Conclusión

La estrategia híbrida es **compatible hacia atrás por diseño** si se respeta la superficie de cambio delimitada en `03_CHANGE_SURFACE.md`.

La única área **parcial** es onboarding interno y operaciones — sin impacto en contratos FE si se mantiene response shape y se usan extensiones aditivas para async dedicated.

**Tenants Shared existentes deben funcionar exactamente igual** — esto es requisito no negociable.
