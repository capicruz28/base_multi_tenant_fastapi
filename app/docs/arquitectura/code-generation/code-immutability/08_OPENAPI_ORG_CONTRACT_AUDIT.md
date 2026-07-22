# Auditoría final OpenAPI — ORG Ola 1 + BR-IMM

**Fecha:** 2026-07-13  
**Tipo:** Verificación de contrato (solo lectura — **sin modificación de código**)  
**Alcance:** Contrato OpenAPI del módulo ORG (5 maestros Motor: empresa, sucursal, departamento, centro de costo, cargo)  
**Fuera de alcance:** INV, CFG, Frontend, runtime changes

---

## 1. Veredicto

| Pregunta | Respuesta |
|----------|-----------|
| ¿El contrato OpenAPI **vivo** (FastAPI a partir de schemas actuales) está alineado con BR-IMM-01…05? | **Sí** |
| ¿Puede considerarse ORG Backend **certificable** como referencia de contrato respecto a BR-IMM? | **Sí** — sobre el contrato **generado en runtime** |
| ¿El artefacto `app/docs/openapi_snapshot.json` está alineado? | **No** — **desactualizado** (legado pre–Ola 1 / pre–BR-IMM) |
| ¿CREATE / READ / LIST / DELETE impactados negativamente? | **No** en el contrato vivo |

**Veredicto ejecutivo:** el contrato Backend ORG **generado por la aplicación** está **completamente alineado con BR-IMM**.  
El único riesgo residual es operativodeocumental: el **snapshot estático** aún publica el contrato legacy y no debe usarse como fuente oficial para Frontend/codegen hasta regenerarse (fuera de esta auditoría).

---

## 2. Método de verificación

| Método | Resultado |
|--------|-----------|
| A. Inspección estática `schemas.py` (`*Create` / `*Update` / `*Read`) | Cumple BR-IMM + Ola 1 |
| B. `model_json_schema()` Pydantic (fuente de OpenAPI) | Update sin campo código Motor |
| C. OpenAPI **vivo** montando `org.presentation.endpoints` bajo `/api/v1/org` | Update sin `codigo` / `codigo_empresa`; Create optional; Read required |
| D. Comparación con `app/docs/openapi_snapshot.json` | Snapshot **obsoleto** |

No se modificó ningún archivo de producto para esta auditoría (este informe es el único entregable documental).

---

## 3. Hallazgos — contrato vivo (fuente oficial)

### 3.1 Schemas `*Update` — campo código Motor **ausente**

| Schema OpenAPI | Campo Motor esperado ausente | `has_field` vivo | Cumple BR-IMM-01/03 |
|----------------|------------------------------|------------------|---------------------|
| `EmpresaUpdate` | `codigo_empresa` | **False** | ✅ |
| `SucursalUpdate` | `codigo` | **False** | ✅ |
| `DepartamentoUpdate` | `codigo` | **False** | ✅ |
| `CentroCostoUpdate` | `codigo` | **False** | ✅ |
| `CargoUpdate` | `codigo` | **False** | ✅ |

**Nota:** `EmpresaUpdate` / `SucursalUpdate` pueden exponer `codigo_ciiu`, `codigo_postal` (campos EXTERNAL / geo). **No** son códigos del Motor secuencial; no violan BR-IMM.

### 3.2 Schemas `*Create` — Ola 1 intacta (optional AUTO_DEFAULT)

| Schema | Campo | Presente | `required` | Esperado Ola 1 |
|--------|-------|----------|------------|----------------|
| `EmpresaCreate` | `codigo_empresa` | Sí | **False** | ✅ optional |
| `SucursalCreate` | `codigo` | Sí | **False** | ✅ |
| `DepartamentoCreate` | `codigo` | Sí | **False** | ✅ |
| `CentroCostoCreate` | `codigo` | Sí | **False** | ✅ |
| `CargoCreate` | `codigo` | Sí | **False** | ✅ |

### 3.3 Schemas `*Read` — código siempre visible

| Schema | Campo | Presente | `required` |
|--------|-------|----------|------------|
| `EmpresaRead` | `codigo_empresa` | Sí | **True** |
| `SucursalRead` | `codigo` | Sí | **True** |
| `DepartamentoRead` | `codigo` | Sí | **True** |
| `CentroCostoRead` | `codigo` | Sí | **True** |
| `CargoRead` | `codigo` | Sí | **True** |

### 3.4 Rutas PUT — requestBody refleja Update sin código Motor

| Path vivo | `$ref` body | Response 200 |
|-----------|-------------|--------------|
| `PUT /api/v1/org/empresa/{empresa_id}` | `EmpresaUpdate` | `EmpresaRead` |
| `PUT /api/v1/org/sucursales/{sucursal_id}` | `SucursalUpdate` | `SucursalRead` |
| `PUT /api/v1/org/departamentos/{departamento_id}` | `DepartamentoUpdate` | `DepartamentoRead` |
| `PUT /api/v1/org/centros-costo/{centro_costo_id}` | `CentroCostoUpdate` | `CentroCostoRead` |
| `PUT /api/v1/org/cargos/{cargo_id}` | `CargoUpdate` | `CargoRead` |

Paths, métodos y `response_model` Read **sin cambio de superficie**. Solo el shape del body Update cambió (campo código eliminado).

### 3.5 Consistencia con BR-IMM-01…05

| Regla | Evidencia en OpenAPI vivo |
|-------|---------------------------|
| **BR-IMM-01** inmutable post-CREATE | Update schemas sin propiedad de código Motor |
| **BR-IMM-02** policy solo CREATE | Create conserva campo optional; Update no tiene política ni código |
| **BR-IMM-03** UPDATE no modifica código | Sin propiedad → no hay contrato para mutar |
| **BR-IMM-04** UPDATE no invoca Motor | Contrato HTTP no expone operación Motor (correcto; enforcement ya en services) |
| **BR-IMM-05** re-maestro excepcional | Sin endpoint UPDATE de código; no aparece escape en ORG OpenAPI (esperado) |

### 3.6 CREATE / READ / LIST / DELETE — sin impacto colateral de contrato

| Operación | Evidencia |
|-----------|-----------|
| **POST Create** | Body Create con código optional; response Read con código required |
| **GET list / detail** | `response_model` `*Read` / `list[*Read]` — código presente |
| **DELETE** soft | Sin body de código; paths estables |
| **POST reactivar** | Response Read — código intacto en contrato |

---

## 4. Hallazgos — artefacto snapshot (`openapi_snapshot.json`)

| Hallazgo | Severidad | Detalle |
|----------|-----------|---------|
| H-SNAP-01 | **Media** | `*Update` aún incluyen `codigo` / `codigo_empresa` |
| H-SNAP-02 | **Media** | `*Create` marcan código como **required=True** (pre Ola 1 optional) |
| H-SNAP-03 | **Baja** | Naming legacy (`DepartamentoRead` con path de módulo en alguna ref) |
| H-SNAP-04 | **Media** | Si FE/codegen usa el snapshot en lugar de `/openapi.json` vivo → contrato **incorrecto** |

**Conclusión snapshot:** no es el contrato vigente. Debe tratarse como **histórico / no autoritativo** hasta regeneración explícita (tarea operativa, no bloqueante de la alineación BR-IMM del Backend vivo).

---

## 5. Referencias residuales “código editable”

| Superficie | ¿Legado editable en Update? |
|------------|-----------------------------|
| OpenAPI vivo ORG 5 maestros | **No** |
| Services UPDATE ORG (ya implementados Fase 2) | **No** (fuera OpenAPI; verificado en implementación previa) |
| `openapi_snapshot.json` | **Sí** — residual |
| Docs FE wave1 (histórico) | Pueden mezclar AS-IS/objetivo; **no** forman parte del OpenAPI generado |

No se hallaron propiedades OpenAPI vivas del tipo “editable code on PUT” para las 5 entidades Motor.

---

## 6. Riesgos residuales

| ID | Riesgo | Severidad | Mitigación recomendada (fuera de esta auditoría) |
|----|--------|-----------|--------------------------------------------------|
| R-01 | Consumir `openapi_snapshot.json` obsoleto | Media | Regenerar snapshot o deprecar el archivo; FE debe usar OpenAPI del entorno desplegado |
| R-02 | Cliente PUT full-object con `codigo` extra | Baja | Pydantic ignora extras por defecto → código no muta; UX: campo read-only |
| R-03 | Confundir `codigo_postal` / `codigo_ciiu` con código Motor | Baja | Documentar en contrato FE que no son identity Motor |
| R-04 | Codegen TS aún tipa `codigo?` en Update | Media | Regenerar tipos tras deploy; falla de compilación es señal deseada |

**Ningún riesgo residual invalida** la alineación BR-IMM del contrato Backend vivo.

---

## 7. Confirmación explícita de alineación

> **El contrato Backend ORG expuesto vía OpenAPI generado por la aplicación FastAPI está completamente alineado con BR-IMM-01…05** para las cinco entidades administradas por el Motor (`org_empresa`, `org_sucursal`, `org_departamento`, `org_centro_costo`, `org_cargo`).
>
> - Update: **no** expone código Motor.  
> - Create: código **optional** (Ola 1 AUTO_DEFAULT).  
> - Read/List responses: código **presente y required**.  
> - PUT: mismos paths; body Update correcto.  
> - CREATE / READ / LIST / DELETE: **sin regresiones de contrato**.
>
> Condición operativa: no usar `app/docs/openapi_snapshot.json` como fuente oficial hasta regenerarlo.

---

## 8. Certificación ORG como referencia Backend

| Criterio | Estado |
|----------|--------|
| Ola 1 CREATE + Motor | ✅ (previo) |
| BR-IMM UPDATE runtime | ✅ (previo) |
| OpenAPI vivo BR-IMM | ✅ **Esta auditoría** |
| Snapshot estático | ⚠ Desalineado — no bloquea certificación del **contrato vivo** |
| INV / CFG | No iniciados (correcto) |

**ORG puede certificarse como referencia oficial del Backend** respecto a Motor CREATE + BR-IMM UPDATE + contrato OpenAPI vivo.

---

## 9. Próximos pasos sugeridos (no ejecutados)

1. Regenerar `openapi_snapshot.json` (o eliminarlo del flujo FE) en una tarea dedicada.  
2. Alinear codegen Frontend con OpenAPI desplegado.  
3. Iniciar Ola INV solo con plantilla BR-IMM (fuera de este alcance).

---

*Auditoría de verificación — sin cambios de código ni OpenAPI regenerado en esta fase.*
