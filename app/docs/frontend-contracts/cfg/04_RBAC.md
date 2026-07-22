# CFG — RBAC para Frontend

**Versión:** 1.0

Solo dos permisos aplican al MVP.

| Permiso | Código |
|---------|--------|
| Consultar | `cfg.secuencias.consultar` |
| Actualizar | `cfg.secuencias.actualizar` |

---

## 1. Pantallas y permisos

| Pantalla / zona | Requiere |
|-----------------|----------|
| Entrada al módulo CFG / menú “Secuencias de código” | `cfg.secuencias.consultar` |
| Listado | `cfg.secuencias.consultar` |
| Detalle (lectura) | `cfg.secuencias.consultar` |
| Panel Preview | `cfg.secuencias.consultar` |
| Formulario de edición / Guardar | `cfg.secuencias.actualizar` |
| Desactivar | `cfg.secuencias.actualizar` |
| Reactivar | `cfg.secuencias.actualizar` |

Sin `consultar`: **ocultar** el módulo completo (o ruta protegida con “sin acceso”).

Con `consultar` y **sin** `actualizar`: modo **solo lectura** (ver listado, detalle, preview).

---

## 2. Botones y controles

| Control | Visible si | Notas |
|---------|------------|-------|
| Ver listado / abrir detalle | `consultar` | |
| Filtros / sort / paginación | `consultar` | |
| Preview | `consultar` | Preferible también `supports_preview !== false` |
| Guardar (PATCH) | `actualizar` **y** `config_locked === false` | Ocultar si solo consulta |
| Desactivar | `actualizar` **y** activa **y** no locked | |
| Reactivar | `actualizar` **y** inactiva **y** no locked | |
| Crear secuencia | — | **No existe** en MVP: no mostrar |
| Alinear / diagnóstico | — | **No existe** en MVP: no mostrar |

---

## 3. Acciones deshabilitadas (aunque haya permiso)

Aunque el usuario tenga `actualizar`:

| Condición | Deshabilitar |
|-----------|--------------|
| `config_locked === true` | Guardar, Desactivar (y Reactivar no aplica de forma útil) |
| Operación en curso (`saving` / `toggling`) | Todas las mutaciones de esa fila |
| `supports_preview === false` | Preview (o ocultar) |

---

## 4. Matriz rápida

| Acción | `consultar` solo | `consultar` + `actualizar` |
|--------|:----------------:|:--------------------------:|
| Listar / detalle | Sí | Sí |
| Preview | Sí | Sí |
| PATCH formato | No | Sí* |
| DELETE soft | No | Sí* |
| POST reactivar | No | Sí* |

\*Sujeto a `config_locked`.

---

## 5. Defensa en profundidad

1. **UI:** ocultar/deshabilitar según permisos + `config_locked`.
2. **API:** el Backend responde **403** si falta permiso; manejar según `03_ERROR_HANDLING.md`.

No confiar solo en ocultar botones: el 403 es la fuente de verdad.
