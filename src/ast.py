"""Abstract syntax tree nodes for KURWA LANG."""

from dataclasses import dataclass


class Node:
    pass


class Statement(Node):
    pass


class Expression(Node):
    pass


@dataclass
class Program(Node):
    body: "Block"
    line: int = 1
    column: int = 1


@dataclass
class Block(Statement):
    statements: list[Statement]
    line: int = 1
    column: int = 1


@dataclass
class VariableDeclaration(Statement):
    name: str
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class FunctionDeclaration(Statement):
    name: str
    parameters: list[str]
    body: "Block"
    is_async: bool = False
    line: int = 1
    column: int = 1


@dataclass
class ExpressionStatement(Statement):
    expression: Expression
    line: int = 1
    column: int = 1


@dataclass
class ReturnStatement(Statement):
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class SetListElementStatement(Statement):
    target: Expression
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class AppendStatement(Statement):
    list_expression: Expression
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class DeleteMapEntryStatement(Statement):
    map_expression: Expression
    key: Expression
    line: int = 1
    column: int = 1


@dataclass
class ImportStatement(Statement):
    module_name: str
    line: int = 1
    column: int = 1


@dataclass
class IfStatement(Statement):
    condition: Expression
    body: Block
    else_body: Block | None = None
    line: int = 1
    column: int = 1


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Block
    line: int = 1
    column: int = 1


@dataclass
class LoopExitStatement(Statement):
    line: int = 1
    column: int = 1


@dataclass
class IncrementStatement(Statement):
    name: str
    amount: Expression
    line: int = 1
    column: int = 1


@dataclass
class PrintTextStatement(Statement):
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class PrintValueStatement(Statement):
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class ExitStatement(Statement):
    line: int = 1
    column: int = 1


@dataclass
class TryStatement(Statement):
    body: Block
    catch_name: str | None = None
    catch_body: Block | None = None
    finally_body: Block | None = None
    line: int = 1
    column: int = 1


@dataclass
class ThrowStatement(Statement):
    value: Expression
    line: int = 1
    column: int = 1


@dataclass
class TestDeclaration(Statement):
    name: str
    body: "Block"
    line: int = 1
    column: int = 1


@dataclass
class AssertStatement(Statement):
    condition: Expression
    line: int = 1
    column: int = 1


@dataclass
class ExpectErrorStatement(Statement):
    body: "Block"
    line: int = 1
    column: int = 1


@dataclass
class SkipStatement(Statement):
    reason: str | None = None
    line: int = 1
    column: int = 1


@dataclass
class NumberLiteral(Expression):
    value: int | float
    line: int = 1
    column: int = 1


@dataclass
class StringLiteral(Expression):
    value: str
    line: int = 1
    column: int = 1


@dataclass
class BooleanLiteral(Expression):
    value: bool
    line: int = 1
    column: int = 1


@dataclass
class ListLiteral(Expression):
    elements: list[Expression]
    line: int = 1
    column: int = 1


@dataclass
class MapLiteral(Expression):
    entries: list[tuple[Expression, Expression]]
    line: int = 1
    column: int = 1


@dataclass
class VariableExpression(Expression):
    name: str
    line: int = 1
    column: int = 1


@dataclass
class MemberExpression(Expression):
    object: Expression
    name: str
    line: int = 1
    column: int = 1


@dataclass
class CallExpression(Expression):
    callee: Expression
    arguments: list[Expression]
    line: int = 1
    column: int = 1


@dataclass
class IndexExpression(Expression):
    collection: Expression
    index: Expression
    line: int = 1
    column: int = 1


@dataclass
class SliceExpression(Expression):
    collection: Expression
    start: Expression
    stop: Expression
    line: int = 1
    column: int = 1


@dataclass
class PopListExpression(Expression):
    list_expression: Expression
    line: int = 1
    column: int = 1


@dataclass
class LessThanExpression(Expression):
    left: Expression
    right: Expression
    line: int = 1
    column: int = 1


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression
    line: int = 1
    column: int = 1


@dataclass
class UnaryExpression(Expression):
    operator: str
    operand: Expression
    line: int = 1
    column: int = 1
