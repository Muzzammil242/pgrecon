"""Enforce the plain-ASCII policy over source and documentation.

Everything in the repository must be ASCII, with two exceptions that
exist for encoding tests: fixture files are exempt entirely, and test
modules may carry non-ASCII inside string literals, where the data
itself is the point. Comments, identifiers, and docstrings stay ASCII
everywhere, and src/ is strict without exception.
"""

import sys
import tokenize
from pathlib import Path

CHECKED_SUFFIXES = {".py", ".sql", ".md", ".toml", ".yml", ".yaml", ".cfg"}
EXEMPT_PARTS = {"fixtures", "dump", "_generated", ".venv", ".git", "__pycache__"}

STRING_TOKENS = {tokenize.STRING} | {
    getattr(tokenize, name)
    for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")
    if hasattr(tokenize, name)
}


def iter_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in CHECKED_SUFFIXES:
            continue
        if EXEMPT_PARTS.intersection(path.parts):
            continue
        files.append(path)
    return files


def check_bytes(path: Path) -> list[str]:
    errors = []
    data = path.read_bytes()
    for lineno, line in enumerate(data.splitlines(), start=1):
        for col, byte in enumerate(line, start=1):
            if byte > 0x7F:
                errors.append(f"{path}:{lineno}:{col}: non-ASCII byte 0x{byte:02x}")
                break
    return errors


def check_test_module(path: Path) -> list[str]:
    # String literals may carry non-ASCII test data; everything else,
    # including comments, may not.
    try:
        with tokenize.open(path) as fh:
            tokens = list(tokenize.generate_tokens(fh.readline))
    except (SyntaxError, tokenize.TokenError, UnicodeDecodeError):
        return check_bytes(path)
    errors = []
    for token in tokens:
        if token.type in STRING_TOKENS:
            continue
        if any(ord(ch) > 0x7F for ch in token.string):
            line, col = token.start
            errors.append(
                f"{path}:{line}:{col + 1}: non-ASCII outside a string literal"
            )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = []
    for path in iter_files(root):
        if path.suffix == ".py" and "tests" in path.parts:
            errors.extend(check_test_module(path))
        else:
            errors.extend(check_bytes(path))
    for err in errors:
        print(err, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
