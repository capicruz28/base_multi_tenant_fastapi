# Implementación — fix `DELETE /clientes/{cliente_id}` HTTP 500

**Fecha:** 2026-06-02  
**Referencia:** `DELETE_CLIENTE_500_AUDIT.md`

## Cambio

`ClienteService.eliminar_cliente` — L453:

```python
resultado = await execute_update(query, (cliente_id,), connection_type=DatabaseConnection.ADMIN)
```

## QA

| Escenario | HTTP | Resultado |
|-----------|------|-----------|
| DELETE cliente creado para prueba | **200** | OK |
| DELETE UUID inexistente | **404** (`CLIENT_NOT_FOUND`) | OK |
| DELETE cliente SYSTEM | **400** (`CANNOT_DELETE_SYSTEM_CLIENT`) | OK |

- Unit: `pytest tests/unit/test_cliente_eliminar_execute_update_await.py tests/unit/test_tenant_exception_propagation.py -q` → 10 passed
- HTTP: `scripts/_run_delete_cliente_fix_qa.py` → evidencia `app/bootstrap_v2/00_manifest/evidence/DELETE_CLIENTE_500_FIX_VALIDATION.json`

## Incidencias

Ninguna durante QA post-fix.
