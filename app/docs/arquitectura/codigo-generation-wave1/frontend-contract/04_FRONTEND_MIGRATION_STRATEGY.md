# Estrategia de migración Frontend

**Objetivo:** Alinear React con Ola 1 ORG **sin romper** despliegues coexistiendo con clientes que aún envían código manual.

---

## 1. Cambios obligatorios para React

| # | Cambio | Entidades | Detalle |
|---|--------|-----------|---------|
| O-01 | Quitar `required` del código en CREATE | 5 maestros ORG | Validación Yup/Zod: `codigo` / `codigo_empresa` optional |
| O-02 | No bloquear submit sin código | 5 formularios CREATE | El Backend genera |
| O-03 | Consumir código del 201 | 5 flujos alta | Usar response para detalle/toast/navegación |
| O-04 | Mantener `empresa_id` en body | Sucursal, Depto, CC, Cargo | Debe igualar empresa sesión |
| O-05 | Manejar 409 duplicado código | 5 entidades | Mensaje campo según §03 |
| O-06 | Manejar 409 RUC duplicado | Empresa | Campo RUC |
| O-07 | Tipos TS Create | 5 entidades | `codigo?` / `codigo_empresa?` optional |

### 1.1 Ejemplo TypeScript Create (cargo)

```typescript
// Antes (legacy)
interface CargoCreate {
  empresa_id: string;
  codigo: string;        // required
  nombre: string;
  moneda_salarial: string;
}

// Después (Ola 1)
interface CargoCreate {
  empresa_id: string;
  codigo?: string | null;  // optional
  nombre: string;
  moneda_salarial: string;
}
```

### 1.2 Ejemplo envío payload

```typescript
// Recomendado — omitir clave
const payload = { empresa_id, nombre, moneda_salarial };

// Alternativa equivalente
const payload = { ..., codigo: null };

// Evitar enviar "" si el formulario lo produce — Backend lo trata como omitido,
// pero omitir la clave es más claro en DevTools.
```

---

## 2. Cambios opcionales para React

| # | Cambio | Beneficio |
|---|--------|-----------|
| P-01 | Ocultar input código en CREATE estándar | UX simplificada |
| P-02 | Badge «Código automático al guardar» | Expectativa usuario |
| P-03 | Sección colapsada «Código manual (avanzado)» | Implantación / migración |
| P-04 | Toast «Creado con código {X}» post-201 | Confirmación visual |
| P-05 | Deshabilitar auto-preview local correlativo | Evitar confusión con Backend |
| P-06 | Integrar preview cfg (futuro) | Mostrar estimado pre-guardado |

---

## 3. Sin cambio requerido

| Área | Motivo |
|------|--------|
| Listados / grillas | Read sin cambio |
| Columna código en tablas | Sigue poblada |
| Búsqueda `buscar` | Backend unchanged |
| UPDATE / edición | Código editable legacy |
| Parámetros sistema | MANUAL_ONLY — fuera Ola 1 |
| RUC, CIIU, ubigeo | EXTERNAL — sin cambio |
| Permisos RBAC | Mismos `org.*.crear` |

---

## 4. Estrategia de migración sin ruptura

### Fase 1 — Compatible (recomendada primera PR)

```
1. Schemas FE optional codigo
2. Formularios: quitar required, mantener input visible disabled o hidden
3. Si usuario no escribe → no enviar campo
4. Si usuario escribe → enviar manual (compat legacy)
5. QA: casos X-01 y X-02
```

**Rollback:** revertir optional → required en FE; Backend sigue aceptando ambos.

### Fase 2 — UX objetivo

```
1. Ocultar input código CREATE usuarios finales
2. Mostrar código solo en detalle post-201
3. Sección avanzada solo rol implantación
4. QA: regresión listados + edición
```

### Fase 3 — Inmutabilidad (BR-IMM — normativa aprobada)

```
1. Código UPDATE solo lectura (**BR-IMM-01** — ADR code-immutability aprobado)
2. Omitir código del payload PUT (coordinar con enforcement Backend Fase 2 runtime)
3. Preview vía API cfg admin (futuro, independiente)
```

> BR-M-30 ya no es la fuente. Ver `code-generation/code-immutability/`.
---

## 5. Feature flags sugeridos

| Flag | Comportamiento |
|------|----------------|
| `ORG_AUTO_CODE_CREATE` (default ON) | Omitir código en submit |
| `ORG_MANUAL_CODE_OVERRIDE` (default OFF prod) | Muestra input avanzado |

Permite despliegue gradual por tenant sin branch Backend.

---

## 6. Checklist PR Frontend

- [ ] CREATE empresa: `codigo_empresa` optional
- [ ] CREATE sucursal/depto/cc/cargo: `codigo` optional
- [ ] Payload sin código genera 201 en staging
- [ ] Response muestra código en UI
- [ ] 409 duplicado mostrado al usuario
- [ ] 403 empresa mismatch manejado
- [ ] Tests e2e: auto + manual (opcional)
- [ ] Sin regresión UPDATE
- [ ] Sin regresión listados

---

## 7. Ambiente y dependencias

| Dependencia | Notas |
|-------------|-------|
| Backend Ola 1 desplegado | Tenant con cfg seed post-onboarding |
| Sesión empresa activa | Requerida formularios company-scoped |
| OpenAPI / codegen | Regenerar tipos si usan generator — campo ya optional en schema |

---

## 8. Preguntas frecuentes Frontend

**¿Debo enviar `codigo: null` explícito?**  
No es necesario; omitir la propiedad es suficiente.

**¿Puedo seguir enviando código generado en FE?**  
Sí, mientras sea único y válido — pero se desaconseja; dejar al Backend.

**¿El listado trae código antes del cambio FE?**  
Sí — Read no cambió.

**¿EMP001 aparece en alta manual?**  
EMP001 lo crea bootstrap; primer alta usuario auto → EMP002. No reservar EMP001 en FE.

**¿Cuándo preview?**  
Cuando exista módulo admin cfg (Fase posterior); no bloquea Ola 1.

---

*Índice paquete: [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md)*
