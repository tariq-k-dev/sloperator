from sloperator.errors import SlopSyntaxError
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


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).parse()


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0
        self.function_depth = 0

    def parse(self) -> Program:
        statements: Program = []
        while not self.at_end():
            statements.append(self.top_level())
        return statements

    def top_level(self) -> Stmt:
        if self.match(TokenType.CLANKER):
            return self.function_decl()
        return self.declaration()

    def function_decl(self) -> FunctionDecl:
        name = self.expect(TokenType.IDENTIFIER, "expected a clanker name after 'clanker'")
        self.expect(TokenType.LEFT_PAREN, "expected '(' after clanker name")
        params: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            params.append(self.expect(TokenType.IDENTIFIER, "expected a parameter name"))
            while self.match(TokenType.COMMA):
                params.append(
                    self.expect(TokenType.IDENTIFIER, "expected a parameter name after ','")
                )
        self.expect(TokenType.RIGHT_PAREN, "expected ')' after parameters")

        seen: set[str] = set()
        for param in params:
            if param.lexeme in seen:
                raise SlopSyntaxError(param.line, f"duplicate parameter name '{param.lexeme}'")
            seen.add(param.lexeme)

        self.function_depth += 1
        body = self.block("expected '{' before clanker body")
        self.function_depth -= 1
        return FunctionDecl(name, tuple(params), body)

    def declaration(self) -> Stmt:
        if self.match(TokenType.SLOP):
            return self.var_decl(self.previous(), mutable=True)
        if self.match(TokenType.LOADBEARING):
            return self.var_decl(self.previous(), mutable=False)
        return self.statement()

    def var_decl(self, keyword: Token, *, mutable: bool) -> VarDecl:
        name = self.expect(
            TokenType.IDENTIFIER, f"expected a variable name after '{keyword.lexeme}'"
        )
        self.expect(TokenType.EQUAL, "expected '=' after variable name, an initializer is required")
        initializer = self.expression()
        self.terminator("variable declaration")
        return VarDecl(name, initializer, mutable=mutable)

    def statement(self) -> Stmt:
        if self.check(TokenType.CLANKER):
            raise SlopSyntaxError(
                self.peek().line, "clanker declarations are only allowed at the top level"
            )
        if self.match(TokenType.VIBE):
            return self.if_stmt()
        if self.match(TokenType.RALPH):
            return self.while_stmt()
        if self.match(TokenType.SHIP):
            return self.ship_stmt()
        if self.check(TokenType.LEFT_BRACE):
            return self.block("expected '{'")
        if self.check(TokenType.IDENTIFIER) and self.peek_next().type is TokenType.EQUAL:
            return self.assign_stmt()
        expression = self.expression()
        self.terminator("expression")
        return ExprStmt(expression)

    def if_stmt(self) -> If:
        condition = self.expression()
        then_branch = self.block("expected '{' after vibe condition")
        else_branch = None
        if self.match(TokenType.NAH):
            else_branch = self.block("expected '{' after nah")
        return If(condition, then_branch, else_branch)

    def while_stmt(self) -> While:
        condition = self.expression()
        body = self.block("expected '{' after ralph condition")
        return While(condition, body)

    def ship_stmt(self) -> Ship:
        keyword = self.previous()
        if self.function_depth == 0:
            raise SlopSyntaxError(keyword.line, "ship is only allowed inside a clanker")
        value = self.expression()
        self.terminator("ship value")
        return Ship(keyword, value)

    def assign_stmt(self) -> Assign:
        name = self.advance()
        operator = self.advance()
        value = self.expression()
        self.terminator("assignment")
        return Assign(name, operator, value)

    def block(self, message: str) -> Block:
        self.expect(TokenType.LEFT_BRACE, message)
        statements: list[Stmt] = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.at_end():
            statements.append(self.declaration())
        self.expect(TokenType.RIGHT_BRACE, "expected '}' to close block")
        return Block(tuple(statements))

    def terminator(self, what: str) -> None:
        self.expect(TokenType.SPARKLES, f"expected ✨ after {what}")

    def expression(self) -> Expr:
        return self.logic_or()

    def logic_or(self) -> Expr:
        expr = self.logic_and()
        while self.match(TokenType.OR):
            expr = Logical(expr, self.previous(), self.logic_and())
        return expr

    def logic_and(self) -> Expr:
        expr = self.comparison()
        while self.match(TokenType.AND):
            expr = Logical(expr, self.previous(), self.comparison())
        return expr

    def equality(self) -> Expr:
        expr = self.term()
        while self.match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            expr = Binary(expr, self.previous(), self.term())
        return expr

    def comparison(self) -> Expr:
        expr = self.equality()
        while self.match(
            TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL
        ):
            expr = Binary(expr, self.previous(), self.equality())
        return expr

    def term(self) -> Expr:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            expr = Binary(expr, self.previous(), self.factor())
        return expr

    def factor(self) -> Expr:
        expr = self.unary()
        return self.factor_tail(expr)

    def factor_tail(self, expr: Expr) -> Expr:
        while self.match(TokenType.STAR, TokenType.SLASH):
            expr = Binary(expr, self.previous(), self.unary())
        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            return Unary(self.previous(), self.unary())
        return self.call()

    def call(self) -> Expr:
        expr = self.primary()
        while self.match(TokenType.LEFT_PAREN):
            paren = self.previous()
            arguments: list[Expr] = []
            if not self.check(TokenType.RIGHT_PAREN):
                arguments.append(self.expression())
                while self.match(TokenType.COMMA):
                    arguments.append(self.expression())
            self.expect(TokenType.RIGHT_PAREN, "expected ')' after arguments")
            expr = Call(expr, paren, tuple(arguments))
        return expr

    def primary(self) -> Expr:
        token = self.advance()
        match token.type:
            case TokenType.NUMBER | TokenType.STRING:
                assert token.literal is not None
                return Literal(token.literal, token)
            case TokenType.TRUE:
                return Literal(True, token)
            case TokenType.FALSE:
                return Literal(False, token)
            case TokenType.IDENTIFIER:
                return Variable(token)
            case TokenType.LEFT_PAREN:
                expression = self.expression()
                self.expect(TokenType.RIGHT_PAREN, "expected ')' after expression")
                return Grouping(expression)
            case _:
                raise self.error(token, "expected an expression")

    def expect(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()
        raise self.error(self.peek(), message)

    def error(self, token: Token, message: str) -> SlopSyntaxError:
        if token.type is TokenType.EOF:
            return SlopSyntaxError(token.line, f"{message}, but reached end of file")
        return SlopSyntaxError(token.line, f"{message}, found '{token.lexeme}'")

    def match(self, *types: TokenType) -> bool:
        if self.peek().type in types:
            self.advance()
            return True
        return False

    def check(self, type: TokenType) -> bool:
        return self.peek().type is type

    def advance(self) -> Token:
        token = self.tokens[self.current]
        if not self.at_end():
            self.current += 1
        return token

    def peek(self) -> Token:
        return self.tokens[self.current]

    def peek_next(self) -> Token:
        return self.tokens[self.current + 1]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def at_end(self) -> bool:
        return self.peek().type is TokenType.EOF
