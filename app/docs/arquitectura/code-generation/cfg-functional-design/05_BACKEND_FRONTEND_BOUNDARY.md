# Frontera Backend / Frontend

**Paquete:** `cfg-functional-design`  
**Fecha:** 2026-07-17  
**Alcance:** recomendaciones de frontera — **sin contratos OpenAPI ni código**

---

## 1. Qué hace el Frontend

| Responsabilidad FE | Detalle |
|--------------------|---------|
| Navegación y menú | Entrada Configuración → Secuencias según permiso |
| Listado | Filtros, paginación, columnas, empty states |
| Detalle | Composición de secciones A–E |
| Formularios | Inputs de campos B; bloqueo visual de A/C/D |
| Confirmaciones | Modal desactivar; toast éxito/error |
| Preview UX | Dispara acción; muestra estimación + disclaimer |
| RBAC UI | Ocultar/deshabilitar según permisos efectivos |
| Copy | Banners de inmutabilidad histórica y preview |

**No hace FE:**

- Calcular el próximo correlativo por su cuenta
- Escribir SQL / llamar Store del Motor
- Decidir policy de generación
- Mutar `ultimo_numero`
- Conocer Shared vs Dedicated

---

## 2. Qué hace el Backend

| Responsabilidad BE | Detalle |
|--------------------|---------|
| Autenticación / sesión ERP | `require_erp_session`, `cfg_deps` |
| Autorización | `cfg.secuencias.*` |
| Aislamiento tenant | Filtro `cliente_id` + 404 cross-tenant |
| Lectura/escritura cfg | Queries + Repo; solo campos B en update |
| Enrich Catalog | Metadatos read-only en Read |
| Preview / align | Delegación a `CodigoGeneracionGateway` |
| Validaciones de negocio admin | org_empresa lock, BR-CUST, inmutables |
| Auditoría | usuario + timestamp en mutaciones |
| Paridad Shared/Dedicated | UoW session correcta |

**No hace BE (en este módulo):**

- Renderizar UI
- Seed de onboarding (sigue en Platform/tenant)
- Emitir códigos de maestros (ORG/INV)

---

## 3. Contrato funcional FE ↔ BE (conceptual)

| Necesidad UI | Capacidad Backend esperada (futura) |
|--------------|-------------------------------------|
| Tabla listado | GET list + filtros + page |
| Ficha detalle | GET by id enriquecido |
| Guardar formato | PATCH campos B |
| Activar/Desactivar | POST dedicados o PATCH `es_activo` (una convención al implementar) |
| Preview | POST preview → `{ codigo_estimado, consume_contador: false, … }` |
| Errores | Códigos/mensajes estables (`ORG_EMPRESA_CFG_LOCKED`, `IMMUTABLE_FIELD`, …) |

El detalle de paths/schemas queda para la fase de diseño técnico OpenAPI **después** de autorizar MVP Backend; este documento no los fija de nuevo (ya existen propuestas en `codigo-generation-admin/03`).

---

## 4. Recomendaciones para Frontend

1. Tratar el módulo como **configuración ERP**, no como dashboard analítico.  
2. Reutilizar patrones de listado/detalle de ORG (filtros, paginación, soft states).  
3. Badges claros para policy y activo; no sobrecargar con chips.  
4. Disclaimer de Preview siempre visible en el resultado.  
5. Banner fijo en modo edición: códigos históricos no cambian.  
6. `org_empresa`: estado “Protegida”, sin inputs.  
7. No mostrar fingerprint en la vista principal.  
8. Preparar feature flags / ocultar Align y Diagnóstico hasta v1.1/v1.2.  
9. i18n de `sequence_key` vía labels de módulo/entidad, no solo la key cruda.  
10. Tras Ola 1 ORG/INV FE: el admin **no** cambia formularios de alta de maestros; solo la consola `cfg`.

---

## 5. Recomendaciones para Backend

1. Implementar como módulo ERP V4 `cfg` (ADR aprobado).  
2. Orquestar; **no** reimplementar Formatter/PolicyResolver.  
3. Preview **solo** vía Gateway; tests de no side-effect.  
4. Rechazar payloads con campos A/C/D.  
5. Lock `org_empresa` en servicio (no solo UI).  
6. Extender persistencia de `numero_inicial` + audit columns si el MVP lo incluye.  
7. Sembrar RBAC antes o junto a los primeros endpoints.  
8. Misma semántica Shared/Dedicated; tests de session path.  
9. No acoplar a services ORG/INV.  
10. Congelar Motor/Catalog/ORG/INV salvo extensiones menores de Repo autorizadas.

---

## 6. Secuencia de entregables recomendada

```text
Diseño funcional (este paquete) ✅
  → Autorización MVP Backend
    → Backend MVP + OpenAPI
      → Paquete contrato Frontend (docs)
        → Frontend MVP
          → v1.1 Align / v1.2 Diagnóstico
```

---

## 7. Frontera con el Motor

```text
FE ──HTTP──▶ módulo cfg (ERP) ──▶ Gateway / Catalog / Repo
                      │
                      └──▶ NO escribe Formatter ni SequenceCatalog
```

El Frontend **nunca** habla con `app/core/codigo` directamente.
