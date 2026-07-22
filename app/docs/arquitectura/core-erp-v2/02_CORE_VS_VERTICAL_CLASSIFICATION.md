# Clasificación Core vs Vertical

**Documento:** 02  
**Serie:** CORE ERP V2 — Auditoría arquitectónica oficial

---

## Regla principal

> Si una capacidad es utilizada por la **mayoría de industrias manufactureras** → pertenece al **Core**.  
> Si representa **conocimiento específico** de una industria → pertenece al **Vertical**.

Industrias de referencia (no exhaustivo): Textil, Alimentos, Metalmecánica, Distribución, Servicios, Farmacéutica, Agroindustria, Construcción, Minería, Automotriz.

---

## 1. Capacidades clasificadas como CORE

| Capacidad | Por qué es Core |
|-----------|-----------------|
| MultiTenant + MultiEmpresa + auditoría + soft delete | Plataforma SaaS transversal |
| Maestro de producto, UoM, categoría, almacén, stock, movimientos | Toda industria con inventario |
| **Lote / partida** como entidad formal | Trazabilidad en manufactura, alimentos, farma, metal, agro, distribución |
| Series / vencimiento (flags + fechas) | Amplio en industrial y regulado |
| **Variantes de producto** por ejes genéricos (atributo_1..N) | Retail + manufactura multi-SKU (color/talla/voltaje/envase) |
| Estrategia de salida FIFO/FEFO/LEFO/MANUAL | Inventario real multi-rubro |
| WMS ubicaciones + tareas + **oleadas** | Operación de almacén industrial |
| QMS inspección / NC con vínculo a lote | Calidad transversal manufactura |
| MFG: CT, BOM, ruta, OP, consumo | Manufactura discreta/proceso genérica |
| **MES**: ejecución de operación + paradas + motivos OEE | Shop-floor transversal |
| **PLN**: calendario de capacidad por CT/fecha | CRP básico en casi toda planta |
| MRP / MPS (esqueleto) | Planeamiento materiales/producción genérico |
| Compras, ventas, logística básica, facturación | Ciclos comerciales universales |
| Event Bus interno + alertas (ALR como consumidor) | Integración asíncrona entre módulos |
| Control-plane de verticales habilitadas por empresa | Gobernanza multi-vertical sin hardcode |

---

## 2. Capacidades clasificadas como VERTICAL

| Capacidad | Vertical típico | Por qué no es Core |
|-----------|-----------------|--------------------|
| Galgas, partidas de tela, rollos, mermas de corte | TXT | Semántica textil |
| Lotes con temperatura de cadena de frío / HACCP checklists | FOD | Semántica alimentos |
| Coladas, aleaciones, tratamientos térmicos tipados | MET | Semántica metal |
| NDC, lotes regulatorios FDA/DIGEMID tipados | FAR | Semántica farma |
| Recetas de proceso continuo específicas | FOD/AGR | Proceso de industria |
| Matrices de talla/color predefinidas como catálogo fijo | TXT/Retail fashion | Catálogo de industria |
| `configuracion_json` con claves de rubro en CFG | cualquiera | Contamina control-plane |
| `atributo_N_referencia_id` → catálogos TXT/FOD | cualquiera | Acopla Core a Vertical |

**Patrón correcto:** el Vertical **extiende** Core (tablas `txt_*`, `fod_*`, …) y/o usa `atributos_*` JSON **opacos** cuando el atributo es altamente variable y no participa en integridad/transacciones Core.

---

## 3. Capacidades PREMATURAS (arquitectura sí, físico no)

| Capacidad | Motivo de diferir |
|-----------|-------------------|
| APS (escenarios, Gantt, restricciones, impacto) | Requiere MES + PLN + MRP estables y un motor de scheduling; tablas ahora serían huérfanas |
| RPT capa semántica autoservicio | Alto riesgo (SQL dinámico); BI V010 ya es placeholder; primero contratos |
| WMS slotting / putaway optimizer / yard | Enterprise WMS avanzado; oleada es el mínimo viable |
| QMS SPC / CAPA formal completo | Tras trazabilidad lote + inspección ligada |
| Costeo por capas FIFO real | Tras lote + movimientos lotificados |

---

## 4. Deuda Core real (no es Vertical, pero no es foco inmediato de esta ola industrial)

Estas capacidades **pertenecen al Core** a largo plazo, pero no están en el centro de las propuestas A/B y pueden fasearse aparte:

- FIN: CxC, CxP, bancos, conciliación
- TAX: obligaciones más allá de metadata PLE
- CST: motor de costeo (no solo snapshot)
- WFL: runtime de instancias (hoy JSON de definición)
- MNT: repuestos formales (hoy JSON)

Documentar como deuda; no confundir con “descartar”.

---

## 5. Matriz de decisión rápida (para futuros PRs de esquema)

```
¿La usan ≥ ~60% de verticales manufactureras/distribución?
  NO → Vertical o feature opcional de Vertical
  SÍ → ¿Tiene semántica de un rubro en nombres/campos/CHECKs?
         SÍ → Rediseñar como genérico o mover a Vertical
         NO → ¿Requiere motor avanzado aún inexistente?
                SÍ → ADR + extensión; diferir tablas
                NO → Candidata Core V2
```

---

## 6. Aplicación a propuestas A/B (síntesis)

| Capacidad A/B | Clasificación | Acción |
|---------------|---------------|--------|
| `cfg_vertical_empresa` (A limpio) | Core | Adoptar |
| `cfg_vertical` + JSON rubro (B) | Contaminación | Descartar JSON |
| `inv_lote` | Core | Adoptar (mejorar con B) |
| `inv_producto_variante` | Core | Adoptar híbrido |
| WMS oleada + estrategia | Core | Adoptar |
| QMS `lote_id` | Core | Adoptar |
| MES + motivos OEE | Core | Adoptar |
| `mfg_calendario_capacidad` | Core (módulo PLN) | Adoptar |
| APS tablas | Prematura | Diferir físico |
| ALR | Core (sobre Event Bus) | Adoptar rediseñado |
| RPT métrica/dimensión | Prematura | Diferir físico |
