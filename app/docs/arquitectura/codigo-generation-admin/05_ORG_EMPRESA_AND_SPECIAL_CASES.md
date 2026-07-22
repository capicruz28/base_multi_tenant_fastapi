# Casos especiales: org_empresa, Preview y Align Counter

---

## 1. `org_empresa` (scope TENANT)

### 1.1 Contexto normativo

| Hecho | Referencia |
|-------|------------|
| EMP001 creado en bootstrap sin motor | BR-M-02 |
| cfg TENANT `ultimo_numero = 1` post-onboarding | BR-BOOT-04 |
| Primer allocate runtime → EMP002 | Ola 1 cerrada |
| Una sola fila cfg TENANT por cliente | BR-MULTI-01 |

### 1.2 Reglas admin propuestas

| Campo | ¿Bloqueado admin? | Justificación |
|-------|-------------------|---------------|
| **prefijo** (`EMP`) | **Sí — change-controlled** | EMP001 bootstrap hardcodeado; cambiar prefijo desincroniza sede |
| **longitud_numero** (3) | **Sí — change-controlled** | Mismo motivo; formato EMP001 |
| **separador** | **Sí** (V1 ∅ fijo) | BS-CFG-01 |
| **generation_policy** | **Sí** (solo lectura global) | AUTO_DEFAULT; BR-UPD-02 |
| **numero_inicial** | **Sí** (solo lectura) | Siempre 1; cambio confunde piso |
| **ultimo_numero** | **Solo motor + align mantenimiento** | BR-BOOT-04 inicializa en 1; no PATCH |
| **es_activo** | **⚠️ Bloqueado desactivar** | Desactivar bloquearía altas de **cualquier** empresa del tenant |

**Veredicto org_empresa:** tratar como secuencia **semi-inmutable** en admin tenant: **consulta + diagnóstico + preview** permitidos; **PATCH configuración denegado** en v1 (422 `ORG_EMPRESA_CFG_LOCKED`). Excepción futura: rol plataforma implantación con change ticket.

### 1.3 Diagnóstico específico DGN-06

| Check | Condición OK |
|-------|--------------|
| Fila TENANT existe | 1 fila `sequence_key=org_empresa` |
| `ultimo_numero >= 1` si EMP001 existe | Coherencia BR-BOOT-04 |
| MAX(`codigo_empresa` parseable) ≤ ultimo_numero | Sin drift post-manual |
| Prefijo/pad = EMP/3 | Match bootstrap |

---

## 2. Preview

### 2.1 Cuándo es útil

| Escenario | Utilidad |
|-----------|----------|
| Alta maestro AUTO_DEFAULT (UX) | Usuario ve estimación pre-save |
| Post-cambio prefijo admin | Verificar formato antes de operar |
| Implantación | Validar cfg tras seed |
| Documentos AUTO_REQUIRED | **Desaconsejado** salvo rol admin (BR-S-01) |

### 2.2 Cómo funciona (AS-IS motor)

Evidencia `PreviewReader`:

```python
next_num = max(row.ultimo_numero, row.numero_inicial - 1) + 1
code = CodeFormatter.format(defn, next_num, prefijo=row.prefijo, ...)
```

| Pregunta | Respuesta |
|----------|-----------|
| ¿Consume contador? | **No** — lectura sin lock escritura |
| ¿Reserva número? | **No** — concurrent allocate puede adelantar |
| ¿Requiere fila cfg? | Sí; si no existe → ensure o 404 según diseño admin |
| Gateway | `CodigoGeneracionGateway.preview` |

### 2.3 Respuesta API esperada

```json
{
  "codigo_estimado": "SUC003",
  "ultimo_numero_leido": 2,
  "numero_inicial": 1,
  "sequence_key": "org_sucursal",
  "disclaimer": "Estimación no reserva correlativo"
}
```

### 2.4 Errores

| Caso | Error |
|------|-------|
| `supports_preview=false` en catálogo | 422 `PREVIEW_NOT_ALLOWED` |
| Secuencia inactiva | 422 |
| Scope incompleto sesión | 403 / 422 scope |

---

## 3. Align Counter

### 3.1 Cuándo utilizar

| Escenario | Usar align |
|-----------|------------|
| Importación masiva códigos históricos | **Sí** — cierre lote BR-M-41 |
| Manual alto AUTO_DEFAULT (CLI999 > contador) | Automático en allocate; align admin solo si drift detectado |
| Post-bootstrap greenfield org_empresa | **No** — seed BR-BOOT-04 |
| Corrección drift DGN-04 | **Sí** — bajo `cfg.secuencias.mantener` |
| Uso rutinario post-cada create | **No** — anti-patrón |

### 3.2 Quién puede ejecutarlo

| Rol | Permiso |
|-----|---------|
| Admin tenant estándar | **No** |
| Implantación / soporte L2 | `cfg.secuencias.mantener` |
| Runtime ERP create | **No** — prohibido greenfield org_empresa |

### 3.3 Mecanismo autorizado

**Única vía:** `CodigoGeneracionGateway.align_counter(sequence_key, context, session, candidate_code)`

Internamente: `CounterAlignmentService.maybe_align` → parse → solo eleva si `candidate > ultimo_numero`.

**Prohibido:** `CfgCodigoSecuenciaRepository.update_ultimo_numero` desde API REST.

### 3.4 Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Align bajo MAX real | DGN-04 pre-check; candidate desde MAX query o código verificado |
| Align sin parseo | 422 si no parseable |
| Concurrencia | Misma UoW; TX tenant |
| Auditoría insuficiente | Log motivo + usuario + antes/después |
| Abuso reinicio | No endpoint «reset»; align solo hacia arriba |

### 3.5 Relación importaciones y migraciones

| Fase migración | Acción |
|----------------|--------|
| Import filas con código | IMPORT_HISTORICAL en ERP; no admin |
| Cierre lote | POST align por scope o batch job con permiso mantener |
| Cutover | DGN-04 = 0 drift |
| Legacy sin admin module | Scripts one-shot equivalentes a align Gateway |

TX-05: align en **misma UoW** del lote o fase cierre.

---

*Seguridad: [`06_SECURITY_RBAC_AND_FRONTEND.md`](06_SECURITY_RBAC_AND_FRONTEND.md)*
