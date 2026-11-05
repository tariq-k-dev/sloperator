import pytest

from sloperator.runner import run_source

CASES = [
    # (source, kind, line, message)
    (
        'hallucinate("hi")✨',
        "lexical",
        1,
        "straight quotes are not supported, use “ and ” for strings",
    ),
    ("slop x = 1;", "lexical", 1, "semicolons are not supported, end statements with ✨"),
    ("– nope", "lexical", 1, "'–' is an en dash, comments start with an em dash (—)"),
    ("hallucinate(“oops)✨", "lexical", 1, "unterminated string"),
    ("hallucinate(“\\q”)✨", "lexical", 1, "unknown escape sequence '\\q'"),
    (
        "slop x = 1\nslop y = 2✨",
        "syntax",
        2,
        "expected ✨ after variable declaration, found 'slop'",
    ),
    ("ship 1✨", "syntax", 1, "ship is only allowed inside a clanker"),
    (
        "clanker outer() {\n    clanker inner() {\n    }\n}",
        "syntax",
        2,
        "clanker declarations are only allowed at the top level",
    ),
    (
        "slop x✨",
        "syntax",
        1,
        "expected '=' after variable name, an initializer is required, found '✨'",
    ),
    (
        "vibe ✅ {\n    hallucinate(“open”)✨\n",
        "syntax",
        3,
        "expected '}' to close block, but reached end of file",
    ),
    ("hallucinate(nope)✨", "runtime", 1, "undefined variable 'nope'"),
    ("hallucinate(1 / 0)✨", "runtime", 1, "division by zero"),
    ("hallucinate(later())✨\nclanker later() {\n}", "runtime", 1, "undefined variable 'later'"),
    ("clanker f() {\n}\nf = 2✨", "runtime", 3, "cannot assign to immutable binding 'f'"),
    ("slop x = 1✨\nslop x = 2✨", "runtime", 2, "'x' is already declared in this scope"),
    ("vibe 1 {\n}", "runtime", 1, "vibe condition must be a boolean, got number"),
    (
        "clanker add(a, b) {\n    ship a + b✨\n}\nhallucinate(add(1))✨",
        "runtime",
        4,
        "clanker 'add' expects 2 arguments, got 1",
    ),
    ("clanker one(a) {\n}\none()✨", "runtime", 3, "clanker 'one' expects 1 argument, got 0"),
    ("slop x = 1✨\nx(2)✨", "runtime", 2, "can only call clankers, got number"),
    (
        "clanker forever(n) {\n    ship forever(n + 1)✨\n}\nforever(0)✨",
        "runtime",
        2,
        "stack overflow (call depth exceeded 500)",
    ),
    (
        "hallucinate(“a” + 1)✨",
        "runtime",
        1,
        "operands of '+' must both be numbers or both be strings, got string and number",
    ),
]


@pytest.mark.parametrize(("source", "kind", "line", "message"), CASES, ids=[c[3] for c in CASES])
def test_error_message(source: str, kind: str, line: int, message: str):
    result = run_source(source)
    assert result.stderr == f"SlopLang {kind} error at line {line}: {message}\n"
    assert result.exit_code == 1


def test_output_before_error_is_kept():
    result = run_source("hallucinate(“before”)✨\nhallucinate(missing)✨\nhallucinate(“after”)✨")
    assert result.stdout == "before\n"
    assert result.stderr == "SlopLang runtime error at line 2: undefined variable 'missing'\n"


def test_python_recursion_limit_is_reported_as_stack_overflow(monkeypatch: pytest.MonkeyPatch):
    import sloperator.evaluator.interpreter as interpreter

    monkeypatch.setattr(interpreter, "MAX_CALL_DEPTH", 10**9)
    source = "clanker forever(n) {\n    ship forever(n + 1)✨\n}\nforever(0)✨"
    assert run_source(source).stderr == "SlopLang runtime error at line 2: stack overflow\n"
