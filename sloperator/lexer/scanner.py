from sloperator.errors import LexicalError
from sloperator.lexer.tokens import KEYWORDS, Token, TokenType

VARIATION_SELECTOR = "\ufe0f"

EMOJI_TOKENS: dict[str, TokenType] = {
    "✨": TokenType.SPARKLES,
    "✅": TokenType.TRUE,
    "❌": TokenType.FALSE,
}

SINGLE_CHAR_TOKENS: dict[str, TokenType] = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
}


MAYBE_EQUAL_TOKENS: dict[str, tuple[TokenType, TokenType]] = {
    "!": (TokenType.BANG, TokenType.BANG_EQUAL),
    "=": (TokenType.EQUAL, TokenType.EQUAL_EQUAL),
    "<": (TokenType.LESS, TokenType.LESS_EQUAL),
    ">": (TokenType.GREATER, TokenType.GREATER_EQUAL),
}


UNSUPPORTED_CHARS: dict[str, str] = {
    '"': "straight quotes are not supported, use “ and ” for strings",
    ";": "semicolons are not supported, end statements with ✨",
    "–": "'–' is an en dash, comments start with an em dash (—)",
    "”": "unexpected closing quote ” without an opening “",
}

ESCAPES: dict[str, str] = {
    "n": "\n",
    "t": "\t",
    "”": "”",
    "\\": "\\",
}


def tokenize(source: str) -> list[Token]:
    return Scanner(source).tokenize()


class Scanner:
    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def tokenize(self) -> list[Token]:
        while not self.at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self) -> None:
        ch = self.advance()

        if ch in " \t\r":
            return
        if ch == "\n":
            self.line += 1
            return
        if ch == "—":
            while not self.at_end() and self.peek() != "\n":
                self.advance()
            self.match("\n")
            return
        if ch == "/" and self.match("/"):
            raise LexicalError(self.line, "comments start with an em dash (—), not //")
        if ch in UNSUPPORTED_CHARS:
            raise LexicalError(self.line, UNSUPPORTED_CHARS[ch])
        if ch in EMOJI_TOKENS:
            self.match(VARIATION_SELECTOR)
            self.add_token(EMOJI_TOKENS[ch])
            return
        if ch == "“":
            self.string()
            return
        if is_digit(ch):
            self.number()
            return
        if is_identifier_start(ch):
            self.identifier()
            return
        if ch in SINGLE_CHAR_TOKENS:
            self.add_token(SINGLE_CHAR_TOKENS[ch])
            return
        if ch in MAYBE_EQUAL_TOKENS:
            single, double = MAYBE_EQUAL_TOKENS[ch]
            self.add_token(double if self.match("=") else single)
            return
        if ch == "&":
            if not self.match("&"):
                raise LexicalError(self.line, "unexpected character '&', did you mean '&&'?")
            self.add_token(TokenType.AND)
            return
        if ch == "|":
            if not self.match("|"):
                raise LexicalError(self.line, "unexpected character '|', did you mean '||'?")
            self.add_token(TokenType.OR)
            return

        raise LexicalError(self.line, f"unexpected character '{ch}'")

    def string(self) -> None:
        chars: list[str] = []
        while True:
            if self.at_end() or self.peek() == "\n":
                raise LexicalError(self.line, "unterminated string")
            ch = self.advance()
            if ch == "”":
                break
            if ch == "\\":
                if self.at_end():
                    raise LexicalError(self.line, "unterminated string")
                escape = self.advance()
                if escape not in ESCAPES:
                    raise LexicalError(self.line, f"unknown escape sequence '\\{escape}'")
                chars.append(ESCAPES[escape])
            else:
                chars.append(ch)
        self.add_token(TokenType.STRING, "".join(chars))

    def number(self) -> None:
        while is_digit(self.peek()):
            self.advance()
        self.add_token(TokenType.NUMBER, int(self.source[self.start : self.current]))

    def identifier(self) -> None:
        while is_identifier_char(self.peek()):
            self.advance()
        text = self.source[self.start : self.current]
        self.add_token(KEYWORDS.get(text, TokenType.IDENTIFIER))

    def add_token(self, type: TokenType, literal: int | str | None = None) -> None:
        lexeme = self.source[self.start : self.current]
        self.tokens.append(Token(type, lexeme, literal, self.line))

    def at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def peek(self) -> str:
        if self.at_end():
            return "\0"
        return self.source[self.current]

    def match(self, expected: str) -> bool:
        if self.at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True


def is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def is_identifier_start(ch: str) -> bool:
    return ch == "_" or "a" <= ch <= "z" or "A" <= ch <= "Z"


def is_identifier_char(ch: str) -> bool:
    return is_identifier_start(ch)
