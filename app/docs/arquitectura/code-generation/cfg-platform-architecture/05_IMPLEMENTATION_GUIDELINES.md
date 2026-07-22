# Guías de implementación (cuando se autorice)

**Paquete:** `cfg-platform-architecture`  
**Fecha:** 2026-07-17  
**Estado:** Orientación normativa — **esta etapa no autoriza escribir código**

---

## 1. Condiciones previas a implementar

1. ADR `03_ARCHITECTURE_DECISION.md` **aprobado** explícitamente.  
2. Alcance MVP de `cfg-admin-audit/06` **aprobado** (GET + PATCH B + preview).  
3. Confirmación: **no** tocar Motor/Gateway/Catalog/ORG/INV salvo extensiones menores de Repo (`numero_inicial`, audit columns) si el MVP lo exige.

---

## 2. Checklist de conformidad SaaS / ERP V4

| Regla | Aplicación al módulo `cfg` |
|-------|----------------------------|
| Orden | schemas → queries → services → routers |
| Session | `require_erp_session` en router padre |
| `cliente_id` | Solo `get_cfg_session_client_id` — nunca body; nunca `current_user.cliente_id` en presentation |
| Conexión | DEFAULT / tenant session — **nunca ADMIN** para writes cfg operativos |
| Authz | `require_permission("cfg.secuencias.…")` — sin LBAC |
| Soft delete | `es_activo`; sin DELETE físico |
| Errores | `ConflictError` / `NotFoundError` / `ValidationError` existentes |
| Listados | `app/shared/pagination/` opt-in `page` |
| Dedicated | Session obligatoria en mutaciones (ADJ-03) |
| Motor | Preview/align solo vía Gateway |

---

## 3. Anti-patrones (prohibidos)

1. Colocar endpoints bajo `/clientes` o `/superadmin` “porque es administración”.  
2. Copiar el estilo Platform (class services + ADMIN) al módulo `cfg`.  
3. Exponer CRUD de `ultimo_numero`.  
4. Permitir editar `generation_policy` / `sequence_key` / fingerprint.  
5. Reimplementar formateo en el servicio admin.  
6. Hacer que ORG o INV “registren” sus secuencias vía sus propios routers.  
7. Usar Branding como plantilla de arquitectura de datos.

---

## 4. Separación Platform ↔ ERP en el tiempo

| Momento | Dueño | Acción permitida sobre cfg |
|---------|-------|----------------------------|
| Provisioning / onboarding | Platform (`tenant`) | Insert seed (como hoy) |
| Tenant READY + operación | ERP `cfg` | List / config / preview |
| Runtime CREATE maestros | ORG/INV + Gateway | allocate |
| Soporte L2 | Impersonación + `cfg.secuencias.mantener` | align (post-MVP) — **no** consola SA cross-tenant |

---

## 5. Orden sugerido de trabajo (post-aprobación)

1. Seed RBAC `cfg.secuencias.consultar|actualizar` (+ menú si aplica).  
2. Esqueleto `app/modules/cfg/` + `cfg_deps` + mount `/cfg`.  
3. Queries list/detail + schemas Read.  
4. Services GET + tests aislamiento tenant / impersonación.  
5. Validator + PATCH B + auditoría columnas.  
6. Preview vía Gateway.  
7. OpenAPI + certificación Backend MVP.  
8. Paquete contrato Frontend (docs) → FE.

Align / diagnóstico: **fases posteriores**, misma ubicación de módulo.

---

## 6. Criterios de aceptación arquitectónicos

El diseño/implementación futura se considera alineada si:

- [ ] Vive en `app/modules/cfg/` (o nombre ERP equivalente aprobado), no en `tenant`/`superadmin`
- [ ] Toda mutación usa session tenant (Shared/Dedicated)
- [ ] SuperAdmin solo opera vía impersonación (o no opera)
- [ ] Motor no se modifica para “hacer admin”
- [ ] Documentación de menú sitúa la UI en shell ERP del tenant

---

## 7. Trazabilidad documental

| Pregunta | Documento |
|----------|-----------|
| ¿Qué existe hoy? | `cfg-admin-audit/` |
| ¿Dónde debe vivir? | **Este paquete** (`cfg-platform-architecture/`) |
| ¿Qué API/RBAC se diseñó? | `codigo-generation-admin/` |
| ¿Qué MVP construir primero? | `cfg-admin-audit/06` + ADR aquí |

---

## 8. Cierre

Hasta nueva instrucción del usuario:

- **No** crear módulo  
- **No** crear endpoints  
- **No** OpenAPI  
- **No** migraciones  
- **No** Frontend  

La consolidación arquitectónica queda documentada: **Administrador del Motor = módulo ERP `cfg`**, no capacidad Platform Administration.
