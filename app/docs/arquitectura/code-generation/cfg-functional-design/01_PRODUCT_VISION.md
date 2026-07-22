# Visión de producto — Administrador del Motor

**Paquete:** `cfg-functional-design`  
**Fecha:** 2026-07-17

---

## 1. Objetivos funcionales del módulo

| ID | Objetivo | Resultado medible |
|----|----------|-------------------|
| OBJ-01 | **Visibilidad** | El Tenant Admin ve todas las secuencias CFG de su tenant (eager + lazy existentes) |
| OBJ-02 | **Comprensión** | En cada secuencia entiende módulo, entidad, política, formato y contador actual |
| OBJ-03 | **Parametrización segura** | Puede cambiar prefijo, separador, padding, piso y activo sin romper históricos |
| OBJ-04 | **Anticipación** | Puede previsualizar el próximo código estimado antes de operar |
| OBJ-05 | **Gobernanza** | No puede alterar identidad, scope, política de catálogo ni contador directo |
| OBJ-06 | **Transversalidad** | Una sola experiencia para ORG, INV y futuros ERP |
| OBJ-07 | **Paridad topología** | Misma UX en Shared y Dedicated Database |

**Fuera de objetivos del módulo:**

- Emitir códigos de negocio (eso lo hacen ORG/INV).
- Crear tenants o suscribir módulos (Platform).
- Administrar series fiscales (store distinto; fase futura aparte).
- Reescribir códigos ya guardados en maestros/documentos.

---

## 2. Perfil de usuarios

| Perfil | Permisos típicos | Necesidad | Frecuencia |
|--------|------------------|-----------|------------|
| **ADMIN_TENANT** | consultar + actualizar | Parametrizar formato corporativo | Baja–media (implantación y cambios de política) |
| **Parametrizador / consultor implantación** | consultar + actualizar (+ mantener post-MVP) | Ajustar secuencias al go-live | Alta en proyecto, baja después |
| **MANAGER_TENANT** | consultar (opcional actualizar) | Entender numeración; cambios limitados | Baja |
| **USER operativo** | ninguno o solo consultar | No es usuario primario | Nula–baja |
| **SuperAdmin (impersonado)** | según rol efectivo en tenant | Soporte L2 sin consola Platform | Excepcional |

**Persona primaria:** Administrador del tenant que configura el ERP, no el operador de almacén ni el SuperAdmin SaaS.

---

## 3. Casos de uso

### 3.1 MVP (obligatorios)

| ID | Caso de uso | Actor | Resultado |
|----|-------------|-------|-----------|
| CU-01 | Consultar listado de secuencias | Admin | Ve tabla filtrable/paginada |
| CU-02 | Abrir detalle de una secuencia | Admin | Ve identidad, formato, contador, policy |
| CU-03 | Editar configuración de formato | Admin con actualizar | Guarda prefijo/separador/padding/piso |
| CU-04 | Activar secuencia | Admin con actualizar | Vuelve a permitir allocate |
| CU-05 | Desactivar secuencia | Admin con actualizar | Bloquea nuevos allocate; confirma impacto |
| CU-06 | Previsualizar próximo código | Admin con consultar | Ve estimación + disclaimer |
| CU-07 | Intentar editar org_empresa | Admin | Sistema rechaza con mensaje claro |
| CU-08 | Intentar editar contador / policy | Admin | Campos no editables o error de inmutabilidad |

### 3.2 Post-MVP (planificados)

| ID | Caso de uso | Fase |
|----|-------------|------|
| CU-09 | Alinear contador tras importación | v1.1 |
| CU-10 | Ver diagnóstico de salud / drift | v1.2 |
| CU-11 | Consultar historial de cambios admin | v1.3 |
| CU-12 | Validar código manual desde admin | v1.3 |

---

## 4. Navegación funcional

```text
Shell ERP (tenant autenticado + sesión ERP)
  └── Menú: Configuración
        └── Secuencias de código          [cfg.secuencias.consultar]
              ├── Listado de secuencias   (pantalla hub)
              └── Detalle / {secuencia}
                    ├── Resumen + metadatos
                    ├── Formulario edición (si actualizar)
                    ├── Acciones: Preview | Activar | Desactivar
                    └── (post-MVP) Mantenimiento | Diagnóstico
```

**Reglas de navegación:**

- Entrada de menú **oculta** sin `consultar`.
- Botones de edición **ocultos o deshabilitados** sin `actualizar`.
- Acciones de align **no visibles** en MVP.
- No existe ruta bajo consola SuperAdmin / Platform.

---

## 5. Organización de pantallas (mapa)

| Pantalla | Propósito | MVP |
|----------|-----------|-----|
| **P1 — Listado** | Descubrir y filtrar secuencias | Sí |
| **P2 — Detalle** | Entender una secuencia + acciones | Sí |
| **P3 — Edición (modo del detalle)** | Cambiar campos B | Sí (inline o drawer en P2) |
| **P4 — Confirmación desactivar** | Modal de impacto | Sí |
| **P5 — Preview** | Modal/panel resultado estimado | Sí |
| **P6 — Align** | Mantenimiento con motivo | No (v1.1) |
| **P7 — Diagnóstico** | Panel alertas | No (v1.2) |
| **P8 — Historial** | Auditoría de cambios | No (v1.3) |

**Decisión de producto MVP:** **no** crear wizard multi-paso. Flujo = Listado → Detalle → Editar/Preview/Activar en el mismo contexto.

---

## 6. Propuesta de valor (una frase)

> Dar al Tenant Admin una consola clara y segura para entender y ajustar cómo el ERP numerará códigos futuros — sin exponer el Motor, sin SQL y sin arriesgar el contador.
