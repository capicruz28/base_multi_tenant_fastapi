# Dominio vs navegación — desacoplamiento y restricción técnica

---

## 1. Conceptos que no deben confundirse

| Concepto | Qué es | Dónde vive hoy | ¿Acoplado a `/app`? |
|----------|--------|----------------|---------------------|
| **Dominio funcional** | Responsabilidad de negocio (secuencias de código) | Decisión: módulo ERP `cfg` | No |
| **API** | Contrato HTTP | `/api/v1/cfg` | No |
| **Contrato OpenAPI** | Schemas, operationIds | Snapshot FE `frontend-contracts/cfg` | No |
| **Permisos RBAC** | Autorización de acciones | `cfg.secuencias.*` | No |
| **Catálogo comercial** | Suscripción módulo | `modulo` + `cliente_modulo` | No |
| **Catálogo de menú** | Árbol UI | `modulo_menu.ruta` + RMP | **La ruta elige el shell** |
| **Shell Frontend** | Contenedor de navegación | `/app`, `/admin`, `/super-admin` | Definición del shell |
| **UX / IA** | Dónde el usuario espera la pantalla | Producto | Independiente del dominio |
| **ERP_MODULES (FE)** | Mapa local FE de módulos | Solo Frontend | Convención FE, no Backend |

### Regla de independencia

```text
Dominio ≠ API path ≠ Shell FE ≠ Prefijo de menú
```

Pueden evolucionar por separado **salvo** que una norma técnica del sistema lo prohíba.  
La pregunta de este ADR es precisamente si existe esa norma para `/app`.

---

## 2. ¿Existe restricción técnica que obligue `/app` a un módulo con API propia?

### Dictamen

**No existe.**

Un módulo con API propia (`/api/v1/{cod}`) **no** está obligado por Backend, menú dinámico ni RBAC a navegar bajo `/app/{cod}`.

### Evidencia Backend

#### 2.1 Normalizador de rutas de menú

`app/core/menu/menu_route_normalizer.py`:

- Prefijos **reservados** (se respetan tal cual): `/app/`, `/admin/`, `/super-admin/`, `/api`
- Solo antepone `/app` a rutas legacy absolutas **que no** empiezan por un reservado (ej. `/org/...` → `/app/org/...`)

Implicación: una `modulo_menu.ruta` ya bajo `/admin/...` **nunca** se reescribe a `/app`.  
No hay lógica del tipo `if modulo.codigo == X then force /app`.

#### 2.2 Construcción de `/auth/menu`

`ModuloMenuService.obtener_menu_usuario`:

- Filtra por `cliente_modulo` + `rol_menu_permiso`
- Emite la `ruta` del catálogo (normalizada)
- **No** clasifica por prefijo de shell para incluir/excluir ítems

#### 2.3 Precedente AS-IS: IAM vs ORG/INV

| Capacidad | API | Módulo catálogo | Ruta menú |
|-----------|-----|-----------------|-----------|
| ORG | `/api/v1/org` | `ORG` | `/app/org/...` |
| INV | `/api/v1/inv` | `INV` | `/app/inv/...` |
| IAM UI | users/rbac (no `/iam`) | `SYS_ADMIN` | `/admin/usuarios` etc. |

Demuestra que el producto **ya separa** dominio/API de shell.  
El caso IAM es aún más extremo (ni módulo propio “IAM”); el Modelo B para CFG es más conservador: **sí** módulo `CFG` + API `/cfg`, **pero** shell `/admin`.

#### 2.4 Permisos de plano (no de dominio)

`S020` define:

- `admin.tenant.access` → pantallas `/admin/*`
- `admin.platform.access` → pantallas `/super-admin/*`

Son permisos de **acceso a shell**, ortogonales a `org.*`, `inv.*`, `cfg.*`.  
Nada impide que una pantalla bajo `/admin` consuma API `/api/v1/cfg` con `cfg.secuencias.*`.

#### 2.5 Contrato FE CFG

`frontend-contracts/cfg` fija API y RBAC de negocio.  
**No** fija path FE `/app/cfg`. El checklist solo exige que menú/ruta exijan `cfg.secuencias.consultar`.

### Conclusión §2

| Afirmación | ¿Verdadera? |
|------------|-------------|
| “Si hay `/api/v1/cfg`, la UI debe ser `/app/cfg`” | **Falsa** — no hay restricción técnica |
| “Si el dominio es ERP, el shell debe ser `/app`” | **Falsa** — “ERP” aquí es dominio de datos/session, no prefijo FE |
| “`/admin` implica Platform” | **Falsa** — Platform es `/super-admin`; `/admin` es Tenant Administration |

---

## 3. Qué *sí* está acoplado (y qué no)

| Par | ¿Acoplado? | Nota |
|-----|------------|------|
| Dominio `cfg` ↔ API `/cfg` | **Sí (deseable)** | Ya certificado |
| Dominio `cfg` ↔ permisos `cfg.*` | **Sí** | Ya certificado |
| Dominio `cfg` ↔ `modulo.codigo=CFG` | **Sí (registro menú)** | Decisión registration-audit |
| Dominio `cfg` ↔ shell `/app` | **No** | Este ADR |
| `modulo_menu.ruta` ↔ shell FE | **Sí** | La ruta *define* el plano |
| Shell `/admin` ↔ Platform ADMIN DB | **No** | Shell ≠ DatabaseConnection.ADMIN |

---

## 4. Lectura correcta de “tenant shell ERP”

En `cfg-platform-architecture/04`:

> Menú sugerido: Configuración → Secuencias de código (**tenant shell ERP**), **no** bajo consola SuperAdmin.

Interpretación normativa de este ADR:

- **Excluye** `/super-admin` (Platform).
- **No prescribe** el prefijo `/app`.
- Es compatible con shell **Tenant Administration** (`/admin`), que es shell del tenant para gobernanza, no Platform.

En `cfg-functional-design/01`:

> Persona primaria: Administrador del tenant que **configura** el ERP, no el operador de almacén ni el SuperAdmin SaaS.

Eso alineará el shell con **quién** usa la pantalla (§5 del paquete).
