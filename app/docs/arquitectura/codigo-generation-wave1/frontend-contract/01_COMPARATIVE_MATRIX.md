# Matriz comparativa — Entidades ORG Ola 1

**Referencia:** Contrato Frontend ↔ Backend  
**Fuente técnica:** `SequenceCatalog` congelado + servicios ORG implementados

---

## 1. Matriz principal

| Dimensión | org_empresa | org_sucursal | org_departamento | org_centro_costo | org_cargo |
|-----------|-------------|--------------|------------------|------------------|-----------|
| **Tabla BD** | `org_empresa` | `org_sucursal` | `org_departamento` | `org_centro_costo` | `org_cargo` |
| **sequence_key** | `org_empresa` | `org_sucursal` | `org_departamento` | `org_centro_costo` | `org_cargo` |
| **Scope motor** | TENANT | EMPRESA | EMPRESA | EMPRESA | EMPRESA |
| **generation_policy** | AUTO_DEFAULT | AUTO_DEFAULT | AUTO_DEFAULT | AUTO_DEFAULT | AUTO_DEFAULT |
| **Prefijo default** | EMP | SUC | DEP | CC | CAR |
| **longitud_numero (padding)** | 3 | 3 | 3 | 3 | 3 |
| **Separador default** | ∅ (vacío) | ∅ | ∅ | ∅ | ∅ |
| **Campo código API** | `codigo_empresa` | `codigo` | `codigo` | `codigo` | `codigo` |
| **Campo opcional CREATE** | ✅ Sí | ✅ Sí | ✅ Sí | ✅ Sí | ✅ Sí |
| **Normalización input** | UPPER | UPPER | UPPER | UPPER | UPPER |
| **max_length campo** | 20 | 20 | 20 | 20 | 20 |
| **Ejemplo auto** | EMP002 | SUC001 | DEP001 | CC001 | CAR001 |
| **Scope sesión ERP** | TENANT | COMPANY | COMPANY | COMPANY | COMPANY |
| **empresa_id en body CREATE** | No aplica | Obligatorio | Obligatorio | Obligatorio | Obligatorio |
| **empresa_id contexto motor** | `null` | JWT sesión | JWT sesión | JWT sesión | JWT sesión |
| **Permiso CREATE** | `org.empresa.crear` | `org.sucursal.crear` | `org.departamento.crear` | `org.centro_costo.crear` | `org.cargo.crear` |
| **Endpoint CREATE** | POST `/org/empresa` | POST `/org/sucursales` | POST `/org/departamentos` | POST `/org/centros-costo` | POST `/org/cargos` |
| **Response 201 campo código** | `codigo_empresa` | `codigo` | `codigo` | `codigo` | `codigo` |
| Código editable UPDATE | Sí (AS-IS) → **objetivo inmutable BR-IMM** | Sí (AS-IS) → **BR-IMM** | Sí → **BR-IMM** | Sí → **BR-IMM** | Sí → **BR-IMM** |
| **UoW transaccional CREATE** | Sí (allocate + insert + bootstrap cfg) | Sí (allocate + insert) | Sí | Sí | Sí |

---

## 2. Comportamiento AUTO_DEFAULT (común a las 5)

| Condición payload CREATE | Comportamiento Backend |
|--------------------------|------------------------|
| Campo código **omitido** | Auto-generación (`allocate` AUTO) |
| Campo código **`null`** | Auto-generación |
| Campo código **`""`** (vacío) | Tratado como omitido → auto-generación |
| Campo código **con valor** | Manual aceptado si pasa validación motor + unicidad BD |
| Política MANUAL_ONLY | **No aplica** — ninguna entidad ORG Ola 1 |
| Política AUTO_REQUIRED | **No aplica** — ninguna entidad ORG Ola 1 |

---

## 3. Diferencias críticas org_empresa vs company-scoped

| Aspecto | org_empresa | Resto (EMPRESA scope) |
|---------|-------------|------------------------|
| Unicidad código | Por **tenant** (`cliente_id`) | Por **empresa** (`cliente_id` + `empresa_id`) |
| Secuencia cfg | TENANT (`empresa_id` null en cfg) | EMPRESA (una fila cfg por empresa) |
| Bootstrap especial | EMP001 onboarding + cfg `ultimo_numero=1` | Seed cfg al crear empresa |
| Primer auto usuario | **EMP002** (EMP001 reservado bootstrap) | **{PREF}001** en cada empresa |
| Pre-check adicional CREATE | Duplicado **RUC** (409) | Solo duplicado código |
| Post-create side effect | `insertar_secuencias_codigo` (cfg EMPRESA) | Ninguno adicional |

---

## 4. Formato de código auto-generado

| Regla | Valor |
|-------|-------|
| Perfil formatter | FMT_STANDARD |
| Patrón | `{prefijo}{número padded}` |
| Separador | Vacío por defecto (sin guión) |
| Padding | 3 dígitos (`001`..`999`) |
| Prefijo | Desde `cfg_codigo_secuencia` del tenant/empresa |

**Nota Frontend:** el prefijo **no** lo elige el usuario en operación normal; proviene de configuración tenant. Cambios de prefijo futuros serán vía módulo admin cfg (fuera Ola 1).

---

## 5. Compatibilidad payload legacy

| Escenario Frontend anterior | ¿Sigue funcionando? |
|------------------------------|---------------------|
| Envía código manual en CREATE | ✅ Sí |
| Envía código obligatorio generado en FE | ✅ Sí (si único y válido) |
| Omite código (nuevo) | ✅ Sí — auto Backend |
| Read/List sin cambios | ✅ Sin cambio de contrato |
| UPDATE cambia código | ✅ Sin cambio |

---

## 6. Entidades ORG fuera de este contrato

| Entidad / campo | Motor Ola 1 | Notas Frontend |
|-----------------|-------------|----------------|
| `org_parametro_sistema.codigo_parametro` | No | MANUAL_ONLY — sin cambio |
| `org_empresa.ruc` | No (EXTERNAL) | Siempre obligatorio usuario |
| `org_empresa.codigo_ciiu` | No (EXTERNAL) | Opcional catálogo |

---

*Contratos detallados: [`02_ENTITY_CONTRACTS.md`](02_ENTITY_CONTRACTS.md)*
