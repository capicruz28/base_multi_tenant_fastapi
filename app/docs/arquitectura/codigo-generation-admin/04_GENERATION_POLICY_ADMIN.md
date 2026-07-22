# Administración de `generation_policy`

**Fuente runtime:** Gateway lee `generation_policy` desde **fila cfg** (`_resolve_generation_policy`), sembrada desde catálogo al crear fila.  
**CK BD:** `AUTO_REQUIRED | AUTO_DEFAULT | MANUAL_ONLY` — **EXTERNAL no aplica** a cfg.

---

## 1. Las cuatro políticas (contexto admin)

| Política | En cfg | Motor | Admin UI |
|----------|--------|-------|----------|
| **AUTO_REQUIRED** | ✅ | Siempre auto; rechaza manual salvo IMPORT | Solo lectura; badge «Documento» |
| **AUTO_DEFAULT** | ✅ | Auto si omitido; acepta manual + align | Solo lectura; badge «Maestro» |
| **MANUAL_ONLY** | ✅ | Rechaza auto; exige manual | Solo lectura; badge «Manual obligatorio» |
| **EXTERNAL** | ❌ | Campos fuera motor secuencial | **No mostrar** en admin cfg |

Referencia: `08_CODE_POLICIES.md` §1.

---

## 2. ¿Cuándo puede cambiarse `generation_policy`?

| Contexto | ¿Editable? | Mecanismo |
|----------|------------|-----------|
| Admin tenant REST | **No** | BR-UPD-02 |
| Seed onboarding | Copia catálogo | Automático |
| Lazy ensure_row | Copia catálogo | Automático |
| Cambio producto / F15A | Enmienda catálogo + migración | Release MAJOR gobernanza `22` |
| Implantación excepcional | **Prohibido** vía UI; solo SQL bajo change control | Fuera admin self-service |

**Veredicto:** el módulo admin **expone** `generation_policy` en Read y **compara** con catálogo en diagnóstico. **Nunca** PATCH.

---

## 3. ¿Quién puede cambiarla?

| Actor | Permiso |
|-------|---------|
| Usuario tenant admin | **Nadie** vía admin |
| Equipo producto / arquitectura | Catálogo + release |
| Implantación | No cambiar policy; solo prefijo/pad |

---

## 4. Restricciones por tipo de secuencia

### AUTO_REQUIRED (~24 documentos + emisión)

| Aspecto | Regla admin |
|---------|-------------|
| Cambio policy | Prohibido |
| Desactivar secuencia | **Alto riesgo** — bloquea procesos; confirmación doble |
| Preview | Permitido con advertencia UX |
| Align | Solo IMPORT / mantenimiento documentado |

### AUTO_DEFAULT (~38 maestros)

| Aspecto | Regla admin |
|---------|-------------|
| Cambio policy | Prohibido |
| Prefijo/pad | Permitido (BR-CUST) |
| Desactivar | Permitido — bloquea auto en altas futuras |
| Align | Post-manual alto / importación (BR-M-41) |

### MANUAL_ONLY (~8 campos motor)

| Aspecto | Regla admin |
|---------|-------------|
| Cambio policy | Prohibido |
| Prefijo/pad | Irrelevante o N/A según entidad |
| Preview | Catálogo `supports_preview` puede ser false |
| Contador | A menudo no consume en manual puro |

### EXTERNAL

| Aspecto | Regla |
|---------|-------|
| Presencia en admin cfg | **No** — no hay fila cfg |
| Ejemplos | RUC, codigo_barra, serie fiscal alta |

---

## 5. Comportamiento admin según policy (UX Backend)

| Acción admin | AUTO_REQUIRED | AUTO_DEFAULT | MANUAL_ONLY |
|--------------|---------------|--------------|-------------|
| Editar prefijo | ⚠️ Limitado (docs proceso) | ✅ | ○ |
| Preview | ✅ con disclaimer | ✅ | ❌ si catálogo no soporta |
| Align | ✅ mantenimiento | ✅ | Raro |
| Desactivar | ⚠️ | ✅ | ✅ |

---

## 6. Drift policy cfg ≠ catálogo

**Diagnóstico DGN-01:**

```text
if cfg.generation_policy != SequenceCatalog.get(key).policy:
  severity = CRITICAL
  recommendation = "Contactar soporte; no editable en admin"
```

Causa típica: downgrade/upgrade incompleto o manipulación SQL directa.

---

## 7. Relación OpenAPI entidades ERP

La policy cfg **no** cambia el contrato Create de entidades (optional vs required código) — eso deriva del **catálogo + release coordinado** (SC-GOV-02). Admin cfg **no sustituye** evolución API por módulo.

---

*Casos especiales org_empresa: [`05_ORG_EMPRESA_AND_SPECIAL_CASES.md`](05_ORG_EMPRESA_AND_SPECIAL_CASES.md)*
