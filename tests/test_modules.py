import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class ModuleTestCase(unittest.TestCase):
    def run_file(self, directory: Path, name: str = "main.kurwa") -> str:
        source_path = directory / name
        program = Parser(Lexer(source_path.read_text(encoding="utf-8")).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter().run(program, source_path.resolve())
        return output.getvalue()

    def write(self, directory: Path, name: str, source: str) -> None:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def test_simple_module_import_and_function(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, "obliczenia.kurwa", "odpierdol funkcja dodaj(a, b) { oddaj a + b }\n")
            self.write(directory, "main.kurwa", "program { zajeb_moduł \"obliczenia\" pierdol obliczenia.dodaj(5, 10) }")
            self.assertEqual(self.run_file(directory), "15\n")

    def test_module_exports_variables_and_collections(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'dane.kurwa', 'kurwa liczba = 7\nkurwa lista = [1, 2]\nkurwa mapa = {"x": "y"}\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "dane" pierdol dane.liczba pierdol dane.lista[1] pierdol dane.mapa["x"] }')
            self.assertEqual(self.run_file(directory), "7\n2\ny\n")

    def test_module_has_own_scope(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'mod.kurwa', 'kurwa tajna = 2137\n')
            self.write(directory, 'main.kurwa', 'program { kurwa tajna = 1 zajeb_moduł "mod" pierdol tajna pierdol mod.tajna }')
            self.assertEqual(self.run_file(directory), "1\n2137\n")

    def test_module_without_program_header(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'mod.kurwa', 'odpierdol funkcja odpowiedz() { oddaj 42 }\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "mod" pierdol mod.odpowiedz() }')
            self.assertEqual(self.run_file(directory), "42\n")

    def test_module_with_program_header(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'mod.kurwa', 'program { kurwa wartosc = "dziala" }\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "mod" pierdol mod.wartosc }')
            self.assertEqual(self.run_file(directory), "dziala\n")

    def test_module_cache(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'mod.kurwa', 'odpierdol funkcja odpowiedz() { oddaj 1 }\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "mod" zajeb_moduł "mod" pierdol mod.odpowiedz() }')
            self.assertEqual(self.run_file(directory), "1\n")

    def test_module_imports_module_relative_to_itself(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'lib/auto.kurwa', 'zajeb_moduł "silnik"\nodpierdol funkcja marka() { oddaj silnik.nazwa }\n')
            self.write(directory, 'lib/silnik.kurwa', 'kurwa nazwa = "Audi"\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "lib/auto" pierdol auto.marka() }')
            self.assertEqual(self.run_file(directory), "Audi\n")

    def test_many_modules(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'a.kurwa', 'kurwa wartosc = 1\n')
            self.write(directory, 'b.kurwa', 'kurwa wartosc = 2\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "a" zajeb_moduł "b" pierdol a.wartosc + b.wartosc }')
            self.assertEqual(self.run_file(directory), "3\n")

    def test_module_recursion(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'silnia.kurwa', 'odpierdol funkcja silnia(n) { jeśli n <= 1 { oddaj 1 } oddaj n * silnia(n - 1) }\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "silnia" pierdol silnia.silnia(5) }')
            self.assertEqual(self.run_file(directory), "120\n")

    def test_module_uses_lists_maps_strings_and_booleans(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'wartosci.kurwa', 'kurwa lista = ["Audi"]\nkurwa mapa = {"aktywny": prawda}\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "wartosci" pierdol wartosci.lista[0] pierdol wartosci.mapa["aktywny"] }')
            self.assertEqual(self.run_file(directory), "Audi\nTrue\n")

    def test_missing_module(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "dupa" }')
            with self.assertRaisesRegex(InterpreterError, "dupa.kurwa.*nie można odczytać"):
                self.run_file(directory)

    def test_cyclic_import(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'a.kurwa', 'zajeb_moduł "b"\n')
            self.write(directory, 'b.kurwa', 'zajeb_moduł "a"\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "a" }')
            with self.assertRaisesRegex(InterpreterError, "cykliczny import.*a.*b.*a"):
                self.run_file(directory)

    def test_parser_error_points_to_module(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'zepsuty.kurwa', 'kurwa x = [1, ]\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "zepsuty" }')
            with self.assertRaisesRegex(InterpreterError, r"zepsuty\.kurwa:.*Expected expression"):
                self.run_file(directory)

    def test_runtime_error_points_to_module(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'zepsuty.kurwa', 'pierdol nie_ma\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "zepsuty" }')
            with self.assertRaisesRegex(InterpreterError, r"zepsuty\.kurwa:.*Undefined variable"):
                self.run_file(directory)

    def test_import_requires_kurwa_extension(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "mod.py" }')
            with self.assertRaisesRegex(InterpreterError, "tylko plik .kurwa"):
                self.run_file(directory)

    def test_module_can_be_imported_through_extension(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            self.write(directory, 'mod.kurwa', 'kurwa wartosc = 9\n')
            self.write(directory, 'main.kurwa', 'program { zajeb_moduł "mod.kurwa" pierdol mod.wartosc }')
            self.assertEqual(self.run_file(directory), "9\n")


if __name__ == "__main__":
    unittest.main()
