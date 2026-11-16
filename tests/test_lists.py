import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser, ParserError


class ListTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_empty_list(self):
        self.assertEqual(self.run_program("program { kurwa lista = [] pierdol lista }"), "[]\n")

    def test_number_list(self):
        source = "program { kurwa lista = [10, 20, 30] pierdol lista }"
        self.assertEqual(self.run_program(source), "[10, 20, 30]\n")

    def test_string_and_boolean_list(self):
        source = """
        program {
            kurwa lista = ["kurwa", "chuj", 1 < 2]
            pierdol lista[0]
            pierdol lista[2]
        }
        """
        self.assertEqual(self.run_program(source), "kurwa\nTrue\n")

    def test_indexing(self):
        source = "program { kurwa lista = [10, 20, 30] pierdol lista[0] pierdol lista[1] }"
        self.assertEqual(self.run_program(source), "10\n20\n")

    def test_list_element_assignment(self):
        source = """
        program {
            kurwa lista = [10, 20, 30]
            lista[1] = 999
            pierdol lista[1]
        }
        """
        self.assertEqual(self.run_program(source), "999\n")

    def test_append_and_pop(self):
        source = """
        program {
            kurwa lista = [10, 20]
            wpierdol lista 30
            kurwa usuniety = wypierdol_z_listy lista
            pierdol lista
            pierdol usuniety
        }
        """
        self.assertEqual(self.run_program(source), "[10, 20]\n30\n")

    def test_list_length(self):
        source = "program { kurwa lista = [10, 20, 30] pierdol ile_kurwa(lista) }"
        self.assertEqual(self.run_program(source), "3\n")

    def test_nested_lists(self):
        source = "program { kurwa matrix = [[1, 2], [3, 4]] pierdol matrix[0][1] }"
        self.assertEqual(self.run_program(source), "2\n")

    def test_lists_in_loop(self):
        source = """
        program {
            kurwa liczby = [10, 20, 30]
            kurwa i = 0
            dopóki i < ile_kurwa(liczby) {
                pierdol liczby[i]
                zajeb i 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "10\n20\n30\n")

    def test_index_out_of_range(self):
        with self.assertRaisesRegex(InterpreterError, "Indeks poza zakresem"):
            self.run_program("program { kurwa lista = [1] pierdol lista[1] }")

    def test_index_must_be_number(self):
        with self.assertRaisesRegex(InterpreterError, "Indeks listy musi być liczbą"):
            self.run_program('program { kurwa lista = [1] pierdol lista["x"] }')

    def test_indexing_requires_list(self):
        with self.assertRaisesRegex(InterpreterError, "indeksowanie wymaga listy"):
            self.run_program("program { kurwa liczba = 10 pierdol liczba[0] }")

    def test_list_operation_requires_list(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga listy"):
            self.run_program("program { kurwa liczba = 10 wpierdol liczba 2 }")

    def test_invalid_list_syntax(self):
        with self.assertRaisesRegex(ParserError, "Expected expression|Expected '\\]' after list elements"):
            self.run_program("program { kurwa lista = [1, ] }")


if __name__ == "__main__":
    unittest.main()
