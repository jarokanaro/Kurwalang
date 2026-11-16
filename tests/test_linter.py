import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from src.main import main


class LinterTestCase(unittest.TestCase):
    def run_main(self, args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_clean_program_has_no_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.kurwa"
            path.write_text('program {\n    kurwa x = 2 + 2\n    pierdol x\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 0)
            self.assertIn("OK:", out)
            self.assertEqual(err, "")

    def test_unused_variable_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unused.kurwa"
            path.write_text('program {\n    kurwa x = 10\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 0)
            self.assertIn("K001", out)
            self.assertIn("x", out)
            self.assertEqual(err, "")

    def test_undefined_variable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "undefined.kurwa"
            path.write_text('program {\n    pierdol x\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("K010", out)
            self.assertIn("x", out)
            self.assertEqual(err, "")

    def test_constant_division_by_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "division.kurwa"
            path.write_text('program {\n    pierdol 10 / 0\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("K040", out)
            self.assertIn("dzielenie", out.lower())
            self.assertEqual(err, "")

    def test_no_execution_during_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "side_effect.kurwa"
            path.write_text('program {\n    plik.zapisz("side_effect.txt", "KURWA")\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("K010", out)
            self.assertFalse(Path(tmp, "side_effect.txt").exists())
            self.assertEqual(err, "")

    def test_invalid_syntax_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.kurwa"
            path.write_text('program {\n    kurwa x = \n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("K000", out)
            self.assertEqual(err, "")

    def test_type_inference_for_basic_values(self):
        diagnostics = self._lint_text('program {\n    kurwa liczba = 42\n    kurwa tekst = "hej"\n    kurwa flaga = prawda\n    kurwa lista = [1, 2, 3]\n    kurwa mapa = {"klucz": 5}\n}\n')
        self.assertEqual([], [d for d in diagnostics if d.code.startswith("T")])

    def test_type_errors_are_reported(self):
        diagnostics = self._lint_text('program {\n    kurwa x = "tekst"\n    pierdol x + 1\n}\n')
        self.assertTrue(any(d.code.startswith("T") for d in diagnostics))

    def test_no_execution_during_type_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "no_execute.kurwa"
            target.write_text('program {\n    plik.zapisz("side_effect.txt", "KURWA")\n}\n', encoding="utf-8")
            code, out, err = self.run_main(["sprawdz_kurwa", str(target)])
            self.assertEqual(code, 1)
            self.assertIn("K010", out)
            self.assertFalse((Path(tmp) / "side_effect.txt").exists())
            self.assertEqual(err, "")

    def _lint_text(self, source):
        from src.linter import Linter
        return Linter().lint_source(source, "memory.kurwa")


if __name__ == "__main__":
    unittest.main()
