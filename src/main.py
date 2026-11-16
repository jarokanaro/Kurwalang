"""Command-line entry point for KURWA LANG."""

import json
import sys
import time
from pathlib import Path
from typing import Sequence

try:
    from .interpreter import Interpreter, InterpreterError, TestFailure, TestSkipSignal
    from .lexer import Lexer, LexerError
    from .linter import Linter, Severity
    from .parser import Parser, ParserError
    from .package_manager import ProjectPackageManager, PackageManagerError, find_project_root
    from .version import LANGUAGE_VERSION
except ImportError:
    from interpreter import Interpreter, InterpreterError, TestFailure, TestSkipSignal
    from lexer import Lexer, LexerError
    from linter import Linter, Severity
    from parser import Parser, ParserError
    from package_manager import ProjectPackageManager, PackageManagerError, find_project_root
    from version import LANGUAGE_VERSION

_COMMAND_ALIASES = {
    "run": "run",
    "uruchom": "run",
    "init": "init",
    "zainicjuj": "init",
    "install": "install",
    "zainstaluj": "install",
    "uninstall": "uninstall",
    "odinstaluj": "uninstall",
    "list": "list",
    "lista": "list",
    "update": "update",
    "zaktualizuj": "update",
    "aktualizuj": "update",
    "help": "help",
    "pomoc": "help",
    "version": "version",
    "wersja": "version",
    "testuj_kurwa": "testuj_kurwa",
    "test": "testuj_kurwa",
    "testuj": "testuj_kurwa",
    "sprawdz_kurwa": "sprawdz_kurwa",
    "sprawdz": "sprawdz_kurwa",
}


def _project_manager_for_cli() -> ProjectPackageManager:
    root = find_project_root(Path.cwd())
    if root is None:
        root = Path.cwd()
    return ProjectPackageManager(root)


def _run_source_file(source_path: Path, program_arguments: list[str]) -> int:
    try:
        source = source_path.read_text(encoding="utf-8")
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Interpreter(program_arguments).run(program, source_path.resolve())
    except OSError as error:
        print(f"File error: {error}", file=sys.stderr)
        return 1
    except (LexerError, ParserError, InterpreterError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


def _build_help() -> str:
    return """KURWA LANG CLI

Użycie:
  python3 src/main.py <plik.kurwa> [argumenty programu]
  python3 src/main.py uruchom <plik.kurwa> [argumenty programu]
  python3 src/main.py zainicjuj [nazwa_projektu]
  python3 src/main.py zainstaluj <pakiet|ścieżka>
  python3 src/main.py odinstaluj <pakiet>
  python3 src/main.py lista
  python3 src/main.py zaktualizuj
  python3 src/main.py testuj_kurwa <plik|katalog> [--filter "nazwa"]
  python3 src/main.py sprawdz_kurwa <plik|katalog> [--quiet]
  python3 src/main.py --version
  python3 src/main.py --help

Komendy kompatybilne (stare aliasy): run, init, install, uninstall, list, update, help, version.
"""


def _normalize_command(raw_command: str | None) -> str:
    if raw_command is None:
        return ""
    command = raw_command.strip().lower()
    return _COMMAND_ALIASES.get(command, command)


def _discover_test_files(target: str | None) -> list[Path]:
    if target is None:
        return []
    path = Path(target)
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(child for child in path.rglob("*.kurwa") if child.is_file())
    return []


def _discover_lint_files(target: str | None) -> list[Path]:
    if target is None:
        return []
    path = Path(target)
    if path.is_file():
        return [path] if path.suffix == ".kurwa" else []
    if path.is_dir():
        return sorted(child for child in path.rglob("*.kurwa") if child.is_file())
    return []


def _run_kurwa_lint(target: str | None, quiet: bool = False, verbose: bool = False) -> int:
    files = _discover_lint_files(target)
    if not files:
        print("KURWA ERROR: nie znaleziono plików .kurwa do sprawdzenia", file=sys.stderr)
        return 2

    total_diagnostics = 0
    error_count = 0
    warning_count = 0
    for file_path in files:
        diagnostics = Linter().lint_file(file_path)
        for diagnostic in diagnostics:
            total_diagnostics += 1
            if diagnostic.severity == Severity.ERROR:
                error_count += 1
            elif diagnostic.severity == Severity.WARNING:
                warning_count += 1
            if not quiet or (verbose and diagnostic.severity == Severity.INFO):
                print(diagnostic.format())
        if not diagnostics and not quiet:
            print(f"OK: {file_path}")

    if not quiet:
        print()
        print(f"BŁĘDY: {error_count}")
        print(f"OSTRZEŻENIA: {warning_count}")
        print(f"RAZEM: {total_diagnostics}")
    return 1 if error_count else 0


def _run_kurwa_test_suite(target: str | None, filter_name: str | None = None) -> int:
    files = _discover_test_files(target)
    if not files:
        print("KURWA ERROR: nie znaleziono plików testowych .kurwa", file=sys.stderr)
        return 2

    total = 0
    passed = 0
    failed = 0
    skipped = 0
    started = time.perf_counter()

    print("KURWA TESTY")
    for file_path in files:
        try:
            source = file_path.read_text(encoding="utf-8")
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse_module()
        except (OSError, LexerError, ParserError) as error:
            print(f"TEST NIE PRZESZEDL: {file_path}")
            print(f"plik: {file_path}")
            print(f"blad: {error}")
            failed += 1
            total += 1
            continue

        interpreter = Interpreter()
        for statement in program.body.statements:
            if not hasattr(statement, "name"):
                continue
            if filter_name is not None and statement.name != filter_name:
                continue
            result = interpreter._execute_test_declaration(statement, interpreter.global_environment)
            total += 1
            status = result.get("status")
            if status == "passed":
                passed += 1
                print(f"PRZESZLO: {result['name']}")
            elif status == "failed":
                failed += 1
                print(f"TEST NIE PRZESZEDL: {result['name']}")
                print(f"plik: {file_path}")
                if result.get("message"):
                    print(f"bledy: {result['message']}")
                if result.get("actual") is not None:
                    print(f"dostano: {result['actual']}")
                if result.get("expected") is not None:
                    print(f"oczekiwano: {result['expected']}")
            elif status == "skipped":
                skipped += 1
                print(f"POMINIEC: {result['name']}")
                if result.get("reason"):
                    print(f"powod: {result['reason']}")

    duration = time.perf_counter() - started
    print()
    print(f"PRZESZLO: {passed}")
    print(f"WYJEBANE: {failed}")
    print(f"POMINIĘTE: {skipped}")
    print(f"RAZEM: {total}")
    print(f"CZAS: {duration:.2f}s")
    return 0 if failed == 0 else 1


def _handle_pack_command(command: str, target: str | None, rest: list[str]) -> int:
    manager = _project_manager_for_cli()
    try:
        if command == "init":
            name = target if target else None
            version = "0.1.0"
            manifest = manager.init_project(name=name, version=version)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
        if command == "install":
            if not target:
                raise ValueError("install requires a package path or package name")
            install_path = Path(target)
            if install_path.exists():
                result = manager.install_local_package(install_path)
            else:
                result = manager.install_local_package(manager.project_root / "packages" / target)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if command == "uninstall":
            if not target:
                raise ValueError("uninstall requires a package name")
            manager.uninstall(target)
            print(f"UNINSTALLED {target}")
            return 0
        if command == "list":
            packages = manager.list_installed()
            print(json.dumps(packages, ensure_ascii=False, indent=2))
            return 0
        if command == "update":
            lock = manager.update()
            print(json.dumps(lock, ensure_ascii=False, indent=2))
            return 0
        if command == "help":
            print(_build_help())
            return 0
        if command == "version":
            print(LANGUAGE_VERSION)
            return 0
        if command == "testuj_kurwa":
            filter_name = None
            if rest and rest[0] == "--filter":
                if len(rest) > 1:
                    filter_name = rest[1]
            return _run_kurwa_test_suite(target, filter_name)
        if command == "sprawdz_kurwa":
            quiet = False
            verbose = False
            if rest:
                for item in rest:
                    if item == "--quiet":
                        quiet = True
                    elif item == "--verbose":
                        verbose = True
            return _run_kurwa_lint(target, quiet=quiet, verbose=verbose)
    except (PackageManagerError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if command == "run":
        if not target:
            print("KURWA ERROR: brak pliku .kurwa do uruchomienia", file=sys.stderr)
            return 2
        return _run_source_file(Path(target), rest)

    print(_build_help(), file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print(_build_help(), file=sys.stderr)
        return 2

    first = arguments[0]
    if first in {"--version", "-V"}:
        print(LANGUAGE_VERSION)
        return 0
    if first in {"--help", "-h"}:
        print(_build_help())
        return 0

    normalized = _normalize_command(first)
    if normalized in {"run", "init", "install", "uninstall", "list", "update", "help", "version", "testuj_kurwa", "sprawdz_kurwa"}:
        return _handle_pack_command(normalized, arguments[1] if len(arguments) > 1 else None, arguments[2:])

    if first.endswith(".kurwa") or Path(first).exists() or first.lower().endswith(".kurwa"):
        return _run_source_file(Path(first), arguments[1:])

    if not first.startswith("-"):
        return _run_source_file(Path(first), arguments[1:])

    print(_build_help(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
