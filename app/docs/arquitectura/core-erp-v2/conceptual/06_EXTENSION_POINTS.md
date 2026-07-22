# Puntos de Extensión para Verticales

**Documento:** Etapa 0.5 · 06  
**Serie:** CORE ERP V2 — Modelo Conceptual  
**Estado:** Definitivo (congelado)  
**Alcance:** Guía oficial para TXT, FOD, MET, MED, AGR, DIS, SRV, CON, …  
**Sin tablas ni SQL**

---

## 1. Propósito

Este documento es el **contrato de extensión** entre el Core y los Verticales industriales.

Congela cómo un Vertical:

- reutiliza el Core,
- añade conocimiento de industria,
- consume eventos,
- y **nunca** contamina el Core.

Audiencia: arquitectos e implementadores de verticales durante los próximos 10–15 años.

---

## 2. Principio rector (congelado)

> El Core contiene **capacidades**.  
> El Vertical contiene **conocimiento de negocio de industria**.

El Vertical **extiende**; no redefine Aggregates Roots del Core.

---

## 3. Qué puede hacer un Vertical

### 3.1 Extensiones permitidas

| Tipo de extensión | Descripción |
|-------------------|-------------|
| **Entidades propias** | Modelos exclusivos del rubro (ej. rollo textil, receta HACCP tipada, colada, registro sanitario) en su propio Bounded Context |
| **Atributos opacos** | Datos altamente variables colgados de Aggregates Core vía extensión aprobada (atributos no transaccionales) |
| **Procesos propios** | Flujos de industria que orquestan Aggregates Core sin mutarlos ilegalmente |
| **UI / menú vertical** | Pantallas y navegación visibles solo si la vertical está activa en la Empresa |
| **Reglas de alerta propias** | Reglas ALR suscritas a eventos Core o eventos del Vertical |
| **Consumo de eventos Core** | Reaccionar a `LoteCreado`, `RecepcionRegistrada`, `OrdenProduccionLiberada`, etc. |
| **Emisión de eventos propios** | Eventos con prefijo de vertical y semántica propia |
| **Reportes de industria** | Informes sobre datos propios + lectura de Core |
| **Servicios anti-corrupción** | Capas que traducen lenguaje de industria ↔ lenguaje ubicuo Core |

### 3.2 Activación

Un Vertical solo opera para una Empresa si existe **VerticalEmpresa** activa (`CFG`) para ese código de vertical.

Sin activación: sin menú, sin APIs de vertical, sin jobs de vertical.

---

## 4. Qué nunca puede hacer un Vertical

| Prohibición | Motivo |
|-------------|--------|
| Redefinir Producto, Lote, Pedido, OP, Movimiento, etc. como “otra cosa” | Rompe el Core multi-vertical |
| Crear FK desde tablas/contratos Core hacia catálogos del Vertical | Acopla el Core a una industria |
| Meter semántica de rubro en CFG Core (JSON de galgas, HACCP, NDC…) | Contamina control-plane |
| Renombrar términos Core en APIs Core (“Partida” reemplazando Lote) | Rompe lenguaje ubicuo |
| Escribir Stock/Lote/OP directamente sin pasar por BC dueño | Viola Aggregates |
| Sustituir BOM Core por “receta vertical” como única verdad para todos | BOM Core debe permanecer genérico |
| Usar el Event Bus como dump de PII/secretos o payloads no versionados | Seguridad y evolución |
| Implementar APS “disfrazado” dentro del Vertical como si fuera Core | APS es dominio futuro de plataforma |
| Duplicar maestros Core (segundo producto, segundo lote) como verdad paralela | Doble verdad |

---

## 5. Entidades Core de reutilización obligatoria

Todo Vertical que opere sobre estos conceptos **debe reutilizar** los Aggregates Core (no crear equivalentes):

| Concepto de industria (ejemplos) | Debe reutilizar |
|----------------------------------|-----------------|
| Artículo / SKU / ítem | **Producto** (+ **Variante** si aplica) |
| Partida / batch / colada / lote proveedor | **Lote** |
| Número de serie / IMEI / matrícula unitaria | **Serie** |
| Depósito / warehouse | **Almacén** (+ WMS si hay ubicaciones) |
| OC / PO | **OrdenCompra** / **Recepcion** |
| Sales order | **PedidoVenta** |
| Work order / manufacturing order | **OrdenProduccion** |
| Shop-floor run | **EjecucionOperacion** |
| QA check | **Inspeccion** / **NoConformidad** |
| Company / plant org | **Empresa** / estructura **ORG** |

El Vertical puede **etiquetar o extender** estos aggregates; no reemplazarlos.

---

## 6. Patrones oficiales de interacción

### 6.1 Lectura de Core

```
Vertical ──lee──► APIs/servicios del BC dueño (Producto, Lote, OP, …)
```

Lectura permitida de identidades y datos publicados.  
Prohibido acceder a persistencia interna de otro BC saltándose su API.

### 6.2 Escritura sobre Core

```
Vertical ──orquesta──► servicios de aplicación del BC dueño
         (ej. “crear recepción”, “liberar OP”, “solicitar cuarentena de lote”)
```

El Vertical **nunca** abre una transacción que escriba el modelo interno ajeno por la espalda.

### 6.3 Extensión de datos (conceptual)

Dos mecanismos legítimos:

1. **Aggregate de extensión del Vertical** con referencia al `aggregate_id` Core (1:1 o 1:N).  
   Ejemplo conceptual: `TxtDatosRollo` referencia `lote_id` Core.
2. **Atributos opacos** en el Core solo cuando:
   - no participan en invariantes/transacciones Core, y
   - no contienen semántica que deba ser queryable/validable por el Core.

Si el dato es regla de negocio del Core (estado, cantidad, FK, vencimiento operativo), **no** va en JSON opaco.

### 6.4 Eventos

```
Core BC ──Domain Event──► EVT ──► Vertical (consumidor)
Vertical ──Domain Event propio──► EVT ──► ALR / otros Verticales / proyecciones
```

Reglas:

- Consumir eventos Core del catálogo oficial (`04_DOMAIN_EVENTS.md`).
- Emitir eventos propios con prefijo (`Txt…`, `Fod…`, `Met…`, `Med…`, …).
- No redefinir el significado de un evento Core.
- Idempotencia obligatoria en consumidores.
- El Vertical puede registrar reglas ALR sobre eventos Core o propios.

### 6.5 UI y menú

- Menú Core: capacidades agnósticas.
- Menú Vertical: visible solo con vertical activa.
- Prohibido hardcodear rubro en menú Core.

---

## 7. Guía por vertical (ejemplos de frontera)

Estos ejemplos **no** diseñan el vertical; ilustran la frontera.

| Vertical | Extiende con (ejemplos) | Reutiliza obligatoriamente |
|----------|-------------------------|----------------------------|
| **TXT** | Galgas, rollos, mermas de corte, matrices fashion | Producto, Variante, Lote, OP, Movimiento |
| **FOD** | HACCP tipado, cadena de frío tipada, alérgenos tipados | Lote (FEFO), Inspeccion, Almacen |
| **MET** | Coladas, aleaciones, tratamientos tipados | Lote, OP, Ejecucion, QMS |
| **MED** | NDC/registros sanitarios tipados, recall regulatorio tipado | Lote, Serie, QMS, BILL |
| **AGR** | Campañas agrícolas tipadas, lotes de cosecha tipados | Lote, Producto, LOG |
| **DIS** | Políticas de distribución multi-depósito tipadas | WMS, LOG, Pedido, Stock |
| **SRV** | Contratos de servicio tipados, SLA tipados | Cliente, SVC (evolución), HCM |
| **CON** | Frentes de obra tipados, valorizaciones tipadas | Proyecto (evolución), CST, INV |

---

## 8. Checklist de aceptación de un Vertical

Un Vertical está bien formado si:

1. Tiene código de vertical registrado y activable por Empresa.
2. No introduce semántica de industria en CFG/ORG Core.
3. Reutiliza Aggregates Core listados en §5.
4. Sus escrituras a Core pasan por BC dueños.
5. Consume eventos Core sin romper contratos.
6. Emite eventos propios namespaced.
7. Usa lenguaje ubicuo Core en integraciones; traduce sinónimos solo en UI/vertical.
8. No crea “Lote2” / “Producto2” paralelos.
9. No depende de tablas APS inexistentes.
10. Puede desactivarse sin corromper datos Core.

---

## 9. Gobernanza de cambios

| Cambio | Quién aprueba |
|--------|---------------|
| Nuevo evento Core | ADR de catálogo de eventos |
| Nueva extensión de Aggregate Core | ADR Core (no decisión unilateral del Vertical) |
| Nuevo Vertical | ADR de producto + registro en CFG de códigos |
| Atributo que afecta invariantes Core | Debe promoverse a modelo Core tipado, no JSON |

---

## 10. Relación con fases posteriores

| Fase | Uso de este documento |
|------|------------------------|
| Diseño físico D1+ | Las FKs/extension tables deben respetar §4–§6 |
| Implementación Vertical | Checklist §8 es Definition of Done |
| Code review | Rechazar PRs que violen prohibiciones §4 |

---

## 11. Criterio de cierre

Los puntos de extensión quedan cerrados cuando un equipo puede construir TXT/FOD/MET/… sin preguntar “¿esto va en Core?” — la respuesta está aquí y en el lenguaje ubicuo.

**Estado:** cerrado.
