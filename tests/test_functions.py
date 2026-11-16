import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser, ParserError


class FunctionTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_function_without_arguments(self):
        source = """
        program {
            odpierdol funkcja dupa() {
                wypierdol "Działa"
            }
            dupa()
        }
        """
        self.assertEqual(self.run_program(source), "Działa\n")

    def test_function_with_one_argument_and_parameters(self):
        source = """
        program {
            odpierdol funkcja przywitaj(imie) {
                wypierdol imie
            }
            przywitaj("Jaro")
        }
        """
        self.assertEqual(self.run_program(source), "Jaro\n")

    def test_function_with_multiple_arguments_and_return(self):
        source = """
        program {
            odpierdol funkcja dodaj(a, b) {
                oddaj a + b
            }
            kurwa wynik = dodaj(10, 20)
            pierdol wynik
        }
        """
        self.assertEqual(self.run_program(source), "30\n")

    def test_local_variables_do_not_overwrite_global_variables(self):
        source = """
        program {
            kurwa x = 100
            odpierdol funkcja test() {
                kurwa x = 500
                pierdol x
            }
            test()
            pierdol x
        }
        """
        self.assertEqual(self.run_program(source), "500\n100\n")

    def test_nested_calls_and_expression_arguments(self):
        source = """
        program {
            odpierdol funkcja podwoj(x) {
                oddaj x * 2
            }
            odpierdol funkcja dodaj(a, b) {
                oddaj a + b
            }
            kurwa wynik = dodaj(podwoj(5), 3 * 2)
            pierdol wynik
        }
        """
        self.assertEqual(self.run_program(source), "16\n")

    def test_recursive_factorial(self):
        source = """
        program {
            odpierdol funkcja silnia(n) {
                jeśli n <= 1 {
                    oddaj 1
                }
                oddaj n * silnia(n - 1)
            }
            kurwa wynik = silnia(5)
            pierdol wynik
        }
        """
        self.assertEqual(self.run_program(source), "120\n")

    def test_function_without_return_has_language_value(self):
        source = """
        program {
            odpierdol funkcja nic() {
                wypierdol "gotowe"
            }
            pierdol nic()
        }
        """
        self.assertEqual(self.run_program(source), "gotowe\nbrak_wyniku\n")

    def test_wrong_argument_count(self):
        source = """
        program {
            odpierdol funkcja dodaj(a, b) { oddaj a + b }
            dodaj(1)
        }
        """
        with self.assertRaisesRegex(InterpreterError, "wymaga 2 argumentów"):
            self.run_program(source)

    def test_undefined_function(self):
        with self.assertRaisesRegex(InterpreterError, "To nie jest funkcja|Undefined variable"):
            self.run_program("program { dupa() }")

    def test_return_outside_function(self):
        with self.assertRaisesRegex(ParserError, "only be used inside a function"):
            self.run_program("program { oddaj 1 }")

    def test_duplicate_function_definition(self):
        source = """
        program {
            odpierdol funkcja dupa() { oddaj 1 }
            odpierdol funkcja dupa() { oddaj 2 }
        }
        """
        with self.assertRaisesRegex(InterpreterError, "Funkcja już istnieje"):
            self.run_program(source)

    def test_invalid_parameter_syntax(self):
        source = "program { odpierdol funkcja dupa(a,) { oddaj a } }"
        with self.assertRaisesRegex(ParserError, "Expected parameter name|Expected '\\)' after function parameters"):
            self.run_program(source)


if __name__ == "__main__":
    unittest.main()
