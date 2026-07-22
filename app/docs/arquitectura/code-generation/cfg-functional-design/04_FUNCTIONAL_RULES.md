# Reglas funcionales

**Paquete:** `cfg-functional-design`  
**Fecha:** 2026-07-17

---

## 1. Operaciones permitidas (producto)

### MVP

| ID | Operación | Permiso |
|----|-----------|---------|
| CFG-01 | Listar secuencias | consultar |
| CFG-02 | Ver detalle enriquecido | consultar |
| CFG-03..06 | Actualizar prefijo / separador / padding / numero_inicial | actualizar |
| CFG-07 | Activar | actualizar |
| CFG-08 | Desactivar | actualizar |
| OPS-01 | Preview próximo código | consultar |
| OPS-03 | Ver contador (en detalle) | consultar |

### Post-MVP (diseñadas, no MVP)

| ID | Operación | Permiso |
|----|-----------|---------|
| MNT-01 | Align counter | mantener |
| MNT-02 | Validar config dry-run | actualizar |
| OPS-02 | Validar manual | consultar |
| DGN-01..06 | Diagnóstico | diagnosticar |
| DGN-07 | Historial | consultar / diagnosticar |

---

## 2. Operaciones explícitamente prohibidas

| Prohibición | Motivo de producto |
|-------------|-------------------|
| Crear secuencia libre (alta admin) | Solo seed/lazy del Motor |
| Eliminar físicamente una secuencia | Soft-disable únicamente |
| Editar `ultimo_numero` en formulario | Riesgo de colisión / bypass |
| Reiniciar contador a 0 arbitrario | Integridad correlativa |
| Cambiar `sequence_key`, scope, fingerprint, cliente | Identidad inmutable |
| Cambiar `generation_policy` desde UI | Gobernanza SequenceCatalog |
| Reescribir códigos históricos en ORG/INV | Inmutabilidad de códigos emitidos |
| Administrar series fiscales en este módulo v1 | Otro store |
| Operar cross-tenant sin impersonación | Aislamiento SaaS |
| Desactivar `org_empresa` | Bloquearía altas de empresa |
| PATCH configuración de `org_empresa` (v1) | Semi-inmutable BR-BOOT-04 |

---

## 3. Shared Database vs Dedicated Database

| Aspecto | Shared | Dedicated | Percepción usuario |
|---------|--------|-----------|-------------------|
| Pantallas | Idénticas | Idénticas | Sin diferencia |
| Datos visibles | Solo su `cliente_id` | Solo su tenant BD | Igual |
| Preview / edición | Misma semántica | Misma semántica | Igual |
| Mensajes de error | Funcionales | Funcionales | Sin filtrar errores de topología |
| Rendimiento | Puede variar | Puede variar | Sin copy que mencione “shared/dedicated” |

**Regla de producto:** la topología es **invisible**. Cualquier fallo de conexión se traduce a error genérico de sistema / reintento, no a explicación de arquitectura.

---

## 4. Estrategia de auditoría funcional

| Evento | Qué debe quedar registrado | Visible en UI MVP |
|--------|----------------------------|-------------------|
| PATCH formato | Usuario, timestamp, valores nuevos (idealmente diff) | `fecha_actualizacion` / usuario en detalle |
| Activar / desactivar | Usuario, nuevo estado | Sí (estado + auditoría básica) |
| Preview | Opcional (solo telemetría; no obligatorio negocio) | No |
| Align (post-MVP) | Antes/después contador + motivo | Sí en resultado + historial v1.3 |

**MVP mínimo:** persistir `usuario_actualizacion_id` + `fecha_actualizacion` en mutaciones.  
**v1.3:** historial consultable (P8).

El usuario debe entender: “quién cambió el prefijo y cuándo”, no el detalle interno del Motor.

---

## 5. Estrategia de permisos (RBAC)

| Permiso | Capacidades de producto |
|---------|-------------------------|
| `cfg.secuencias.consultar` | Menú, listado, detalle, preview |
| `cfg.secuencias.actualizar` | Editar B, activar, desactivar |
| `cfg.secuencias.mantener` | Align (post-MVP) — **no** incluido en “actualizar” |
| `cfg.secuencias.diagnosticar` | Panel diagnóstico (post-MVP) |

### Asignación sugerida de roles

| Rol | consultar | actualizar | mantener | diagnosticar |
|-----|-----------|------------|----------|--------------|
| ADMIN_TENANT | ✅ | ✅ | ○ opcional | ○ opcional |
| Implantación L2 | ✅ | ✅ | ✅ | ✅ |
| MANAGER | ✅ | ○ | ❌ | ○ |
| USER | ❌ / ○ | ❌ | ❌ | ❌ |

**SEC-01:** se puede otorgar `mantener` sin `actualizar`.  
**SEC-02:** preview exige `consultar`, no `actualizar`.

Gates de sesión: sesión ERP completa; `cliente_id` operativo impersonación-safe.

---

## 6. Estrategia de validaciones (funcionales)

| Validación | Momento | Mensaje tipo |
|------------|---------|--------------|
| Campos inmutables en payload | Guardar | “Este campo no se puede modificar” |
| org_empresa locked | Guardar / editar | “La secuencia de empresa está protegida por el sistema” |
| Prefijo vacío cuando formato lo requiere | Guardar | “El prefijo es obligatorio para esta secuencia” |
| Prefijo longitud / charset | Guardar | “Prefijo inválido (máx. 10, alfanumérico…)” |
| Padding insuficiente / agotamiento | Guardar | “Con este ancho el correlativo se agotaría pronto / es inválido” |
| numero_inicial inconsistente con ultimo_numero | Guardar | “El número inicial no es compatible con el contador actual” |
| Desactivar org_empresa | Acción | “No se puede desactivar esta secuencia” |
| Sin permiso | Acción | 403 / UI oculto |
| No encontrada | Detalle | 404 |

Validaciones de formato profundo de códigos de negocio siguen en el Motor; el admin valida **configuración**, no sustituye validators de CREATE ERP.

---

## 7. Riesgos de UX

| ID | Riesgo | Mitigación |
|----|--------|------------|
| UX-01 | Usuario cree que Preview “guarda” el número | Disclaimer obligatorio |
| UX-02 | Cambiar prefijo pensando que reescribe históricos | Banner en edición |
| UX-03 | Desactivar secuencia crítica sin entender impacto | Modal + copy por policy AUTO_REQUIRED |
| UX-04 | Exponer `sequence_key` críptica sin label | Enrich módulo/entidad en listado |
| UX-05 | Confundir módulo cfg con Platform | Menú bajo Configuración ERP, no SuperAdmin |
| UX-06 | Editar org_empresa y romper EMP001 | Lock total v1 |
| UX-07 | Mostrar fingerprint/UUIDs como campos principales | Panel técnico colapsado |
| UX-08 | Listado enorme sin filtros | Filtros módulo/scope/activo + paginación |
| UX-09 | Diferenciar Shared/Dedicated en UI | Prohibido en copy |
| UX-10 | Botón Align visible a todos | Solo post-MVP + permiso mantener |

---

## 8. Reglas especiales org_empresa (resumen producto)

| Capacidad | ¿Permitida? |
|-----------|-------------|
| Ver en listado/detalle | Sí |
| Preview | Sí |
| Editar formato | **No** (v1) |
| Desactivar | **No** |
| Align | Post-MVP, rol elevado, change-controlled |

---

## 9. Efecto sobre códigos ya emitidos

**Regla de producto global:** ningún flujo del Administrador modifica filas de negocio ORG/INV ni altera códigos ya persistidos. Solo cambia la configuración que usará el Motor en **futuras** generaciones.
