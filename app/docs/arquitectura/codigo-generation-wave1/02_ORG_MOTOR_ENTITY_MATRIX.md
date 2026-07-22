# Ola 1 — Matriz entidad ORG ↔ Motor ↔ Infraestructura

**Estado:** Referencia de auditoría — motor congelado  
**Fecha:** 2026-07-10

---

## 1. Matriz maestra

| # | Tabla | Campo | sequence_key | Policy | ScopeType | Prefijo | Service create | Query by codigo | UNIQUE BD | UoW hoy |
|---|-------|-------|--------------|--------|-----------|---------|----------------|-----------------|-----------|---------|
| 1 | `org_cargo` | `codigo` | `org_cargo` | AUTO_DEFAULT | EMPRESA | CAR | `create_cargo_servicio` | `get_cargo_by_codigo` | `UQ_cargo_codigo` | No |
| 2 | `org_departamento` | `codigo` | `org_departamento` | AUTO_DEFAULT | EMPRESA | DEP | `create_departamento_servicio` | `get_departamento_by_codigo` | `UQ_dpto_codigo` | No |
| 3 | `org_centro_costo` | `codigo` | `org_centro_costo` | AUTO_DEFAULT | EMPRESA | CC | `create_centro_costo_servicio` | `get_centro_costo_by_codigo` | `UQ_cc_codigo` | No |
| 4 | `org_sucursal` | `codigo` | `org_sucursal` | AUTO_DEFAULT | EMPRESA | SUC | `create_sucursal_servicio` | `get_sucursal_by_codigo` | `UQ_sucursal_codigo` | No |
| 5 | `org_empresa` | `codigo_empresa` | `org_empresa` | AUTO_DEFAULT | TENANT | EMP | `create_empresa_servicio` | `get_empresa_by_codigo` | `UQ_org_empresa_cliente` | **Sí** |

---

## 2. GenerationContext por entidad

| sequence_key | client_id | empresa_id | almacen_id | manual_code | operation |
|--------------|-----------|------------|------------|-------------|-----------|
| `org_cargo` | sesión ORG | JWT `empresa_id` | — | body opcional | CREATE |
| `org_departamento` | sesión ORG | JWT `empresa_id` | — | body opcional | CREATE |
| `org_centro_costo` | sesión ORG | JWT `empresa_id` | — | body opcional | CREATE |
| `org_sucursal` | sesión ORG | JWT `empresa_id` | — | body opcional | CREATE |
| `org_empresa` | sesión ORG | **None** | — | body opcional | CREATE |

---

## 3. Flujo AS-IS vs TARGET por entidad

### 3.1 Patrón company-scoped (cargo, departamento, centro_costo, sucursal)

**AS-IS:**

```
POST → servicio
  → get_*_by_codigo (409 si existe)
  → create_* → execute_insert (commit aislado)
```

**TARGET Ola 1:**

```
POST → servicio
  async with get_connection_for_tenant(...) as session:
    async with session.begin():
      → CodigoGeneracionGateway.allocate(key, context, session)
      → create_*(..., session=session)   # dual-path queries
  → Read response
```

### 3.2 Patrón tenant-scoped (org_empresa)

**AS-IS (post Empresa Bootstrap V1):**

```
POST → create_empresa_servicio
  → session.begin()
      → pre-check codigo / ruc
      → create_empresa
      → EmpresaBootstrapService.insertar_secuencias_codigo
  → commit
```

**TARGET Ola 1:**

```
POST → create_empresa_servicio
  → session.begin()
      → pre-check ruc (codigo si manual)
      → allocate("org_empresa", context TENANT, session)  # NUEVO
      → create_empresa
      → insertar_secuencias_codigo (sin cambio)
  → commit
```

---

## 4. Endpoints y RBAC (sin cambio previsto)

| Recurso | POST | Permiso crear |
|---------|------|---------------|
| Empresa | `/org/empresa` | `org.empresa.crear` |
| Sucursal | `/org/sucursales` | `org.sucursal.crear` |
| Centro costo | `/org/centros-costo` | `org.centro_costo.crear` |
| Departamento | `/org/departamentos` | `org.departamento.crear` |
| Cargo | `/org/cargos` | `org.cargo.crear` |

---

## 5. cfg_codigo_secuencia — disponibilidad de fila

| sequence_key | Scope seed | Cuándo existe fila cfg |
|--------------|------------|------------------------|
| `org_empresa` | TENANT | Onboarding (`seed_cfg_tenant`) |
| `org_sucursal` | EMPRESA | Onboarding EMP001 + cada empresa adicional (EBS V1) |
| `org_centro_costo` | EMPRESA | idem |
| `org_departamento` | EMPRESA | idem |
| `org_cargo` | EMPRESA | idem |

**Prerequisito allocate:** fila cfg debe existir para fingerprint resuelto. Empresas creadas post-V1 cumplen; tenants legacy pueden requerir repair (fuera Ola 1).

---

## 6. Entidades excluidas de la matriz motor

| Tabla | Campo | Tratamiento Ola 1 |
|-------|-------|-------------------|
| `org_parametro_sistema` | `codigo_parametro` | Manual permanente; clave de config |
| `org_parametro_sistema` | `modulo_codigo` | Identificador módulo |
| `org_empresa` | `codigo_ciiu` | Dato tributario externo |
| Varios | `codigo_postal`, `ubigeo` | Datos geo |

---

## 7. Consumo actual del motor en el repo

| Componente | Usa gateway |
|------------|-------------|
| `app/modules/org/**` | **No** |
| `app/modules/inv/**` | **No** |
| Tests unit motor | Sí (aislados) |
| Bootstrap cfg seed | No (insert directo repo) |

**Ola 1 ORG = primera integración runtime ERP.**
