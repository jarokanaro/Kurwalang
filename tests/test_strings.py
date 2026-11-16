import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class StringTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_concatenation(self):
        source = 'program { kurwa imie = "Jaro" pierdol "Siema " + imie }'
        self.assertEqual(self.run_program(source), "Siema Jaro\n")

    def test_empty_and_multiple_concatenations(self):
        source = 'program { pierdol "" + "A" + "" + "B" }'
        self.assertEqual(self.run_program(source), "AB\n")

    def test_mixed_concatenation_is_error(self):
        with self.assertRaisesRegex(InterpreterError, "two numbers or two strings"):
            self.run_program('program { pierdol "x" + 1 }')

    def test_length(self):
        source = 'program { pierdol ile_kurwa("KURWA") pierdol ile_kurwa("") pierdol ile_kurwa("zażółć") }'
        self.assertEqual(self.run_program(source), "5\n0\n6\n")

    def test_indexing(self):
        source = 'program { kurwa tekst = "KURWA" pierdol tekst[0] pierdol tekst[2] pierdol tekst[4] }'
        self.assertEqual(self.run_program(source), "K\nR\nA\n")

    def test_slicing(self):
        source = 'program { pierdol "KURWALANG"[0:5] pierdol "KURWALANG"[5:9] }'
        self.assertEqual(self.run_program(source), "KURWA\nLANG\n")

    def test_string_index_errors(self):
        with self.assertRaisesRegex(InterpreterError, "Indeks stringa poza zakresem"):
            self.run_program('program { pierdol "A"[1] }')
        with self.assertRaisesRegex(InterpreterError, "Indeks stringa musi być liczbą"):
            self.run_program('program { pierdol "A"["x"] }')

    def test_case_conversion(self):
        source = 'program { pierdol wielkie_kurwa("Jaro") pierdol male_kurwa("JARO") pierdol wielkie_kurwa("") }'
        self.assertEqual(self.run_program(source), "JARO\njaro\n\n")

    def test_contains(self):
        source = 'program { pierdol zawiera_kurwa("Audi A3", "Audi") pierdol zawiera_kurwa("Audi A3", "BMW") pierdol zawiera_kurwa("", "") }'
        self.assertEqual(self.run_program(source), "True\nFalse\nTrue\n")

    def test_replace(self):
        source = 'program { pierdol zamien_kurwa("Audi jest wolne, wolne", "wolne", "szybkie") pierdol zamien_kurwa("Audi", "BMW", "A3") }'
        self.assertEqual(self.run_program(source), "Audi jest szybkie, szybkie\nAudi\n")

    def test_replace_empty_search_is_error(self):
        with self.assertRaisesRegex(InterpreterError, "nie przyjmuje pustego"):
            self.run_program('program { pierdol zamien_kurwa("A", "", "B") }')

    def test_find(self):
        source = 'program { pierdol znajdz_kurwa("Audi A3", "A3") pierdol znajdz_kurwa("Audi", "BMW") }'
        self.assertEqual(self.run_program(source), "5\n-1\n")

    def test_conversions(self):
        source = 'program { pierdol tekst_kurwa(123) pierdol liczba_kurwa("123") }'
        self.assertEqual(self.run_program(source), "123\n123\n")

    def test_invalid_conversion(self):
        with self.assertRaisesRegex(InterpreterError, "Nie można zamienić stringa"):
            self.run_program('program { pierdol liczba_kurwa("abc") }')

    def test_string_function_and_return(self):
        source = """
        program {
            odpierdol funkcja przywitaj(imie) {
                oddaj "Siema " + imie
            }
            pierdol przywitaj("Jaro")
        }
        """
        self.assertEqual(self.run_program(source), "Siema Jaro\n")

    def test_string_in_list_and_map(self):
        source = """
        program {
            kurwa teksty = ["Audi", "BMW"]
            kurwa auto = {"marka": "Audi"}
            pierdol teksty[1]
            pierdol auto["marka"]
        }
        """
        self.assertEqual(self.run_program(source), "BMW\nAudi\n")

    def test_string_condition_is_rejected(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga wartości boolean.*string"):
            self.run_program('program { jeśli "Audi" { pierdol "nie" } }')

    def test_string_builtins_require_strings(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga stringów"):
            self.run_program("program { pierdol wielkie_kurwa(123) }")


if __name__ == "__main__":
    unittest.main()
