# Seguridad RBAC e impacto Frontend

---

## 1. Modelo de permisos RBAC

**Módulo propuesto:** `cfg`  
**Recurso:** `secuencias`  
**Patrón:** `{modulo}.{recurso}.{accion}` (ERP V4)

### 1.1 Permisos definidos

| Permiso | Clase operaciones | Roles típicos |
|---------|-------------------|---------------|
| `cfg.secuencias.consultar` | Listado, detalle, preview, validar-manual | ADMIN_TENANT, MANAGER_TENANT, consultor implantación |
| `cfg.secuencias.actualizar` | PATCH config, activar/desactivar, validar-config | ADMIN_TENANT, responsable parametrización |
| `cfg.secuencias.mantener` | align counter, reparación drift | Rol implantación, soporte L2 (no usuario operativo diario) |
| `cfg.secuencias.diagnosticar` | GET diagnostico, reportes drift | ADMIN_TENANT + implantación |

### 1.2 Separación consulta / configuración / mantenimiento

```
consultar  ⊂  actualizar  (disjoint de mantener en práctica)
mantener   →  superconjunto peligroso; no heredar de actualizar
diagnosticar → puede otorgarse sin actualizar (solo lectura extendida)
```

**Regla SEC-01:** otorgar `mantener` **sin** `actualizar` permitido (implantación solo align).

**Regla SEC-02:** `preview` exige `consultar`, no `actualizar`.

### 1.3 Gates de sesión ERP

| Gate | Aplicación |
|------|------------|
| `require_erp_session` | Router padre `/cfg` |
| `cliente_id` operativo | `cfg_deps.get_cfg_session_client_id` — impersonación-safe |
| Scope EMPRESA listados | Filtro opcional; no autorizar via body |
| Cross-tenant | 404 |

### 1.4 Auditoría

| Evento | Campos mínimos |
|--------|----------------|
| PATCH config | secuencia_id, diff campos, usuario_id, timestamp |
| align | antes/después ultimo_numero, candidate_code, motivo |
| activar/desactivar | es_activo nuevo |

Persistencia: `usuario_actualizacion_id` en cfg + log aplicación / `auth_audit_log` futuro.

---

## 2. Matriz permiso × endpoint

| Endpoint | consultar | actualizar | mantener | diagnosticar |
|----------|-----------|------------|----------|--------------|
| GET list/detail | ✅ | — | — | ○ |
| GET diagnostico | — | — | — | ✅ |
| PATCH config | — | ✅ | — | — |
| activar/desactivar | — | ✅ | — | — |
| preview | ✅ | — | — | — |
| align | — | — | ✅ | — |
| validar-config | — | ✅ | — | ○ |

---

## 3. Impacto Frontend (React) — contrato funcional

**Sin diseño de pantallas.** Funcionalidades que consumirá:

### 3.1 Módulo menú

| Ítem menú | Permiso | Descripción |
|-----------|---------|-------------|
| Configuración → Secuencias de código | consultar | Hub del motor |

### 3.2 Funcionalidades por vista

| Vista | API | Permiso |
|-------|-----|---------|
| **Listado secuencias** | GET `/cfg/secuencias` | consultar |
| Filtros scope/empresa/módulo/activo | query params | consultar |
| **Detalle secuencia** | GET `/{id}` | consultar |
| Badge policy (AUTO_*) | Read.enriquecido | consultar |
| **Edición configuración** | PATCH `/{id}` | actualizar |
| Campos: prefijo, separador, padding, numero_inicial | form | actualizar |
| Toggle activo | POST activar/desactivar | actualizar |
| **Preview** | POST preview | consultar |
| Mostrar código estimado + disclaimer | response | consultar |
| **Panel diagnóstico** | GET diagnostico | diagnosticar |
| Alertas drift, agotamiento, lazy pending | response | diagnosticar |
| **Mantenimiento align** | POST align | mantener |
| Modal confirmación + motivo obligatorio | body.motivo | mantener |
| **org_empresa** | detalle read-only config | consultar |
| Sin formulario edición v1 | 422 si intento | — |

### 3.3 UX transversal

| Regla UX | Detalle |
|----------|---------|
| No editar ultimo_numero | Solo display |
| Preview no es reserva | Texto legal breve |
| Desactivar secuencia | Confirmación destructiva |
| org_empresa locked | Tooltip explicando BR-BOOT-04 |
| Dedicated/Shared | Misma UI |

### 3.4 Integración con altas maestros

| Pantalla ERP existente | Integración |
|------------------------|-------------|
| Create cargo/sucursal/… sin código | Opcional: llamar preview para hint |
| Create empresa | Preview EMP003+; no editar cfg org_empresa |

---

## 4. Permisos documentados previamente (alineación)

Fuente `08_CODE_POLICIES.md` §7:

| Acción histórica | Permiso propuesto | Estado |
|------------------|-------------------|--------|
| Cambiar prefijo | `cfg.secuencias.actualizar` | Alineado |
| Reiniciar secuencia | `cfg.secuencias.mantener` | Alineado (align, no reset) |
| Preview | `cfg.secuencias.consultar` | Alineado |

---

*Arquitectura módulo: [`07_MODULE_ARCHITECTURE.md`](07_MODULE_ARCHITECTURE.md)*
