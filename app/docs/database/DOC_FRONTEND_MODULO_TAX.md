# Documentación Frontend — Módulo TAX (Libros Electrónicos / PLE SUNAT)

**Versión:** 1.0  
**Fecha:** 2026-02-18  
**Módulo:** TAX - Libros Electrónicos

---

## Índice

1. [Información General](#información-general)
2. [Autenticación](#autenticación)
3. [Endpoints](#endpoints)
4. [Schemas TypeScript](#schemas-typescript)
5. [Códigos de Error](#códigos-de-error)
6. [Rutas SPA Recomendadas](#rutas-spa-recomendadas)
7. [Flujo de Implementación Recomendado](#flujo-de-implementación-recomendado)
8. [Notas Importantes](#notas-importantes)

---

## Información General

### Base URL

```
/api/v1/tax
```

### Dependencias

- **Módulo ORG:** Empresa (obligatorio).
- **Módulo FIN:** Periodo contable (obligatorio; vincular libro a un periodo ya creado).
- **Orden recomendado:** Configurar ORG y FIN (periodos contables); luego generar y registrar libros electrónicos (PLE).

---

## Autenticación

Todos los endpoints requieren JWT en el header:

```http
Authorization: Bearer <token>
```

El `cliente_id` se obtiene del token; **no enviar en el body**.

---

## Endpoints

### 1. Libros Electrónicos (PLE)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/v1/tax/libros-electronicos | Listar (empresa_id, tipo_libro, anio, mes, estado) |
| GET | /api/v1/tax/libros-electronicos/{libro_id} | Detalle |
| POST | /api/v1/tax/libros-electronicos | Crear registro de libro (generado) |
| PUT | /api/v1/tax/libros-electronicos/{libro_id} | Actualizar (archivo, estado, respuesta SUNAT) |

**Campos principales en creación:** empresa_id, tipo_libro (ventas, compras, diario, mayor, inventarios), periodo_id (UUID del periodo contable FIN), **anio** (número, ej. 2025), mes (1-12), nombre_archivo, ruta_archivo, estado (generado, enviado, aceptado, rechazado), total_registros, observaciones, generado_por_usuario_id.

**En actualización:** nombre_archivo, ruta_archivo, estado, fecha_envio_sunat, codigo_respuesta_sunat, total_registros, observaciones (por ejemplo tras generar el TXT o recibir respuesta de SUNAT).

---

## Schemas TypeScript

### Libro Electrónico

```typescript
interface LibroElectronicoCreate {
  empresa_id: string;
  tipo_libro: 'ventas' | 'compras' | 'diario' | 'mayor' | 'inventarios';
  periodo_id: string;   // UUID de fin_periodo_contable
  anio: number;         // En API se usa "anio" (sin ñ), ej. 2025
  mes: number;         // 1-12
  nombre_archivo?: string;
  ruta_archivo?: string;
  estado?: 'generado' | 'enviado' | 'aceptado' | 'rechazado';
  fecha_envio_sunat?: string;
  codigo_respuesta_sunat?: string;
  total_registros?: number;
  observaciones?: string;
  generado_por_usuario_id?: string;
}

interface LibroElectronicoUpdate {
  nombre_archivo?: string;
  ruta_archivo?: string;
  estado?: string;
  fecha_envio_sunat?: string;
  codigo_respuesta_sunat?: string;
  total_registros?: number;
  observaciones?: string;
}

interface LibroElectronicoRead extends LibroElectronicoCreate {
  libro_id: string;
  cliente_id: string;
  fecha_generacion: string;
  fecha_creacion: string;
}
```

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 401 | No autenticado |
| 403 | Sin permisos |
| 404 | Libro electrónico no encontrado |
| 422 | Error de validación (body o query) |
| 500 | Error interno |

---

## Rutas SPA Recomendadas

```
/tax
  /ple-sunat
    /list          # Lista de libros (filtros: empresa, tipo, año, mes, estado)
    /create        # Crear registro de libro (tras generar TXT)
    /:libro_id     # Detalle y edición (actualizar estado, archivo, respuesta SUNAT)
```

---

## Flujo de Implementación Recomendado

### 1. Configuración previa

- Tener ORG (empresa) y FIN con periodos contables creados (año/mes). El libro se asocia a un periodo_id.

### 2. Generar y registrar libro

- Tras generar el archivo PLE (TXT) en el flujo de negocio: POST /tax/libros-electronicos (empresa_id, tipo_libro, periodo_id, anio, mes, nombre_archivo, ruta_archivo, estado: "generado", total_registros, generado_por_usuario_id).
- Listar por empresa_id, tipo_libro, anio, mes para la pantalla “PLE SUNAT”.

### 3. Actualizar tras envío a SUNAT

- Al enviar a SUNAT: PUT /tax/libros-electronicos/{libro_id} (estado: "enviado", fecha_envio_sunat).
- Al recibir respuesta: PUT (estado: "aceptado" o "rechazado", codigo_respuesta_sunat).

---

## Notas Importantes

1. **Multi-tenancy:** Todo se filtra por `cliente_id` del token. No enviar `cliente_id` en el body.

2. **Campo año:** En la API se usa **anio** (sin ñ) en JSON. Enviar y leer como número (ej. 2025). En base de datos la columna es `año`; el backend realiza la conversión.

3. **periodo_id:** Debe ser un UUID válido de `fin_periodo_contable`. Obtener periodos desde el módulo FIN (GET /fin/periodos-contables o equivalente) para el combo de selección.

4. **Estados del libro:** generado → enviado → aceptado | rechazado. Ajustar flujo en frontend según el proceso de envío a SUNAT.

5. **IDs en URLs:** libro_id es UUID.

6. **Pantalla PLE SUNAT:** Menú “PLE SUNAT” puede mostrar la lista de libros con filtros (empresa, tipo, año, mes, estado) y acciones: ver detalle, subir/descargar archivo (si se implementa en otro servicio), actualizar estado tras envío.

---

**Fin de la documentación del módulo TAX**
