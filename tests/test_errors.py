import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter, InterpreterError
from src.lexer import Lexer
from src.parser import Parser


class ErrorHandlingTestCase(unittest.TestCase):
    def run_program(self, source: str, arguments=None) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter(arguments).run(program, Path("/tmp/kurwa-error-test.kurwa"))
        return output.getvalue()

    def test_try_catch_and_cleanup(self):
        source = """
        program {
            wjebaj {
                wyrzuc_kurwa "dupa"
            } zlap_kurwa blad {
                pierdol blad["typ_kurwa"]
                pierdol blad["wiadomosc_kurwa"]
            } wyczysc_kurwa {
                wypierdol "cleanup"
            }
        }
        """
        self.assertEqual(self.run_program(source), "user_error\ndupa\ncleanup\n")

    def test_handled_runtime_error_continues(self):
        source = """
        program {
            wjebaj {
                kurwa x = 1 / 0
            } zlap_kurwa blad {
                pierdol "caught"
            }
            wypierdol "after"
        }
        """
        self.assertEqual(self.run_program(source), "caught\nafter\n")

    def test_unhandled_error_raises(self):
        source = """
        program {
            wyrzuc_kurwa "błąd"
        }
        """
        with self.assertRaises(InterpreterError):
            self.run_program(source)

    def test_function_error_propagation(self):
        source = """
        program {
            odpierdol funkcja f() {
                wyrzuc_kurwa "z funkcji"
            }
            wjebaj {
                f()
            } zlap_kurwa blad {
                pierdol blad["wiadomosc_kurwa"]
            }
        }
        """
        self.assertEqual(self.run_program(source), "z funkcji\n")


if __name__ == "__main__":
    unittest.main()
