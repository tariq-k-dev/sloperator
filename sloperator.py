import sys
from pathlib import Path

from sloperator.runner import run_program


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: uv run sloperator.py <file.slop>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"could not read '{path}': {error.strerror}", file=sys.stderr)
        return 2

    error = run_program(source, sys.stdout)
    if error is not None:
        sys.stdout.flush()
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
