import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class JsonTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter().run(program, Path("/tmp/kurwa-json.kurwa"))
        return output.getvalue()

    def test_primitive_values(self):
        source = """
        program {
            zajeb_moduł "dane"
            pierdol dane.skurw("kurwa")
            pierdol dane.skurw(19)
            pierdol dane.skurw(3.14)
            pierdol dane.skurw(prawda)
            pierdol dane.skurw(fałsz)
        }
        """
        self.assertEqual(
            self.run_program(source),
            '"kurwa"\n19\n3.14\ntrue\nfalse\n',
        )

    def test_map_list_and_null_round_trip(self):
        source = """
        program {
            zajeb_moduł "dane"
            kurwa dane_we = {"tekst": "żółć 😎", "liczby": [1, 2.5], "aktywny": prawda, "pustka": "x"}
            kurwa tekst = dane.skurw(dane_we)
            kurwa dane_wy = dane.odkurw(tekst)
            pierdol dane_wy["tekst"]
            pierdol dane_wy["liczby"][1]
            pierdol dane_wy["aktywny"]
        }
        """
        self.assertEqual(self.run_program(source), "żółć 😎\n2.5\nTrue\n")

    def test_json_null_maps_to_no_value(self):
        source = r"""
        program {
            zajeb_moduł "dane"
            kurwa dane_wy = dane.odkurw("{\"pustka\":null}")
            pierdol dane_wy["pustka"]
        }
        """
        self.assertEqual(self.run_program(source), "brak_wyniku\n")

    def test_escaping_and_unicode_round_trip(self):
        source = r"""
        program {
            zajeb_moduł "dane"
            kurwa tekst = "Jaro powiedział: \"kurwa\"\nżółć 😎"
            kurwa wynik = dane.odkurw(dane.skurw(tekst))
            pierdol wynik
        }
        """
        self.assertEqual(self.run_program(source), "Jaro powiedział: \"kurwa\"\nżółć 😎\n")

    def test_pretty_json(self):
        source = "program { zajeb_moduł \"dane\" pierdol dane.ładnie_skurw({\"a\": 1}) }"
        output = self.run_program(source)
        self.assertIn("\n  \"a\": 1\n", output)

    def test_json_file_io(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "config.json"
            source = f'''program {{
                zajeb_moduł "dane"
                kurwa dane_we = {{"nazwa": "KURWA LANG", "wersja": 1.2}}
                dane.zapisz("{path}", dane_we)
                kurwa dane_wy = dane.czytaj("{path}")
                pierdol dane_wy["nazwa"]
                pierdol dane_wy["wersja"]
            }}'''
            self.assertEqual(self.run_program(source), "KURWA LANG\n1.2\n")

    def test_malformed_json(self):
        with self.assertRaisesRegex(InterpreterError, "niepoprawny JSON"):
            self.run_program('program { zajeb_moduł "dane" pierdol dane.odkurw("{invalid}") }')

    def test_non_standard_json_numbers_are_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), self.assertRaisesRegex(InterpreterError, "niepoprawny JSON"):
                self.run_program(
                    f'program {{ zajeb_moduł "dane" pierdol dane.odkurw("{value}") }}'
                )

    def test_unsupported_json_value(self):
        source = """
        program {
            zajeb_moduł "dane"
            odpierdol funkcja dupa() { oddaj 1 }
            pierdol dane.skurw(dupa)
        }
        """
        with self.assertRaisesRegex(InterpreterError, "nie może zostać zapisany jako JSON"):
            self.run_program(source)

    def test_cyclic_structure(self):
        source = """
        program {
            zajeb_moduł "dane"
            kurwa mapa = {}
            mapa["self"] = mapa
            pierdol dane.skurw(mapa)
        }
        """
        with self.assertRaisesRegex(InterpreterError, "cykliczną strukturę"):
            self.run_program(source)

    def test_json_argument_type_errors(self):
        with self.assertRaisesRegex(InterpreterError, "wymaga stringa JSON"):
            self.run_program('program { zajeb_moduł "dane" pierdol dane.odkurw(1) }')


if __name__ == "__main__":
    unittest.main()
