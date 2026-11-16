import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class StandardLibraryTestCase(unittest.TestCase):
    def run_program(self, source: str, arguments=None) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter(arguments).run(program, Path("/tmp/kurwa-stdlib-test.kurwa"))
        return output.getvalue()

    def test_math_functions_and_constants(self):
        source = """
        program {
            zajeb_moduł "matematyka"
            pierdol matematyka.abs_kurwa(-3)
            pierdol matematyka.potega_kurwa(2, 3)
            pierdol matematyka.pierwiastek_kurwa(9)
            pierdol matematyka.minimum_kurwa(4, 2, 8)
            pierdol matematyka.maksimum_kurwa(4, 2, 8)
            pierdol matematyka.zaokraglij_kurwa(2.6)
            jeśli matematyka.PI > 3 i matematyka.E > 2 {
                wypierdol "stale"
            }
        }
        """
        self.assertEqual(self.run_program(source), "3\n8\n3.0\n2\n8\n3\nstale\n")

    def test_math_errors(self):
        with self.assertRaisesRegex(InterpreterError, "liczby ujemnej"):
            self.run_program('program { zajeb_moduł "matematyka" pierdol matematyka.pierwiastek_kurwa(-1) }')
        with self.assertRaisesRegex(InterpreterError, "co najmniej 1"):
            self.run_program('program { zajeb_moduł "matematyka" pierdol matematyka.minimum_kurwa() }')

    def test_random_integer_range_and_element(self):
        source = """
        program {
            zajeb_moduł "losuj"
            kurwa liczba = losuj.liczba(7, 7)
            kurwa lista = ["a", "b"]
            kurwa element = losuj.element(lista)
            pierdol liczba
            jeśli (liczba >= 7 i liczba <= 7) i (element == "a" albo element == "b") {
                wypierdol "losowanie okej"
            }
        }
        """
        self.assertEqual(self.run_program(source), "7\nlosowanie okej\n")

    def test_random_errors(self):
        with self.assertRaisesRegex(InterpreterError, "pustej liście"):
            self.run_program('program { zajeb_moduł "losuj" pierdol losuj.element([]) }')
        with self.assertRaisesRegex(InterpreterError, "min <= max"):
            self.run_program('program { zajeb_moduł "losuj" pierdol losuj.liczba(2, 1) }')

    def test_text_module(self):
        source = """
        program {
            zajeb_moduł "tekst"
            pierdol tekst.oczysc("  Jaro  ")
            pierdol tekst.zaczyna_sie("Audi A3", "Audi")
            pierdol tekst.konczy_sie("Audi A3", "A3")
            pierdol tekst.polacz(tekst.rozdziel("a,b,c", ","), "-")
            pierdol tekst.powtorz("ha", 3)
        }
        """
        self.assertEqual(self.run_program(source), "Jaro\nTrue\nTrue\na-b-c\nhahaha\n")

    def test_text_errors(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga niepustego separatora"):
            self.run_program('program { zajeb_moduł "tekst" pierdol tekst.rozdziel("a", "") }')
        with self.assertRaisesRegex(InterpreterError, "wymaga listy stringów"):
            self.run_program('program { zajeb_moduł "tekst" pierdol tekst.polacz([1], "-") }')

    def test_time_module(self):
        source = """
        program {
            zajeb_moduł "czas"
            kurwa timestamp = czas.teraz()
            pierdol timestamp
            pierdol czas.data()
            pierdol czas.uspij(0)
        }
        """
        output = self.run_program(source)
        lines = output.splitlines()
        self.assertGreater(float(lines[0]), 0)
        self.assertIn("-", lines[1])
        self.assertEqual(lines[2], "brak_wyniku")

    def test_time_error(self):
        with self.assertRaisesRegex(InterpreterError, "milisekund"):
            self.run_program('program { zajeb_moduł "czas" pierdol czas.uspij(-1) }')

    def test_system_module_and_version(self):
        source = """
        program {
            zajeb_moduł "system"
            pierdol system.wersja()
            pierdol system.operacyjny()
            pierdol system.katalog()
            pierdol ile_kurwa(system.argumenty())
        }
        """
        output = self.run_program(source, ["jeden", "dwa"])
        lines = output.splitlines()
        self.assertEqual(lines[0], "1.12.0")
        self.assertTrue(lines[1])
        self.assertTrue(lines[2])
        self.assertEqual(lines[3], "2")

    def test_standard_library_cache_and_user_module_precedence(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "matematyka.kurwa").write_text('kurwa PI = "podrobka"\n', encoding="utf-8")
            source_path = directory / "main.kurwa"
            source_path.write_text(
                'program { zajeb_moduł "matematyka" zajeb_moduł "matematyka" pierdol matematyka.PI }',
                encoding="utf-8",
            )
            program = Parser(Lexer(source_path.read_text(encoding="utf-8")).tokenize()).parse()
            output = io.StringIO()
            with redirect_stdout(output):
                Interpreter().run(program, source_path.resolve())
            self.assertEqual(output.getvalue(), "3.141592653589793\n")

    def test_standard_library_in_existing_language_features(self):
        source = """
        program {
            zajeb_moduł "tekst"
            zajeb_moduł "matematyka"
            kurwa lista = tekst.rozdziel("1,2,3", ",")
            kurwa i = 0
            dopóki i < ile_kurwa(lista) {
                pierdol matematyka.potega_kurwa(liczba_kurwa(lista[i]), 2)
                zajeb i 1
            }
        }
        """
        self.assertEqual(self.run_program(source), "1\n4\n9\n")


if __name__ == "__main__":
    unittest.main()
