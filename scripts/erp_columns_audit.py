import os
import re
import json
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.infrastructure.database.tables_erp import tables_org
from sqlalchemy import String, Text, Numeric, Integer, BigInteger, Boolean, Date, DateTime, Time

SQL_PATH = os.path.join(
    BASE_DIR,
    "app",
    "docs",
    "database",
    "3.- TABLAS_BD_ERP_COMPLETO.sql",
)


def load_sql_lines() -> list[str]:
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_create_table_blocks(lines: list[str]) -> dict[str, list[str]]:
    tables: dict[str, list[str]] = {}
    current: str | None = None
    buffer: list[str] = []

    for line in lines:
        m = re.search(r"CREATE TABLE\s+([A-Za-z0-9_]+)\s*\(", line, re.IGNORECASE)
        if m:
            if current and buffer:
                tables[current] = buffer
            current = m.group(1)
            buffer = []
            continue
        if current:
            buffer.append(line)
            if line.strip().startswith(")"):
                # leave closing line in buffer; we'll stop when parsing columns
                continue

    if current and buffer:
        tables[current] = buffer

    return tables


def parse_sql_columns(raw_lines: list[str]) -> dict[str, dict]:
    cols: dict[str, dict] = {}
    for raw in raw_lines:
        line = raw.strip()
        if not line or line.startswith("--"):
            continue
        if line.upper().startswith("CONSTRAINT"):
            continue
        if line.startswith(")"):
            break

        if line.endswith(","):
            line = line[:-1]

        parts = line.split()
        if len(parts) < 2:
            continue

        col_name = parts[0]
        if col_name.upper() in {"CONSTRAINT", "PRIMARY"}:
            continue

        col_type = parts[1]
        rest = " ".join(parts[2:])
        urest = rest.upper()

        not_null = "NOT NULL" in urest
        null_explicit = " NULL" in urest and not not_null

        default_val = None
        m_def = re.search(r"DEFAULT\s+([^,]+)", rest, re.IGNORECASE)
        if m_def:
            default_val = m_def.group(1).strip()

        cols[col_name] = {
            "type_raw": col_type,
            "rest": rest,
            "not_null": not_null,
            "null_explicit": null_explicit,
            "default": default_val,
        }

    return cols


def normalize_sql_type(type_raw: str) -> dict:
    t = type_raw.strip().upper()
    base = t
    params = None
    m = re.match(r"([A-Z]+)\s*\(([^)]+)\)", t)
    if m:
        base = m.group(1)
        params = m.group(2)

    category = None
    length = None
    prec = None
    scale = None

    if base in {"NVARCHAR", "VARCHAR", "NCHAR", "CHAR"}:
        category = "string"
        if params and "MAX" not in params.upper():
            try:
                length = int(params.split(",")[0].strip())
            except ValueError:
                pass
    elif base in {"TEXT"}:
        category = "text"
    elif base in {"DECIMAL", "NUMERIC"}:
        category = "numeric"
        if params:
            ps = params.split(",")
            if len(ps) >= 1:
                try:
                    prec = int(ps[0].strip())
                except ValueError:
                    pass
            if len(ps) >= 2:
                try:
                    scale = int(ps[1].strip())
                except ValueError:
                    pass
    elif base in {"INT", "INTEGER", "BIGINT", "SMALLINT"}:
        category = "integer"
    elif base in {"UNIQUEIDENTIFIER"}:
        category = "uuid"
    elif base in {"BIT"}:
        category = "boolean"
    elif base in {"DATE"}:
        category = "date"
    elif base in {"DATETIME", "DATETIME2"}:
        category = "datetime"
    elif base in {"TIME"}:
        category = "time"
    else:
        category = base

    return {
        "base": base,
        "category": category,
        "length": length,
        "precision": prec,
        "scale": scale,
    }


def normalize_model_type(col) -> dict:
    t = col.type
    length = getattr(t, "length", None)
    prec = getattr(t, "precision", None)
    scale = getattr(t, "scale", None)
    base = type(t).__name__

    if isinstance(t, String):
        category = "string"
    elif isinstance(t, Text):
        category = "text"
    elif isinstance(t, Numeric):
        category = "numeric"
    elif isinstance(t, (Integer, BigInteger)):
        category = "integer"
    elif isinstance(t, Boolean):
        category = "boolean"
    elif isinstance(t, Date):
        category = "date"
    elif isinstance(t, DateTime):
        category = "datetime"
    elif isinstance(t, Time):
        category = "time"
    else:
        if base.upper() == "UNIQUEIDENTIFIER":
            category = "uuid"
        else:
            category = base

    return {
        "base": base,
        "category": category,
        "length": length,
        "precision": prec,
        "scale": scale,
    }


def collect_differences() -> list[dict]:
    lines = load_sql_lines()
    sql_blocks = extract_create_table_blocks(lines)
    sql_schema = {t: parse_sql_columns(buf) for t, buf in sql_blocks.items()}

    metadata_erp = tables_org.metadata_erp
    model_tables = dict(metadata_erp.tables)

    results: list[dict] = []

    common_tables = sorted(set(sql_schema.keys()) & set(model_tables.keys()))

    for tname in common_tables:
        sql_cols = sql_schema[tname]
        model_table = model_tables[tname]
        model_cols = {c.name: c for c in model_table.columns}
        issues: list[dict] = []

        for cname in sorted(sql_cols.keys()):
            if cname not in model_cols:
                issues.append(
                    {
                        "column": cname,
                        "kind": "missing_in_model",
                    }
                )

        for cname in sorted(model_cols.keys()):
            if cname not in sql_cols:
                issues.append(
                    {
                        "column": cname,
                        "kind": "extra_in_model",
                    }
                )

        for cname in sorted(set(sql_cols.keys()) & set(model_cols.keys())):
            s = sql_cols[cname]
            mcol = model_cols[cname]
            st = normalize_sql_type(s["type_raw"])
            mt = normalize_model_type(mcol)

            if st["category"] != mt["category"]:
                issues.append(
                    {
                        "column": cname,
                        "kind": "type_mismatch",
                        "sql_type": s["type_raw"],
                        "model_type": mt["base"],
                    }
                )
            else:
                if st["category"] == "string":
                    slen = st["length"]
                    mlen = mt["length"]
                    if (
                        slen is not None
                        and mlen is not None
                        and slen != mlen
                    ):
                        issues.append(
                            {
                                "column": cname,
                                "kind": "length_mismatch",
                                "sql": slen,
                                "model": mlen,
                                "sql_type": s["type_raw"],
                                "model_type": f"String({mlen})",
                            }
                        )
                if st["category"] == "numeric":
                    sp, ss = st["precision"], st["scale"]
                    mp, ms = mt["precision"], mt["scale"]
                    if (sp is not None and mp is not None and sp != mp) or (
                        ss is not None and ms is not None and ss != ms
                    ):
                        issues.append(
                            {
                                "column": cname,
                                "kind": "precision_scale_mismatch",
                                "sql": (sp, ss),
                                "model": (mp, ms),
                                "sql_type": s["type_raw"],
                                "model_type": f"Numeric({mp},{ms})"
                                if mp is not None
                                else mt["base"],
                            }
                        )

            sql_not_null = s["not_null"]
            model_not_null = not mcol.nullable
            if sql_not_null != model_not_null:
                issues.append(
                    {
                        "column": cname,
                        "kind": "nullability_mismatch",
                        "sql_not_null": sql_not_null,
                        "model_not_null": model_not_null,
                    }
                )

            sql_def = s["default"]
            model_def = None
            if mcol.server_default is not None:
                try:
                    model_def = str(mcol.server_default.arg.text)
                except Exception:
                    model_def = str(mcol.server_default)

            if bool(sql_def) != bool(model_def):
                issues.append(
                    {
                        "column": cname,
                        "kind": "default_presence_mismatch",
                        "sql_default": sql_def,
                        "model_default": model_def,
                    }
                )
            elif sql_def and model_def:
                norm_sql = sql_def.upper().replace(" ", "")
                norm_model = model_def.upper().replace(" ", "")
                if norm_sql != norm_model:
                    issues.append(
                        {
                            "column": cname,
                            "kind": "default_value_mismatch",
                            "sql_default": sql_def,
                            "model_default": model_def,
                        }
                    )

        if issues:
            results.append({"table": tname, "issues": issues})

    return results


if __name__ == "__main__":
    diffs = collect_differences()
    print(json.dumps(diffs, indent=2, ensure_ascii=False))

