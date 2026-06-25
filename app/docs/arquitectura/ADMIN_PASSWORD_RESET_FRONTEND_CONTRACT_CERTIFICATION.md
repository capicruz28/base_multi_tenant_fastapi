# Certificación de Contrato — Reset Administrativo de Contraseña (Frontend)

**Documento:** `ADMIN_PASSWORD_RESET_FRONTEND_CONTRACT_CERTIFICATION.md`  
**Fecha:** 2026-06-24  
**Modo:** Certificación READ ONLY (sin cambios de código, OpenAPI ni implementación)  
**Alcance:** Contrato HTTP observable para consumo Frontend — Gestión de Usuarios  
**Fuentes auditadas:** Implementación PR1, OpenAPI generado, specs funcionales y técnicas aprobadas

**Relacionado (flujo post-reset del usuario afectado):** [`AUTH_FRONTEND_CONTRACT_CERTIFICATION.md`](AUTH_FRONTEND_CONTRACT_CERTIFICATION.md) — Force Password Change y `POST /auth/password/change/`

---

## 1. Estado de certificación

| Campo | Valor |
|-------|-------|
| **Endpoint auditado** | `POST /api/v1/usuarios/{usuario_id}/reset-password/` |
| **OpenAPI** | ✅ Incluido (`operationId`: `reset_usuario_password_admin`) |
| **Implementable por Frontend** | **Sí** |
| **Dictamen** | **B) Certificado con observaciones** |

### Observaciones de certificación (no bloqueantes)

| # | Observación | Impacto FE |
|---|-------------|------------|
| O1 | Errores de negocio del endpoint se devuelven como `HTTPException` con solo `detail` — **sin `error_code` en el body** en la práctica observable | Clasificar errores por **HTTP + texto `detail`**, no depender de `error_code` |
| O2 | Permiso `admin.usuario.reset_password` puede no estar asignado en tenants legacy hasta repair RBAC | Admin sin permiso recibe **403**; ocultar acción si el perfil no tiene el permiso |
| O3 | El flujo del **usuario afectado** (login + cambio obligatorio) no es parte de este endpoint — usar contrato Auth existente | Ver §6 y documento Auth relacionado |
| O4 | Usuario **inactivo** puede recibir reset exitoso pero **no puede iniciar sesión** hasta reactivación | Mostrar advertencia post-reset si `es_activo = false` en ficha de usuario |

---

## 2. Endpoint oficial

| Campo | Valor |
|-------|-------|
| **Método HTTP** | `POST` |
| **Ruta canónica** | `/api/v1/usuarios/{usuario_id}/reset-password/` |
| **Prefijo API** | `/api/v1` |
| **Montaje** | Módulo Gestión de Usuarios (`/usuarios`) |
| **`operationId` OpenAPI** | `reset_usuario_password_admin` |
| **Tag OpenAPI** | `Usuarios` |
| **Código éxito** | `200 OK` |

### Headers

| Header | Obligatorio | Notas |
|--------|-------------|-------|
| `Authorization: Bearer <access_token>` | ✅ Sí | JWT del administrador autenticado |
| `Host` / subdominio tenant | ✅ Implícito | Resolución de tenant vía middleware (mismo patrón que resto del ERP) |
| `Content-Type` | ❌ No | No hay body JSON requerido |
| `X-Client-Type` | ❌ No | No aplica — este endpoint no emite tokens |

### Autenticación

- Sesión JWT activa del **administrador** que ejecuta el reset.
- El tenant operativo es el del JWT (incluye sesiones de impersonación con permisos de admin en el tenant impersonado).

### RBAC esperado

| Requisito | Valor |
|-----------|-------|
| Rol | «Administrador» (`require_admin` / nivel de acceso LBAC) |
| Permiso API | `admin.usuario.reset_password` |

**Recomendación FE:** mostrar la acción «Restablecer contraseña» solo si el usuario autenticado tiene el permiso `admin.usuario.reset_password` en su lista de permisos (o equivalente del contexto Auth). Adicionalmente, ocultar para usuarios con `proveedor_autenticacion ≠ 'local'` y para el propio usuario autenticado.

---

## 3. Body

| Decisión | **No requiere payload** |
|----------|-------------------------|
| Forma | `POST` sin body, o `{}` tolerado |
| Prohibido enviar | `contrasena`, `password`, `new_password` — el Backend **ignora** cualquier campo en v1 |

**Ejemplo de petición:**

```http
POST /api/v1/usuarios/3fa85f64-5717-4562-b3fc-2c963f66afa6/reset-password/ HTTP/1.1
Host: {tenant}.ejemplo.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 4. Response 200

### Schema OpenAPI: `AdminPasswordResetResponse`

| Campo | Tipo | Siempre presente | Descripción |
|-------|------|------------------|-------------|
| `success` | `boolean` | ✅ | `true` en respuestas exitosas |
| `message` | `string` | ✅ | Mensaje operativo en español |
| `usuario_id` | `UUID` | ✅ | ID del usuario afectado |
| `credenciales_temporales` | `CredencialesTemporalesRead` | ✅ | Bloque de entrega **única** |
| `sesiones_revocadas` | `integer` (≥ 0) | ✅ | Sesiones invalidadas del usuario afectado |

### Schema anidado: `CredencialesTemporalesRead`

| Campo | Tipo | Siempre presente | Descripción |
|-------|------|------------------|-------------|
| `nombre_usuario` | `string` | ✅ | Login del usuario afectado |
| `contrasena` | `string` | ✅ | Contraseña temporal en **texto plano** — solo en esta respuesta |
| `requiere_cambio` | `boolean` | ✅ | Siempre `true` |

### Mensaje de éxito verificado

```
Contraseña restablecida exitosamente. La contraseña temporal solo se muestra una vez; el usuario deberá cambiarla en su próximo acceso.
```

### Ejemplo JSON completo

```json
{
  "success": true,
  "message": "Contraseña restablecida exitosamente. La contraseña temporal solo se muestra una vez; el usuario deberá cambiarla en su próximo acceso.",
  "usuario_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "credenciales_temporales": {
    "nombre_usuario": "jperez",
    "contrasena": "Kx9#mP2vLq4n",
    "requiere_cambio": true
  },
  "sesiones_revocadas": 3
}
```

### Campos que NO vienen en la respuesta

No esperar: hash de contraseña, tokens del usuario afectado, roles, perfil completo, contraseña recuperable en llamadas posteriores.

---

## 5. Catálogo completo de errores

### 5.1 Formato de error observable

| Origen | Formato típico |
|--------|----------------|
| Errores de negocio (400, 404, 500 del servicio) | `{ "detail": "<string>" }` — **sin `error_code`** |
| Sin permiso / sin rol admin (403) | `{ "detail": "<string>" }` — **sin `error_code`** |
| JWT inválido/ausente (401) | `{ "detail": "<string>" }` |
| UUID inválido en path (422) | `{ "detail": "<string \| string[]>", "error_code": "VALIDATION_ERROR" }` |
| Error genérico no capturado (500) | `{ "detail": "Error interno del servidor al restablecer la contraseña." }` |

> **Regla FE:** usar `detail` como fuente primaria; tratar `error_code` como **opcional** (solo garantizado en 422).

### 5.2 Catálogo

| HTTP | `error_code` (si existe) | `detail` esperado (texto verificado o plantilla) | Acción Frontend |
|------|--------------------------|--------------------------------------------------|-----------------|
| **401** | — | `"No se pudieron validar las credenciales"` u otro según deps JWT | Redirigir a login; refrescar sesión admin si aplica |
| **403** | — | `"Permisos insuficientes. Nivel de acceso del usuario (X) es menor al requerido (Y)."` | Ocultar acción; mensaje «sin permisos de administrador» |
| **403** | — | `"No tiene permisos suficientes para realizar esta acción. Se requiere: admin.usuario.reset_password"` | Ocultar acción; contactar admin del tenant |
| **403** | — | `"Usuario inactivo"` | Sesión admin inválida — cerrar sesión |
| **404** | — | `"Usuario no encontrado en este cliente"` | Usuario eliminado, inexistente o cross-tenant — refrescar listado; no reintentar |
| **400** | — | `"El restablecimiento de contraseña no está disponible para usuarios SSO externos"` | No ofrecer reset; indicar gestión vía IdP |
| **400** | — | `"No puede restablecer su propia contraseña por esta vía. Use el cambio de contraseña o solicítelo a otro administrador"` | Redirigir a cambio de contraseña en Account Center / perfil |
| **422** | `VALIDATION_ERROR` | Mensaje de UUID inválido en `usuario_id` | Validar UUID antes de llamar |
| **500** | — | `"Error interno al restablecer la contraseña del usuario"` | Toast de error; permitir reintento |
| **500** | — | `"Error interno al invalidar sesiones del usuario"` | Informar que la contraseña pudo haberse restablecido; sugerir verificar con usuario o reintentar |
| **500** | — | `"Error interno del servidor al restablecer la contraseña."` | Error genérico — reintento o soporte |

### 5.3 Casos que NO son error

| Condición | Comportamiento |
|-----------|----------------|
| Usuario inactivo (`es_activo = false`) | **200 permitido** — advertir que debe reactivarse para que el usuario ingrese |
| Usuario con cambio obligatorio previo | **200 permitido** — nueva temporal invalida la anterior |
| Cuenta bloqueada por intentos | **200 permitido** — bloqueo normalizado en Backend |

---

## 6. Flujo esperado

```mermaid
sequenceDiagram
    participant ADM as Administrador (FE Gestión Usuarios)
    participant API as Backend
    participant USR as Usuario afectado (FE Login)

    ADM->>ADM: Confirmar acción destructiva
    ADM->>API: POST /usuarios/{id}/reset-password/
    API-->>ADM: 200 + credenciales_temporales (una vez)
    ADM->>ADM: Mostrar contraseña temporal (modal)
    ADM->>USR: Comunicar credencial (canal externo)
    USR->>API: POST /auth/login/ (contraseña temporal)
    API-->>USR: 200 + requires_password_change=true
    USR->>API: POST /auth/password/change/
    API-->>USR: 200 + requires_password_change=false
    USR->>API: Acceso ERP normal
```

### Pasos resumidos

1. **Administrador** — desde ficha/listado de usuario local, confirma reset.
2. **Reset** — `POST /api/v1/usuarios/{usuario_id}/reset-password/`.
3. **Recepción única** — mostrar `credenciales_temporales` en UI de confirmación (modal/drawer).
4. **Comunicación** — el administrador entrega usuario + contraseña al afectado (fuera del alcance técnico del FE).
5. **Usuario inicia sesión** — flujo login estándar; recibirá `requires_password_change: true` en `user_data` y JWT.
6. **Force Password Change** — pantalla existente; `POST /api/v1/auth/password/change/` con la temporal como `current_password` (ver contrato Auth).
7. **Acceso ERP** — tras cambio exitoso, `requires_password_change: false`.

### Efectos colaterales transparentes para FE admin

- Todas las sesiones del usuario afectado quedan cerradas (`sesiones_revocadas` informativo).
- La sesión del **administrador** que ejecutó el reset **no** se modifica.

---

## 7. UX esperada

### Mostrar

| Momento | Contenido |
|---------|-----------|
| Confirmación previa | Diálogo de confirmación con advertencia de invalidez de sesiones y entrega única |
| Éxito (200) | `message` del Backend |
| Credenciales | `credenciales_temporales.nombre_usuario` + `contrasena` en pantalla dedicada |
| Copiar | Botón «Copiar contraseña» / «Copiar credenciales» (clipboard API) |
| Advertencia persistente | «Esta contraseña no se volverá a mostrar» |
| Inactivo | Si el usuario tenía `es_activo = false`, avisar: «Debe reactivar al usuario antes de que pueda iniciar sesión» |
| SSO | No mostrar acción de reset (usar `proveedor_autenticacion` del listado/detalle) |
| Propio usuario | No mostrar reset sobre la cuenta del admin autenticado |

### Ocultar

- Campo para que el admin escriba contraseña (no existe en contrato).
- Cualquier intento de «ver contraseña después» o «regenerar sin nuevo POST».
- Reset en usuarios SSO o eliminados.

### Advertir

- Entrega **única** — cierre del modal = pérdida irreversible en UI.
- El usuario **deberá cambiar** la contraseña en el primer acceso (`requiere_cambio: true`).
- Sesiones del usuario afectado serán cerradas.

### Nunca persistir

| Dato | Motivo |
|------|--------|
| `credenciales_temporales.contrasena` | Secreto de un solo uso |
| Response completa en `localStorage` / `sessionStorage` / IndexedDB | Riesgo de exposición |
| Contraseña en logs de consola, analytics o error trackers | Seguridad |
| Cache HTTP de la respuesta | Evitar relectura |

Mantener la contraseña solo en **estado de componente volátil** hasta que el administrador cierre el modal o navegue fuera.

---

## 8. Restricciones

| # | Restricción |
|---|-------------|
| R1 | La contraseña temporal **solo existe** en la respuesta `200` de este endpoint |
| R2 | **No existe** endpoint para recuperarla posteriormente |
| R3 | **No almacenarla** en storage del navegador ni en estado global persistente |
| R4 | **No volver a consultarla** — un segundo reset genera una **nueva** temporal |
| R5 | **No imprimirla** en logs de aplicación, consola ni telemetría |
| R6 | El usuario afectado resuelve el cambio obligatorio solo vía **Auth** (`/auth/password/change/`), no vía Gestión de Usuarios |

---

## 9. Checklist Frontend

### Rutas y API

- [ ] Usar exactamente `POST /api/v1/usuarios/{usuario_id}/reset-password/` (con slash final).
- [ ] Enviar `Authorization: Bearer` del admin.
- [ ] No enviar body (o `{}` vacío como máximo).
- [ ] Tipar respuesta según `AdminPasswordResetResponse` (OpenAPI / cliente generado).

### Visibilidad de la acción

- [ ] Mostrar solo con permiso `admin.usuario.reset_password`.
- [ ] Ocultar si `proveedor_autenticacion !== 'local'`.
- [ ] Ocultar si `usuario_id === currentUser.usuario_id`.
- [ ] Ocultar o deshabilitar si usuario eliminado (no debería aparecer en listado activo).

### Flujo de éxito

- [ ] Diálogo de confirmación antes del POST.
- [ ] Modal post-éxito con usuario + contraseña temporal.
- [ ] Botón copiar al portapapeles.
- [ ] Advertencia de entrega única visible.
- [ ] Cerrar modal limpia estado en memoria (sin dejar rastro).
- [ ] Opcional: mostrar `sesiones_revocadas` como información.

### Manejo de errores

- [ ] Parser basado en `HTTP status` + `detail` (no depender de `error_code` salvo 422).
- [ ] 404 → refrescar datos del usuario / volver al listado.
- [ ] 400 SSO → mensaje específico IdP.
- [ ] 400 auto-reset → enlace a cambio de contraseña propio.
- [ ] 403 → mensaje permisos insuficientes.

### Usuario inactivo

- [ ] Si `es_activo === false`, tras reset exitoso advertir reactivación previa al login.

### Integración Auth (usuario afectado — fuera de esta pantalla)

- [ ] Tras login con temporal: detectar `requires_password_change === true`.
- [ ] Redirigir a pantalla Force Password Change existente.
- [ ] Usar `POST /api/v1/auth/password/change/` — contrato en `AUTH_FRONTEND_CONTRACT_CERTIFICATION.md`.
- [ ] Interceptor `PASSWORD_CHANGE_REQUIRED` ya implementado debe seguir aplicando.

### Seguridad

- [ ] No loguear response ni contraseña.
- [ ] No persistir en storage.
- [ ] Deshabilitar autocompletado en campos que muestren la temporal.

---

## 10. Riesgos (Frontend)

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RF1 | Admin cierra modal sin copiar contraseña | Alta | Alta | Confirmación de cierre; texto de advertencia; botón copiar prominente |
| RF2 | Persistencia accidental en storage global | Media | Alta | Estado local de modal; wipe al unmount |
| RF3 | `error_code` ausente en 400/404/403 | Alta | Baja | Clasificar por status + `detail` |
| RF4 | Permiso no asignado en tenant legacy (403) | Media | Media | Gate por permisos en UI; mensaje claro |
| RF5 | Reset a usuario inactivo sin reactivar | Media | Media | Advertencia explícita post-reset |
| RF6 | Confundir reset admin con «olvidé mi contraseña» | Media | Media | Copy/UI distintos; autoservicio no implementado |
| RF7 | Mostrar reset en usuario SSO | Baja | Media | Gate por `proveedor_autenticacion` |

---

## 11. Dictamen final

## **B) Certificado con observaciones**

El endpoint `POST /api/v1/usuarios/{usuario_id}/reset-password/` está **implementado, documentado en OpenAPI y listo para consumo Frontend**, con contrato de respuesta `200` estable y alineado a las especificaciones aprobadas.

Las observaciones **O1** (errores sin `error_code` uniforme) y **O2** (permiso en tenants legacy) no impiden la implementación; deben incorporarse al diseño de manejo de errores y visibilidad de la acción.

El flujo del usuario afectado post-reset debe implementarse reutilizando el contrato Auth ya certificado (Force Password Change).

---

*Documento generado en modo READ ONLY. Única fuente de verdad Frontend para Reset Administrativo de Contraseña.*
