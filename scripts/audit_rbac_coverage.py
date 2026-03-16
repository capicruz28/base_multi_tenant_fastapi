# Script: list endpoints with get_current_active_user but without require_permission
import os
import re

base = "app/modules"
results = []

for root, dirs, files in os.walk(base):
    if "presentation" not in root:
        continue
    for f in files:
        if not f.endswith(".py") or not f.startswith("endpoints"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
        if "get_current_active_user" not in content:
            continue

        # Split by @router.METHOD to get each endpoint block
        blocks = re.split(r"@router\.(get|post|put|patch|delete)\s*\(", content)
        for i in range(1, len(blocks)):
            method = blocks[i][:1].upper() if blocks[i] else ""
            rest = blocks[i][1:] if len(blocks[i]) > 1 else ""
            # path is in first "..." or '...'
            path_m = re.search(r'["\']([^"\']*)["\']', rest)
            ep_path = path_m.group(1).strip() if path_m else ""
            # find async def name(
            def_m = re.search(r"async\s+def\s+(\w+)\s*\((.*?)\):", rest, re.DOTALL)
            if not def_m:
                continue
            name, params = def_m.group(1), def_m.group(2)
            # params can span multiple lines; get until ): or next async def
            full_params = params
            if "):" not in params and "\n" in rest:
                idx = rest.find("):", rest.find("async def"))
                if idx != -1:
                    full_params = rest[rest.find("(", rest.find("async def")) + 1 : idx]
            has_user = "get_current_active_user" in full_params
            has_perm = "require_permission" in full_params
            # decorator might have dependencies=[Depends(require_permission(...))]
            block_start = content.find(blocks[i])
            decorator = content[max(0, content.rfind("@router", 0, block_start)) : block_start + 500]
            if not has_perm and "require_permission" in decorator:
                has_perm = True
            if has_user and not has_perm:
                mod = root.replace("app\\modules\\", "").replace("app/modules/", "").split(os.sep)[0]
                results.append((mod, path.replace("\\", "/"), method, ep_path, name))

for r in results:
    print("|".join(r))
