# Revisión de riesgos

**Paquete:** `cfg-backend-final-review`  
**Fecha:** 2026-07-17

---

## 1. Riesgos que el blueprint ya mitiga bien

| Riesgo | Mitigación presente |
|--------|---------------------|
| Dedicated write a Control Plane | Session obligatoria / no Path A |
| Mutar contador desde admin | Prohibido + forbid schema |
| Bypass Motor en preview | Solo Gateway.preview |
| Cross-tenant | cliente_id + 404 |
| Editar org_empresa | Lock 422 |
| Expandir MVP a align | Excluido explícitamente |

---

## 2. Riesgos abiertos (pre-ajuste)

| ID | Riesgo | Impacto | Mitigado por |
|----|--------|---------|--------------|
| R-A | Divergencia soft-delete vs ORG/FE patterns | FE confuso; deuda permanente | **G-01** |
| R-B | False positive colisión formato | Bloqueo ops legítimas | **G-02** |
| R-C | Regla numero_inicial ambigua → bugs/tests frágiles | Retrabajo | **G-03** |
| R-D | `page` + filtro `modulo_codigo` → totales incorrectos | Bug contrato paginación | **G-04** |
| R-E | Implementador bloquea preview inactiva por texto ambiguo | UX rota vs diseño funcional | **G-05** |
| R-F | Doble path escritura (queries + Repo extendido) | Drift onboarding vs admin | **G-06** |

---

## 3. Riesgos de mantenimiento

| Riesgo | Comentario |
|--------|------------|
| Tres archivos helper + servicio | Más imports/tests de los necesarios (O-01) |
| Enrich Read muy ancho | Acopla FE a muchos campos Catalog; aceptable admin, vigilar evolución |
| Filtro modulo in-memory | Documentar límite ~100–200 filas; si crece, rediseñar |

---

## 4. Escalabilidad futura

| Capacidad | ¿El MVP la dificulta? |
|-----------|------------------------|
| Align v1.1 | No — endpoint nuevo limpio |
| Diagnóstico | No |
| Historial audit | No — columnas audit basales bastan |
| Fiscal admin | No — fuera de cfg store |
| Multi-empresa filtros | OK con `empresa_id` query |

Ningún ajuste obligatorio bloquea el roadmap post-MVP.

---

## 5. Riesgos si se implementa **sin** G-01..G-06

1. OpenAPI nace divergente de STANDARDS § soft-delete.  
2. Tests de colisión/numero_inicial discuten semántica indefinida.  
3. Bug sutil de paginación con `modulo_codigo`.  
4. Posible 409 espurio en preview de secuencias inactivas.  
5. Extensión Repo innecesaria aumenta superficie ADJ-03.

**Conclusión de riesgo:** los ajustes son baratos ahora y caros después → **obligatorios antes de código**.
