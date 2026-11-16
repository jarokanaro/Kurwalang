import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.main import main


class CliTestCase(unittest.TestCase):
    def run_main(self, args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_version_and_help(self):
        code, out, err = self.run_main(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("1.12.0", out)
        self.assertEqual(err, "")

        code, out, err = self.run_main(["pomoc"])
        self.assertEqual(code, 0)
        self.assertIn("zainicjuj", out)
        self.assertIn("uruchom", out)
        self.assertEqual(err, "")

    def test_init_and_run_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                code, out, err = self.run_main(["zainicjuj", "demo_app"])
                self.assertEqual(code, 0)
                self.assertIn("demo_app", out)
                self.assertEqual(err, "")

                source = Path(tmp) / "src" / "main.kurwa"
                self.assertTrue(source.exists())
                code, out, err = self.run_main(["uruchom", str(source)])
                self.assertEqual(code, 0)
                self.assertIn("KURWA LANG v1.12", out)
                self.assertEqual(err, "")
            finally:
                os.chdir(old_cwd)

    def test_pack_install_list_and_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                code, _, _ = self.run_main(["zainicjuj", "demo"])
                self.assertEqual(code, 0)

                pkg = Path(tmp) / "packages" / "tiny"
                pkg.mkdir(parents=True)
                (pkg / "kurwa.pack").write_text(
                    "nazwa: tiny\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\n",
                    encoding="utf-8",
                )
                (pkg / "src").mkdir()
                (pkg / "src" / "tiny.kurwa").write_text("kurwa liczba = 7\n", encoding="utf-8")

                code, out, err = self.run_main(["zainstaluj", str(pkg)])
                self.assertEqual(code, 0)
                self.assertIn("tiny", out)
                self.assertEqual(err, "")

                code, out, err = self.run_main(["lista"])
                self.assertEqual(code, 0)
                self.assertIn("tiny", out)
                self.assertEqual(err, "")

                code, out, err = self.run_main(["odinstaluj", "tiny"])
                self.assertEqual(code, 0)
                self.assertIn("UNINSTALLED tiny", out)
                self.assertEqual(err, "")
            finally:
                os.chdir(old_cwd)

    def test_script_argument_passthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "demo.kurwa"
            script.write_text('program { zajeb_moduł "system" pierdol system.argumenty()[0] }\n', encoding="utf-8")
            code, out, err = self.run_main([str(script), "hej"])
            self.assertEqual(code, 0)
            self.assertIn("hej", out)
            self.assertEqual(err, "")


if __name__ == "__main__":
    unittest.main()
