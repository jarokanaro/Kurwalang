"""Static analysis for KURWA LANG without execution."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    from .ast import (
        AppendStatement,
        AssertStatement,
        BinaryExpression,
        Block,
        BooleanLiteral,
        CallExpression,
        DeleteMapEntryStatement,
        ExpectErrorStatement,
        Expression,
        ExpressionStatement,
        ExitStatement,
        FunctionDeclaration,
        IfStatement,
        IncrementStatement,
        ImportStatement,
        IndexExpression,
        ListLiteral,
        LoopExitStatement,
        MapLiteral,
        MemberExpression,
        NumberLiteral,
        PopListExpression,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        SetListElementStatement,
        SliceExpression,
        SkipStatement,
        StringLiteral,
        TestDeclaration,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
    )
    from .lexer import Lexer, LexerError
    from .parser import Parser, ParserError
except ImportError:  # pragma: no cover - support direct script execution
    from ast import (
        AppendStatement,
        AssertStatement,
        BinaryExpression,
        Block,
        BooleanLiteral,
        CallExpression,
        DeleteMapEntryStatement,
        ExpectErrorStatement,
        Expression,
        ExpressionStatement,
        ExitStatement,
        FunctionDeclaration,
        IfStatement,
        IncrementStatement,
        ImportStatement,
        IndexExpression,
        ListLiteral,
        LoopExitStatement,
        MapLiteral,
        MemberExpression,
        NumberLiteral,
        PopListExpression,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        SetListElementStatement,
        SliceExpression,
        SkipStatement,
        StringLiteral,
        TestDeclaration,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
    )
    from lexer import Lexer, LexerError
    from parser import Parser, ParserError


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


_UNKNOWN_CONSTANT = object()


@dataclass
class Diagnostic:
    code: str
    severity: Severity
    message: str
    file: str | None = None
    line: int = 1
    column: int = 1
    suggestion: str | None = None

    def format(self) -> str:
        location = f"{self.file}:{self.line}"
        if self.column and self.column > 0:
            location = f"{location}:{self.column}"
        rendered = f"{location} — {self.severity.value.upper()} {self.code}\n{self.message}"
        if self.suggestion:
            rendered = f"{rendered}\nSugestia: {self.suggestion}"
        return rendered


@dataclass
class Symbol:
    name: str
    kind: str
    declared_at: int = 1
    column: int = 1
    used: bool = False
    constant: object = _UNKNOWN_CONSTANT
    availability: str = "definite"
    reassigned: bool = False
    mutated: bool = False
    shadowed: bool = False


class Scope:
    def __init__(self, parent: "Scope | None" = None):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def define(self, name: str, kind: str, line: int = 1, column: int = 1) -> Symbol:
        existing = self.symbols.get(name)
        shadowed = self.parent is not None and self.parent.lookup(name) is not None
        symbol = Symbol(
            name=name,
            kind=kind,
            declared_at=line,
            column=column,
            reassigned=existing is not None or bool(existing and existing.reassigned),
            shadowed=shadowed,
        )
        self.symbols[name] = symbol
        return symbol

    def resolve(self, name: str) -> Symbol | None:
        result = self.lookup(name)
        if result is None:
            return None
        symbol, _ = result
        symbol.used = True
        return symbol

    def lookup(self, name: str) -> tuple[Symbol, "Scope"] | None:
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name], scope
            scope = scope.parent
        return None

    def clone(self) -> "Scope":
        parent = self.parent.clone() if self.parent is not None else None
        result = Scope(parent)
        result.symbols = {
            name: Symbol(**vars(symbol))
            for name, symbol in self.symbols.items()
        }
        return result

    def merge_from(self, paths: list["Scope"]) -> None:
        names = set().union(*(path.symbols.keys() for path in paths))
        merged = {}
        for name in names:
            symbols = [path.symbols.get(name) for path in paths]
            present = [symbol for symbol in symbols if symbol is not None]
            symbol = Symbol(**vars(present[0]))
            symbol.used = any(item.used for item in present)
            symbol.reassigned = any(item.reassigned for item in present)
            symbol.mutated = any(item.mutated for item in present)
            symbol.shadowed = any(item.shadowed for item in present)
            if len(present) != len(paths):
                symbol.availability = "maybe"
                symbol.constant = _UNKNOWN_CONSTANT
            else:
                first = present[0].constant
                symbol.constant = first if all(
                    self._same_value(item.constant, first)
                    for item in present[1:]
                ) else _UNKNOWN_CONSTANT
                symbol.availability = "definite"
            merged[name] = symbol
        self.symbols = merged
        if self.parent is not None:
            parents = [path.parent for path in paths if path.parent is not None]
            if len(parents) == len(paths):
                self.parent.merge_from(parents)

    @staticmethod
    def _same_value(left, right) -> bool:
        if left is _UNKNOWN_CONSTANT or right is _UNKNOWN_CONSTANT:
            return left is right
        return type(left) is type(right) and left == right

    def collect_unused(self, diagnostics: list[Diagnostic], file: str | None) -> None:
        for name, symbol in self.symbols.items():
            if symbol.kind == "parameter":
                continue
            if not symbol.used:
                diagnostics.append(
                    Diagnostic(
                        code="K001",
                        severity=Severity.WARNING,
                        message=f'Zmienna "{name}" została zadeklarowana, ale nie jest używana.',
                        file=file,
                        line=symbol.declared_at,
                        column=symbol.column,
                    )
                )


class TypeInfo:
    def __init__(self, name: str, item_type: "TypeInfo | None" = None, key_type: "TypeInfo | None" = None, value_type: "TypeInfo | None" = None, return_type: "TypeInfo | None" = None, parameter_types: list["TypeInfo"] | None = None):
        self.name = name
        self.item_type = item_type
        self.key_type = key_type
        self.value_type = value_type
        self.return_type = return_type
        self.parameter_types = parameter_types or []

    def __eq__(self, other):
        if not isinstance(other, TypeInfo):
            return NotImplemented
        return (
            self.name == other.name
            and self.item_type == other.item_type
            and self.key_type == other.key_type
            and self.value_type == other.value_type
            and self.return_type == other.return_type
            and self.parameter_types == other.parameter_types
        )

    def __hash__(self):
        return hash((self.name, self.item_type, self.key_type, self.value_type, self.return_type, tuple(self.parameter_types)))

    def __str__(self):
        if self.name == "lista":
            return f"lista<{self.item_type or 'nieznane'}>"
        if self.name == "mapa":
            return f"mapa<{self.key_type or 'string'}, {self.value_type or 'nieznane'}>"
        if self.name == "funkcja":
            if self.return_type is not None:
                return f"funkcja -> {self.return_type}"
            return "funkcja"
        return self.name


def _same_type(left: TypeInfo | None, right: TypeInfo | None) -> bool:
    if left is None or right is None:
        return left is right
    return left == right


UNKNOWN = TypeInfo("nieznane")
LICZBA = TypeInfo("liczba")
TEKST = TypeInfo("tekst")
BOOLEAN = TypeInfo("boolean")
NO_VALUE = TypeInfo("brak_wyniku")
MODUL = TypeInfo("moduł")
ASYNC = TypeInfo("task")


class TypeScope:
    def __init__(self, parent: "TypeScope | None" = None):
        self.parent = parent
        self.values: dict[str, TypeInfo] = {}

    def define(self, name: str, type_info: TypeInfo):
        self.values[name] = type_info

    def resolve(self, name: str):
        scope = self
        while scope is not None:
            if name in scope.values:
                return scope.values[name]
            scope = scope.parent
        return None


class TypeAnalyzer:
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []
        self._function_stack: set[str] = set()

    def analyze_program(self, program: Program, file: str | None = None) -> list[Diagnostic]:
        self.diagnostics = []
        self._function_stack = set()
        scope = TypeScope()
        self._analyze_block(program.body, scope, file)
        return self.diagnostics

    def _record(self, code: str, severity: Severity, message: str, node=None, file: str | None = None, suggestion: str | None = None) -> None:
        self.diagnostics.append(
            Diagnostic(
                code=code,
                severity=severity,
                message=message,
                file=file,
                line=getattr(node, "line", 1),
                column=getattr(node, "column", 1),
                suggestion=suggestion,
            )
        )

    def _analyze_block(self, block: Block, scope: TypeScope, file: str | None, function_return: TypeInfo | None = None) -> TypeInfo | None:
        merged_return = function_return
        for statement in block.statements:
            if isinstance(statement, VariableDeclaration):
                inferred = self._infer_expression(statement.value, scope)
                scope.define(statement.name, inferred)
            elif isinstance(statement, FunctionDeclaration):
                function_type = TypeInfo("funkcja", return_type=TypeInfo(UNKNOWN.name), parameter_types=[UNKNOWN for _ in statement.parameters])
                scope.define(statement.name, function_type)
                function_scope = TypeScope(scope)
                for param in statement.parameters:
                    function_scope.define(param, UNKNOWN)
                return_type = self._analyze_function_body(statement, function_scope, function_type, file)
                if return_type is not None:
                    function_type.return_type = return_type
            elif isinstance(statement, ReturnStatement):
                inferred = self._infer_expression(statement.value, scope)
                if function_return is not None:
                    if function_return.name == "nieznane":
                        function_return.name = inferred.name
                    if function_return.name != "nieznane" and inferred.name != "nieznane" and function_return.name != inferred.name:
                        self._record("T030", Severity.ERROR, f"Zwrot z funkcji ma typ {inferred}, ale funkcja oczekuje {function_return}.", statement, file)
                merged_return = self._merge_types(merged_return, inferred) if merged_return is not None else inferred
            elif isinstance(statement, IfStatement):
                condition_type = self._infer_expression(statement.condition, scope)
                if condition_type != BOOLEAN and condition_type != UNKNOWN:
                    self._record("T020", Severity.ERROR, "Warunek 'jeśli' musi mieć typ boolean.", statement, file, suggestion="Użyj wyrażenia zwracającego boolean, np. x > 0 albo prawda.")
                body_return = self._analyze_block(statement.body, TypeScope(scope), file)
                if statement.else_body is not None:
                    else_return = self._analyze_block(statement.else_body, TypeScope(scope), file)
                    if body_return is not None and else_return is not None:
                        self._merge_types(body_return, else_return)
            elif isinstance(statement, WhileStatement):
                condition_type = self._infer_expression(statement.condition, scope)
                if condition_type != BOOLEAN and condition_type != UNKNOWN:
                    self._record("T020", Severity.ERROR, "Warunek 'dopóki' musi mieć typ boolean.", statement, file, suggestion="Użyj warunku boolean, np. i != 0 albo wartosc == prawda.")
                self._analyze_block(statement.body, TypeScope(scope), file)
            elif isinstance(statement, ExpressionStatement):
                self._infer_expression(statement.expression, scope)
            elif isinstance(statement, PrintTextStatement):
                self._infer_expression(statement.value, scope)
            elif isinstance(statement, PrintValueStatement):
                self._infer_expression(statement.value, scope)
            elif isinstance(statement, AssertStatement):
                condition_type = self._infer_expression(statement.condition, scope)
                if condition_type != BOOLEAN and condition_type != UNKNOWN:
                    self._record("T020", Severity.ERROR, "Asercja 'sprawdz_kurwa' musi sprawdzać wartość boolean.", statement, file, suggestion="Asercja powinna oceniać wyrażenie zwracające boolean.")
            elif isinstance(statement, ThrowStatement):
                self._infer_expression(statement.value, scope)
            elif isinstance(statement, TryStatement):
                self._analyze_block(statement.body, TypeScope(scope), file)
                if statement.catch_body is not None:
                    catch_scope = TypeScope(scope)
                    if statement.catch_name is not None:
                        catch_scope.define(statement.catch_name, MODUL)
                    self._analyze_block(statement.catch_body, catch_scope, file)
                if statement.finally_body is not None:
                    self._analyze_block(statement.finally_body, TypeScope(scope), file)
            elif isinstance(statement, AppendStatement):
                list_type = self._infer_expression(statement.list_expression, scope)
                if list_type.name == "lista":
                    self._infer_expression(statement.value, scope)
                else:
                    self._record("T040", Severity.ERROR, "'wpierdol' wymaga listy.", statement, file, suggestion="Dodaj operację na liście, np. kurwa moja_lista = [1, 2] i wpierdol moja_lista 3.")
            elif isinstance(statement, DeleteMapEntryStatement):
                map_type = self._infer_expression(statement.map_expression, scope)
                if map_type.name != "mapa":
                    self._record("T040", Severity.ERROR, "'wypierdol_z_mapy' wymaga mapy.", statement, file, suggestion="Najpierw zdefiniuj mapę, a następnie usuń klucz z niej.")
            elif isinstance(statement, SetListElementStatement):
                collection_type = self._infer_expression(statement.target.collection, scope)
                if collection_type.name not in {"lista", "mapa", "tekst"}:
                    self._record("T040", Severity.ERROR, "Przypisanie elementu wymaga listy, mapy albo tekstu.", statement, file, suggestion="Ustaw element tylko w liście, mapie albo tekście.")
                self._infer_expression(statement.value, scope)
            elif isinstance(statement, ImportStatement):
                scope.define(statement.module_name, MODUL)
        return merged_return

    def _analyze_function_body(self, declaration: FunctionDeclaration, function_scope: TypeScope, function_type: TypeInfo, file: str | None) -> TypeInfo | None:
        function_name = declaration.name
        if function_name in self._function_stack:
            return function_type.return_type if function_type.return_type is not None else UNKNOWN
        self._function_stack.add(function_name)
        try:
            body_return = self._analyze_block(declaration.body, function_scope, file, function_return=function_type.return_type)
            if body_return is not None:
                function_type.return_type = body_return
            else:
                function_type.return_type = NO_VALUE
            return function_type.return_type
        finally:
            self._function_stack.discard(function_name)

    def _infer_expression(self, expression, scope: TypeScope):
        if expression is None:
            return UNKNOWN
        if isinstance(expression, NumberLiteral):
            return LICZBA
        if isinstance(expression, StringLiteral):
            return TEKST
        if isinstance(expression, BooleanLiteral):
            return BOOLEAN
        if isinstance(expression, ListLiteral):
            element_types = [self._infer_expression(item, scope) for item in expression.elements]
            if not element_types:
                return TypeInfo("lista", item_type=UNKNOWN)
            merged = self._merge_types_many(element_types)
            return TypeInfo("lista", item_type=merged)
        if isinstance(expression, MapLiteral):
            value_types = [self._infer_expression(value, scope) for _, value in expression.entries]
            merged_values = self._merge_types_many(value_types) if value_types else UNKNOWN
            return TypeInfo("mapa", key_type=TEKST, value_type=merged_values)
        if isinstance(expression, VariableExpression):
            resolved = scope.resolve(expression.name)
            if resolved is None:
                return UNKNOWN
            return resolved
        if isinstance(expression, BinaryExpression):
            left = self._infer_expression(expression.left, scope)
            right = self._infer_expression(expression.right, scope)
            if expression.operator in {"+", "-", "*", "/"}:
                if expression.operator == "+":
                    if left == TEKST and right == TEKST:
                        return TEKST
                    if left == LICZBA and right == LICZBA:
                        return LICZBA
                    if left != UNKNOWN and right != UNKNOWN:
                        self._record("T010", Severity.ERROR, f"Operator '{expression.operator}' nie jest wspierany dla typów {left} i {right}.", expression, suggestion="Użyj tej samej liczby albo tekstu w obu operandach dla danego operatora.")
                    return UNKNOWN
                if left == LICZBA and right == LICZBA:
                    return LICZBA
                if left != UNKNOWN and right != UNKNOWN:
                    self._record("T010", Severity.ERROR, f"Operator '{expression.operator}' nie jest wspierany dla typów {left} i {right}.", expression, suggestion="Użyj tej samej liczby albo tekstu w obu operandach dla danego operatora.")
                return UNKNOWN
            if expression.operator in {"i", "albo"}:
                if (left == BOOLEAN or left == UNKNOWN) and (right == BOOLEAN or right == UNKNOWN):
                    return BOOLEAN
                self._record("T020", Severity.ERROR, f"Operator '{expression.operator}' wymaga wartości boolean.", expression, suggestion="Użyj prawda/fałsz jako operandów dla operatorów logicznych.")
                return BOOLEAN
            if expression.operator in {"<", "<=", ">", ">="}:
                if left == LICZBA and right == LICZBA:
                    return BOOLEAN
                if left != UNKNOWN and right != UNKNOWN:
                    self._record("T010", Severity.ERROR, f"Porównanie '{expression.operator}' wymaga liczb.", expression, suggestion="Porównaj dwie liczby, nie teksty ani mapy.")
                return BOOLEAN
            if expression.operator in {"==", "!="}:
                if left != UNKNOWN and right != UNKNOWN and left.name == right.name:
                    return BOOLEAN
                if left == UNKNOWN or right == UNKNOWN:
                    return BOOLEAN
                return BOOLEAN
            return UNKNOWN
        if isinstance(expression, UnaryExpression):
            operand = self._infer_expression(expression.operand, scope)
            if expression.operator == "nie":
                if operand != UNKNOWN and operand != BOOLEAN:
                    self._record("T020", Severity.ERROR, "Operator 'nie' wymaga wartości boolean.", expression, suggestion="Zastosuj 'nie' tylko do wyrażenia boolean.")
                return BOOLEAN
            if expression.operator == "-":
                if operand != UNKNOWN and operand != LICZBA:
                    self._record("T010", Severity.ERROR, "Operator '-' wymaga liczby.", expression, suggestion="Użyj operatora unarnego '-' dla wartości liczbowej.")
                return LICZBA
            return UNKNOWN
        if isinstance(expression, CallExpression):
            callee_type = self._infer_expression(expression.callee, scope)
            if callee_type is None:
                return UNKNOWN
            if callee_type.name == "funkcja":
                if len(expression.arguments) != len(callee_type.parameter_types):
                    if len(callee_type.parameter_types) > 0:
                        self._record("T010", Severity.ERROR, f"Funkcja oczekuje {len(callee_type.parameter_types)} argumentów, a otrzymała {len(expression.arguments)}.", expression, suggestion="Przekaż odpowiednią liczbę argumentów do funkcji.")
                if callee_type.return_type is not None:
                    return callee_type.return_type
                return UNKNOWN
            if isinstance(expression.callee, VariableExpression):
                name = expression.callee.name
                if name in {"ile_kurwa", "tekst_kurwa", "liczba_kurwa"}:
                    return TEKST if name == "tekst_kurwa" else LICZBA
            if isinstance(expression.callee, MemberExpression):
                if expression.callee.name in {"wypierdol", "pierdol"}:
                    return UNKNOWN
            return UNKNOWN
        if isinstance(expression, MemberExpression):
            object_type = self._infer_expression(expression.object, scope)
            if object_type and object_type.name == "mapa":
                return object_type.value_type or UNKNOWN
            return UNKNOWN
        if isinstance(expression, IndexExpression):
            collection_type = self._infer_expression(expression.collection, scope)
            index_type = self._infer_expression(expression.index, scope)
            if collection_type.name == "lista":
                if index_type == LICZBA or index_type == UNKNOWN:
                    return collection_type.item_type or UNKNOWN
                self._record("T040", Severity.ERROR, "Indeks listy musi być liczbą.", expression, suggestion="Indeks listy musi być liczbą całkowitą albo wartością liczbową.")
                return UNKNOWN
            if collection_type.name == "mapa":
                if index_type in {TEKST, UNKNOWN}:
                    return collection_type.value_type or UNKNOWN
                self._record("T040", Severity.ERROR, "Indeks mapy musi być tekstem.", expression, suggestion="Klucz mapy musi być tekstem, np. moja_mapa[\"klucz\"] .")
                return UNKNOWN
            if collection_type.name == "tekst":
                if index_type in {LICZBA, UNKNOWN}:
                    return TEKST
                self._record("T040", Severity.ERROR, "Indeks tekstu musi być liczbą.", expression, suggestion="Do tekstu użyj indeksu liczbowego, nie boola ani mapy.")
                return UNKNOWN
            return UNKNOWN
        if isinstance(expression, SliceExpression):
            collection_type = self._infer_expression(expression.collection, scope)
            if collection_type.name == "tekst":
                return TEKST
            self._record("T040", Severity.ERROR, "Slicing działa tylko na tekście.", expression, suggestion="Użyj slicingu tylko na wartościach tekstowych.")
            return UNKNOWN
        if isinstance(expression, PopListExpression):
            collection_type = self._infer_expression(expression.list_expression, scope)
            if collection_type.name == "lista":
                return collection_type.item_type or UNKNOWN
            self._record("T040", Severity.ERROR, "'wypierdol_z_listy' wymaga listy.", expression, suggestion="Najpierw podaj listę, potem pobierz element z końca listy.")
            return UNKNOWN
        return UNKNOWN

    def _merge_types(self, left: TypeInfo | None, right: TypeInfo | None):
        if left is None:
            return right
        if right is None:
            return left
        if left == right:
            return left
        if left == UNKNOWN:
            return right
        if right == UNKNOWN:
            return left
        if left.name == "lista" and right.name == "lista":
            return TypeInfo("lista", item_type=self._merge_types(left.item_type, right.item_type))
        if left.name == "mapa" and right.name == "mapa":
            return TypeInfo("mapa", key_type=TEKST, value_type=self._merge_types(left.value_type, right.value_type))
        return UNKNOWN

    def _merge_types_many(self, types):
        merged = UNKNOWN
        for value in types:
            merged = self._merge_types(merged, value)
        return merged


@dataclass
class _FlowResult:
    normal: bool = True
    returned: bool = False
    broken: bool = False
    exited: bool = False


class _ProgramFlowAnalysis:
    """Conservative flow facts derived from the existing AST only."""

    _EXTERNAL_MODULES = {"plik", "katalog", "sciezka", "siec", "system", "czas", "losuj"}

    def __init__(self, file: str | None = None):
        self.file = file
        self.diagnostics: list[Diagnostic] = []
        self.function_calls: dict[str, set[str]] = {}
        self.recursive_functions: set[str] = set()
        self.function_effects: dict[str, str] = {}
        self._function_nodes: dict[str, FunctionDeclaration] = {}
        self._current_function: str | None = None
        self._top_level_calls: set[str] = set()
        self._maybe_uses: list[VariableExpression] = []
        self.variable_uses: list[tuple[VariableExpression, str]] = []
        self.variable_events: dict[str, set[str]] = {}
        self._condition_facts: list[tuple[str, str, object]] = []

    def analyze(self, program: Program) -> list[Diagnostic]:
        self._collect_functions(program.body)
        self._analyze_block(program.body, Scope())
        self._summarize_functions()
        for expression in self._maybe_uses:
            self._record(
                "A010",
                Severity.WARNING,
                f'Zmienna "{expression.name}" może nie być dostępna na każdej ścieżce.',
                expression,
            )
        return self.diagnostics

    def _record(self, code: str, severity: Severity, message: str, node) -> None:
        self.diagnostics.append(
            Diagnostic(
                code=code,
                severity=severity,
                message=message,
                file=self.file,
                line=getattr(node, "line", 1),
                column=getattr(node, "column", 1),
            )
        )

    def _event(self, name: str, event: str) -> None:
        self.variable_events.setdefault(name, set()).add(event)

    def _collect_functions(self, block: Block) -> None:
        for statement in block.statements:
            if isinstance(statement, FunctionDeclaration):
                self._function_nodes[statement.name] = statement
                self._collect_functions(statement.body)
            elif isinstance(statement, IfStatement):
                self._collect_functions(statement.body)
                if statement.else_body is not None:
                    self._collect_functions(statement.else_body)
            elif isinstance(statement, WhileStatement):
                self._collect_functions(statement.body)
            elif isinstance(statement, TryStatement):
                self._collect_functions(statement.body)
                if statement.catch_body is not None:
                    self._collect_functions(statement.catch_body)
                if statement.finally_body is not None:
                    self._collect_functions(statement.finally_body)
            elif isinstance(statement, ExpectErrorStatement):
                self._collect_functions(statement.body)
            elif isinstance(statement, TestDeclaration):
                self._collect_functions(statement.body)

    def _analyze_block(self, block: Block, state: Scope) -> _FlowResult:
        outcome = _FlowResult()
        previous_statement = None
        for statement in block.statements:
            if not outcome.normal:
                if not isinstance(previous_statement, (ReturnStatement, ExitStatement, LoopExitStatement)):
                    self._record("A001", Severity.WARNING, "Kod jest nieosiągalny po bezwarunkowym zakończeniu ścieżki.", statement)
                continue
            current = self._analyze_statement(statement, state)
            previous_statement = statement
            outcome.returned = outcome.returned or current.returned
            outcome.broken = outcome.broken or current.broken
            outcome.exited = outcome.exited or current.exited
            outcome.normal = current.normal
        return outcome

    def _analyze_statement(self, statement, state: Scope) -> _FlowResult:
        if isinstance(statement, VariableDeclaration):
            self._analyze_expression(statement.value, state)
            constant = self._constant(statement.value, state)
            self._forget_condition_facts(statement.name)
            if statement.name in state.symbols:
                self._event(statement.name, "reassigned")
                self._forget_condition_facts(statement.name)
            if state.parent is not None and state.parent.lookup(statement.name) is not None and statement.name not in state.symbols:
                self._event(statement.name, "shadowed")
                self._record("A012", Severity.WARNING, f'Zmienna "{statement.name}" zasłania nazwę z zakresu zewnętrznego.', statement)
            symbol = state.define(statement.name, "variable", statement.line, statement.column)
            symbol.constant = constant
            if symbol.reassigned:
                self._event(statement.name, "reassigned")
            if symbol.shadowed:
                self._event(statement.name, "shadowed")
        elif isinstance(statement, FunctionDeclaration):
            state.define(statement.name, "function", statement.line, statement.column)
            previous = self._current_function
            self._current_function = statement.name
            function_state = Scope(state.clone())
            ancestor = function_state.parent
            while ancestor is not None:
                for outer_symbol in ancestor.symbols.values():
                    outer_symbol.constant = _UNKNOWN_CONSTANT
                ancestor = ancestor.parent
            original_facts = self._condition_facts
            self._condition_facts = []
            for name in statement.parameters:
                if function_state.parent.lookup(name) is not None:
                    self._forget_condition_facts(name)
                    self._event(name, "shadowed")
                    self._record("A012", Severity.WARNING, f'Parametr "{name}" zasłania nazwę z zakresu zewnętrznego.', statement)
                function_state.define(name, "parameter", statement.line, statement.column)
            function_outcome = self._analyze_block(statement.body, function_state)
            self._condition_facts = original_facts
            self._current_function = previous
            if function_outcome.returned and function_outcome.normal:
                self._record(
                    "A031",
                    Severity.WARNING,
                    f'Funkcja "{statement.name}" zwraca wartość tylko na części ścieżek.',
                    statement,
                )
        elif isinstance(statement, TestDeclaration):
            self._analyze_block(statement.body, Scope(state.clone()))
        elif isinstance(statement, ImportStatement):
            state.define(statement.module_name, "import", statement.line, statement.column)
        elif isinstance(statement, ExpressionStatement):
            self._analyze_expression(statement.expression, state)
        elif isinstance(statement, (PrintTextStatement, PrintValueStatement)):
            self._analyze_expression(statement.value, state)
        elif isinstance(statement, ReturnStatement):
            self._analyze_expression(statement.value, state)
            return _FlowResult(normal=False, returned=True)
        elif isinstance(statement, ExitStatement):
            return _FlowResult(normal=False, exited=True)
        elif isinstance(statement, LoopExitStatement):
            return _FlowResult(normal=False, broken=True)
        elif isinstance(statement, IncrementStatement):
            self._analyze_expression(statement.amount, state)
            binding = state.lookup(statement.name)
            if binding is not None:
                symbol, _ = binding
                symbol.constant = _UNKNOWN_CONSTANT
                symbol.reassigned = True
                self._event(statement.name, "reassigned")
                self._forget_condition_facts(statement.name)
        elif isinstance(statement, IfStatement):
            self._analyze_expression(statement.condition, state)
            condition = self._condition_truth(statement.condition, state)
            if isinstance(condition, bool):
                selected = statement.body if condition else statement.else_body
                skipped = statement.else_body if condition else statement.body
                if skipped is not None:
                    self._record("A020", Severity.WARNING, "Ta gałąź nigdy się nie wykona przy znanym warunku.", skipped)
                if selected is None:
                    return _FlowResult()
                original_facts = self._condition_facts
                self._condition_facts = original_facts + self._facts_for(statement.condition, condition, state)
                try:
                    return self._analyze_block(selected, state)
                finally:
                    self._condition_facts = original_facts
            then_state = state.clone()
            original_facts = self._condition_facts
            self._condition_facts = original_facts + self._facts_for(statement.condition, True, then_state)
            try:
                then_result = self._analyze_block(statement.body, then_state)
            finally:
                self._condition_facts = original_facts
            else_state = state.clone()
            self._condition_facts = original_facts + self._facts_for(statement.condition, False, else_state)
            try:
                else_result = self._analyze_block(statement.else_body, else_state) if statement.else_body is not None else _FlowResult()
            finally:
                self._condition_facts = original_facts
            paths = []
            if then_result.normal:
                paths.append(then_state)
            if else_result.normal:
                paths.append(else_state)
            if paths:
                state.merge_from(paths)
            return _FlowResult(
                normal=then_result.normal or else_result.normal,
                returned=then_result.returned or else_result.returned,
                broken=then_result.broken or else_result.broken,
                exited=then_result.exited or else_result.exited,
            )
        elif isinstance(statement, WhileStatement):
            self._analyze_expression(statement.condition, state)
            condition = self._condition_truth(statement.condition, state)
            if condition is False:
                self._record("A020", Severity.WARNING, "Pętla nigdy się nie wykona przy znanym warunku.", statement.body)
                return _FlowResult()
            before = state.clone()
            body_state = state.clone()
            original_facts = self._condition_facts
            self._condition_facts = original_facts + self._facts_for(statement.condition, True, body_state)
            try:
                body_result = self._analyze_block(statement.body, body_state)
            finally:
                self._condition_facts = original_facts
            if condition is True:
                if body_result.broken:
                    state.merge_from([body_state])
                return _FlowResult(
                    normal=body_result.broken,
                    returned=body_result.returned,
                    exited=body_result.exited,
                )
            state.merge_from([before, body_state])
            return _FlowResult()
        elif isinstance(statement, TryStatement):
            before = state.clone()
            body_state = state.clone()
            body_result = self._analyze_block(statement.body, body_state)
            paths = [body_state]
            outcomes = [body_result]
            if statement.catch_body is not None:
                catch_state = before.clone()
                if statement.catch_name:
                    catch_state.define(statement.catch_name, "variable", statement.line, statement.column)
                catch_result = self._analyze_block(statement.catch_body, catch_state)
                paths.append(catch_state)
                outcomes.append(catch_result)
            state.merge_from(paths)
            if statement.finally_body is not None:
                final_result = self._analyze_block(statement.finally_body, state)
                if not final_result.normal:
                    return final_result
            return _FlowResult(
                normal=any(result.normal for result in outcomes),
                returned=any(result.returned for result in outcomes),
                broken=any(result.broken for result in outcomes),
                exited=any(result.exited for result in outcomes),
            )
        elif isinstance(statement, ThrowStatement):
            self._analyze_expression(statement.value, state)
        elif isinstance(statement, AssertStatement):
            self._analyze_expression(statement.condition, state)
        elif isinstance(statement, ExpectErrorStatement):
            self._analyze_block(statement.body, state)
        elif isinstance(statement, AppendStatement):
            self._analyze_expression(statement.list_expression, state)
            self._analyze_expression(statement.value, state)
            self._invalidate_expression(statement.list_expression, state)
        elif isinstance(statement, DeleteMapEntryStatement):
            self._analyze_expression(statement.map_expression, state)
            self._analyze_expression(statement.key, state)
            self._invalidate_expression(statement.map_expression, state)
        elif isinstance(statement, SetListElementStatement):
            self._analyze_expression(statement.target, state)
            self._analyze_expression(statement.value, state)
            self._invalidate_expression(statement.target, state)
        return _FlowResult()

    def _analyze_expression(self, expression, state):
        if isinstance(expression, VariableExpression):
            binding = state.lookup(expression.name)
            if binding is None:
                self._event(expression.name, "unavailable")
                self.variable_uses.append((expression, "unavailable"))
                return
            symbol, owner = binding
            if symbol.availability == "maybe":
                fallback = owner.parent.lookup(expression.name) if owner.parent is not None else None
                if fallback is None or fallback[0].availability != "definite":
                    self._maybe_uses.append(expression)
                    self._event(expression.name, "possibly_defined")
                    self.variable_uses.append((expression, "maybe"))
                    return
            self.variable_uses.append((expression, "definite"))
        elif isinstance(expression, BinaryExpression):
            self._analyze_expression(expression.left, state)
            self._analyze_expression(expression.right, state)
        elif isinstance(expression, UnaryExpression):
            self._analyze_expression(expression.operand, state)
        elif isinstance(expression, CallExpression):
            self._analyze_expression(expression.callee, state)
            for argument in expression.arguments:
                self._analyze_expression(argument, state)
            if self._current_function is not None:
                name = self._called_function_name(expression.callee)
                if name in self._function_nodes:
                    self.function_calls.setdefault(self._current_function, set()).add(name)
            else:
                name = self._called_function_name(expression.callee)
                if name in self._function_nodes:
                    self._top_level_calls.add(name)
            self._invalidate_call_effects(state, expression.callee)
        elif isinstance(expression, ListLiteral):
            for item in expression.elements:
                self._analyze_expression(item, state)
        elif isinstance(expression, MapLiteral):
            for key, value in expression.entries:
                self._analyze_expression(key, state)
                self._analyze_expression(value, state)
        elif isinstance(expression, MemberExpression):
            self._analyze_expression(expression.object, state)
        elif isinstance(expression, IndexExpression):
            self._analyze_expression(expression.collection, state)
            self._analyze_expression(expression.index, state)
        elif isinstance(expression, SliceExpression):
            self._analyze_expression(expression.collection, state)
            self._analyze_expression(expression.start, state)
            self._analyze_expression(expression.stop, state)
        elif isinstance(expression, PopListExpression):
            self._analyze_expression(expression.list_expression, state)
            self._invalidate_expression(expression.list_expression, state)

    def _invalidate_expression(self, expression, state):
        if isinstance(expression, VariableExpression):
            binding = state.lookup(expression.name)
            if binding is not None:
                symbol, _ = binding
                symbol.constant = _UNKNOWN_CONSTANT
                symbol.mutated = True
                self._event(expression.name, "mutated")
                self._forget_condition_facts(expression.name)

    def _invalidate_call_effects(self, state, callee):
        name = self._called_function_name(callee)
        if name is None or name not in self._function_nodes or self.function_effects.get(name) != "pure":
            scope = state
            while scope is not None:
                for symbol in scope.symbols.values():
                    symbol.constant = _UNKNOWN_CONSTANT
                scope = scope.parent
            self._condition_facts = []

    def _called_function_name(self, callee):
        if isinstance(callee, VariableExpression):
            return callee.name
        return None

    def _constant(self, expression, state):
        if isinstance(expression, (NumberLiteral, StringLiteral, BooleanLiteral)):
            return expression.value
        if isinstance(expression, VariableExpression):
            binding = state.lookup(expression.name)
            if binding is None or binding[0].availability != "definite":
                return _UNKNOWN_CONSTANT
            return binding[0].constant
        if isinstance(expression, UnaryExpression):
            value = self._constant(expression.operand, state)
            if expression.operator == "nie" and isinstance(value, bool):
                return not value
            if expression.operator == "-" and isinstance(value, (int, float)) and not isinstance(value, bool):
                return -value
        if isinstance(expression, BinaryExpression):
            left = self._constant(expression.left, state)
            right = self._constant(expression.right, state)
            if left is _UNKNOWN_CONSTANT or right is _UNKNOWN_CONSTANT:
                return _UNKNOWN_CONSTANT
            try:
                if expression.operator == "+" and type(left) is type(right) and type(left) in {int, float, str}:
                    return left + right
                if expression.operator == "-" and type(left) in {int, float} and type(right) in {int, float}:
                    return left - right
                if expression.operator == "*" and type(left) in {int, float} and type(right) in {int, float}:
                    return left * right
                if expression.operator == "/" and type(left) in {int, float} and type(right) in {int, float} and right != 0:
                    return left / right
                if expression.operator in {"==", "!="}:
                    equal = type(left) is type(right) and left == right
                    return equal if expression.operator == "==" else not equal
                if expression.operator in {"<", "<=", ">", ">="} and type(left) in {int, float} and type(right) in {int, float}:
                    return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[expression.operator]
                if expression.operator == "i" and isinstance(left, bool) and isinstance(right, bool):
                    return left and right
                if expression.operator == "albo" and isinstance(left, bool) and isinstance(right, bool):
                    return left or right
            except (ArithmeticError, TypeError, ValueError):
                return _UNKNOWN_CONSTANT
        return _UNKNOWN_CONSTANT

    def _condition_truth(self, expression, state):
        value = self._constant(expression, state)
        if isinstance(value, bool):
            return value
        if isinstance(expression, UnaryExpression) and expression.operator == "nie":
            nested = self._condition_truth(expression.operand, state)
            return not nested if isinstance(nested, bool) else None
        if isinstance(expression, BinaryExpression) and expression.operator in {"i", "albo"}:
            left = self._condition_truth(expression.left, state)
            right = self._condition_truth(expression.right, state)
            if expression.operator == "i":
                if left is False or right is False:
                    return False
                if left is True and right is True:
                    return True
            else:
                if left is True or right is True:
                    return True
                if left is False and right is False:
                    return False
            return None
        atom = self._comparison_fact(expression, state)
        if atom is None:
            return None
        if not self._facts_satisfiable(self._condition_facts + [atom]):
            return False
        inverse = (atom[0], self._invert_operator(atom[1]), atom[2])
        if not self._facts_satisfiable(self._condition_facts + [inverse]):
            return True
        return None

    def _comparison_fact(self, expression, state):
        if not isinstance(expression, BinaryExpression) or expression.operator not in {"==", "!=", "<", "<=", ">", ">="}:
            return None
        if isinstance(expression.left, VariableExpression):
            variable = expression.left.name
            value = self._literal_value(expression.right)
            operator = expression.operator
        elif isinstance(expression.right, VariableExpression):
            variable = expression.right.name
            value = self._literal_value(expression.left)
            operator = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "==", "!=": "!="}[expression.operator]
        else:
            return None
        if value is _UNKNOWN_CONSTANT:
            return None
        resolved = state.lookup(variable)
        if resolved is None or resolved[0].availability != "definite":
            return None
        if operator in {"<", "<=", ">", ">="} and (type(value) not in {int, float}):
            return None
        return variable, operator, value

    def _literal_value(self, expression):
        if isinstance(expression, (NumberLiteral, StringLiteral, BooleanLiteral)):
            return expression.value
        if isinstance(expression, UnaryExpression) and expression.operator == "-":
            value = self._literal_value(expression.operand)
            if type(value) in {int, float}:
                return -value
        return _UNKNOWN_CONSTANT

    def _facts_for(self, expression, truth, state):
        if isinstance(expression, UnaryExpression) and expression.operator == "nie":
            return self._facts_for(expression.operand, not truth, state)
        if isinstance(expression, BinaryExpression) and expression.operator == "i" and truth:
            return self._facts_for(expression.left, True, state) + self._facts_for(expression.right, True, state)
        if isinstance(expression, BinaryExpression) and expression.operator == "albo" and not truth:
            return self._facts_for(expression.left, False, state) + self._facts_for(expression.right, False, state)
        if isinstance(expression, BinaryExpression) and expression.operator in {"i", "albo"}:
            return []
        atom = self._comparison_fact(expression, state)
        if atom is None:
            return []
        if not truth:
            atom = (atom[0], self._invert_operator(atom[1]), atom[2])
        return [atom]

    def _invert_operator(self, operator):
        return {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}[operator]

    def _facts_satisfiable(self, facts):
        grouped: dict[str, list[tuple[str, object]]] = {}
        for name, operator, value in facts:
            grouped.setdefault(name, []).append((operator, value))
        for constraints in grouped.values():
            equalities = [value for operator, value in constraints if operator == "=="]
            excluded = [value for operator, value in constraints if operator == "!="]
            if equalities and any(not self._same_literal(equalities[0], value) for value in equalities[1:]):
                return False
            if equalities and any(self._same_literal(equalities[0], value) for value in excluded):
                return False
            lower = None
            upper = None
            for operator, value in constraints:
                if operator in {">", ">="}:
                    candidate = (value, operator == ">=")
                    if lower is None or value > lower[0] or (value == lower[0] and not candidate[1]):
                        lower = candidate
                elif operator in {"<", "<="}:
                    candidate = (value, operator == "<=")
                    if upper is None or value < upper[0] or (value == upper[0] and not candidate[1]):
                        upper = candidate
            if lower is not None and upper is not None:
                if lower[0] > upper[0] or (lower[0] == upper[0] and not (lower[1] and upper[1])):
                    return False
                if lower[0] == upper[0] and any(self._same_literal(lower[0], value) for value in excluded):
                    return False
            if equalities and lower is not None:
                value = equalities[0]
                if type(value) in {int, float} and (value < lower[0] or (value == lower[0] and not lower[1])):
                    return False
            if equalities and upper is not None:
                value = equalities[0]
                if type(value) in {int, float} and (value > upper[0] or (value == upper[0] and not upper[1])):
                    return False
        return True

    def _same_literal(self, left, right):
        return type(left) is type(right) and left == right

    def _forget_condition_facts(self, name):
        self._condition_facts = [fact for fact in self._condition_facts if fact[0] != name]

    def _summarize_functions(self):
        graph: dict[str, set[str]] = {}
        effects: dict[str, str] = {}
        for name, declaration in self._function_nodes.items():
            calls: set[str] = set()
            effect = self._block_effect(declaration.body, calls)
            graph[name] = calls
            effects[name] = effect
        if self._top_level_calls:
            graph["<program>"] = set(self._top_level_calls)
            effects["<program>"] = "unknown"
        self.function_calls = graph
        self.function_effects = effects
        for name in graph:
            if self._reaches(name, name, graph, set(), first=True):
                self.recursive_functions.add(name)
        changed = True
        while changed:
            changed = False
            for name, calls in graph.items():
                effect = effects[name]
                for called in calls:
                    called_effect = effects.get(called, "unknown")
                    effect = self._combine_effects(effect, called_effect)
                if effect != effects[name]:
                    effects[name] = effect
                    changed = True
        self.function_effects = effects

    def _reaches(self, start, target, graph, visited, first=False):
        for neighbor in graph.get(start, set()):
            if neighbor == target:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                if self._reaches(neighbor, target, graph, visited):
                    return True
        return False

    def _block_effect(self, block, calls):
        effect = "pure"
        for statement in block.statements:
            effect = self._combine_effects(effect, self._statement_effect(statement, calls))
        return effect

    def _statement_effect(self, statement, calls):
        if isinstance(statement, (AppendStatement, DeleteMapEntryStatement, SetListElementStatement, IncrementStatement)):
            return "mutation"
        if isinstance(statement, FunctionDeclaration):
            return "pure"
        expressions = []
        if isinstance(statement, VariableDeclaration):
            expressions.append(statement.value)
        elif isinstance(statement, (ExpressionStatement, ReturnStatement, ThrowStatement, PrintTextStatement, PrintValueStatement)):
            expressions.append(statement.expression if isinstance(statement, ExpressionStatement) else statement.value)
        elif isinstance(statement, IfStatement):
            expressions.append(statement.condition)
            return self._combine_effects(self._expression_effects(expressions, calls), self._combine_effects(self._block_effect(statement.body, calls), self._block_effect(statement.else_body, calls) if statement.else_body else "pure"))
        elif isinstance(statement, WhileStatement):
            expressions.append(statement.condition)
            return self._combine_effects(self._expression_effects(expressions, calls), self._block_effect(statement.body, calls))
        elif isinstance(statement, TryStatement):
            effect = self._block_effect(statement.body, calls)
            if statement.catch_body:
                effect = self._combine_effects(effect, self._block_effect(statement.catch_body, calls))
            if statement.finally_body:
                effect = self._combine_effects(effect, self._block_effect(statement.finally_body, calls))
            return effect
        elif isinstance(statement, ImportStatement):
            return "unknown"
        return self._expression_effects(expressions, calls)

    def _expression_effects(self, expressions, calls):
        effect = "pure"
        for expression in expressions:
            if isinstance(expression, CallExpression):
                name = self._called_function_name(expression.callee)
                if name in self._function_nodes:
                    calls.add(name)
                elif isinstance(expression.callee, MemberExpression):
                    root = expression.callee.object
                    while isinstance(root, MemberExpression):
                        root = root.object
                    category = "external" if isinstance(root, VariableExpression) and root.name in self._EXTERNAL_MODULES else "unknown"
                    effect = self._combine_effects(effect, category)
                else:
                    effect = self._combine_effects(effect, "unknown")
                effect = self._combine_effects(effect, self._expression_effects(expression.arguments, calls))
            elif isinstance(expression, BinaryExpression):
                effect = self._combine_effects(effect, self._expression_effects([expression.left, expression.right], calls))
            elif isinstance(expression, UnaryExpression):
                effect = self._combine_effects(effect, self._expression_effects([expression.operand], calls))
            elif isinstance(expression, (ListLiteral, MapLiteral)):
                children = expression.elements if isinstance(expression, ListLiteral) else [item for pair in expression.entries for item in pair]
                effect = self._combine_effects(effect, self._expression_effects(children, calls))
            elif isinstance(expression, (MemberExpression, IndexExpression, SliceExpression, PopListExpression)):
                children = [expression.object] if isinstance(expression, MemberExpression) else [expression.collection, expression.index] if isinstance(expression, IndexExpression) else [expression.collection, expression.start, expression.stop] if isinstance(expression, SliceExpression) else [expression.list_expression]
                effect = self._combine_effects(effect, self._expression_effects(children, calls))
                if isinstance(expression, PopListExpression):
                    effect = self._combine_effects(effect, "mutation")
        return effect

    def _combine_effects(self, left, right):
        order = {"pure": 0, "mutation": 1, "external": 2, "unknown": 3}
        return left if order[left] >= order[right] else right


class _StaticModuleAnalysis:
    """Parse local imports and metadata without constructing a runtime module."""

    _STANDARD_MODULES = {"matematyka", "losuj", "tekst", "czas", "system", "plik", "katalog", "sciezka", "dane", "siec"}

    def __init__(self, file: str | None):
        self.file = file
        self.diagnostics: list[Diagnostic] = []
        self._programs: dict[Path, Program | None] = {}
        self._exports: dict[Path, set[str]] = {}
        self._checked_metadata: set[Path] = set()
        self._cycle_edges: set[tuple[Path, Path]] = set()
        self._analyzed: set[Path] = set()

    def analyze(self, program: Program, source_path: str | None) -> list[Diagnostic]:
        if not source_path:
            return self.diagnostics
        path = Path(source_path).resolve()
        self._analyze_program(program, path, [])
        return self.diagnostics

    def _record(self, code, message, node, path=None):
        self.diagnostics.append(Diagnostic(
            code=code,
            severity=Severity.ERROR if code in {"A040", "A041", "A042", "A043"} else Severity.WARNING,
            message=message,
            file=str(path or self.file) if (path or self.file) else None,
            line=getattr(node, "line", 1),
            column=getattr(node, "column", 1),
        ))

    def _resolve(self, module_name: str, importer: Path) -> Path | None:
        try:
            try:
                from .interpreter import ModuleLoader
            except ImportError:  # pragma: no cover - direct script compatibility
                from interpreter import ModuleLoader
            candidate = ModuleLoader._resolve(module_name, importer)
            if candidate.is_file():
                return candidate.resolve()
            if ModuleLoader._standard_name(module_name) is not None:
                return None
        except Exception:
            return None
        return None

    def _parse_module(self, path: Path) -> Program | None:
        resolved = path.resolve()
        if resolved in self._programs:
            return self._programs[resolved]
        try:
            source = resolved.read_text(encoding="utf-8")
            program = Parser(Lexer(source).tokenize()).parse_module()
        except (OSError, LexerError, ParserError) as error:
            self._programs[resolved] = None
            self.diagnostics.append(Diagnostic(
                code="K000",
                severity=Severity.ERROR,
                message=f"Błąd składni modułu: {error}",
                file=str(resolved),
                line=1,
                column=1,
            ))
            return None
        self._programs[resolved] = program
        self._exports[resolved] = self._module_symbols(program.body, resolved)
        return program

    def _module_symbols(self, block: Block, importer: Path) -> set[str]:
        symbols: set[str] = set()
        for statement in block.statements:
            if isinstance(statement, (VariableDeclaration, FunctionDeclaration)):
                symbols.add(statement.name)
            elif isinstance(statement, ImportStatement):
                resolved = self._resolve(statement.module_name, importer)
                symbols.add(resolved.stem if resolved is not None else Path(statement.module_name).stem)
            elif isinstance(statement, IfStatement):
                symbols.update(self._module_symbols(statement.body, importer))
                if statement.else_body is not None:
                    symbols.update(self._module_symbols(statement.else_body, importer))
            elif isinstance(statement, WhileStatement):
                symbols.update(self._module_symbols(statement.body, importer))
            elif isinstance(statement, TryStatement):
                symbols.update(self._module_symbols(statement.body, importer))
                if statement.catch_body is not None:
                    symbols.update(self._module_symbols(statement.catch_body, importer))
                if statement.finally_body is not None:
                    symbols.update(self._module_symbols(statement.finally_body, importer))
        return symbols

    def _analyze_program(self, program: Program, path: Path, stack: list[Path]) -> set[str]:
        current = path.resolve()
        if current in self._analyzed and current not in stack:
            return self._exports.get(current, set())
        self._analyzed.add(current)
        if current not in self._exports:
            self._exports[current] = self._module_symbols(program.body, current)
            self._programs[current] = program
        self._check_package_metadata(current, program)
        self._check_duplicate_functions(program.body, current)
        aliases: dict[str, tuple[Path, set[str] | None]] = {}
        imports = self._all_imports(program.body)
        for statement in imports:
            resolved = self._resolve(statement.module_name, current)
            if resolved is None:
                if self._is_known_standard(statement.module_name):
                    continue
                if self._definitely_invalid_module(statement.module_name):
                    self._record("A040", f'Import wskazuje niedozwolone rozszerzenie dla modułu "{statement.module_name}".', statement, current)
                continue
            if resolved in stack or resolved == current:
                edge = (current, resolved)
                if edge not in self._cycle_edges:
                    self._cycle_edges.add(edge)
                    chain = " -> ".join(item.stem for item in stack + [current, resolved])
                    self._record("A041", f"Wykryto cykliczny import modułów: {chain}.", statement, current)
                exports = self._exports.get(resolved)
            else:
                module_program = self._parse_module(resolved)
                if module_program is None:
                    continue
                exports = self._exports.get(resolved, set())
                if resolved not in self._analyzed:
                    imported_linter = Linter()
                    imported_linter._analyze_program(module_program, str(resolved))
                    imported_linter.diagnostics.extend(TypeAnalyzer().analyze_program(module_program, str(resolved)))
                    imported_flow = _ProgramFlowAnalysis(str(resolved))
                    imported_linter.diagnostics.extend(imported_flow.analyze(module_program))
                    self.diagnostics.extend(imported_linter.diagnostics)
                self._analyze_program(module_program, resolved, stack + [current])
            aliases[resolved.stem] = (resolved, exports)
        self._check_member_references(program.body, aliases, current, self._declared_names(program.body))
        return self._exports.get(current, set())

    def _all_imports(self, block: Block) -> list[ImportStatement]:
        found = []
        for statement in block.statements:
            if isinstance(statement, ImportStatement):
                found.append(statement)
            elif isinstance(statement, IfStatement):
                found.extend(self._all_imports(statement.body))
                if statement.else_body is not None:
                    found.extend(self._all_imports(statement.else_body))
            elif isinstance(statement, WhileStatement):
                found.extend(self._all_imports(statement.body))
            elif isinstance(statement, TryStatement):
                found.extend(self._all_imports(statement.body))
                if statement.catch_body is not None:
                    found.extend(self._all_imports(statement.catch_body))
                if statement.finally_body is not None:
                    found.extend(self._all_imports(statement.finally_body))
        return found

    def _check_member_references(self, block: Block, aliases, path, hidden_names):
        def inspect_expression(expression):
            if isinstance(expression, MemberExpression):
                if (
                    isinstance(expression.object, VariableExpression)
                    and expression.object.name in aliases
                    and expression.object.name not in hidden_names
                ):
                    _, exports = aliases[expression.object.name]
                    if exports is not None and expression.name not in exports:
                        self._record(
                            "A040",
                            f'Moduł "{expression.object.name}" nie udostępnia wartości "{expression.name}".',
                            expression,
                            path,
                        )
                inspect_expression(expression.object)
            elif isinstance(expression, CallExpression):
                inspect_expression(expression.callee)
                for argument in expression.arguments:
                    inspect_expression(argument)
            elif isinstance(expression, BinaryExpression):
                inspect_expression(expression.left)
                inspect_expression(expression.right)
            elif isinstance(expression, UnaryExpression):
                inspect_expression(expression.operand)
            elif isinstance(expression, ListLiteral):
                for item in expression.elements:
                    inspect_expression(item)
            elif isinstance(expression, MapLiteral):
                for key, value in expression.entries:
                    inspect_expression(key)
                    inspect_expression(value)
            elif isinstance(expression, IndexExpression):
                inspect_expression(expression.collection)
                inspect_expression(expression.index)
            elif isinstance(expression, SliceExpression):
                inspect_expression(expression.collection)
                inspect_expression(expression.start)
                inspect_expression(expression.stop)
            elif isinstance(expression, PopListExpression):
                inspect_expression(expression.list_expression)

        for statement in block.statements:
            for expression in self._statement_expressions(statement):
                inspect_expression(expression)
            if isinstance(statement, FunctionDeclaration):
                function_hidden = hidden_names | set(statement.parameters) | self._declared_names(statement.body)
                self._check_member_references(statement.body, aliases, path, function_hidden)
            elif isinstance(statement, IfStatement):
                self._check_member_references(statement.body, aliases, path, hidden_names)
                if statement.else_body is not None:
                    self._check_member_references(statement.else_body, aliases, path, hidden_names)
            elif isinstance(statement, WhileStatement):
                self._check_member_references(statement.body, aliases, path, hidden_names)
            elif isinstance(statement, TryStatement):
                self._check_member_references(statement.body, aliases, path, hidden_names)
                if statement.catch_body is not None:
                    catch_hidden = hidden_names | ({statement.catch_name} if statement.catch_name else set())
                    self._check_member_references(statement.catch_body, aliases, path, catch_hidden)
                if statement.finally_body is not None:
                    self._check_member_references(statement.finally_body, aliases, path, hidden_names)

    def _declared_names(self, block: Block) -> set[str]:
        names = set()
        for statement in block.statements:
            if isinstance(statement, (VariableDeclaration, FunctionDeclaration)):
                names.add(statement.name)
            elif isinstance(statement, IfStatement):
                names.update(self._declared_names(statement.body))
                if statement.else_body is not None:
                    names.update(self._declared_names(statement.else_body))
            elif isinstance(statement, WhileStatement):
                names.update(self._declared_names(statement.body))
            elif isinstance(statement, TryStatement):
                names.update(self._declared_names(statement.body))
                if statement.catch_body is not None:
                    names.update(self._declared_names(statement.catch_body))
                if statement.finally_body is not None:
                    names.update(self._declared_names(statement.finally_body))
        return names

    def _statement_expressions(self, statement):
        if isinstance(statement, VariableDeclaration):
            return [statement.value]
        if isinstance(statement, ExpressionStatement):
            return [statement.expression]
        if isinstance(statement, (ReturnStatement, ThrowStatement, PrintTextStatement, PrintValueStatement)):
            return [statement.value]
        if isinstance(statement, IfStatement):
            return [statement.condition]
        if isinstance(statement, WhileStatement):
            return [statement.condition]
        if isinstance(statement, AssertStatement):
            return [statement.condition]
        if isinstance(statement, AppendStatement):
            return [statement.list_expression, statement.value]
        if isinstance(statement, DeleteMapEntryStatement):
            return [statement.map_expression, statement.key]
        if isinstance(statement, SetListElementStatement):
            return [statement.target, statement.value]
        return []

    def _is_known_standard(self, module_name):
        name = Path(module_name).name.removesuffix(".kurwa")
        return name in self._STANDARD_MODULES and "/" not in module_name and "\\" not in module_name

    def _definitely_invalid_module(self, module_name):
        return "." in Path(module_name).name and not module_name.endswith(".kurwa")

    def _check_duplicate_functions(self, block: Block, path: Path):
        names = set()
        for statement in block.statements:
            if isinstance(statement, FunctionDeclaration):
                if statement.name in names:
                    self._record("A043", f'Funkcja "{statement.name}" ma konfliktującą deklarację w tym samym zakresie.', statement, path)
                names.add(statement.name)

    def _check_package_metadata(self, source_path: Path, node):
        manifest_path = next(
            (parent / "kurwa.pack" for parent in (source_path.parent, *source_path.parents) if (parent / "kurwa.pack").is_file()),
            None,
        )
        if manifest_path is None:
            return
        if not manifest_path.is_file() or manifest_path in self._checked_metadata:
            return
        self._checked_metadata.add(manifest_path)
        try:
            try:
                from .package_manager import ProjectPackageManager
            except ImportError:  # pragma: no cover - direct script compatibility
                from package_manager import ProjectPackageManager
            manager = ProjectPackageManager(manifest_path.parent)
            manifest = manager._parse_manifest_file(manifest_path)
            lock_path = manifest_path.parent / "kurwa.lock"
            if not lock_path.is_file():
                return
            try:
                lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return
            if not isinstance(lock_data, dict):
                return
            for dependency, requirement in manifest.dependencies.items():
                locked = lock_data.get(dependency)
                if not isinstance(locked, str):
                    continue
                try:
                    matches = manager._satisfies(locked, requirement)
                except Exception:
                    continue
                if not matches:
                    self._record(
                        "A042",
                        f'Wersja zależności "{dependency}" w blokadzie nie spełnia wymogu z kurwa.pack.',
                        node,
                        manifest_path,
                    )
        except Exception:
            return


class Linter:
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []

    def lint_source(self, source: str, file_name: str | None = None) -> list[Diagnostic]:
        self.diagnostics = []
        try:
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse_module()
        except (LexerError, ParserError) as error:
            self.diagnostics.append(
                Diagnostic(
                    code="K000",
                    severity=Severity.ERROR,
                    message=f"Błąd składni: {error}",
                    file=file_name,
                    line=1,
                    column=1,
                )
            )
            return self.diagnostics
        self._analyze_program(program, file_name)
        self.diagnostics.extend(TypeAnalyzer().analyze_program(program, file_name))
        flow_analysis = _ProgramFlowAnalysis(file_name)
        flow_diagnostics = flow_analysis.analyze(program)
        flow_use_states = {
            (expression.name, expression.line, expression.column): availability
            for expression, availability in flow_analysis.variable_uses
        }
        self.diagnostics = [
            item for item in self.diagnostics
            if not (
                item.code == "K010"
                and any(
                    item.line == line
                    and item.column == column
                    and f'Zmienna "{name}"' in item.message
                    and availability in {"maybe", "definite"}
                    for (name, line, column), availability in flow_use_states.items()
                )
            )
        ]
        reported_undefined = {
            (name, item.line, item.column)
            for item in self.diagnostics
            if item.code == "K010"
            for name in [item.message.split('"', 2)[1] if '"' in item.message else ""]
        }
        for (name, line, column), availability in flow_use_states.items():
            if availability == "unavailable" and (name, line, column) not in reported_undefined:
                self.diagnostics.append(Diagnostic(
                    code="K010",
                    severity=Severity.ERROR,
                    message=f'Zmienna "{name}" nie została zdefiniowana w bieżącym zakresie.',
                    file=file_name,
                    line=line,
                    column=column,
                ))
        self.diagnostics.extend(flow_diagnostics)
        if file_name is not None:
            module_analysis = _StaticModuleAnalysis(file_name)
            self.diagnostics.extend(module_analysis.analyze(program, file_name))
        return self.diagnostics

    def lint_file(self, path: str | Path) -> list[Diagnostic]:
        file_path = Path(path)
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError as error:
            return [
                Diagnostic(
                    code="K000",
                    severity=Severity.ERROR,
                    message=f"Nie można odczytać pliku: {error}",
                    file=str(file_path),
                    line=1,
                    column=1,
                )
            ]
        return self.lint_source(source, str(file_path))

    def _record(self, code: str, severity: Severity, message: str, node=None, file: str | None = None) -> None:
        self.diagnostics.append(
            Diagnostic(
                code=code,
                severity=severity,
                message=message,
                file=file,
                line=getattr(node, "line", 1),
                column=getattr(node, "column", 1),
            )
        )

    def _analyze_program(self, program: Program, file: str | None) -> None:
        if not isinstance(program, Program):
            return
        global_scope = Scope()
        self._analyze_block(program.body, global_scope, file)
        global_scope.collect_unused(self.diagnostics, file)

    def _analyze_block(self, block: Block, scope: Scope, file: str | None, in_function: bool = False) -> None:
        seen_unconditional_exit = False
        for statement in block.statements:
            if seen_unconditional_exit:
                if isinstance(statement, (ReturnStatement, ExitStatement)):
                    self._record("K020", Severity.WARNING, "Kod po nieodwracalnym zakończeniu jest nieosiągalny.", statement, file)
                else:
                    self._record("K020", Severity.WARNING, "Kod po punktach wyjścia jest nieosiągalny.", statement, file)
            if isinstance(statement, VariableDeclaration):
                scope.define(statement.name, "variable", self._line_of(statement), self._column_of(statement))
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, FunctionDeclaration):
                scope.define(statement.name, "function", self._line_of(statement), self._column_of(statement))
                func_scope = Scope(scope)
                for parameter in statement.parameters:
                    func_scope.define(parameter, "parameter", self._line_of(statement), self._column_of(statement))
                self._analyze_block(statement.body, func_scope, file, in_function=True)
                func_scope.collect_unused(self.diagnostics, file)
            elif isinstance(statement, ImportStatement):
                self._check_duplicate_import(statement, scope, file)
            elif isinstance(statement, ExpressionStatement):
                self._analyze_expression(statement.expression, scope, file)
            elif isinstance(statement, ReturnStatement):
                self._analyze_expression(statement.value, scope, file)
                seen_unconditional_exit = True
            elif isinstance(statement, IfStatement):
                self._analyze_expression(statement.condition, scope, file)
                self._constant_condition(statement.condition, statement, file)
                then_scope = scope.clone()
                self._analyze_block(statement.body, then_scope, file)
                branch_scopes = [then_scope]
                if statement.else_body is not None:
                    else_scope = scope.clone()
                    self._analyze_block(statement.else_body, else_scope, file)
                    branch_scopes.append(else_scope)
                else:
                    branch_scopes.append(scope.clone())
                scope.merge_from(branch_scopes)
            elif isinstance(statement, WhileStatement):
                self._analyze_expression(statement.condition, scope, file)
                self._constant_condition(statement.condition, statement, file)
                body_scope = scope.clone()
                self._analyze_block(statement.body, body_scope, file)
                scope.merge_from([scope.clone(), body_scope])
            elif isinstance(statement, TryStatement):
                body_scope = scope.clone()
                self._analyze_block(statement.body, body_scope, file)
                branch_scopes = [body_scope]
                if statement.catch_body is not None:
                    catch_scope = scope.clone()
                    if statement.catch_name is not None:
                        catch_scope.define(statement.catch_name, "variable", self._line_of(statement), self._column_of(statement))
                    self._analyze_block(statement.catch_body, catch_scope, file)
                    branch_scopes.append(catch_scope)
                if statement.finally_body is not None:
                    for branch_scope in branch_scopes:
                        self._analyze_block(statement.finally_body, branch_scope, file)
                scope.merge_from(branch_scopes)
            elif isinstance(statement, ThrowStatement):
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, AssertStatement):
                self._analyze_expression(statement.condition, scope, file)
                self._constant_condition(statement.condition, statement, file)
            elif isinstance(statement, ExpectErrorStatement):
                self._analyze_block(statement.body, scope, file)
            elif isinstance(statement, SkipStatement):
                continue
            elif isinstance(statement, AppendStatement):
                self._analyze_expression(statement.list_expression, scope, file)
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, DeleteMapEntryStatement):
                self._analyze_expression(statement.map_expression, scope, file)
                self._analyze_expression(statement.key, scope, file)
            elif isinstance(statement, SetListElementStatement):
                self._analyze_expression(statement.target, scope, file)
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, PrintTextStatement):
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, PrintValueStatement):
                self._analyze_expression(statement.value, scope, file)
            elif isinstance(statement, ExitStatement):
                seen_unconditional_exit = True
            elif isinstance(statement, LoopExitStatement):
                seen_unconditional_exit = True
            elif isinstance(statement, (CallExpression, BinaryExpression, UnaryExpression, VariableExpression)):
                self._analyze_expression(statement, scope, file)

    def _check_duplicate_import(self, statement: ImportStatement, scope: Scope, file: str | None) -> None:
        if scope.resolve(statement.module_name) is not None:
            self._record("K060", Severity.WARNING, f'Import "{statement.module_name}" jest duplikowany.', statement, file)
        else:
            scope.define(statement.module_name, "import", self._line_of(statement), self._column_of(statement))

    def _analyze_expression(self, expression: Expression, scope: Scope, file: str | None) -> None:
        if expression is None:
            return
        if isinstance(expression, VariableExpression):
            symbol = scope.resolve(expression.name)
            if symbol is None:
                self._record("K010", Severity.ERROR, f'Zmienna "{expression.name}" nie została zdefiniowana w bieżącym zakresie.', expression, file)
            return
        if isinstance(expression, BinaryExpression):
            self._analyze_expression(expression.left, scope, file)
            self._analyze_expression(expression.right, scope, file)
            if expression.operator == "/":
                zero = self._constant_value(expression.right)
                if zero == 0:
                    self._record("K040", Severity.ERROR, "Wykryto statyczne dzielenie przez zero.", expression, file)
            if expression.operator in {"==", "!="}:
                self._check_constant_equality(expression, file)
            return
        if isinstance(expression, UnaryExpression):
            self._analyze_expression(expression.operand, scope, file)
            if expression.operator == "nie":
                constant = self._constant_value(expression.operand)
                if isinstance(constant, bool):
                    self._record("K030", Severity.WARNING, "Wyrażenie logiczne jest statycznie stałe.", expression, file)
            return
        if isinstance(expression, CallExpression):
            self._analyze_expression(expression.callee, scope, file)
            for argument in expression.arguments:
                self._analyze_expression(argument, scope, file)
            return
        if isinstance(expression, ListLiteral):
            for element in expression.elements:
                self._analyze_expression(element, scope, file)
            return
        if isinstance(expression, MapLiteral):
            seen_keys: set[str] = set()
            for key_expression, value_expression in expression.entries:
                self._analyze_expression(key_expression, scope, file)
                self._analyze_expression(value_expression, scope, file)
                if isinstance(key_expression, StringLiteral):
                    if key_expression.value in seen_keys:
                        self._record("K050", Severity.ERROR, f'Duplikat klucza mapy "{key_expression.value}".', key_expression, file)
                    seen_keys.add(key_expression.value)
            return
        if isinstance(expression, MemberExpression):
            self._analyze_expression(expression.object, scope, file)
            return
        if isinstance(expression, IndexExpression):
            self._analyze_expression(expression.collection, scope, file)
            self._analyze_expression(expression.index, scope, file)
            return
        if isinstance(expression, SliceExpression):
            self._analyze_expression(expression.collection, scope, file)
            self._analyze_expression(expression.start, scope, file)
            self._analyze_expression(expression.stop, scope, file)
            return
        if isinstance(expression, PopListExpression):
            self._analyze_expression(expression.list_expression, scope, file)
            return
        if isinstance(expression, (NumberLiteral, StringLiteral, BooleanLiteral)):
            return

    def _constant_condition(self, expression: Expression, node, file: str | None) -> None:
        value = self._constant_value(expression)
        if isinstance(value, bool):
            if value:
                self._record("K030", Severity.WARNING, "Warunek jest zawsze prawdziwy.", node, file)
            else:
                self._record("K031", Severity.WARNING, "Warunek jest zawsze fałszywy.", node, file)

    def _check_constant_equality(self, expression: BinaryExpression, file: str | None) -> None:
        left = self._constant_value(expression.left)
        right = self._constant_value(expression.right)
        if left is not None and right is not None:
            if left == right:
                if expression.operator == "==":
                    self._record("K030", Severity.WARNING, "Porównanie jest zawsze prawdziwe.", expression, file)
                else:
                    self._record("K031", Severity.WARNING, "Porównanie jest zawsze fałszywe.", expression, file)

    def _constant_value(self, expression: Expression):
        if isinstance(expression, NumberLiteral):
            return expression.value
        if isinstance(expression, BooleanLiteral):
            return expression.value
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, UnaryExpression) and expression.operator == "nie":
            value = self._constant_value(expression.operand)
            if isinstance(value, bool):
                return not value
        if isinstance(expression, BinaryExpression):
            left = self._constant_value(expression.left)
            right = self._constant_value(expression.right)
            if left is None or right is None:
                return None
            if expression.operator == "+":
                return left + right
            if expression.operator == "-":
                return left - right
            if expression.operator == "*":
                return left * right
            if expression.operator == "/":
                if right == 0:
                    return None
                return left / right
            if expression.operator == "==":
                return left == right
            if expression.operator == "!=":
                return left != right
            if expression.operator in {"<", "<=", ">", ">="}:
                if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                    return None
                return {
                    "<": left < right,
                    "<=": left <= right,
                    ">": left > right,
                    ">=": left >= right,
                }[expression.operator]
            if expression.operator == "i":
                if isinstance(left, bool) and isinstance(right, bool):
                    return left and right
            if expression.operator == "albo":
                if isinstance(left, bool) and isinstance(right, bool):
                    return left or right
        return None

    def _line_of(self, node) -> int:
        return int(getattr(node, "line", 1) or 1)

    def _column_of(self, node) -> int:
        return int(getattr(node, "column", 1) or 1)


def lint_source(source: str, file_name: str | None = None) -> list[Diagnostic]:
    return Linter().lint_source(source, file_name)


def lint_file(path: str | Path) -> list[Diagnostic]:
    return Linter().lint_file(path)
