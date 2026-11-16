import io
import unittest
from contextlib import redirect_stdout

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser, ParserError


class MapTestCase(unittest.TestCase):
    def run_program(self, source: str) -> str:
        output = io.StringIO()
        program = Parser(Lexer(source).tokenize()).parse()
        with redirect_stdout(output):
            Interpreter().run(program)
        return output.getvalue()

    def test_empty_map(self):
        self.assertEqual(self.run_program("program { kurwa mapa = {} pierdol mapa }"), "{}\n")

    def test_map_values_and_reading(self):
        source = """
        program {
            kurwa osoba = {"imie": "Jaro", "wiek": 19, "aktywny": prawda}
            pierdol osoba["imie"]
            pierdol osoba["wiek"]
            pierdol osoba["aktywny"]
        }
        """
        self.assertEqual(self.run_program(source), "Jaro\n19\nTrue\n")

    def test_map_value_expressions(self):
        source = """
        program {
            kurwa wiek = 19
            kurwa osoba = {"wiek": wiek + 1, "pelnoletni": wiek >= 18}
            pierdol osoba["wiek"]
            pierdol osoba["pelnoletni"]
        }
        """
        self.assertEqual(self.run_program(source), "20\nTrue\n")

    def test_map_update_and_new_key(self):
        source = """
        program {
            kurwa osoba = {"wiek": 19}
            osoba["wiek"] = 20
            osoba["miasto"] = "Opole"
            pierdol osoba["wiek"]
            pierdol osoba["miasto"]
        }
        """
        self.assertEqual(self.run_program(source), "20\nOpole\n")

    def test_map_delete(self):
        source = """
        program {
            kurwa osoba = {"imie": "Jaro", "wiek": 19}
            wypierdol_z_mapy osoba "wiek"
            pierdol ile_kurwa(osoba)
            pierdol jest_kurwa(osoba, "wiek")
        }
        """
        self.assertEqual(self.run_program(source), "1\nFalse\n")

    def test_key_existence(self):
        source = """
        program {
            kurwa osoba = {"wiek": 19}
            pierdol jest_kurwa(osoba, "wiek")
            pierdol jest_kurwa(osoba, "imie")
        }
        """
        self.assertEqual(self.run_program(source), "True\nFalse\n")

    def test_map_length(self):
        self.assertEqual(
            self.run_program('program { pierdol ile_kurwa({"a": 1, "b": 2}) }'),
            "2\n",
        )

    def test_nested_maps_and_lists(self):
        source = """
        program {
            kurwa dane = {
                "uzytkownik": {"imie": "Jaro", "wiek": 19},
                "auta": ["Audi", "BMW"]
            }
            pierdol dane["uzytkownik"]["imie"]
            pierdol dane["auta"][0]
            wypierdol_z_mapy dane["uzytkownik"] "wiek"
            pierdol jest_kurwa(dane["uzytkownik"], "wiek")
        }
        """
        self.assertEqual(self.run_program(source), "Jaro\nAudi\nFalse\n")

    def test_list_containing_maps(self):
        source = "program { kurwa rzeczy = [{" + '"x": 1' + "}] pierdol rzeczy[0][\"x\"] }"
        self.assertEqual(self.run_program(source), "1\n")

    def test_map_as_function_argument_and_return(self):
        source = """
        program {
            odpierdol funkcja stworz_osobe(imie, wiek) {
                kurwa osoba = {"imie": imie, "wiek": wiek}
                oddaj osoba
            }
            kurwa jaro = stworz_osobe("Jaro", 19)
            pierdol jaro["imie"]
            pierdol jaro["wiek"]
        }
        """
        self.assertEqual(self.run_program(source), "Jaro\n19\n")

    def test_map_modified_inside_function(self):
        source = """
        program {
            odpierdol funkcja podbij(mapa) {
                mapa["wynik"] = 500
            }
            kurwa dane = {}
            podbij(dane)
            pierdol dane["wynik"]
        }
        """
        self.assertEqual(self.run_program(source), "500\n")

    def test_map_condition(self):
        source = """
        program {
            kurwa osoba = {"wiek": 19}
            jeśli osoba["wiek"] >= 18 {
                wypierdol "Dorosly"
            }
        }
        """
        self.assertEqual(self.run_program(source), "Dorosly\n")

    def test_missing_key(self):
        with self.assertRaisesRegex(InterpreterError, "mapa nie zawiera klucza"):
            self.run_program('program { kurwa mapa = {"a": 1} pierdol mapa["b"] }')

    def test_invalid_map_type(self):
        with self.assertRaisesRegex(InterpreterError, "indeksowanie wymaga listy lub mapy"):
            self.run_program("program { kurwa liczba = 10 pierdol liczba[\"a\"] }")

    def test_invalid_map_key_type(self):
        with self.assertRaisesRegex(InterpreterError, "Klucz mapy musi być stringiem"):
            self.run_program("program { kurwa mapa = {} pierdol mapa[1] }")

    def test_invalid_map_syntax(self):
        with self.assertRaisesRegex(ParserError, "Expected ':' after map key"):
            self.run_program('program { kurwa mapa = {"a" 1} }')

    def test_map_builtins_require_map(self):
        with self.assertRaisesRegex(InterpreterError, "'jest_kurwa' wymaga mapy"):
            self.run_program("program { pierdol jest_kurwa([1], \"a\") }")


if __name__ == "__main__":
    unittest.main()
