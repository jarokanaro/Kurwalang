"""Lexer for the minimal KURWA LANG syntax."""

from dataclasses import dataclass
from enum import Enum, auto


class LexerError(Exception):
    """Raised when source text contains an invalid character or string."""


class TokenType(Enum):
    PROGRAM = auto()
    KURWA = auto()
    JESLI = auto()
    CO_JEST_KURWA = auto()
    SPIERDALAJ = auto()
    ZAJEB = auto()
    WYPIERDOL = auto()
    PIERDOL = auto()
    INACZEJ = auto()
    DOPOKI = auto()
    WYPERDALAJ = auto()
    ODPIERDOL = auto()
    ODPIERDOL_KURWICZNIE = auto()
    FUNKCJA = auto()
    ODDAJ = auto()
    CZEKAJ_KURWA = auto()
    WYJEB_TASK = auto()
    CZEKAJ_WIELE_KURWA = auto()
    KURWA_PAUZA = auto()
    WPIERDOL = auto()
    WYPIERDOL_Z_LISTY = auto()
    WYPIERDOL_Z_MAPY = auto()
    ZAJEB_MODUL = auto()
    WJEBAJ = auto()
    ZLAP_KURWA = auto()
    WYCZYSC_KURWA = auto()
    WYRZUC_KURWA = auto()
    TESTUJ_KURWA = auto()
    SPRAWDZ_KURWA = auto()
    OCZEKUJ_BLAD_KURWA = auto()
    POMIN_KURWA = auto()
    PRAWDA = auto()
    FALSZ = auto()
    I = auto()
    ALBO = auto()
    NIE = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    EQUALS = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()
    EQUAL_EQUAL = auto()
    NOT_EQUAL = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    COMMA = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COLON = auto()
    DOT = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int


KEYWORDS = {
    "program": TokenType.PROGRAM,
    "kurwa": TokenType.KURWA,
    "jeśli": TokenType.JESLI,
    "co_jest_kurwa": TokenType.CO_JEST_KURWA,
    "spierdalaj": TokenType.SPIERDALAJ,
    "zajeb": TokenType.ZAJEB,
    "wypierdol": TokenType.WYPIERDOL,
    "pierdol": TokenType.PIERDOL,
    "inaczej": TokenType.INACZEJ,
    "dopóki": TokenType.DOPOKI,
    "wypierdalaj": TokenType.WYPERDALAJ,
    "odpierdol": TokenType.ODPIERDOL,
    "odpierdol_kurwicznie": TokenType.ODPIERDOL_KURWICZNIE,
    "funkcja": TokenType.FUNKCJA,
    "oddaj": TokenType.ODDAJ,
    "wpierdol": TokenType.WPIERDOL,
    "wypierdol_z_listy": TokenType.WYPIERDOL_Z_LISTY,
    "wypierdol_z_mapy": TokenType.WYPIERDOL_Z_MAPY,
    "zajeb_moduł": TokenType.ZAJEB_MODUL,
    "wjebaj": TokenType.WJEBAJ,
    "zlap_kurwa": TokenType.ZLAP_KURWA,
    "wyczysc_kurwa": TokenType.WYCZYSC_KURWA,
    "wyrzuc_kurwa": TokenType.WYRZUC_KURWA,
    "testuj_kurwa": TokenType.TESTUJ_KURWA,
    "sprawdz_kurwa": TokenType.SPRAWDZ_KURWA,
    "oczekuj_blad_kurwa": TokenType.OCZEKUJ_BLAD_KURWA,
    "pomin_kurwa": TokenType.POMIN_KURWA,
    "prawda": TokenType.PRAWDA,
    "fałsz": TokenType.FALSZ,
    "i": TokenType.I,
    "albo": TokenType.ALBO,
    "nie": TokenType.NIE,
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._at_end():
            character = self._peek()
            if character.isspace():
                self._advance()
            elif character.isalpha() or character == "_":
                tokens.append(self._identifier_or_keyword())
            elif character.isdigit():
                tokens.append(self._number())
            elif character == '"':
                tokens.append(self._string())
            else:
                tokens.append(self._operator_or_delimiter())

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _operator_or_delimiter(self) -> Token:
        line, column = self.line, self.column
        character = self._advance()
        next_character = self._peek() if not self._at_end() else ""
        two_character = character + next_character
        token_type = {
            "<=": TokenType.LESS_EQUAL,
            ">=": TokenType.GREATER_EQUAL,
            "==": TokenType.EQUAL_EQUAL,
            "!=": TokenType.NOT_EQUAL,
        }.get(two_character)
        if token_type is not None:
            self._advance()
            return Token(token_type, two_character, line, column)
        token_type = {
            "=": TokenType.EQUALS,
            "<": TokenType.LESS_THAN,
            ">": TokenType.GREATER_THAN,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "{": TokenType.LEFT_BRACE,
            "}": TokenType.RIGHT_BRACE,
            "(": TokenType.LEFT_PAREN,
            ")": TokenType.RIGHT_PAREN,
            ",": TokenType.COMMA,
            "[": TokenType.LEFT_BRACKET,
            "]": TokenType.RIGHT_BRACKET,
            ":": TokenType.COLON,
            ".": TokenType.DOT,
        }.get(character)
        if token_type is None:
            raise LexerError(f"Unknown character {character!r} at line {line}, column {column}")
        return Token(token_type, character, line, column)

    def _identifier_or_keyword(self) -> Token:
        line, column = self.line, self.column
        start = self.position
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        lexeme = self.source[start:self.position]
        return Token(KEYWORDS.get(lexeme, TokenType.IDENTIFIER), lexeme, line, column)

    def _number(self) -> Token:
        line, column = self.line, self.column
        start = self.position
        while not self._at_end() and self._peek().isdigit():
            self._advance()
        if (
            not self._at_end()
            and self._peek() == "."
            and self.position + 1 < len(self.source)
            and self.source[self.position + 1].isdigit()
        ):
            self._advance()
            while not self._at_end() and self._peek().isdigit():
                self._advance()
            return Token(TokenType.FLOAT, self.source[start:self.position], line, column)
        return Token(TokenType.INTEGER, self.source[start:self.position], line, column)

    def _string(self) -> Token:
        line, column = self.line, self.column
        self._advance()  # opening quote
        characters: list[str] = []
        while not self._at_end() and self._peek() != '"':
            if self._peek() == "\\":
                self._advance()
                if self._at_end():
                    raise LexerError(f"Unterminated escape sequence at line {line}, column {column}")
                escaped = self._advance()
                mapping = {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    '\\': "\\",
                    '"': '"',
                }
                if escaped not in mapping:
                    raise LexerError(f"Unsupported escape sequence \\{escaped} at line {line}, column {column}")
                characters.append(mapping[escaped])
                continue
            if self._peek() == "\n":
                raise LexerError(f"Unterminated string at line {line}, column {column}")
            characters.append(self._advance())
        if self._at_end():
            raise LexerError(f"Unterminated string at line {line}, column {column}")
        self._advance()  # closing quote
        return Token(TokenType.STRING, "".join(characters), line, column)

    def _peek(self) -> str:
        return self.source[self.position]

    def _advance(self) -> str:
        character = self.source[self.position]
        self.position += 1
        if character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return character

    def _at_end(self) -> bool:
        return self.position >= len(self.source)
