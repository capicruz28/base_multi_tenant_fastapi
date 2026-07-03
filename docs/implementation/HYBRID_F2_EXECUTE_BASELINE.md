# Hybrid Platform — execute_* Baseline (F2-WP01 / PR-F2-01)

- **Timestamp (UTC):** 2026-06-25T23:52:25.867483+00:00
- **Gate target:** G-F2
- **p95 regression threshold:** ±10%
- **Methodology:** 10 warmup + 100 measured iterations (mocked I/O)

## Scenarios

| Scenario | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |
|----------|----------|----------|----------|-----------|
| execute_query_shared_cold_la | 4.104 | 5.523 | 9.3012 | 4.6495 |
| execute_query_shared_warm_la | 4.4509 | 6.4632 | 7.9601 | 4.9801 |
| execute_query_admin_control_plane | 6.6648 | 8.691 | 9.3983 | 7.1794 |
| get_connection_metadata_lb_hit | 0.011 | 0.0114 | 0.0119 | 0.0111 |
| get_connection_metadata_cold_path | 0.1652 | 0.3043 | 0.3876 | 0.1909 |
| prepare_core_query_gateway | 2.2447 | 3.0979 | 3.6673 | 2.4141 |

## Usage

Compare future runs against this baseline; **pass** if each scenario p95 remains within ±10% (GF2-03 / DOD-F2-02).

Regenerate:

```bash
python scripts/benchmark_execute_baseline.py
```
