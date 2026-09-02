from pathlib import Path


TARGET = Path(
    "/app/packages/unifi-mcp-shared/src/unifi_mcp_shared/permissioned_tool.py"
)

OLD = '''                # 2. Bypass injection — only for mutation actions with confirm param
                #    Only inject if caller didn't explicitly provide confirm
                if action.lower() != "read":
                    mode = resolve_permission_mode(server_prefix)
                    if mode == "bypass":
                        sig = inspect.signature(func)
                        if "confirm" in sig.parameters and "confirm" not in kwargs:
                            kwargs["confirm"] = True
'''

NEW = '''                # 2. Full-access bypass for mutation actions with a confirm param.
                #    FastMCP materializes default arguments before this wrapper runs,
                #    so bypass must override confirm=false even when the caller omitted it.
                if action.lower() != "read":
                    mode = resolve_permission_mode(server_prefix)
                    if mode == "bypass":
                        sig = inspect.signature(func)
                        if "confirm" in sig.parameters:
                            kwargs["confirm"] = True
'''


source = TARGET.read_text(encoding="utf-8")
matches = source.count(OLD)
if matches != 1:
    raise RuntimeError(f"expected one permission bypass block, found {matches}")

TARGET.write_text(source.replace(OLD, NEW), encoding="utf-8")
