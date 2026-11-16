import io
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class ExtensionTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_extension_file_loads_and_calls_function(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            extension_dir = root / "extensions"
            extension_dir.mkdir()
            (extension_dir / "demo_ext.py").write_text(
                textwrap.dedent(
                    '''
                    from src.extensions import Extension

                    def dodaj(a, b):
                        return a + b

                    EXTENSION = Extension(
                        name="demo_ext",
                        version="1.0.0",
                        description="demo extension",
                        functions={"dodaj": dodaj},
                    )
                    '''
                ).strip() + "\n",
                encoding="utf-8",
            )
            source = '''
            program {
                kurwa ext = zaladuj_rozszerzenie("demo_ext")
                pierdol ext.dodaj(2, 3)
            }
            '''
            with mock.patch("pathlib.Path.cwd", return_value=root):
                self.assertEqual(self.run_program(source), "5\n")

    def test_extension_invalid_name_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "extensions").mkdir()
            source = 'program { kurwa x = zaladuj_rozszerzenie("../pwn") }'
            with mock.patch("pathlib.Path.cwd", return_value=root):
                with self.assertRaisesRegex(InterpreterError, "niepoprawna nazwa|niedozwolona|path"):
                    self.run_program(source)

    def test_extension_list_is_exposed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            extension_dir = root / "extensions"
            extension_dir.mkdir()
            (extension_dir / "demo_ext.py").write_text(
                textwrap.dedent(
                    '''
                    from src.extensions import Extension

                    EXTENSION = Extension(
                        name="demo_ext",
                        version="1.0.0",
                        description="demo",
                        functions={},
                    )
                    '''
                ).strip() + "\n",
                encoding="utf-8",
            )
            source = 'program { kurwa lista = rozszerzenia_kurwa() pierdol lista[0] }'
            with mock.patch("pathlib.Path.cwd", return_value=root):
                self.assertEqual(self.run_program(source), "demo_ext\n")

    def test_extension_metadata_is_exposed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            extension_dir = root / "extensions"
            extension_dir.mkdir()
            (extension_dir / "meta_ext.py").write_text(
                textwrap.dedent(
                    '''
                    from src.extensions import Extension

                    EXTENSION = Extension(
                        name="meta_ext",
                        version="2.1.0",
                        description="meta",
                        functions={},
                    )
                    '''
                ).strip() + "\n",
                encoding="utf-8",
            )
            source = '''
            program {
                kurwa ext = zaladuj_rozszerzenie("meta_ext")
                pierdol ext.metadane["wersja_kurwa"]
            }
            '''
            with mock.patch("pathlib.Path.cwd", return_value=root):
                self.assertEqual(self.run_program(source), "2.1.0\n")

    def test_duplicate_extension_registration_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            extension_dir = root / "extensions"
            extension_dir.mkdir()
            (extension_dir / "dup_ext.py").write_text(
                textwrap.dedent(
                    '''
                    from src.extensions import Extension

                    EXTENSION = Extension(
                        name="dup_ext",
                        version="1.0.0",
                        description="dup",
                        functions={},
                    )
                    '''
                ).strip() + "\n",
                encoding="utf-8",
            )
            source = '''
            program {
                kurwa a = zaladuj_rozszerzenie("dup_ext")
                kurwa b = zaladuj_rozszerzenie("dup_ext")
            }
            '''
            with mock.patch("pathlib.Path.cwd", return_value=root):
                with self.assertRaisesRegex(InterpreterError, "już jest zarejestrowane|zarejestrowane"):
                    self.run_program(source)

    def test_extension_builtin_name_collision_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            extension_dir = root / "extensions"
            extension_dir.mkdir()
            (extension_dir / "bad_ext.py").write_text(
                textwrap.dedent(
                    '''
                    from src.extensions import Extension

                    EXTENSION = Extension(
                        name="ile_kurwa",
                        version="1.0.0",
                        description="bad",
                        functions={"guz": lambda value: value},
                    )
                    '''
                ).strip() + "\n",
                encoding="utf-8",
            )
            source = 'program { kurwa ext = zaladuj_rozszerzenie("ile_kurwa") }'
            with mock.patch("pathlib.Path.cwd", return_value=root):
                with self.assertRaisesRegex(InterpreterError, "zarezerwowane|zajebane|nie może zastąpić"):
                    self.run_program(source)


if __name__ == "__main__":
    unittest.main()
