"""Enforce the plain-ASCII policy over source and documentation.

Test fixtures are exempt: encoding-related tests need non-ASCII input
by design. Everything else in the repository must be ASCII.
"""

import sys
from pathlib import Path

CHECKED_SUFFIXES = {".py", ".sql", ".md", ".toml", ".yml", ".yaml", ".cfg"}
EXEMPT_PARTS = {"fixtures", "dump", ".venv", ".git", "__pycache__"}


def iter_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in CHECKED_SUFFIXES:
            continue
        if EXEMPT_PARTS.intersection(path.parts):
            continue
        files.append(path)
    return files


def check_file(path: Path) -> list[str]:
    errors = []
    data = path.read_bytes()
    for lineno, line in enumerate(data.splitlines(), start=1):
        for col, byte in enumerate(line, start=1):
            if byte > 0x7F:
                errors.append(f"{path}:{lineno}:{col}: non-ASCII byte 0x{byte:02x}")
                break
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = []
    for path in iter_files(root):
        errors.extend(check_file(path))
    for err in errors:
        print(err, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
