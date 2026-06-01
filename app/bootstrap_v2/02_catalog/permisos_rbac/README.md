# permisos_rbac — Orden S040–S067

Ejecutar después de `S030__seed_permisos_core.sql` y antes de `03_runtime/`.

| Orden | Archivo | Módulo |
|------:|---------|--------|
| 40 | `S040__permisos_rbac_org.sql` | ORG |
| 41 | `S041__permisos_rbac_inv-fase4.sql` | INV |
| 42 | `S042__permisos_rbac_inv-lifecycle.sql` | INV |
| 43 | `S043__permisos_rbac_wms.sql` | WMS |
| 44 | `S044__permisos_rbac_qms.sql` | QMS |
| 45 | `S045__permisos_rbac_pur.sql` | PUR |
| 46 | `S046__permisos_rbac_log.sql` | LOG |
| 47 | `S047__permisos_rbac_mfg.sql` | MFG |
| 48 | `S048__permisos_rbac_mrp.sql` | MRP |
| 49 | `S049__permisos_rbac_mps.sql` | MPS |
| 50 | `S050__permisos_rbac_mnt.sql` | MNT |
| 51 | `S051__permisos_rbac_sls.sql` | SLS |
| 52 | `S052__permisos_rbac_crm.sql` | CRM |
| 53 | `S053__permisos_rbac_inv-bill.sql` | INV_BILL |
| 54 | `S054__permisos_rbac_pos.sql` | POS |
| 55 | `S055__permisos_rbac_hcm.sql` | HCM |
| 56 | `S056__permisos_rbac_fin.sql` | FIN |
| 57 | `S057__permisos_rbac_bdg.sql` | BDG |
| 58 | `S058__permisos_rbac_cst.sql` | CST |
| 59 | `S059__permisos_rbac_pm.sql` | PM |
| 60 | `S060__permisos_rbac_svc.sql` | SVC |
| 61 | `S061__permisos_rbac_tkt.sql` | TKT |
| 62 | `S062__permisos_rbac_bi.sql` | BI |
| 63 | `S063__permisos_rbac_dms.sql` | DMS |
| 64 | `S064__permisos_rbac_wfl.sql` | WFL |
| 65 | `S065__permisos_rbac_aud.sql` | AUD |
| 66 | `S066__permisos_rbac_fase4-candidatos.sql` | LOG/FIN extras |
| 67 | `S067__permisos_rbac__legacy_empty_stub.sql` | **SKIP** (legacy vacío) |

**Nota:** `SEED_PERMISOS_RBAC_PRC.sql` no existe en repo; módulo PRC solo tiene menú en `S010`.
