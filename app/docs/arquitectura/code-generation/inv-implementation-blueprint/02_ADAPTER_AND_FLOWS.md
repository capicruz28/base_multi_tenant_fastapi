# Adapter INV, flujos CREATE/UPDATE y OpenAPI

---

## 1. Adapter `InvCodigoGenerationService`

### 1.1 Origen

Copiar estructura de:

`app/modules/org/application/services/org_codigo_generation_service.py`

### 1.2 Destino propuesto

`app/modules/inv/application/services/inv_codigo_generation_service.py`

### 1.3 Contrato (idéntico en semántica a ORG)

| Método | Responsabilidad |
|--------|-----------------|
| `build_empresa_context(...)` | `GenerationContext` con `client_id` + `empresa_id` + `manual_code` |
| `build_context(...)` | Genérico (empresa_id opcional) |
| `resolve_codigo_for_create(sequence_key, *, session, client_id, empresa_id, manual_code)` | `Gateway.allocate` → `result.code` |

### 1.4 Diferencias permitidas vs ORG

| Aspecto | Decisión |
|---------|----------|
| Nombre clase | `InvCodigoGenerationService` |
| `build_tenant_context` | **Opcional** — ninguna key INV Ola 1 es TENANT; puede omitirse o dejarse por simetría |
| Conocimiento de entidades | **Ninguno** — solo `sequence_key` |

### 1.5 Prohibido en el adapter

- Lógica de formato, UNIQUE de negocio, RBAC  
- Imports desde `app.modules.org`  
- Modificar Gateway  

---

## 2. Flujo CREATE (oficial — espejo ORG cargo)

```text
POST /inv/categorias  (piloto)
  → RBAC + get_inv_session_client_id
  → enforce_body_empresa_matches_session
  → ensure_empresa_in_tenant
  → manual_codigo = normalize(omit/null/"" → None)
  → async with get_connection_for_tenant(...) as session:
       async with session.begin():
         → [si manual] get_categoria_by_codigo(..., session=session)
              → ConflictError 409 si existe
         → codigo = InvCodigoGenerationService.resolve_codigo_for_create(
                "inv_categoria_producto",
                session=session,
                client_id=...,
                empresa_id=...,
                manual_code=manual_codigo,
           )
         → payload = model_dump(); payload["codigo"] = codigo
         → apply_create_audit(payload, usuario_id)   # conservar INV
         → create_categoria(..., session=session)
  → 201 CategoriaRead
```

### 2.1 Variantes por policy

| Policy | Body | Service |
|--------|------|---------|
| AUTO_DEFAULT (F1) | omit / manual | Como arriba |
| AUTO_REQUIRED (F2) | omit / ignorar si llega | `manual_code=None` siempre; no pre-check manual |

### 2.2 Queries obligatorias para CREATE (gap Categoría AS-IS)

| Query | Estado Categoría | Acción |
|-------|------------------|--------|
| `get_categoria_by_codigo(client_id, empresa_id, codigo, session=, exclude_id=)` | **No existe** | **Crear** (plantilla `get_cargo_by_codigo`) |
| `create_categoria(..., session=)` | Sin dual-path | **Añadir** `session: Optional[AsyncSession]` |
| `get_categoria_by_id` en TX | Sin session | Dual-path si se lee dentro de UoW |

> Baseline permite tocar queries **solo** para dual-path / `get_by_codigo` — no cambiar SQL de negocio.

---

## 3. Flujo UPDATE (BR-IMM)

```text
PUT /inv/categorias/{id}
  → require_session_empresa_id
  → get_categoria_by_id
  → payload = model_dump(exclude_unset=True)
       # CategoriaUpdate YA NO tiene "codigo"
  → update_categoria(...)   # sin ramas de código
  → 200 CategoriaRead (codigo intacto)
```

| Prohibido en UPDATE | |
|---------------------|---|
| `if "codigo" in payload` | |
| `get_*_by_codigo` | |
| `InvCodigoGenerationService` / Gateway | |

**Categoría AS-IS:** Update ya no hace UNIQUE de código, pero el schema aún expone `codigo` → OpenAPI legacy. Quitar el campo es suficiente para alineación BR-IMM (Pydantic ignora extras).

---

## 4. OpenAPI esperado (post-implementación)

### 4.1 Piloto Categoría

| Schema | `codigo` |
|--------|----------|
| `CategoriaCreate` | Presente, **not required** |
| `CategoriaUpdate` | **Ausente** |
| `CategoriaRead` | Presente, **required** |

| Path | Body |
|------|------|
| `POST /api/v1/inv/categorias` | `CategoriaCreate` |
| `PUT /api/v1/inv/categorias/{categoria_id}` | `CategoriaUpdate` (sin código) |

### 4.2 Siete entidades (contrato objetivo)

| Entity schemas | Create código/número | Update | Read |
|----------------|----------------------|--------|------|
| Categoria, UM, TipoMov, Almacen | optional `codigo` | sin campo | required |
| Producto | optional `codigo_sku` | sin `codigo_sku` | required |
| Movimiento | sin required `numero_movimiento` | sin número | required |
| InventarioFisico | sin required `numero_inventario` | sin número | required |

Al cerrar cada fase: regenerar `app/docs/openapi_snapshot.json` (tarea dedicada, como ORG).

---

## 5. Pseudocódigo adapter (referencia — no implementar aquí)

```python
# Estructura objetivo — espejo ORG
class InvCodigoGenerationService:
    @staticmethod
    async def resolve_codigo_for_create(
        sequence_key: str,
        *,
        session: AsyncSession,
        client_id: UUID,
        empresa_id: UUID | None = None,
        manual_code: str | None = None,
    ) -> str:
        context = GenerationContext(
            client_id=client_id,
            empresa_id=empresa_id,
            operation=GenerationOperation.CREATE,
            manual_code=_normalize(manual_code),
        )
        result = await CodigoGeneracionGateway.allocate(
            sequence_key, context, session
        )
        return result.code
```

---

*Secuencia y tests: [`03_IMPLEMENTATION_SEQUENCE.md`](03_IMPLEMENTATION_SEQUENCE.md)*
