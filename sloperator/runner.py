import sys
from dataclasses import dataclass
from io import StringIO
from typing import TextIO

from sloperator.errors import SlopError
from sloperator.evaluator import Interpreter
from sloperator.lexer import tokenize
from sloperator.parser import parse

PYTHON_RECURSION_LIMIT = 20_000


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int


def _raise_recursion_limit() -> None:
    if sys.getrecursionlimit() < PYTHON_RECURSION_LIMIT:
        sys.setrecursionlimit(PYTHON_RECURSION_LIMIT)


def check_program(source: str) -> SlopError | None:
    """Tokenize and parse source without executing it."""
    _raise_recursion_limit()
    try:
        parse(tokenize(source))
    except SlopError as error:
        return error
    return None


def run_program(source: str, out: TextIO) -> SlopError | None:
    _raise_recursion_limit()
    try:
        program = parse(tokenize(source))
        Interpreter(out).run(program)
    except SlopError as error:
        return error
    return None


def run_source(source: str) -> RunResult:
    out = StringIO()
    error = run_program(source, out)
    if error is None:
        return RunResult(out.getvalue(), "", 0)
    return RunResult(out.getvalue(), f"{error}\n", 1)
