# 02 — Request Lifecycle

**Etapa:** 4 — Runtime Architecture  
**Fecha:** 2026-06-25  
**Estado:** Borrador para revisión

---

## 1. Propósito

Documentar **paso a paso** el ciclo completo de una petición HTTP desde el cliente hasta la respuesta, indicando responsable, entradas, salidas, información propagada y prohibiciones.

---

## 2. Pipeline canónico

```
Cliente → Nginx → FastAPI → Middleware → Tenant Resolution → Context
→ Persistence Resolution (en acceso datos) → Application → Queries → Response
```

---

## 3. Fases detalladas

### Fase 0 — Cliente

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Cliente (FE / mobile) |
| **Entradas** | Acción usuario, tokens almacenados, Host del tenant |
| **Salidas** | HTTP Request (method, path, headers, body, cookies) |
| **Propagado** | `Host`, `Authorization` (si aplica), cookies refresh |
| **Nunca debe** | Enviar Installation Mode; elegir almacén; enviar tenant_id arbitrario para autorización |

---

### Fase 1 — Nginx / Edge

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Reverse proxy |
| **Entradas** | Request TLS, routing rules |
| **Salidas** | Request forward a upstream FastAPI |
| **Propagado** | `Host` original (crítico); `X-Forwarded-*` si configurado |
| **Nunca debe** | Reescribir Host a dominio incorrecto en producción; strip subdominio tenant |

---

### Fase 2 — FastAPI Ingress

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | HTTP router |
| **Entradas** | Request, route table |
| **Salidas** | Handler seleccionado + dependency chain |
| **Propagado** | Request object, matched path |
| **Nunca debe** | Resolver tenant; abrir conexión datos |

---

### Fase 3 — Middleware Stack

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Cross-cutting pipeline |
| **Entradas** | Request sin contexto |
| **Salidas** | Request con Tenant Context registrado |
| **Propagado** | Tenant identifier, installation metadata reference (infra interna) |
| **Nunca debe** | Ejecutar lógica ERP; validar JWT (ocurre en gates posteriores) |

**Sub-pasos:**

1. CORS preflight (si aplica)
2. Rate limiting (si aplica)
3. Tenant Resolution
4. Registro cleanup al finalizar request

---

### Fase 4 — Tenant Resolution

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Ingress / Tenant Resolution |
| **Entradas** | Host header, Tenant Registry (Control Plane) |
| **Salidas** | Tenant Context válido o error 400/404 |
| **Propagado** | Tenant identifier, tenant state (activo/suspendido), subdomain binding |
| **Nunca debe** | Usar tenant del body para routing; confiar Origin en producción como primario |

**Errores:**

- Host inválido → 400
- Subdominio desconocido → 404 (tenant not found)
- Tenant suspendido → 403 (post-lookup, pre o post auth según endpoint)

---

### Fase 5 — Context Establishment (pre-handler)

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Security Gates + deps |
| **Entradas** | Tenant Context, headers auth |
| **Salidas** | Identity Context, Authorization Context, Company Context (si ERP) |
| **Propagado** | User identifier, permissions effective set, company identifier, session state |
| **Nunca debe** | Sobrescribir Tenant Context desde JWT sin regla impersonation |

**Orden:**

1. Decode JWT → Identity Context draft
2. Validate tenant access (JWT tenant vs Host tenant)
3. Session probe (si endpoint lo requiere)
4. RBAC permission check
5. ERP session contract → Company Context

---

### Fase 6 — Application Layer

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Platform / IAM / ERP services |
| **Entradas** | Contextos lógicos + DTO request |
| **Salidas** | Resultado negocio o excepción mapeada |
| **Propagado** | Tenant identifier, company identifier como parámetros explícitos o contexto |
| **Nunca debe** | Resolver almacén; consultar Installation Mode; abrir conexión directa |

---

### Fase 7 — Persistence Resolution

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Persistence Gateway (L6) |
| **Entradas** | Operation type (control vs tenant data), Tenant Context |
| **Salidas** | Persistence Context bound a store correcto |
| **Propagado** | Store route (control plane | tenant data plane) |
| **Nunca debe** | Exponer Persistence Context a L5; ejecutar reglas negocio |

**Reglas:**

- Operación Control Plane → Control Plane Store
- Operación Tenant Data → lookup Installation Mode metadata → Tenant Data Store
- Fallback Shared si metadata ausente (tenants legacy)

**Nota canónica vs AS-IS:** Resolución puede ocurrir por operación de datos. Ver RD-01.

---

### Fase 8 — Data Access (Queries)

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Persistence Gateway |
| **Entradas** | Data operation + Persistence Context |
| **Salidas** | Rows / affected count |
| **Propagado** | Tenant filter (shared); scope filters |
| **Nunca debe** | Skip tenant filter en tenant data sin bypass autorizado |

---

### Fase 9 — Response Construction

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Handler + exception mappers |
| **Entradas** | Service result |
| **Salidas** | HTTP Response (status, body, cookies si auth) |
| **Propagado** | Ningún dato infra |
| **Nunca debe** | Incluir stack trace SQL; incluir Installation Mode |

---

### Fase 10 — Teardown

| Aspecto | Detalle |
|---------|---------|
| **Responsable** | Middleware finally |
| **Entradas** | Request completada |
| **Salidas** | Contextos destruidos |
| **Propagado** | Ninguno (limpieza) |
| **Nunca debe** | Dejar Tenant Context en task hijo async |

---

## 4. Variantes por tipo de endpoint

| Tipo | Fases omitidas | Fases extra |
|------|----------------|-------------|
| Health público | Identity, Company | — |
| Auth login | Identity previa | Post-auth session creation |
| Platform admin | Company | Superadmin gate |
| ERP operativo | — | ERP session contract |
| Static/OpenAPI | Tenant parcial | — |

---

## 5. Información propagada (consolidado)

| Dato lógico | Origen | Consumidores | Scope |
|-------------|--------|--------------|-------|
| Tenant identifier | Host → Registry | Todos | Request |
| User identifier | JWT | IAM, ERP audit | Request |
| Company identifier | JWT / selection | ERP | Request |
| Effective permissions | IAM resolver | Gates, ERP | Request + cache |
| Session identifier | JWT / IAM | IAM probe | Request |
| Installation mode | Metadata lookup | L6 only | Persistence op |
| Store route | L6 resolution | L6 only | Data op |

---

## 6. Timeline conceptual (ERP request autenticada)

```
t0  Request arrives Edge
t1  FastAPI routing
t2  Tenant Context set
t3  JWT validated → Identity Context
t4  RBAC check → Authorization Context
t5  ERP gate → Company Context
t6  Handler invokes service
t7  Service invokes data access (×N ops)
t7i Persistence resolve per op (canonical)
t8  Response assembled
t9  Contexts destroyed
```

---

## 7. Errores y terminación anticipada

| Punto fallo | HTTP típico | Contextos |
|-------------|-------------|-------------|
| Host inválido | 400 | Teardown |
| Tenant not found | 404 | Teardown |
| JWT inválido | 401 | Teardown |
| Tenant mismatch | 403 | Teardown |
| Permission denied | 403 | Teardown |
| Session revoked | 401 | Teardown |
| ERP sin empresa | 403 | Teardown |
| Not found cross-scope | 404 | Teardown |
| Business validation | 422 | Teardown |
| Infra error | 500 mapped | Teardown |

**Regla:** Toda terminación pasa por teardown.

---

## 8. Conclusión

El lifecycle es **secuencial y determinista**: contextos lógicos primero, negocio después, persistencia al acceder datos, teardown siempre.

La resolución de almacén es **tarde** (late binding) y **baja** (solo L6).
