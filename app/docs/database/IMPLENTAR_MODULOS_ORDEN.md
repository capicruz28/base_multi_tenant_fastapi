Orden recomendado por capas de dependencia
CAPA 1 — Base absoluta (sin dependencias)

ORG — Todo el sistema depende de org_empresa, org_sucursal, org_centro_costo

CAPA 2 — Maestros de datos (dependen solo de ORG)
2. INV — inv_producto, inv_almacen, inv_unidad_medida son referenciados por casi todos los módulos
3. PRC — Precios dependen de productos, sin lógica transaccional pesada
4. TAX — Configuración tributaria, referenciada por FIN, PUR, SLS
CAPA 3 — Módulos operativos independientes
5. PUR — Depende de ORG + INV. Es el más usado como referencia por MRP, MFG, CST
6. SLS — Depende de ORG + INV + PRC. Paralelo a PUR
7. CRM — Depende de ORG + SLS (clientes/prospectos)
8. WMS — Depende de INV (almacenes y stock)
9. QMS — Depende de INV + PUR (inspecciones de recepción)
CAPA 4 — Módulos de producción (dependen de INV + PUR)
10. MRP — Depende de INV + PUR + MPS
11. MPS — Depende de INV + SLS
12. MFG — Depende de INV + MRP + MPS + WMS
CAPA 5 — Módulos de soporte operativo
13. LOG — Depende de INV + PUR + SLS
14. MNT — Depende de ORG + INV (activos)
15. HCM — Depende de ORG (cargos, departamentos)
16. POS — Depende de SLS + INV + PRC
CAPA 6 — Módulos financieros (dependen de todo lo anterior)
17. FIN — Depende de ORG + PUR + SLS + HCM
18. BDG — Depende de FIN + ORG
19. CST — Depende de INV + MFG + FIN
20. INV_BILL — Depende de SLS + FIN + TAX
CAPA 7 — Módulos de gestión y soporte
21. PM — Depende de ORG + HCM
22. SVC — Depende de CRM + INV
23. TKT — Depende de ORG (independiente funcionalmente)
CAPA 8 — Infraestructura transversal (van al final)
24. DMS — Puede implementarse en cualquier momento, no bloquea nada
25. WFL — Depende de que los módulos que usa existan
26. BI — Va último, consume datos de todos
27. AUD — Va último, es logging puro