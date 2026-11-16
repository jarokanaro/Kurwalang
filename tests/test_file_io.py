import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class FileIOTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter().run(program, Path("/tmp/kurwa-file-io.kurwa"))
        return output.getvalue()

    def test_write_and_read_file(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa path = "{directory / "dane.txt"}"
                plik.zapisz(path, "Kurwa działa")
                pierdol plik.czytaj(path)
            }}'''
            self.assertEqual(self.run_program(source), "Kurwa działa\n")

    def test_overwrite_and_append(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa path = "{directory / "log.txt"}"
                plik.zapisz(path, "A\\n")
                plik.dopisz(path, "B\\n")
                pierdol plik.czytaj(path)
            }}'''
            self.assertEqual(self.run_program(source), "A\nB\n\n")

    def test_exists_and_delete(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "usunme.txt"
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa text = "x"
                plik.zapisz("{path}", text)
                pierdol plik.czy_jest("{path}")
                plik.usun("{path}")
                pierdol plik.czy_jest("{path}")
            }}'''
            self.assertEqual(self.run_program(source), "True\nFalse\n")

    def test_utf8_polish_characters(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa path = "{directory / "polski.txt"}"
                kurwa tekst = "Kurwa, żółć, gęś i Łódź."
                plik.zapisz(path, tekst)
                pierdol plik.czytaj(path)
            }}'''
            self.assertEqual(self.run_program(source), "Kurwa, żółć, gęś i Łódź.\n")

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "empty.txt"
            source = f'''program {{
                zajeb_moduł "plik"
                plik.zapisz("{path}", "")
                pierdol ile_kurwa(plik.czytaj("{path}"))
            }}'''
            self.assertEqual(self.run_program(source), "0\n")

    def test_directory_creation_and_listing(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "katalog"
                kurwa dir_path = "{directory / "folder"}"
                katalog.utworz(dir_path)
                pierdol katalog.czy_jest(dir_path)
                kurwa items = katalog.lista("{directory}")
                pierdol ile_kurwa(items)
            }}'''
            self.assertEqual(self.run_program(source), "True\n1\n")

    def test_directory_errors(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            file_path = directory / "plik.txt"
            file_path.write_text("x", encoding="utf-8")
            source = f'''program {{
                zajeb_moduł "katalog"
                pierdol katalog.lista("{file_path}")
            }}'''
            with self.assertRaisesRegex(InterpreterError, "wymaga katalogu"):
                self.run_program(source)

    def test_file_info(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            path = directory / "info.txt"
            path.write_text("12345", encoding="utf-8")
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa info = plik.info("{path}")
                pierdol info["rozmiar"]
                pierdol info["czy_plik"]
                pierdol info["czy_katalog"]
            }}'''
            self.assertEqual(self.run_program(source), "5\nTrue\nFalse\n")

    def test_path_helpers(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "sciezka"
                kurwa joined = sciezka.polacz("{directory}", "folder/file.txt")
                pierdol sciezka.nazwa(joined)
                pierdol sciezka.rozszerzenie(joined)
                pierdol sciezka.katalog(joined)
                pierdol sciezka.absolutna("folder")
            }}'''
            output = self.run_program(source).splitlines()
            self.assertEqual(output[0], "file.txt")
            self.assertEqual(output[1], ".txt")
            self.assertEqual(output[2], str(Path(directory) / "folder"))
            self.assertTrue(output[3].endswith("folder"))

    def test_missing_file_error(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                pierdol plik.czytaj("{directory / "brak.txt"}")
            }}'''
            with self.assertRaisesRegex(InterpreterError, "nieistniejącego pliku"):
                self.run_program(source)

    def test_append_to_missing_file_creates_it(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                kurwa path = "{directory / "new.txt"}"
                plik.dopisz(path, "hello")
                pierdol plik.czytaj(path)
            }}'''
            self.assertEqual(self.run_program(source), "hello\n")

    def test_type_errors(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            source = f'''program {{
                zajeb_moduł "plik"
                plik.zapisz("{directory}", "x")
            }}'''
            with self.assertRaisesRegex(InterpreterError, "wymaga pliku"):
                self.run_program(source)


if __name__ == "__main__":
    unittest.main()
