# Modelo A vs Modelo B

---

## 1. Definiciones (inalterables en ambos)

Común a A y B (fuera de disputa en este ADR):

| Elemento | Valor |
|----------|--------|
| Dominio | Módulo ERP `cfg` |
| Backend API | `/api/v1/cfg` |
| OpenAPI / contrato FE API | Certificado |
| Permisos | `cfg.secuencias.consultar` / `actualizar` |
| Catálogo | `modulo.codigo = CFG` (patrón módulo propio) |
| Suscripción | `cliente_modulo(CFG)` |
| Visibilidad menú | `rol_menu_permiso` sobre menús CFG |
| Platform | No |

**Única variable:** plano de navegación FE + valor de `modulo_menu.ruta`.

---

## 2. Modelo A — ERP operativo

```text
API:     /api/v1/cfg/*
Menú FE: /app/cfg/*
Shell:   ERP operativo (mismo plano que ORG / INV / WMS)
```

### Fortalezas

| Eje | Valoración |
|-----|------------|
| Simetría con ORG/INV/WMS | Alta — mismo patrón visual “módulo → /app/{cod}” |
| Familiaridad para quien ya navega ERP | Media — operadores ven módulos en `/app` |
| Alineación S021/normalizer “legacy → /app” | Alta si se siembra `/cfg/...` |
| Descubribilidad junto a módulos de negocio | Media |

### Debilidades

| Eje | Valoración |
|-----|------------|
| Perfil de usuario real (ADMIN_TENANT / implantación) | Baja coherencia — `/app` es plano operativo diario |
| Riesgo de que operadores busquen/entren a parametrizar numeración | Más alto |
| Mezcla gobernanza con transaccionalidad en el mismo sidebar | Peor IA |
| Coherencia con Tenant Administration existente | Baja — IAM ya está en `/admin` |

---

## 3. Modelo B — Tenant Administration

```text
API:     /api/v1/cfg/*          (igual)
Menú FE: /admin/configuracion/secuencias   (o equivalente bajo /admin)
Shell:   Tenant Administration
Módulo:  CFG propio + cliente_modulo + permisos propios
```

### Fortalezas

| Eje | Valoración |
|-----|------------|
| Alineación con persona primaria | **Alta** — Admin tenant / consultor / implementador |
| Separación operación vs configuración | **Alta** |
| Coherencia con IAM UI (`/admin/usuarios|roles|sesiones`) | **Alta** — mismo shell de gobernanza |
| Coherencia con rechazo de Platform | **Alta** — sigue fuera de `/super-admin` |
| Escalabilidad de “configuración tenant” | **Alta** — futuros ítems (parametrización) caben bajo `/admin/configuracion/*` |
| Independencia dominio/API | Intacta |

### Debilidades

| Eje | Valoración |
|-----|------------|
| Simetría visual “todo módulo ERP en /app” | Más baja (intencional) |
| FE debe tratar CFG fuera de lista operativa `ERP_MODULES` típica | Requiere disciplina FE |
| Posible doble gate (`admin.tenant.access` + `cfg.secuencias.*`) | Aceptable; ya existe precedente de plano |

---

## 4. Comparación por criterios pedidos

| Criterio | Modelo A (`/app`) | Modelo B (`/admin`) | Preferido |
|----------|-------------------|---------------------|-----------|
| Arquitectura Backend | Neutro | Neutro | Empate |
| Arquitectura de información FE | Mezcla config en operativo | Config en admin tenant | **B** |
| UX (usuario real) | Operador ve config en sidebar ERP | Admin encuentra config junto a IAM | **B** |
| Escalabilidad de pantallas de configuración | Compite con módulos operativos | Namespace `/admin/configuracion` | **B** |
| Mantenibilidad | Dos “lugares mentales” si hay más config | Un shell de gobernanza | **B** |
| SaaS Multi-Tenant | Válido | Válido y más claro (tenant admin vs app) | **B** |
| Tenant Administration | Débil | **Fuerte** | **B** |
| Platform Administration | Ambos la excluyen si no usan `/super-admin` | Igual | Empate |

---

## 5. Perfil de usuario (evidencia de producto)

Fuente: `cfg-functional-design/01_PRODUCT_VISION.md` + grants `S068` (ADMIN_TENANT).

| Perfil | ¿Usuario normal de CFG? | Shell natural |
|--------|-------------------------|---------------|
| Operador ERP | No (primario) | `/app` |
| Supervisor / Manager | Opcional consulta | Mixto |
| **Administrador Tenant** | **Sí — primario** | **`/admin`** |
| Consultor / Implementador | Sí — alta en go-live | `/admin` (a menudo vía ADMIN_TENANT o rol implantación) |
| SuperAdmin Platform | No como consola Platform; sí vía impersonación tenant | Efectivo = shell tenant |

**Conclusión de perfil:** el shell que representa mejor el dominio CFG en operación normal es **Administración del Tenant (`/admin`)**.

---

## 6. Analogías correctas e incorrectas

| Analogía | ¿Válida para navegación? |
|----------|---------------------------|
| CFG ≈ ORG/INV porque ambos son módulos ERP con API | Válida para **dominio/API/catálogo**; **no** fuerza shell `/app` |
| CFG ≈ IAM porque lo usa Tenant Admin | Válida para **shell `/admin`**; **no** implica eliminar módulo `CFG` ni API `/cfg` |
| CFG ≈ Branding / Platform | **Inválida** (ya rechazada: store y conexión distintos) |
| CFG ≈ SuperAdmin módulos | **Inválida** |
