
"""Recursive-descent parser for KURWA LANG."""

try:
    from .ast import (
        Block,
        BinaryExpression,
        CallExpression,
        AppendStatement,
        BooleanLiteral,
        DeleteMapEntryStatement,
        ExitStatement,
        Expression,
        ExpressionStatement,
        FunctionDeclaration,
        IfStatement,
        ImportStatement,
        IncrementStatement,
        LoopExitStatement,
        IndexExpression,
        ListLiteral,
        MapLiteral,
        MemberExpression,
        LessThanExpression,
        NumberLiteral,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        PopListExpression,
        SetListElementStatement,
        SliceExpression,
        StringLiteral,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        TestDeclaration,
        AssertStatement,
        ExpectErrorStatement,
        SkipStatement,
    )
except ImportError:
    from ast import (
        Block,
        BinaryExpression,
        CallExpression,
        AppendStatement,
        BooleanLiteral,
        DeleteMapEntryStatement,
        ExitStatement,
        Expression,
        ExpressionStatement,
        FunctionDeclaration,
        IfStatement,
        ImportStatement,
        IncrementStatement,
        LoopExitStatement,
        IndexExpression,
        ListLiteral,
        MapLiteral,
        MemberExpression,
        LessThanExpression,
        NumberLiteral,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        PopListExpression,
        SetListElementStatement,
        SliceExpression,
        StringLiteral,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        TestDeclaration,
        AssertStatement,
        ExpectErrorStatement,
        SkipStatement,
    )
try:
    from .lexer import Token, TokenType
except ImportError:
    from lexer import Token, TokenType


class ParserError(Exception):
    """Raised when the token stream does not match KURWA LANG grammar."""


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0
        self.function_depth = 0

    def parse(self) -> Program:
        self._consume(TokenType.PROGRAM, "Expected 'program' at the start of the file")
        body = self._block()
        self._consume(TokenType.EOF, "Expected end of file")
        return Program(body)

    def parse_module(self) -> Program:
        if self._check(TokenType.PROGRAM):
            return self.parse()
        statements = []
        while not self._check(TokenType.EOF):
            statements.append(self._statement())
        return Program(Block(statements))

    def _block(self) -> Block:
        self._consume(TokenType.LEFT_BRACE, "Expected '{' to start a block")
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._check(TokenType.EOF):
            statements.append(self._statement())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' to close a block")
        return Block(statements)

    def _statement(self):
        token = self._peek()
        if token.type is TokenType.KURWA:
            return self._declaration()
        if token.type is TokenType.ODPIERDOL:
            return self._function_declaration()
        if token.type is TokenType.ODPIERDOL_KURWICZNIE:
            return self._async_function_declaration()
        if token.type is TokenType.ODDAJ:
            if self.function_depth == 0:
                raise self._error("'oddaj' can only be used inside a function")
            self._advance()
            return ReturnStatement(self._expression())
        if token.type is TokenType.ZAJEB_MODUL:
            return self._import_statement()
        if token.type is TokenType.WPIERDOL:
            return self._append()
        if token.type is TokenType.WYPIERDOL_Z_MAPY:
            return self._delete_map_entry()
        if token.type is TokenType.JESLI:
            return self._if_statement()
        if token.type is TokenType.DOPOKI:
            return self._while_statement()
        if token.type is TokenType.INACZEJ:
            raise self._error("Unexpected 'inaczej' without a preceding 'jeśli'")
        if token.type is TokenType.WYPERDALAJ:
            self._advance()
            return LoopExitStatement()
        if token.type is TokenType.ZAJEB:
            return self._increment()
        if token.type is TokenType.WYPIERDOL:
            return self._print(PrintTextStatement)
        if token.type is TokenType.PIERDOL:
            return self._print(PrintValueStatement)
        if token.type is TokenType.CO_JEST_KURWA:
            return self._print(PrintTextStatement)
        if token.type is TokenType.WJEBAJ:
            return self._try_statement()
        if token.type is TokenType.WYRZUC_KURWA:
            return self._throw_statement()
        if token.type is TokenType.TESTUJ_KURWA:
            return self._test_declaration()
        if token.type is TokenType.SPRAWDZ_KURWA:
            return self._assert_statement()
        if token.type is TokenType.OCZEKUJ_BLAD_KURWA:
            return self._expect_error_statement()
        if token.type is TokenType.POMIN_KURWA:
            return self._skip_statement()
        if token.type in (TokenType.IDENTIFIER, TokenType.I):
            expression = self._expression()
            if self._match(TokenType.EQUALS):
                if not isinstance(expression, IndexExpression):
                    raise self._error("Only a list or map element can be assigned")
                return SetListElementStatement(expression, self._expression())
            if isinstance(expression, CallExpression):
                return ExpressionStatement(expression)
            raise self._error("Expected a function call or list assignment as a statement")
        if token.type is TokenType.SPIERDALAJ:
            self._advance()
            return ExitStatement()
        raise self._error(f"Unexpected token {token.lexeme!r}")

    def _declaration(self) -> VariableDeclaration:
        self._advance()
        name = self._consume_name("Expected variable name after 'kurwa'")
        self._consume(TokenType.EQUALS, "Expected '=' after variable name")
        return VariableDeclaration(name.lexeme, self._expression())

    def _append(self) -> AppendStatement:
        self._advance()
        list_expression = self._expression()
        if not isinstance(list_expression, VariableExpression):
            raise self._error("Expected a list variable after 'wpierdol'")
        return AppendStatement(list_expression, self._expression())

    def _delete_map_entry(self) -> DeleteMapEntryStatement:
        self._advance()
        map_expression = self._expression()
        key = self._expression()
        return DeleteMapEntryStatement(map_expression, key)

    def _import_statement(self) -> ImportStatement:
        self._advance()
        module = self._consume(TokenType.STRING, "Expected module name after 'zajeb_moduł'")
        return ImportStatement(module.lexeme)

    def _function_declaration(self) -> FunctionDeclaration:
        self._advance()
        return self._declaration_body(False)

    def _async_function_declaration(self) -> FunctionDeclaration:
        self._advance()
        return self._declaration_body(True)

    def _declaration_body(self, is_async: bool) -> FunctionDeclaration:
        self._consume(TokenType.FUNKCJA, "Expected 'funkcja' after async/sync function declaration")
        name = self._consume_name("Expected function name")
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        parameters = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                parameter = self._consume_name("Expected parameter name")
                if parameter.lexeme in parameters:
                    raise self._error(f"Duplicate parameter: {parameter.lexeme}")
                parameters.append(parameter.lexeme)
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after function parameters")
        self.function_depth += 1
        try:
            body = self._block()
        finally:
            self.function_depth -= 1
        return FunctionDeclaration(name.lexeme, parameters, body, is_async=is_async)

    def _if_statement(self) -> IfStatement:
        self._advance()
        condition = self._expression()
        body = self._block()
        else_body = self._block() if self._match(TokenType.INACZEJ) else None
        return IfStatement(condition, body, else_body)

    def _while_statement(self) -> WhileStatement:
        self._advance()
        condition = self._expression()
        return WhileStatement(condition, self._block())

    def _try_statement(self) -> TryStatement:
        self._advance()
        body = self._block()
        catch_name = None
        catch_body = None
        if self._match(TokenType.ZLAP_KURWA):
            catch_name = self._consume_name("Expected error variable name after 'zlap_kurwa'").lexeme
            catch_body = self._block()
        finally_body = None
        if self._match(TokenType.WYCZYSC_KURWA):
            finally_body = self._block()
        return TryStatement(body, catch_name, catch_body, finally_body)

    def _throw_statement(self) -> ThrowStatement:
        self._advance()
        return ThrowStatement(self._expression())

    def _test_declaration(self) -> TestDeclaration:
        self._advance()
        name = self._consume(TokenType.STRING, "Expected string test name after 'testuj_kurwa'")
        body = self._block()
        return TestDeclaration(name.lexeme, body)

    def _assert_statement(self) -> AssertStatement:
        self._advance()
        return AssertStatement(self._expression())

    def _expect_error_statement(self) -> ExpectErrorStatement:
        self._advance()
        return ExpectErrorStatement(self._block())

    def _skip_statement(self) -> SkipStatement:
        self._advance()
        reason = None
        if self._check(TokenType.STRING):
            reason = self._advance().lexeme
        return SkipStatement(reason)

    def _increment(self) -> IncrementStatement:
        self._advance()
        name = self._consume_name("Expected variable name after 'zajeb'")
        amount = self._expression()
        return IncrementStatement(name.lexeme, amount)

    def _print(self, statement_type):
        self._advance()
        return statement_type(self._expression())

    def _expression(self) -> Expression:
        return self._or()

    def _or(self) -> Expression:
        expression = self._and()
        while self._match(TokenType.ALBO):
            expression = BinaryExpression(expression, "albo", self._and())
        return expression

    def _and(self) -> Expression:
        expression = self._equality()
        while self._match(TokenType.I):
            expression = BinaryExpression(expression, "i", self._equality())
        return expression

    def _equality(self) -> Expression:
        expression = self._comparison()
        while self._match(TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL):
            operator = self.tokens[self.position - 1].lexeme
            expression = BinaryExpression(expression, operator, self._comparison())
        return expression

    def _comparison(self) -> Expression:
        expression = self._term()
        while self._match(
            TokenType.LESS_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_THAN,
            TokenType.GREATER_EQUAL,
        ):
            operator = self.tokens[self.position - 1].lexeme
            expression = BinaryExpression(expression, operator, self._term())
        return expression

    def _term(self) -> Expression:
        expression = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self.tokens[self.position - 1].lexeme
            expression = BinaryExpression(expression, operator, self._factor())
        return expression

    def _factor(self) -> Expression:
        expression = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self.tokens[self.position - 1].lexeme
            expression = BinaryExpression(expression, operator, self._unary())
        return expression

    def _unary(self) -> Expression:
        if self._match(TokenType.NIE):
            return UnaryExpression("nie", self._unary())
        if self._match(TokenType.MINUS):
            return UnaryExpression("-", self._unary())
        return self._primary()

    def _primary(self) -> Expression:
        token = self._peek()
        if self._match(TokenType.INTEGER):
            return NumberLiteral(int(token.lexeme))
        if self._match(TokenType.FLOAT):
            return NumberLiteral(float(token.lexeme))
        if self._match(TokenType.STRING):
            return self._postfix(StringLiteral(token.lexeme))
        if self._match(TokenType.PRAWDA):
            return self._postfix(BooleanLiteral(True))
        if self._match(TokenType.FALSZ):
            return self._postfix(BooleanLiteral(False))
        if self._match(TokenType.LEFT_BRACKET):
            elements = []
            if not self._check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after list elements")
            return self._postfix(ListLiteral(elements))
        if self._match(TokenType.LEFT_BRACE):
            entries = []
            if not self._check(TokenType.RIGHT_BRACE):
                while True:
                    key = self._consume(TokenType.STRING, "Expected string key in map")
                    self._consume(TokenType.COLON, "Expected ':' after map key")
                    entries.append((StringLiteral(key.lexeme), self._expression()))
                    if not self._match(TokenType.COMMA):
                        break
            self._consume(TokenType.RIGHT_BRACE, "Expected '}' after map entries")
            return self._postfix(MapLiteral(entries))
        if self._match(TokenType.WYPIERDOL_Z_LISTY):
            return self._postfix(PopListExpression(self._expression()))
        if self._match(TokenType.IDENTIFIER, TokenType.I):
            return self._postfix(VariableExpression(token.lexeme))
        if self._match(TokenType.LEFT_PAREN):
            expression = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return self._postfix(expression)
        raise self._error(f"Expected expression, got {token.lexeme!r}")

    def _postfix(self, expression: Expression) -> Expression:
        while True:
            if self._match(TokenType.LEFT_PAREN):
                arguments = []
                if not self._check(TokenType.RIGHT_PAREN):
                    while True:
                        arguments.append(self._expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._consume(TokenType.RIGHT_PAREN, "Expected ')' after function arguments")
                expression = CallExpression(expression, arguments)
            elif self._match(TokenType.LEFT_BRACKET):
                start = self._expression()
                if self._match(TokenType.COLON):
                    stop = self._expression()
                    self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after string slice")
                    expression = SliceExpression(expression, start, stop)
                else:
                    self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after collection index")
                    expression = IndexExpression(expression, start)
            elif self._match(TokenType.DOT):
                name = self._consume_name("Expected member name after '.'")
                expression = MemberExpression(expression, name.lexeme)
            else:
                break
        return expression

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(message)

    def _consume_name(self, message: str) -> Token:
        if self._check(TokenType.IDENTIFIER) or self._check(TokenType.I):
            return self._advance()
        raise self._error(message)

    def _match(self, *token_types: TokenType) -> bool:
        if not any(self._check(token_type) for token_type in token_types):
            return False
        self._advance()
        return True

    def _check(self, token_type: TokenType) -> bool:
        return self._peek().type is token_type

    def _advance(self) -> Token:
        token = self._peek()
        if token.type is not TokenType.EOF:
            self.position += 1
        return token

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _error(self, message: str) -> ParserError:
        token = self._peek()
        return ParserError(f"{message} at line {token.line}, column {token.column}")
