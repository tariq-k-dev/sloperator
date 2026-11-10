from sloperator.lexer import TokenType, tokenize
from sloperator.parser import parse
from sloperator.parser.ast import Binary, ExprStmt
from sloperator.runner import run_source


def parse_expression(source: str):
    (statement,) = parse(tokenize(source))
    assert isinstance(statement, ExprStmt)
    return statement.expression


def test_multiplication_binds_tighter_than_addition():
    expr = parse_expression("1 + 2 * 3✨")

    assert isinstance(expr, Binary) and expr.operator.type is TokenType.PLUS
    assert isinstance(expr.right, Binary) and expr.right.operator.type is TokenType.STAR


def test_multiplication_is_evaluated_before_addition():
    result = run_source("hallucinate(1 + 2 * 3)✨")

    assert result.stdout == "7\n"
    assert result.stderr == ""
