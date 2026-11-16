import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from src.main import main


class KurwaTestSystemTestCase(unittest.TestCase):
    def run_main(self, args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_kurwa_native_test_syntax_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                tests_dir = Path(tmp) / "tests" / "kurwa"
                tests_dir.mkdir(parents=True)
                suite = tests_dir / "demo.kurwa"
                suite.write_text(
                    '''program {
    testuj_kurwa "dodawanie" {
        sprawdz_kurwa 2 + 2 == 4
        sprawdz_kurwa 5 > 3
        sprawdz_kurwa 1 != 2
    }

    testuj_kurwa "brak_bledu" {
        oczekuj_blad_kurwa {
            wyrzuc_kurwa "kurwa"
        }
    }
}
''', encoding="utf-8",
                )
                code, out, err = self.run_main(["testuj_kurwa", str(tests_dir)])
                self.assertEqual(code, 0, msg=err or out)
                self.assertIn("PRZESZLO", out)
                self.assertIn("dodawanie", out)
                self.assertEqual(err, "")
            finally:
                os.chdir(old_cwd)

    def test_kurwa_test_failure_reports_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                suite = Path(tmp) / "tests.kurwa"
                suite.write_text(
                    '''program {
    testuj_kurwa "fail" {
        sprawdz_kurwa 2 + 2 == 5
    }
}
''', encoding="utf-8",
                )
                code, out, err = self.run_main(["testuj_kurwa", str(suite)])
                self.assertNotEqual(code, 0)
                self.assertIn("fail", out)
                self.assertIn("TEST NIE PRZESZEDL", out)
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
