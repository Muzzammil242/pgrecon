"""Fail when a deterministic package imports the AI layer.

Every number in a report must come from deterministic code. That claim
holds only while the extract, inventory, and rules packages are unable
to reach the AI layer, so the import graph is checked mechanically
instead of trusted.
"""

import ast
import sys
from pathlib import Path

DETERMINISTIC_PACKAGES = ("extract", "inventory", "rules", "plsql", "effort")
FORBIDDEN_PREFIXES = ("pgrecon.ai", "pgrecon_report", "anthropic")


def forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    errors = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            if name.startswith(FORBIDDEN_PREFIXES):
                errors.append(f"{path}:{node.lineno}: forbidden import of {name}")
    return errors


def main() -> int:
    src = Path(__file__).resolve().parent.parent / "src" / "pgrecon"
    errors = []
    for package in DETERMINISTIC_PACKAGES:
        package_dir = src / package
        if package_dir.is_dir():
            for path in sorted(package_dir.rglob("*.py")):
                errors.extend(forbidden_imports(path))
        elif package_dir.with_suffix(".py").is_file():
            errors.extend(forbidden_imports(package_dir.with_suffix(".py")))
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
