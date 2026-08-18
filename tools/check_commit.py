"""Validate commit messages against the project's PG/kernel style.

Runs two ways: as the commit-msg hook, where git passes the message
file as the first argument, and in CI with --head, where the message
of the head commit is checked. The rules are the ones documented in
CONTRIBUTING.md; anything a script cannot judge is left to review.
"""

import subprocess
import sys
from pathlib import Path

SUBJECT_LIMIT = 72
BODY_LIMIT = 72

# Conventional-commit type tokens are not subsystem areas here. The
# area prefix names the code touched: extractor, inventory, rules, ...
BANNED_AREAS = {"feat", "fix", "chore", "perf", "style", "refactor", "ci"}

# Commits carry the owner's identity and nothing else. No attribution
# trailers of any kind.
BANNED_PHRASES = (
    "co-authored-by:",
    "generated with",
    "generated-by:",
    "signed-off-by:",
)


def check_message(text: str) -> list[str]:
    errors = []
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return ["empty commit message"]

    subject = lines[0].rstrip()
    if subject.startswith(("fixup!", "squash!")):
        return []
    if subject.startswith("Merge "):
        # Merge commits, including the synthetic one GitHub builds for
        # a pull request's CI run, follow git's own subject shape.
        return []

    if len(subject) > SUBJECT_LIMIT:
        errors.append(f"subject exceeds {SUBJECT_LIMIT} characters")
    if subject.endswith("."):
        errors.append("subject must not end with a period")
    if ":" in subject:
        area = subject.split(":", 1)[0].strip().lower()
        if area in BANNED_AREAS:
            errors.append(
                f"'{area}:' is a conventional-commit token, not a subsystem;"
                " use the area of the code touched"
            )
    if len(lines) > 1 and lines[1].strip():
        errors.append("second line must be blank")

    for number, line in enumerate(lines[1:], start=2):
        if len(line) > BODY_LIMIT and "://" not in line:
            errors.append(f"line {number} exceeds {BODY_LIMIT} characters")

    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            errors.append(f"forbidden trailer or phrase: {phrase.rstrip(':')}")

    if any(ord(ch) > 0x7F for ch in text):
        errors.append("commit message must be plain ASCII")

    return errors


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--head":
        text = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    elif len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    else:
        print("usage: check_commit.py <message-file> | --head", file=sys.stderr)
        return 2

    errors = check_message(text)
    for error in errors:
        print(f"commit message: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
