from typing import TextIO, TypeIs

from sloperator.errors import SlopRuntimeError
from sloperator.evaluator.environment import Environment
from sloperator.evaluator.values import (
    Builtin,
    SlopFunction,
    Value,
    stringify,
    type_name,
    values_equal,
)
from sloperator.lexer.tokens import Token, TokenType
from sloperator.parser.ast import (
    Assign,
    Binary,
    Block,
    Call,
    Expr,
    ExprStmt,
    FunctionDecl,
    Grouping,
    If,
    Literal,
    Logical,
    Program,
    Ship,
    Stmt,
    Unary,
    VarDecl,
    Variable,
    While,
)

MAX_CALL_DEPTH = 500


class ShipSignal(Exception):
    def __init__(self, value: Value) -> None:
        super().__init__()
        self.value = value


class Interpreter:
    def __init__(self, out: TextIO) -> None:
        self.out = out
        self.globals = Environment()
        self.globals.declare("hallucinate", Builtin("hallucinate", self.hallucinate), False, 0)
        self.environment = self.globals
        self.call_depth = 0
        self.last_call_line = 0

    def run(self, program: Program) -> None:
        try:
            for statement in program:
                self.execute(statement)
        except RecursionError:
            raise SlopRuntimeError(self.last_call_line, "stack overflow") from None

    def execute(self, statement: Stmt) -> None:
        match statement:
            case VarDecl(name, initializer, mutable):
                value = self.evaluate(initializer)
                self.environment.declare(name.lexeme, value, mutable, name.line)
            case Assign(name, _, value_expr):
                value = self.evaluate(value_expr)
                self.environment.assign(name.lexeme, value, name.line)
            case ExprStmt(expression):
                self.evaluate(expression)
            case If(condition, then_branch, else_branch):
                if self.condition(condition, "vibe"):
                    self.execute_block(then_branch, Environment(self.environment))
                elif else_branch is not None:
                    self.execute_block(else_branch, Environment(self.environment))
            case While(condition, body):
                self.execute_block(body, Environment(self.environment))
                while self.condition(condition, "ralph"):
                    self.execute_block(body, Environment(self.environment))
            case Ship(_, value_expr):
                raise ShipSignal(self.evaluate(value_expr))
            case Block():
                self.execute_block(statement, Environment(self.globals))
            case FunctionDecl(name, _, _):
                self.environment.declare(name.lexeme, SlopFunction(statement), False, name.line)
            case _:
                raise NotImplementedError(f"unknown statement {statement!r}")

    def execute_block(self, block: Block, environment: Environment) -> None:
        previous = self.environment
        self.environment = environment
        try:
            for statement in block.statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def condition(self, expression: Expr, keyword: str) -> bool:
        value = self.evaluate(expression)
        if not isinstance(value, bool):
            raise SlopRuntimeError(
                expression.line, f"{keyword} condition must be a boolean, got {type_name(value)}"
            )
        return value

    def evaluate(self, expression: Expr) -> Value:
        match expression:
            case Literal(value, _):
                return value
            case Variable(name):
                return self.environment.get(name.lexeme, name.line)
            case Grouping(inner):
                return self.evaluate(inner)
            case Unary(operator, operand):
                return self.unary(operator, self.evaluate(operand))
            case Logical(left, operator, right):
                return self.logical(left, operator, right)
            case Binary(left, operator, right):
                return self.binary(self.evaluate(left), operator, self.evaluate(right))
            case Call(callee, paren, arguments):
                function = self.evaluate(callee)
                values = [self.evaluate(argument) for argument in arguments]
                return self.call(function, values, paren)
            case _:
                raise NotImplementedError(f"unknown expression {expression!r}")

    def unary(self, operator: Token, operand: Value) -> Value:
        if operator.type is TokenType.MINUS:
            if not is_number(operand):
                raise SlopRuntimeError(
                    operator.line,
                    f"operand of unary '-' must be a number, got {type_name(operand)}",
                )
            return -operand
        raise SlopRuntimeError(operator.line, "unary '!' is not implemented")

    def logical(self, left_expr: Expr, operator: Token, right_expr: Expr) -> Value:
        left = self.evaluate(left_expr)
        self.require_boolean(left, operator, "left")
        if operator.type is TokenType.OR and left:
            return True
        if operator.type is TokenType.AND and not left:
            return False
        right = self.evaluate(right_expr)
        self.require_boolean(right, operator, "right")
        return right

    def require_boolean(self, value: Value, operator: Token, side: str) -> None:
        if not isinstance(value, bool):
            raise SlopRuntimeError(
                operator.line,
                f"{side} operand of '{operator.lexeme}' must be a boolean, got {type_name(value)}",
            )

    def binary(self, left: Value, operator: Token, right: Value) -> Value:
        match operator.type:
            case TokenType.PLUS:
                return self.add(left, right, operator)
            case TokenType.EQUAL_EQUAL:
                return values_equal(left, right)
            case TokenType.BANG_EQUAL:
                return not values_equal(left, right)
            case _:
                pass

        if not (is_number(left) and is_number(right)):
            raise SlopRuntimeError(
                operator.line,
                f"operands of '{operator.lexeme}' must be numbers, "
                f"got {type_name(left)} and {type_name(right)}",
            )
        match operator.type:
            case TokenType.MINUS:
                return left - right
            case TokenType.STAR:
                return left * right
            case TokenType.SLASH:
                if right == 0:
                    raise SlopRuntimeError(operator.line, "division by zero")
                quotient = abs(left) // abs(right)
                return quotient if (left < 0) == (right < 0) else -quotient
            case TokenType.LESS:
                return left < right
            case TokenType.LESS_EQUAL:
                return left <= right
            case TokenType.GREATER:
                return left > right
            case TokenType.GREATER_EQUAL:
                return left >= right
            case _:
                raise NotImplementedError(f"unknown operator {operator.lexeme}")

    def add(self, left: Value, right: Value, operator: Token) -> Value:
        if is_number(left) and is_number(right):
            return left + right
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        raise SlopRuntimeError(
            operator.line,
            f"operands of '{operator.lexeme}' must both be numbers or both be strings, "
            f"got {type_name(left)} and {type_name(right)}",
        )

    def call(self, function: Value, arguments: list[Value], paren: Token) -> Value:
        if isinstance(function, Builtin):
            return function.call(arguments, paren.line)
        if not isinstance(function, SlopFunction):
            raise SlopRuntimeError(paren.line, f"can only call clankers, got {type_name(function)}")

        declaration = function.declaration
        if len(arguments) != len(declaration.params):
            expected = len(declaration.params)
            plural = "" if expected == 1 else "s"
            raise SlopRuntimeError(
                paren.line,
                f"clanker '{function.name}' expects {expected} argument{plural}, "
                f"got {len(arguments)}",
            )
        if self.call_depth >= MAX_CALL_DEPTH:
            raise SlopRuntimeError(
                paren.line, f"stack overflow (call depth exceeded {MAX_CALL_DEPTH})"
            )

        environment = Environment(self.globals)
        for param, argument in zip(declaration.params, arguments, strict=True):
            environment.declare(param.lexeme, argument, True, param.line)

        self.call_depth += 1
        self.last_call_line = paren.line
        previous = self.environment
        self.environment = environment
        try:
            for statement in declaration.body.statements:
                self.execute(statement)
            return None
        except ShipSignal as signal:
            return signal.value
        finally:
            self.environment = previous
            self.call_depth -= 1

    def hallucinate(self, arguments: list[Value], line: int) -> Value:
        if len(arguments) != 1:
            raise SlopRuntimeError(line, "hallucinate expects 1 argument")
        self.out.write(stringify(arguments[0]) + "\n")
        return None


def is_number(value: Value) -> TypeIs[int]:
    return isinstance(value, int) and not isinstance(value, bool)
