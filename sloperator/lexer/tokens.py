from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    PLUS = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    AND = auto()
    OR = auto()

    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    SLOP = auto()
    LOADBEARING = auto()
    CLANKER = auto()
    VIBE = auto()
    NAH = auto()
    RALPH = auto()
    SHIP = auto()

    TRUE = auto()
    FALSE = auto()
    SPARKLES = auto()

    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "slop": TokenType.SLOP,
    "loadbearing": TokenType.LOADBEARING,
    "clanker": TokenType.CLANKER,
    "vibe": TokenType.VIBE,
    "nah": TokenType.NAH,
    "ralph": TokenType.RALPH,
    "ship": TokenType.SHIP,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: int | str | None
    line: int
