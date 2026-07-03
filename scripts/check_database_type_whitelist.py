#!/usr/bin/env python3
"""
F3-WP04 / PR-F3-04 — database_type whitelist grep gate (G-10 / G-F3 / DOD-F3-04).

Escanea ``app/**/*.py`` buscando el literal ``database_type``. Permitido solo en:
- Whitelist infra G-10 (+ middleware/context F3)
- Baseline congelada de deuda L5 AS-IS (post F3-WP01–03)
- Archivos F3 mandatory-clean deben tener **cero** ocurrencias

Uso:
    python scripts/check_database_type_whitelist.py
    python scripts/check_database_type_whitelist.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
PATTERN = "database_type"

# G-10 infra whitelist (DOD-F3-05) — paths relative to repo root, POSIX slashes
G10_INFRA_WHITELIST: frozenset[str] = frozenset(
    {
        "app/infrastructure/database/connection_async.py",
        "app/core/tenant/routing.py",
        "app/infrastructure/database/queries_async.py",
        "app/infrastructure/database/query_helpers.py",
        "app/core/tenant/cache.py",
        "app/core/tenant/middleware.py",
        "app/core/tenant/context.py",
    }
)

# F3-WP02/WP03 — must remain clean (zero database_type)
F3_MANDATORY_CLEAN: frozenset[str] = frozenset(
    {
        "app/core/auth/user_context.py",
        "app/modules/rbac/application/services/rol_service.py",
    }
)

# AS-IS L5 debt frozen at F3-04 — no new files may appear here without ADR
KNOWN_L5_DEBT_BASELINE: frozenset[str] = frozenset(
    {
        "app/api/deps.py",
        "app/core/auth/impersonation_rbac.py",
        "app/core/auth/user_builder.py",
        "app/core/authorization/menu_resolver.py",
        "app/core/authorization/permission_resolver.py",
        "app/core/tenant/__init__.py",
        "app/core/tenant/empresa_preference.py",
        "app/infrastructure/database/queries.py",
        "app/modules/auth/application/services/auth_service.py",
        "app/modules/auth/application/services/refresh_token_cleanup_job.py",
        "app/modules/auth/presentation/endpoints.py",
        "app/modules/rbac/application/services/permisos_negocio_service.py",
        "app/modules/rbac/application/services/permisos_usuario_service.py",
        "app/modules/superadmin/application/services/audit_service.py",
        "app/modules/superadmin/application/services/superadmin_usuario_service.py",
        "app/modules/users/application/services/user_service.py",
    }
)

SELFTEST_REL_PATH = "app/_hybrid_f3_gate_selftest_violation.py"
SELFTEST_SNIPPET = 'database_type = "forbidden_l5"\n'


def _posix_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _iter_app_python_files() -> Iterable[Path]:
    if not APP_ROOT.is_dir():
        return
    yield from APP_ROOT.rglob("*.py")


def _scan_file(path: Path) -> List[Tuple[int, str]]:
    hits: List[Tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        hits.append((0, f"<read error: {exc}>"))
        return hits
    for line_no, line in enumerate(text.splitlines(), start=1):
        if PATTERN in line:
            hits.append((line_no, line.strip()))
    return hits


def run_check() -> Tuple[int, List[str]]:
    """Return (exit_code, messages). exit_code 0 = pass."""
    violations: Dict[str, List[Tuple[int, str]]] = {}
    mandatory_failures: List[str] = []
    debt_reports: List[str] = []

    for py_file in _iter_app_python_files():
        rel = _posix_rel(py_file)
        hits = _scan_file(py_file)
        if not hits:
            continue

        if rel in F3_MANDATORY_CLEAN:
            mandatory_failures.append(
                f"{rel}: {len(hits)} occurrence(s) — F3 mandatory-clean requires zero"
            )
            continue

        if rel in G10_INFRA_WHITELIST:
            continue

        if rel in KNOWN_L5_DEBT_BASELINE:
            debt_reports.append(f"{rel}: {len(hits)} occurrence(s) (frozen L5 debt)")
            continue

        violations[rel] = hits

    messages: List[str] = []
    if mandatory_failures:
        messages.append("F3 mandatory-clean violations:")
        messages.extend(f"  - {item}" for item in mandatory_failures)

    if violations:
        messages.append("database_type outside G-10 whitelist / known L5 debt baseline:")
        for rel, hits in sorted(violations.items()):
            for line_no, snippet in hits[:3]:
                messages.append(f"  - {rel}:{line_no}: {snippet[:120]}")
            if len(hits) > 3:
                messages.append(f"  - {rel}: ... +{len(hits) - 3} more")

    if debt_reports:
        messages.append(
            f"Known L5 debt baseline: {len(debt_reports)} file(s) "
            f"({sum(1 for _ in debt_reports)} logged)"
        )
        for item in debt_reports:
            messages.append(f"  · {item}")

    if mandatory_failures or violations:
        messages.insert(
            0,
            "FAIL — database_type whitelist gate (PR-F3-04 / G-F3)",
        )
        return 1, messages

    messages.append(
        "PASS — database_type whitelist gate "
        f"(infra whitelist={len(G10_INFRA_WHITELIST)}, "
        f"known L5 debt={len(debt_reports)} file(s))"
    )
    return 0, messages


def run_self_test() -> int:
    """Inject violation file; gate must fail; then restore."""
    code, messages = run_check()
    if code != 0:
        print("SELF-TEST setup failed: baseline check must pass first")
        for line in messages:
            print(line)
        return 1

    violation_path = ROOT / SELFTEST_REL_PATH
    violation_path.write_text(SELFTEST_SNIPPET, encoding="utf-8")
    try:
        fail_code, fail_messages = run_check()
        if fail_code == 0:
            print("SELF-TEST FAIL: injected violation did not trigger gate failure")
            return 1
        if SELFTEST_REL_PATH not in "\n".join(fail_messages):
            print("SELF-TEST FAIL: expected injected path in violation report")
            for line in fail_messages:
                print(line)
            return 1
        print("SELF-TEST PASS: gate correctly fails on injected L5 violation")
        return 0
    finally:
        if violation_path.is_file():
            violation_path.unlink()


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G-F3 database_type whitelist grep gate")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Verify gate fails on an intentional injected violation",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    code, messages = run_check()
    for line in messages:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
