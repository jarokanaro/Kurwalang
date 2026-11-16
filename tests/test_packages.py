import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.interpreter import Interpreter
from src.lexer import Lexer
from src.package_manager import ProjectPackageManager, ManifestError
from src.parser import Parser


class PackageManagerTestCase(unittest.TestCase):
    def run_program(self, source: str, source_path: Path | None = None) -> str:
        program = Parser(Lexer(source).tokenize()).parse()
        output = io.StringIO()
        with redirect_stdout(output):
            Interpreter().run(program, source_path)
        return output.getvalue()

    def test_manifest_init_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manager = ProjectPackageManager(root)
            manager.init_project("demo_app")
            manifest = manager.load_manifest()
            self.assertEqual(manifest.name, "demo_app")
            self.assertEqual(manifest.version, "0.1.0")
            self.assertEqual(manager.read_lockfile(), {})

    def test_install_local_package_and_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg_dir = root / "packages" / "mathz"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "kurwa.pack").write_text(
                "nazwa: mathz\nwersja: 1.2.0\nwymagana_wersja_kurwa: 1.4.0\nzależności:\n",
                encoding="utf-8",
            )
            src_dir = pkg_dir / "src"
            src_dir.mkdir()
            (src_dir / "mathz.kurwa").write_text(
                'kurwa wynik = 21\n',
                encoding="utf-8",
            )
            manager = ProjectPackageManager(root)
            manager.install_local_package(pkg_dir)
            source = '''
            program {
                zajeb_moduł "mathz"
                pierdol mathz.wynik
            }
            '''
            self.assertEqual(self.run_program(source, root / "main.kurwa"), "21\n")

    def test_dependency_resolution_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_dir = root / "packages" / "a"; a_dir.mkdir(parents=True)
            (a_dir / "kurwa.pack").write_text("nazwa: a\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\nzależności:\n  b: >=2.0.0\n", encoding="utf-8")
            (a_dir / "src").mkdir(); (a_dir / "src" / "a.kurwa").write_text("kurwa x = 1\n", encoding="utf-8")
            b_dir = root / "packages" / "b"; b_dir.mkdir(parents=True)
            (b_dir / "kurwa.pack").write_text("nazwa: b\nwersja: 2.0.0\nwymagana_wersja_kurwa: 1.4.0\n", encoding="utf-8")
            (b_dir / "src").mkdir(); (b_dir / "src" / "b.kurwa").write_text("kurwa y = 2\n", encoding="utf-8")
            manager = ProjectPackageManager(root)
            manager.install_local_package(a_dir)
            self.assertIn("b", manager.read_lockfile())

            c_dir = root / "packages" / "c"; c_dir.mkdir(parents=True)
            (c_dir / "kurwa.pack").write_text("nazwa: c\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\nzależności:\n  b: <2.0.0\n", encoding="utf-8")
            (c_dir / "src").mkdir(); (c_dir / "src" / "c.kurwa").write_text("kurwa y = 3\n", encoding="utf-8")
            with self.assertRaises(Exception):
                manager.install_local_package(c_dir)

    def test_cli_commands_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manager = ProjectPackageManager(root)
            manager.init_project("demo")
            pkg = root / "packages" / "tiny"; pkg.mkdir(parents=True)
            (pkg / "kurwa.pack").write_text("nazwa: tiny\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\n", encoding="utf-8")
            (pkg / "src").mkdir(); (pkg / "src" / "tiny.kurwa").write_text("kurwa liczba = 7\n", encoding="utf-8")
            manager.install_local_package(pkg)
            installed = manager.list_installed()
            self.assertEqual(installed[0]["nazwa"], "tiny")

    def test_dependency_cycle_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_dir = root / "packages" / "a"; a_dir.mkdir(parents=True)
            (a_dir / "kurwa.pack").write_text("nazwa: a\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\nzależności:\n  b: >=1.0.0\n", encoding="utf-8")
            (a_dir / "src").mkdir(); (a_dir / "src" / "a.kurwa").write_text("kurwa x = 1\n", encoding="utf-8")
            b_dir = root / "packages" / "b"; b_dir.mkdir(parents=True)
            (b_dir / "kurwa.pack").write_text("nazwa: b\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\nzależności:\n  a: >=1.0.0\n", encoding="utf-8")
            (b_dir / "src").mkdir(); (b_dir / "src" / "b.kurwa").write_text("kurwa y = 2\n", encoding="utf-8")
            manager = ProjectPackageManager(root)
            with self.assertRaises(Exception):
                manager.install_local_package(a_dir)

    def test_bad_manifest_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manager = ProjectPackageManager(root)
            bad = root / "packages" / "bad"; bad.mkdir(parents=True)
            (bad / "kurwa.pack").write_text("nazwa: bad\n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                manager.install_local_package(bad)

            unsafe = root / "packages" / "../unsafe"; unsafe.mkdir(parents=True)
            (unsafe / "kurwa.pack").write_text("nazwa: unsafe\nwersja: 1.0.0\nwymagana_wersja_kurwa: 1.4.0\n", encoding="utf-8")
            with self.assertRaises(Exception):
                manager.install_local_package(unsafe)


if __name__ == "__main__":
    unittest.main()
