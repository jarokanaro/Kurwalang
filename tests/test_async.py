import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter
from src.lexer import Lexer
from src.parser import Parser


class AsyncExecutionTestCase(unittest.TestCase):
    def run_async_program(self, source: str, arguments=None) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter(arguments).run_async(program, Path("/tmp/kurwa-async-test.kurwa"))
        return output.getvalue()

    def test_async_function_and_await(self):
        source = '''
        program {
            odpierdol_kurwicznie funkcja slow() {
                kurwa_pauza(0.02)
                oddaj "gotowe"
            }

            kurwa wynik = czekaj_kurwa(slow())
            pierdol wynik
        }
        '''
        self.assertEqual(self.run_async_program(source), "gotowe\n")

    def test_task_concurrency_and_wait_multiple(self):
        source = '''
        program {
            odpierdol_kurwicznie funkcja robota(name, delay) {
                kurwa_pauza(delay)
                oddaj name
            }

            kurwa a = wyjeb_task(robota, "a", 0.05)
            kurwa b = wyjeb_task(robota, "b", 0.01)
            kurwa wynik = czekaj_wiele_kurwa(a, b)
            pierdol wynik[0]
            pierdol wynik[1]
        }
        '''
        self.assertEqual(self.run_async_program(source), "a\nb\n")

    def test_async_error_propagation(self):
        source = '''
        program {
            odpierdol_kurwicznie funkcja fail() {
                wyrzuc_kurwa "z async"
            }

            wjebaj {
                czekaj_kurwa(fail())
            } zlap_kurwa blad {
                pierdol blad["wiadomosc_kurwa"]
            }
        }
        '''
        self.assertEqual(self.run_async_program(source), "z async\n")


if __name__ == "__main__":
    unittest.main()
