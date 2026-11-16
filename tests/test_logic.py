import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class LogicTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_boolean_literals_and_variables(self):
        source = """
        program {
            kurwa aktywny = prawda
            kurwa gotowy = fałsz
            pierdol aktywny
            pierdol gotowy
        }
        """
        self.assertEqual(self.run_program(source), "True\nFalse\n")

    def test_comparisons_return_booleans(self):
        source = """
        program {
            pierdol 1 < 2
            pierdol 2 > 1
            pierdol 2 <= 2
            pierdol 2 >= 2
            pierdol 2 == 2
            pierdol 2 != 3
        }
        """
        self.assertEqual(self.run_program(source), "True\nTrue\nTrue\nTrue\nTrue\nTrue\n")

    def test_and_all_combinations(self):
        source = """
        program {
            pierdol prawda i prawda
            pierdol prawda i fałsz
            pierdol fałsz i prawda
            pierdol fałsz i fałsz
        }
        """
        self.assertEqual(self.run_program(source), "True\nFalse\nFalse\nFalse\n")

    def test_or_all_combinations(self):
        source = """
        program {
            pierdol prawda albo prawda
            pierdol prawda albo fałsz
            pierdol fałsz albo prawda
            pierdol fałsz albo fałsz
        }
        """
        self.assertEqual(self.run_program(source), "True\nTrue\nTrue\nFalse\n")

    def test_not(self):
        source = "program { pierdol nie prawda pierdol nie fałsz }"
        self.assertEqual(self.run_program(source), "False\nTrue\n")

    def test_logic_precedence(self):
        source = "program { pierdol nie prawda albo prawda i prawda }"
        self.assertEqual(self.run_program(source), "True\n")

    def test_logic_parentheses(self):
        source = "program { pierdol (prawda albo fałsz) i prawda }"
        self.assertEqual(self.run_program(source), "True\n")

    def test_nested_condition(self):
        source = """
        program {
            kurwa a = 10
            kurwa b = 20
            kurwa c = 30
            jeśli (a < b i b < c) albo c == 100 {
                wypierdol "Warunek spełniony"
            }
        }
        """
        self.assertEqual(self.run_program(source), "Warunek spełniony\n")

    def test_boolean_comparisons(self):
        source = """
        program {
            kurwa a = prawda
            kurwa b = fałsz
            jeśli a == prawda { wypierdol "a jest prawdą" }
            jeśli a != b { wypierdol "Różne" }
        }
        """
        self.assertEqual(self.run_program(source), "a jest prawdą\nRóżne\n")

    def test_function_boolean_argument_and_return(self):
        source = """
        program {
            odpierdol funkcja odwróc(wartosc) {
                oddaj nie wartosc
            }
            kurwa wynik = odwróc(fałsz)
            jeśli wynik { wypierdol "Działa" }
        }
        """
        self.assertEqual(self.run_program(source), "Działa\n")

    def test_boolean_loop_condition(self):
        source = """
        program {
            kurwa dalej = prawda
            kurwa licznik = 0
            dopóki dalej {
                zajeb licznik 1
                jeśli licznik == 3 { wypierdalaj }
            }
            pierdol licznik
        }
        """
        self.assertEqual(self.run_program(source), "3\n")

    def test_boolean_in_list(self):
        source = "program { kurwa rzeczy = [prawda, fałsz, prawda] pierdol rzeczy[1] }"
        self.assertEqual(self.run_program(source), "False\n")

    def test_and_short_circuit(self):
        source = "program { pierdol fałsz i nie_istnieje }"
        self.assertEqual(self.run_program(source), "False\n")

    def test_or_short_circuit(self):
        source = "program { pierdol prawda albo nie_istnieje }"
        self.assertEqual(self.run_program(source), "True\n")

    def test_logic_requires_booleans(self):
        with self.assertRaisesRegex(InterpreterError, "operator 'i'.*number"):
            self.run_program("program { pierdol 1 i prawda }")

    def test_condition_requires_boolean(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga wartości boolean.*number"):
            self.run_program("program { jeśli 1 { pierdol \"nie\" } }")

    def test_unsupported_relational_type(self):
        with self.assertRaisesRegex(InterpreterError, "requires numeric values"):
            self.run_program('program { pierdol "a" < "b" }')


if __name__ == "__main__":
    unittest.main()
