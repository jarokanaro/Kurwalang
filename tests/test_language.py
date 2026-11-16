import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class LanguageTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_arithmetic_operators(self):
        source = """
        program {
            kurwa x = 10
            kurwa y = 5
            pierdol x + y
            pierdol x - y
            pierdol x * y
            pierdol x / y
        }
        """
        self.assertEqual(self.run_program(source), "15\n5\n50\n2\n")

    def test_comparison_operators(self):
        source = """
        program {
            kurwa x = 10
            jeśli x < 20 { wypierdol "lt" }
            jeśli x <= 10 { wypierdol "le" }
            jeśli x > 5 { wypierdol "gt" }
            jeśli x >= 10 { wypierdol "ge" }
            jeśli x == 10 { wypierdol "eq" }
            jeśli x != 5 { wypierdol "ne" }
        }
        """
        self.assertEqual(self.run_program(source), "lt\nle\ngt\nge\neq\nne\n")

    def test_else_branch(self):
        source = """
        program {
            kurwa kasa = 500
            jeśli kasa >= 1000 {
                wypierdol "Bogacz"
            } inaczej {
                wypierdol "Biedak"
            }
        }
        """
        self.assertEqual(self.run_program(source), "Biedak\n")

    def test_operator_precedence(self):
        source = "program { pierdol 100 + 50 * 2 }"
        self.assertEqual(self.run_program(source), "200\n")

    def test_parentheses(self):
        source = "program { pierdol (100 + 50) * 2 }"
        self.assertEqual(self.run_program(source), "300\n")

    def test_division_by_zero(self):
        source = "program { pierdol 10 / 0 }"
        with self.assertRaisesRegex(InterpreterError, "division by zero"):
            self.run_program(source)

    def test_undefined_variable(self):
        source = "program { pierdol nie_zdefiniowana }"
        with self.assertRaisesRegex(InterpreterError, "Undefined variable: nie_zdefiniowana"):
            self.run_program(source)

    def test_while_loop(self):
        source = """
        program {
            kurwa x = 0
            dopóki x < 5 {
                pierdol x
                zajeb x 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "0\n1\n2\n3\n4\n")

    def test_while_loop_runs_zero_times(self):
        source = """
        program {
            kurwa x = 5
            dopóki x < 5 {
                wypierdol "nie powinno się pojawić"
            }
            wypierdol "koniec"
        }
        """
        self.assertEqual(self.run_program(source), "koniec\n")

    def test_loop_exit(self):
        source = """
        program {
            kurwa x = 0
            dopóki x < 100 {
                pierdol x
                jeśli x == 5 {
                    wypierdalaj
                }
                zajeb x 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "0\n1\n2\n3\n4\n5\n")

    def test_loop_exit_inside_else(self):
        source = """
        program {
            kurwa x = 0
            dopóki x < 2 {
                jeśli x == 1 {
                    wypierdol "nie"
                } inaczej {
                    wypierdalaj
                }
                zajeb x 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "")

    def test_nested_while_loops(self):
        source = """
        program {
            kurwa x = 0
            dopóki x < 2 {
                kurwa y = 0
                dopóki y < 3 {
                    pierdol y
                    zajeb y 1
                }
                zajeb x 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "0\n1\n2\n0\n1\n2\n")

    def test_loop_exit_outside_loop(self):
        source = "program { wypierdalaj }"
        with self.assertRaisesRegex(InterpreterError, "requires a 'dopóki' loop"):
            self.run_program(source)

    def test_repeated_loop_statements(self):
        source = """
        program {
            kurwa x = 0
            kurwa suma = 0
            dopóki x < 4 {
                zajeb suma x
                zajeb x 1
            }
            pierdol suma
        }
        """
        self.assertEqual(self.run_program(source), "6\n")


if __name__ == "__main__":
    unittest.main()
