"""Tree-walk interpreter for KURWA LANG."""

import math
import json
import os
import platform
import random
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from .version import LANGUAGE_VERSION
except ImportError:
    from version import LANGUAGE_VERSION

try:
    from .ast import (
        Block,
        BinaryExpression,
        CallExpression,
        AppendStatement,
        BooleanLiteral,
        DeleteMapEntryStatement,
        ExitStatement,
        Expression,
        ExpressionStatement,
        FunctionDeclaration,
        IfStatement,
        ImportStatement,
        IndexExpression,
        IncrementStatement,
        ListLiteral,
        MapLiteral,
        MemberExpression,
        LoopExitStatement,
        LessThanExpression,
        NumberLiteral,
        PopListExpression,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        SetListElementStatement,
        SliceExpression,
        StringLiteral,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        TestDeclaration,
        AssertStatement,
        ExpectErrorStatement,
        SkipStatement,
    )
    from .extensions import Extension, ExtensionLoadError, ExtensionRegistry, safe_from_kurwa, safe_to_kurwa
except ImportError:
    from ast import (
        Block,
        BinaryExpression,
        CallExpression,
        AppendStatement,
        BooleanLiteral,
        DeleteMapEntryStatement,
        ExitStatement,
        Expression,
        ExpressionStatement,
        FunctionDeclaration,
        IfStatement,
        ImportStatement,
        IndexExpression,
        IncrementStatement,
        ListLiteral,
        MapLiteral,
        MemberExpression,
        LoopExitStatement,
        LessThanExpression,
        NumberLiteral,
        PopListExpression,
        PrintTextStatement,
        PrintValueStatement,
        Program,
        ReturnStatement,
        SetListElementStatement,
        SliceExpression,
        StringLiteral,
        ThrowStatement,
        TryStatement,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        TestDeclaration,
        AssertStatement,
        ExpectErrorStatement,
        SkipStatement,
    )
    from extensions import Extension, ExtensionLoadError, ExtensionRegistry, safe_from_kurwa, safe_to_kurwa


class InterpreterError(Exception):
    """Raised for invalid runtime operations."""


class ProgramExit(Exception):
    """Internal signal for the spierdalaj statement."""


class LoopExitSignal(Exception):
    """Internal signal for the wypierdalaj statement."""


class UserRuntimeError(InterpreterError):
    def __init__(self, error_type: str, message: str, source: str | None = None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.source = source or "brak_źródła"

    def as_map(self):
        return RuntimeMap([
            ("typ_kurwa", self.error_type),
            ("wiadomosc_kurwa", self.message),
            ("zrodlo_kurwa", self.source),
        ])


class TestFailure(InterpreterError):
    def __init__(self, test_name: str, message: str, actual=None, expected=None):
        super().__init__(message)
        self.test_name = test_name
        self.message = message
        self.actual = actual
        self.expected = expected


class TestSkipSignal(Exception):
    def __init__(self, reason: str | None = None):
        self.reason = reason


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class NoValue:
    def __str__(self):
        return "brak_wyniku"


NO_VALUE = NoValue()


class RuntimeMap:
    def __init__(self, entries=None):
        self.values = dict(entries or [])

    def __str__(self):
        return str(self.values)

    __repr__ = __str__


class RuntimeHttpResponse(RuntimeMap):
    def __init__(self, status_code: int, url: str, text: str, headers: dict[str, str], success: bool, json_value=None):
        payload = {
            "status_kurwa": status_code,
            "tekst_kurwa": text,
            "naglowki_kurwa": RuntimeMap((str(key), str(value)) for key, value in headers.items()),
            "adres_kurwa": url,
            "udalo_sie_kurwa": success,
            "json_kurwa": json_value if json_value is not None else NO_VALUE,
        }
        super().__init__(payload.items())


class RuntimeModule:
    def __init__(self, name: str, path: Path, environment):
        self.name = name
        self.path = path
        self.environment = environment

    def __str__(self):
        return f"<moduł {self.name}>"


class ModuleLoader:
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.cache = {}
        self.loading = []

    def load(self, module_name: str, importer_path: Path | None):
        standard_name = self._standard_name(module_name)
        if standard_name == "dane" and self._resolve(module_name, importer_path).exists():
            standard_name = None
        if standard_name is not None:
            key = f"stdlib:{standard_name}"
            if key in self.loading:
                raise InterpreterError(f"KURWA BŁĄD: cykliczny import modułu standardowego: {standard_name}")
            if key in self.cache:
                return self.cache[key]
            self.loading.append(key)
            try:
                module = self.interpreter._build_standard_module(standard_name)
                self.cache[key] = module
                return module
            finally:
                self.loading.pop()
        module_path = self._resolve(module_name, importer_path)
        if module_path in self.loading:
            cycle_start = self.loading.index(module_path)
            cycle = self.loading[cycle_start:] + [module_path]
            chain = " -> ".join(path.stem for path in cycle)
            raise InterpreterError(f"KURWA BŁĄD: cykliczny import modułu: {chain}")
        if module_path in self.cache:
            return self.cache[module_path]

        self.loading.append(module_path)
        try:
            source = module_path.read_text(encoding="utf-8")
            try:
                from .lexer import Lexer
                from .parser import Parser
            except ImportError:
                from lexer import Lexer
                from parser import Parser

            program = Parser(Lexer(source).tokenize()).parse_module()
            environment = Environment(self.interpreter.builtins_environment, module_path)
            module = RuntimeModule(module_path.stem, module_path, environment)
            self.cache[module_path] = module
            self.interpreter._execute_block(program.body, environment)
            return module
        except OSError as error:
            raise InterpreterError(
                f"KURWA BŁĄD: modułu {module_path} nie można odczytać: {error}"
            ) from error
        except Exception as error:
            if isinstance(error, InterpreterError) and str(error).startswith(f"{module_path}:"):
                raise
            raise InterpreterError(f"{module_path}: {error}") from error
        finally:
            self.loading.pop()

    @staticmethod
    def _standard_name(module_name: str) -> str | None:
        if "/" in module_name or "\\" in module_name:
            return None
        name = Path(module_name).name
        if name.endswith(".kurwa"):
            name = name[:-6]
        if name in {"matematyka", "losuj", "tekst", "czas", "system", "plik", "katalog", "sciezka", "dane", "siec"}:
            return name
        return None

    @staticmethod
    def _resolve(module_name: str, importer_path: Path | None) -> Path:
        if "." in Path(module_name).name and not module_name.endswith(".kurwa"):
            raise InterpreterError("KURWA BŁĄD: import może wskazywać tylko plik .kurwa")
        if not module_name.endswith(".kurwa"):
            module_name += ".kurwa"
        candidate = Path(module_name)
        if candidate.suffix != ".kurwa":
            raise InterpreterError("KURWA BŁĄD: import może wskazywać tylko plik .kurwa")
        base = importer_path.parent if importer_path is not None else Path.cwd()
        direct = (base / candidate).resolve()
        if direct.exists():
            return direct

        package_candidate = ModuleLoader._find_package_candidate(module_name, importer_path)
        if package_candidate is not None:
            return package_candidate
        return direct

    @staticmethod
    def _find_package_candidate(module_name: str, importer_path: Path | None) -> Path | None:
        name = Path(module_name).name
        if name.endswith(".kurwa"):
            name = name[:-6]
        if importer_path is not None:
            bases = [importer_path.parent]
            current = importer_path.parent
            while current != current.parent:
                current = current.parent
                bases.append(current)
        else:
            bases = [Path.cwd()]

        seen = set()
        for base in bases:
            for root_name in (".kurwa_packages", "packages"):
                root = base / root_name
                if not root.exists():
                    continue
                package_root = root / name
                if package_root.exists():
                    candidates = [package_root / "src" / f"{name}.kurwa"]
                    for child in package_root.iterdir():
                        if child.is_dir():
                            try:
                                from .package_manager import Version
                                Version.parse(child.name)
                                candidate = child / "src" / f"{name}.kurwa"
                                if candidate.exists():
                                    candidates.append(candidate)
                            except Exception:
                                continue
                    for candidate in candidates:
                        resolved = candidate.resolve()
                        if resolved.exists() and resolved not in seen:
                            seen.add(resolved)
                            return resolved
                direct = root / name / "src" / f"{name}.kurwa"
                if direct.exists():
                    resolved = direct.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        return resolved
        return None


class AsyncTask:
    def __init__(self, runner, arguments):
        self.runner = runner
        self.arguments = arguments
        self.result = None
        self.error = None
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            value = self.runner(self.arguments)
            self.result = value.wait() if isinstance(value, AsyncTask) else value
        except BaseException as error:  # pragma: no cover - runtime propagation below
            self.error = error
        finally:
            self._done.set()

    def wait(self):
        self._done.wait()
        if self.error is not None:
            raise self.error
        return self.result


class RuntimeCallable:
    name = "funkcja"

    def call(self, arguments):
        raise NotImplementedError

    def check_argument_count(self, count: int) -> None:
        return


class ExtensionFunction(RuntimeCallable):
    def __init__(self, name: str, function, extension_name: str):
        self.name = name
        self.function = function
        self.extension_name = extension_name

    def call(self, arguments):
        try:
            python_args = [safe_from_kurwa(arg) for arg in arguments]
            result = self.function(*python_args)
            return safe_to_kurwa(result)
        except Exception as error:
            raise InterpreterError(
                f"KURWA ERROR: rozszerzenie {self.extension_name} wywaliło się w {self.name}: {error}"
            ) from error

    def check_argument_count(self, count: int) -> None:
        try:
            import inspect

            signature = inspect.signature(self.function)
            parameters = [
                parameter for parameter in signature.parameters.values()
                if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            if any(parameter.kind == inspect.Parameter.VAR_POSITIONAL for parameter in signature.parameters.values()):
                return
            if len(parameters) != count:
                raise InterpreterError(
                    f"KURWA ERROR: rozszerzenie {self.extension_name} funkcja {self.name} wymaga {len(parameters)} argumentów, otrzymała {count}"
                )
        except (TypeError, ValueError):
            return


class RuntimeExtension(RuntimeModule):
    def __init__(self, extension: Extension, registry: ExtensionRegistry):
        self.extension = extension
        self.registry = registry
        self.name = extension.name
        self.path = Path(f"<extension:{extension.name}>")
        environment = Environment()
        environment.define("metadane", RuntimeMap([
            ("nazwa_kurwa", extension.name),
            ("wersja_kurwa", extension.version),
            ("opis_kurwa", extension.description),
            ("autor_kurwa", extension.author or "nieznany"),
            ("mozliwosci_kurwa", [str(item) for item in extension.capabilities]),
        ]))
        for function_name, function in extension.functions.items():
            environment.define(function_name, ExtensionFunction(function_name, function, extension.name))
        super().__init__(extension.name, self.path, environment)

    def __str__(self):
        return f"<rozszerzenie {self.name}>"


class Environment:
    def __init__(self, parent=None, source_path: Path | None = None):
        self.values = {}
        self.parent = parent
        self.source_path = source_path or (parent.source_path if parent is not None else None)

    def define(self, name: str, value) -> None:
        self.values[name] = value

    def get(self, name: str):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise InterpreterError(f"KURWA ERROR: Undefined variable: {name}")

    def assign(self, name: str, value) -> None:
        if name in self.values:
            self.values[name] = value
        elif self.parent is not None:
            self.parent.assign(name, value)
        else:
            raise InterpreterError(f"KURWA ERROR: Undefined variable: {name}")


class RuntimeFunction(RuntimeCallable):
    def __init__(self, declaration: FunctionDeclaration, closure: Environment, interpreter):
        self.declaration = declaration
        self.closure = closure
        self.interpreter = interpreter

    def call(self, arguments):
        local = Environment(self.closure)
        for name, value in zip(self.declaration.parameters, arguments):
            local.define(name, value)
        try:
            self.interpreter._execute_block(self.declaration.body, local)
        except ReturnSignal as signal:
            return signal.value
        return NO_VALUE

    def check_argument_count(self, count: int) -> None:
        expected = len(self.declaration.parameters)
        if count != expected:
            raise InterpreterError(
                f"KURWA ERROR: Funkcja {self.declaration.name} wymaga "
                f"{expected} argumentów, otrzymała {count}"
            )


class AsyncFunction(RuntimeCallable):
    def __init__(self, declaration: FunctionDeclaration, closure: Environment, interpreter):
        self.declaration = declaration
        self.closure = closure
        self.interpreter = interpreter

    def call(self, arguments):
        return AsyncTask(self._invoke, arguments)

    def _invoke(self, arguments):
        local = Environment(self.closure)
        for name, value in zip(self.declaration.parameters, arguments):
            local.define(name, value)
        try:
            self.interpreter._execute_block(self.declaration.body, local)
        except ReturnSignal as signal:
            return signal.value
        return NO_VALUE

    def check_argument_count(self, count: int) -> None:
        expected = len(self.declaration.parameters)
        if count != expected:
            raise InterpreterError(
                f"KURWA ERROR: Funkcja {self.declaration.name} wymaga "
                f"{expected} argumentów, otrzymała {count}"
            )


class BuiltinFunction(RuntimeCallable):
    def __init__(self, name, function, argument_count, minimum_arguments=0):
        self.name = name
        self.function = function
        self.argument_count = argument_count
        self.minimum_arguments = minimum_arguments

    def call(self, arguments):
        return self.function(arguments)

    def check_argument_count(self, count: int) -> None:
        if self.argument_count is None and count >= self.minimum_arguments:
            return
        if self.argument_count is not None and count == self.argument_count:
            return
        expected = f"co najmniej {self.minimum_arguments}" if self.argument_count is None else str(self.argument_count)
        if self.argument_count is None and self.minimum_arguments == 1:
            expected = "co najmniej 1"
        raise InterpreterError(
            f"KURWA ERROR: Funkcja {self.name} wymaga {expected} argumentów, otrzymała {count}"
        )


class ExtensionRuntimeHandle:
    def __init__(self, extension_name: str, registry: ExtensionRegistry, metadata: dict):
        self.extension_name = extension_name
        self.registry = registry
        self.metadata = metadata
        self.functions = {}
        for name, function in registry.get(extension_name)["functions"].items():
            self.functions[name] = function

    def __getattr__(self, item):
        if item in self.functions:
            return self.functions[item]
        raise AttributeError(f"KURWA ERROR: rozszerzenie {self.extension_name} nie udostępnia {item}")

    def as_map(self):
        return RuntimeMap([
            ("nazwa_kurwa", self.extension_name),
            ("wersja_kurwa", self.metadata.get("version", "1.0.0")),
            ("opis_kurwa", self.metadata.get("description", "")),
            ("metadane", RuntimeMap(list(self.metadata.items()))),
        ])


class Interpreter:
    def __init__(self, program_arguments=None):
        self.program_arguments = list(program_arguments or [])
        self.builtins_environment = Environment()
        self.global_environment = Environment(self.builtins_environment)
        self.module_loader = ModuleLoader(self)
        self.extension_registry = ExtensionRegistry()
        self.extension_search_locations = [
            Path.cwd() / "extensions",
            Path.cwd() / ".kurwa_extensions",
            Path.cwd() / "examples" / "extensions",
            Path.cwd() / "packages",
            Path.cwd(),
        ]
        self.builtins_environment.define(
            "ile_kurwa", BuiltinFunction("ile_kurwa", self._builtin_length, 1)
        )
        self.builtins_environment.define(
            "jest_kurwa", BuiltinFunction("jest_kurwa", self._builtin_has_key, 2)
        )
        self.builtins_environment.define(
            "czekaj_kurwa", BuiltinFunction("czekaj_kurwa", self._builtin_await, 1)
        )
        self.builtins_environment.define(
            "wyjeb_task", BuiltinFunction("wyjeb_task", self._builtin_spawn_task, None, 1)
        )
        self.builtins_environment.define(
            "czekaj_wiele_kurwa", BuiltinFunction("czekaj_wiele_kurwa", self._builtin_await_many, None, 1)
        )
        self.builtins_environment.define(
            "kurwa_pauza", BuiltinFunction("kurwa_pauza", self._builtin_pause, 1)
        )
        self.builtins_environment.define(
            "zaladuj_rozszerzenie", BuiltinFunction("zaladuj_rozszerzenie", self._builtin_load_extension, 1)
        )
        self.builtins_environment.define(
            "wywal_rozszerzenie", BuiltinFunction("wywal_rozszerzenie", self._builtin_unload_extension, 1)
        )
        self.builtins_environment.define(
            "rozszerzenia_kurwa", BuiltinFunction("rozszerzenia_kurwa", self._builtin_list_extensions, 0)
        )
        for name, function, count in (
            ("wielkie_kurwa", self._builtin_upper, 1),
            ("male_kurwa", self._builtin_lower, 1),
            ("zawiera_kurwa", self._builtin_contains, 2),
            ("zamien_kurwa", self._builtin_replace, 3),
            ("znajdz_kurwa", self._builtin_find, 2),
            ("tekst_kurwa", self._builtin_text, 1),
            ("liczba_kurwa", self._builtin_number, 1),
        ):
            self.builtins_environment.define(name, BuiltinFunction(name, function, count))

    def _builtin_await(self, arguments):
        task = arguments[0]
        if not isinstance(task, AsyncTask):
            return task
        return task.wait()

    def _builtin_load_extension(self, arguments):
        extension_name = arguments[0]
        if not isinstance(extension_name, str):
            raise InterpreterError("KURWA ERROR: zaladuj_rozszerzenie wymaga nazwy string")
        extension = self._load_extension_by_name(extension_name)
        registry_entry = self.extension_registry.get(extension_name)
        for function_name in registry_entry["functions"]:
            if function_name in self.builtins_environment.values:
                raise InterpreterError(f"KURWA ERROR: rozszerzenie {extension_name} próbuje zastąpić istniejącą funkcję {function_name}")
        return extension

    def _builtin_unload_extension(self, arguments):
        extension_name = arguments[0]
        if not isinstance(extension_name, str):
            raise InterpreterError("KURWA ERROR: wywal_rozszerzenie wymaga nazwy string")
        self.extension_registry.unregister(extension_name)
        return True

    def _builtin_list_extensions(self, arguments):
        discovered = set(self.extension_registry.list_names())
        for location in self.extension_search_locations:
            if not location.exists():
                continue
            for candidate in sorted(location.iterdir()):
                if candidate.is_file() and candidate.suffix == ".py" and not candidate.name.startswith("_"):
                    discovered.add(candidate.stem)
        return [name for name in sorted(discovered)]

    def _builtin_spawn_task(self, arguments):
        if len(arguments) < 1:
            raise InterpreterError("KURWA ERROR: wyjeb_task wymaga co najmniej funkcji")
        callee = arguments[0]
        if not isinstance(callee, RuntimeCallable):
            raise InterpreterError("KURWA ERROR: wyjeb_task wymaga funkcji lub asynchronicznej procedury")
        task_arguments = list(arguments[1:])

        def task_runner(call_args):
            value = callee.call(call_args)
            if isinstance(value, AsyncTask):
                return value.wait()
            return value

        return AsyncTask(task_runner, task_arguments)

    def _builtin_await_many(self, arguments):
        if len(arguments) == 0:
            return []
        tasks = list(arguments)
        results = []
        for task in tasks:
            if not isinstance(task, AsyncTask):
                results.append(task)
            else:
                results.append(task.wait())
        return results

    def _builtin_pause(self, arguments):
        wait_time = arguments[0]
        if not self._is_number(wait_time):
            raise InterpreterError("KURWA ERROR: kurwa_pauza wymaga liczby w sekundach")
        time.sleep(float(wait_time))
        return NO_VALUE

    def _load_extension_by_name(self, extension_name: str):
        if not isinstance(extension_name, str) or not extension_name.strip() or extension_name in {"", ".", ".."}:
            raise InterpreterError("KURWA ERROR: niepoprawna nazwa rozszerzenia")
        if "/" in extension_name or "\\" in extension_name or extension_name.startswith("."):
            raise InterpreterError("KURWA ERROR: niedozwolona ścieżka rozszerzenia")
        if extension_name in self.builtins_environment.values:
            raise InterpreterError(
                f"KURWA ERROR: rozszerzenie {extension_name} nie może zastąpić zarezerwowanej funkcji runtime"
            )
        if self.extension_registry.has(extension_name):
            raise InterpreterError(f"KURWA ERROR: rozszerzenie {extension_name} jest już zarejestrowane")
        for location in self.extension_search_locations:
            candidate = location / f"{extension_name}.py"
            if not candidate.exists():
                continue
            try:
                import importlib.util

                spec = importlib.util.spec_from_file_location(f"extension_{extension_name}", str(candidate))
                if spec is None or spec.loader is None:
                    raise ExtensionLoadError("KURWA ERROR: nie można załadować rozszerzenia")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                extension = getattr(module, "EXTENSION", None)
                if extension is None:
                    raise ExtensionLoadError("KURWA ERROR: rozszerzenie nie dostarcza EXTENSION")
                if not isinstance(extension, Extension):
                    if isinstance(extension, dict):
                        extension = Extension(
                            name=str(extension.get("name", extension_name)),
                            version=str(extension.get("version", "1.0.0")),
                            description=str(extension.get("description", "")),
                            functions=dict(extension.get("functions", {})),
                        )
                    else:
                        raise ExtensionLoadError("KURWA ERROR: rozszerzenie ma niepoprawny format")
                if extension.name != extension_name:
                    raise ExtensionLoadError("KURWA ERROR: nazwa rozszerzenia nie zgadza się z plikiem")
                self.extension_registry.register(extension)
                return RuntimeExtension(extension, self.extension_registry)
            except Exception as exc:  # pragma: no cover - runtime error contract
                if isinstance(exc, InterpreterError):
                    raise
                raise InterpreterError(f"KURWA ERROR: nie można załadować rozszerzenia {extension_name}: {exc}") from exc
        raise InterpreterError(f"KURWA ERROR: nie znaleziono rozszerzenia {extension_name}")

    @staticmethod
    def _is_number(value) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _is_integer(value) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def _build_standard_module(self, name: str) -> RuntimeModule:
        path = Path("<stdlib>") / f"{name}.kurwa"
        environment = Environment(self.builtins_environment, path)
        module = RuntimeModule(name, path, environment)
        definitions = {
            "matematyka": {
                "PI": math.pi,
                "E": math.e,
                "abs_kurwa": BuiltinFunction("matematyka.abs_kurwa", self._stdlib_abs, 1),
                "potega_kurwa": BuiltinFunction("matematyka.potega_kurwa", self._stdlib_power, 2),
                "pierwiastek_kurwa": BuiltinFunction("matematyka.pierwiastek_kurwa", self._stdlib_sqrt, 1),
                "minimum_kurwa": BuiltinFunction("matematyka.minimum_kurwa", self._stdlib_minimum, None, 1),
                "maksimum_kurwa": BuiltinFunction("matematyka.maksimum_kurwa", self._stdlib_maximum, None, 1),
                "zaokraglij_kurwa": BuiltinFunction("matematyka.zaokraglij_kurwa", self._stdlib_round, 1),
            },
            "losuj": {
                "liczba": BuiltinFunction("losuj.liczba", self._stdlib_random_integer, 2),
                "ulamek": BuiltinFunction("losuj.ulamek", self._stdlib_random_float, 2),
                "element": BuiltinFunction("losuj.element", self._stdlib_random_element, 1),
            },
            "tekst": {
                "oczysc": BuiltinFunction("tekst.oczysc", self._stdlib_trim, 1),
                "zaczyna_sie": BuiltinFunction("tekst.zaczyna_sie", self._stdlib_starts_with, 2),
                "konczy_sie": BuiltinFunction("tekst.konczy_sie", self._stdlib_ends_with, 2),
                "rozdziel": BuiltinFunction("tekst.rozdziel", self._stdlib_split, 2),
                "polacz": BuiltinFunction("tekst.polacz", self._stdlib_join, 2),
                "powtorz": BuiltinFunction("tekst.powtorz", self._stdlib_repeat, 2),
            },
            "czas": {
                "teraz": BuiltinFunction("czas.teraz", self._stdlib_timestamp, 0),
                "data": BuiltinFunction("czas.data", self._stdlib_datetime, 0),
                "uspij": BuiltinFunction("czas.uspij", self._stdlib_sleep, 1),
            },
            "system": {
                "argumenty": BuiltinFunction("system.argumenty", self._stdlib_arguments, 0),
                "operacyjny": BuiltinFunction("system.operacyjny", self._stdlib_os, 0),
                "katalog": BuiltinFunction("system.katalog", self._stdlib_cwd, 0),
                "wersja": BuiltinFunction("system.wersja", self._stdlib_version, 0),
            },
            "plik": {
                "czy_jest": BuiltinFunction("plik.czy_jest", self._stdlib_file_exists, 1),
                "czytaj": BuiltinFunction("plik.czytaj", self._stdlib_read_text, 1),
                "zapisz": BuiltinFunction("plik.zapisz", self._stdlib_write_text, 2),
                "dopisz": BuiltinFunction("plik.dopisz", self._stdlib_append_text, 2),
                "usun": BuiltinFunction("plik.usun", self._stdlib_delete_file, 1),
                "info": BuiltinFunction("plik.info", self._stdlib_file_info, 1),
            },
            "katalog": {
                "czy_jest": BuiltinFunction("katalog.czy_jest", self._stdlib_dir_exists, 1),
                "utworz": BuiltinFunction("katalog.utworz", self._stdlib_make_dir, 1),
                "lista": BuiltinFunction("katalog.lista", self._stdlib_list_dir, 1),
            },
            "sciezka": {
                "polacz": BuiltinFunction("sciezka.polacz", self._stdlib_path_join, 2),
                "nazwa": BuiltinFunction("sciezka.nazwa", self._stdlib_path_name, 1),
                "rozszerzenie": BuiltinFunction("sciezka.rozszerzenie", self._stdlib_path_extension, 1),
                "katalog": BuiltinFunction("sciezka.katalog", self._stdlib_path_directory, 1),
                "absolutna": BuiltinFunction("sciezka.absolutna", self._stdlib_path_absolute, 1),
            },
            "dane": {
                "skurw": BuiltinFunction("dane.skurw", self._stdlib_json_encode, 1),
                "odkurw": BuiltinFunction("dane.odkurw", self._stdlib_json_decode, 1),
                "ładnie_skurw": BuiltinFunction("dane.ładnie_skurw", self._stdlib_json_pretty, 1),
                "zapisz": BuiltinFunction("dane.zapisz", self._stdlib_json_write, 2),
                "czytaj": BuiltinFunction("dane.czytaj", self._stdlib_json_read, 1),
            },
            "siec": {
                "wjeb": BuiltinFunction("siec.wjeb", self._stdlib_http_get, None, 1),
                "wyślij": BuiltinFunction("siec.wyślij", self._stdlib_http_post, None, 1),
                "wrzuć": BuiltinFunction("siec.wrzuć", self._stdlib_http_put, None, 1),
                "wyjeb": BuiltinFunction("siec.wyjeb", self._stdlib_http_delete, None, 1),
                "zjeb": BuiltinFunction("siec.zjeb", self._stdlib_http_request, None, 2),
            },
        }[name]
        for export_name, value in definitions.items():
            environment.define(export_name, value)
        return module

    def run(self, program: Program, source_path: Path | None = None) -> None:
        self.global_environment.source_path = source_path
        try:
            self._execute_block(program.body, self.global_environment)
        except ProgramExit:
            return
        except LoopExitSignal as error:
            raise InterpreterError("KURWA LANG: 'wypierdalaj' requires a 'dopóki' loop") from error

    def run_async(self, program: Program, source_path: Path | None = None) -> None:
        self.run(program, source_path)

    def _execute_block(self, block: Block, environment: Environment) -> None:
        for statement in block.statements:
            self._execute(statement, environment)

    def _execute(self, statement, environment: Environment) -> None:
        if isinstance(statement, VariableDeclaration):
            environment.define(statement.name, self._evaluate(statement.value, environment))
        elif isinstance(statement, ImportStatement):
            module = self.module_loader.load(statement.module_name, environment.source_path)
            environment.define(module.name, module)
        elif isinstance(statement, FunctionDeclaration):
            if statement.name in environment.values:
                raise InterpreterError(f"KURWA ERROR: Funkcja już istnieje: {statement.name}")
            if statement.is_async:
                environment.define(statement.name, AsyncFunction(statement, environment, self))
            else:
                environment.define(statement.name, RuntimeFunction(statement, environment, self))
        elif isinstance(statement, SetListElementStatement):
            self._set_list_element(statement.target, statement.value, environment)
        elif isinstance(statement, AppendStatement):
            list_value = self._evaluate(statement.list_expression, environment)
            self._require_list(list_value, "'wpierdol'")
            list_value.append(self._evaluate(statement.value, environment))
        elif isinstance(statement, DeleteMapEntryStatement):
            map_value = self._evaluate(statement.map_expression, environment)
            key = self._evaluate(statement.key, environment)
            self._require_map(map_value, "'wypierdol_z_mapy'")
            self._delete_map_entry(map_value, key)
        elif isinstance(statement, ExpressionStatement):
            self._evaluate(statement.expression, environment)
        elif isinstance(statement, ReturnStatement):
            raise ReturnSignal(self._evaluate(statement.value, environment))
        elif isinstance(statement, IfStatement):
            if self._condition_is_true(statement.condition, environment, "jeśli"):
                self._execute_block(statement.body, environment)
            elif statement.else_body is not None:
                self._execute_block(statement.else_body, environment)
        elif isinstance(statement, WhileStatement):
            while self._condition_is_true(statement.condition, environment, "dopóki"):
                try:
                    self._execute_block(statement.body, environment)
                except LoopExitSignal:
                    break
        elif isinstance(statement, LoopExitStatement):
            raise LoopExitSignal()
        elif isinstance(statement, IncrementStatement):
            current = environment.get(statement.name)
            amount = self._evaluate(statement.amount, environment)
            if not self._is_number(current) or not self._is_number(amount):
                raise InterpreterError("'zajeb' requires numeric variables and values")
            environment.assign(statement.name, current + amount)
        elif isinstance(statement, PrintTextStatement):
            value = self._evaluate(statement.value, environment)
            if not isinstance(value, (int, float, str)) or isinstance(value, bool):
                raise InterpreterError("'wypierdol' requires text or a numeric value")
            print(value)
        elif isinstance(statement, PrintValueStatement):
            print(self._evaluate(statement.value, environment))
        elif isinstance(statement, ExitStatement):
            raise ProgramExit()
        elif isinstance(statement, TryStatement):
            self._execute_try_statement(statement, environment)
        elif isinstance(statement, ThrowStatement):
            raise self._raise_user_error(self._evaluate(statement.value, environment), "wyrzuc_kurwa")
        elif isinstance(statement, AssertStatement):
            condition = self._evaluate(statement.condition, environment)
            if not self._require_boolean(condition, "sprawdz_kurwa"):
                raise TestFailure("sprawdz_kurwa", "TEST NIE PRZESZEDL: sprawdz_kurwa otrzymało fałsz", condition, True)
        elif isinstance(statement, ExpectErrorStatement):
            try:
                self._execute_block(statement.body, environment)
            except BaseException as error:
                if isinstance(error, (ProgramExit, LoopExitSignal, ReturnSignal)):
                    raise
                return
            raise TestFailure("oczekuj_blad_kurwa", "TEST NIE PRZESZEDL: oczekiwano błędu, ale wykonanie zakończyło się sukcesem")
        elif isinstance(statement, SkipStatement):
            raise TestSkipSignal(statement.reason)
        elif isinstance(statement, TestDeclaration):
            self._execute_test_declaration(statement, environment)
        else:
            raise InterpreterError(f"Unsupported statement: {type(statement).__name__}")

    def _execute_try_statement(self, statement: TryStatement, environment: Environment) -> None:
        try:
            self._execute_block(statement.body, environment)
        except BaseException as error:
            if isinstance(error, (ProgramExit, LoopExitSignal, ReturnSignal)):
                raise
            handled_error = self._coerce_error(error)
            if statement.catch_body is None:
                if statement.finally_body is not None:
                    try:
                        self._execute_block(statement.finally_body, environment)
                    finally:
                        raise error
                raise
            if statement.catch_name is not None:
                environment.define(statement.catch_name, handled_error)
            try:
                self._execute_block(statement.catch_body, environment)
            finally:
                if statement.finally_body is not None:
                    self._execute_block(statement.finally_body, environment)
            return
        else:
            if statement.finally_body is not None:
                self._execute_block(statement.finally_body, environment)

    def _execute_test_declaration(self, statement: TestDeclaration, environment: Environment) -> dict:
        test_environment = Environment(environment)
        try:
            self._execute_block(statement.body, test_environment)
        except TestSkipSignal as skip:
            return {"name": statement.name, "status": "skipped", "reason": skip.reason}
        except TestFailure as failure:
            return {"name": statement.name, "status": "failed", "message": str(failure), "actual": failure.actual, "expected": failure.expected}
        except BaseException as error:
            if isinstance(error, (ProgramExit, LoopExitSignal, ReturnSignal)):
                raise
            return {"name": statement.name, "status": "failed", "message": str(error), "actual": None, "expected": None}
        return {"name": statement.name, "status": "passed"}

    def _coerce_error(self, error: Exception):
        if isinstance(error, UserRuntimeError):
            return error.as_map()
        if isinstance(error, InterpreterError):
            kind = "runtime_error"
            message = str(error)
            if "division by zero" in message.lower() or "zero" in message.lower():
                kind = "arithmetic_error"
            return RuntimeMap([
                ("typ_kurwa", kind),
                ("wiadomosc_kurwa", message),
                ("zrodlo_kurwa", "runtime"),
            ])
        return RuntimeMap([
            ("typ_kurwa", type(error).__name__),
            ("wiadomosc_kurwa", str(error)),
            ("zrodlo_kurwa", "runtime"),
        ])

    def _raise_user_error(self, value, location: str):
        if value is NO_VALUE:
            value = "brak_wyniku"
        if not isinstance(value, str):
            raise InterpreterError(f"KURWA ERROR: {location} wymaga stringa jako komunikatu błędu")
        return UserRuntimeError("user_error", value, location)

    def _condition_is_true(self, expression: Expression, environment: Environment, context: str) -> bool:
        condition = self._evaluate(expression, environment)
        return self._require_boolean(condition, f"warunek '{context}'")

    def _require_boolean(self, value, context: str) -> bool:
        if not isinstance(value, bool):
            raise InterpreterError(
                f"KURWA ERROR: {context} wymaga wartości boolean, otrzymano {self._runtime_type(value)}"
            )
        return value

    def _evaluate(self, expression: Expression, environment: Environment):
        if isinstance(expression, NumberLiteral):
            return expression.value
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, BooleanLiteral):
            return expression.value
        if isinstance(expression, ListLiteral):
            return [self._evaluate(element, environment) for element in expression.elements]
        if isinstance(expression, MapLiteral):
            entries = [
                (self._evaluate(key, environment), self._evaluate(value, environment))
                for key, value in expression.entries
            ]
            self._validate_map_keys(entries)
            return RuntimeMap(entries)
        if isinstance(expression, VariableExpression):
            return environment.get(expression.name)
        if isinstance(expression, MemberExpression):
            module = self._evaluate(expression.object, environment)
            if not isinstance(module, RuntimeModule):
                raise InterpreterError("KURWA BŁĄD: dostęp przez kropkę wymaga modułu")
            if expression.name not in module.environment.values:
                raise InterpreterError(
                    f"KURWA BŁĄD: moduł {module.name} nie udostępnia wartości {expression.name}"
                )
            return module.environment.values[expression.name]
        if isinstance(expression, LessThanExpression):
            left = self._evaluate(expression.left, environment)
            right = self._evaluate(expression.right, environment)
            if not self._is_number(left) or not self._is_number(right):
                raise InterpreterError("Operator '<' requires numeric values")
            return left < right
        if isinstance(expression, BinaryExpression):
            return self._evaluate_binary(expression, environment)
        if isinstance(expression, UnaryExpression):
            operand = self._evaluate(expression.operand, environment)
            if expression.operator == "-":
                if not self._is_number(operand):
                    raise InterpreterError("KURWA ERROR: unary '-' wymaga number")
                return -operand
            if expression.operator != "nie":
                raise InterpreterError(f"KURWA ERROR: Nieznany operator jednoargumentowy: {expression.operator}")
            return not self._require_boolean(operand, "operator 'nie'")
        if isinstance(expression, CallExpression):
            callee = self._evaluate(expression.callee, environment)
            if not isinstance(callee, RuntimeCallable):
                raise InterpreterError("KURWA ERROR: To nie jest funkcja")
            arguments = [self._evaluate(argument, environment) for argument in expression.arguments]
            callee.check_argument_count(len(arguments))
            return callee.call(arguments)
        if isinstance(expression, IndexExpression):
            collection = self._evaluate(expression.collection, environment)
            index = self._evaluate(expression.index, environment)
            return self._get_collection_element(collection, index)
        if isinstance(expression, SliceExpression):
            collection = self._evaluate(expression.collection, environment)
            start = self._evaluate(expression.start, environment)
            stop = self._evaluate(expression.stop, environment)
            return self._get_string_slice(collection, start, stop)
        if isinstance(expression, PopListExpression):
            list_value = self._evaluate(expression.list_expression, environment)
            self._require_list(list_value, "'wypierdol_z_listy'")
            if not list_value:
                raise InterpreterError("KURWA ERROR: Nie można usunąć elementu z pustej listy")
            return list_value.pop()
        raise InterpreterError(f"Unsupported expression: {type(expression).__name__}")

    def _evaluate_binary(self, expression: BinaryExpression, environment: Environment):
        left = self._evaluate(expression.left, environment)
        if expression.operator == "i":
            left = self._require_boolean(left, "operator 'i'")
            if not left:
                return False
            return self._require_boolean(self._evaluate(expression.right, environment), "operator 'i'")
        if expression.operator == "albo":
            left = self._require_boolean(left, "operator 'albo'")
            if left:
                return True
            return self._require_boolean(self._evaluate(expression.right, environment), "operator 'albo'")
        right = self._evaluate(expression.right, environment)
        if expression.operator in {"+", "-", "*", "/"}:
            if expression.operator == "+" and isinstance(left, str) and isinstance(right, str):
                return left + right
            if not self._is_number(left) or not self._is_number(right):
                raise InterpreterError(f"Operator '{expression.operator}' requires two numbers or two strings")
            if expression.operator == "/" and right == 0:
                raise InterpreterError("KURWA LANG: division by zero")
            return {
                "+": lambda: left + right,
                "-": lambda: left - right,
                "*": lambda: left * right,
                "/": lambda: left // right if self._is_integer(left) and self._is_integer(right) else left / right,
            }[expression.operator]()
        if expression.operator in {"<", "<=", ">", ">=", "==", "!="}:
            if expression.operator in {"<", "<=", ">", ">="}:
                if not self._is_number(left) or not self._is_number(right):
                    raise InterpreterError(f"Operator '{expression.operator}' requires numeric values")
            if expression.operator in {"==", "!="}:
                if self._runtime_type(left) != self._runtime_type(right):
                    return expression.operator == "!="
                return self._values_equal(left, right) if expression.operator == "==" else not self._values_equal(left, right)
            return {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
                "==": left == right,
                "!=": left != right,
            }[expression.operator]
        raise InterpreterError(f"Unsupported operator: {expression.operator}")

    @staticmethod
    def _values_equal(left, right) -> bool:
        return left == right

    @staticmethod
    def _runtime_type(value) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, RuntimeMap):
            return "map"
        if isinstance(value, RuntimeModule):
            return "module"
        if isinstance(value, RuntimeCallable):
            return "function"
        if value is NO_VALUE:
            return "no-value"
        return type(value).__name__

    def _set_list_element(self, target: IndexExpression, value_expression, environment: Environment) -> None:
        collection = self._evaluate(target.collection, environment)
        index = self._evaluate(target.index, environment)
        value = self._evaluate(value_expression, environment)
        if isinstance(collection, list):
            collection[self._validate_index(index, collection)] = value
            return
        if isinstance(collection, RuntimeMap):
            self._validate_map_key(index)
            collection.values[index] = value
            return
        raise InterpreterError("KURWA ERROR: przypisanie elementu wymaga listy lub mapy")

    def _get_collection_element(self, collection, index):
        if isinstance(collection, list):
            return collection[self._validate_index(index, collection)]
        if isinstance(collection, str):
            return collection[self._validate_string_index(index, collection)]
        if isinstance(collection, RuntimeMap):
            self._validate_map_key(index)
            if index not in collection.values:
                raise InterpreterError(f'KURWA BŁĄD: mapa nie zawiera klucza "{index}"')
            return collection.values[index]
        raise InterpreterError(
            "KURWA ERROR: indeksowanie wymaga listy lub mapy; string jest obsługiwany osobno"
        )

    def _get_string_slice(self, collection, start, stop):
        if not isinstance(collection, str):
            raise InterpreterError("KURWA ERROR: slicing wymaga stringa")
        self._validate_string_index(start, collection, allow_end=True)
        self._validate_string_index(stop, collection, allow_end=True)
        if start > stop:
            raise InterpreterError("KURWA ERROR: początek fragmentu nie może być większy od końca")
        return collection[start:stop]

    @staticmethod
    def _require_list(value, operation: str) -> None:
        if not isinstance(value, list):
            raise InterpreterError(f"KURWA ERROR: {operation} wymaga listy")

    @staticmethod
    def _require_map(value, operation: str) -> None:
        if not isinstance(value, RuntimeMap):
            raise InterpreterError(f"KURWA ERROR: {operation} wymaga mapy")

    @staticmethod
    def _validate_map_key(key) -> None:
        if not isinstance(key, str):
            raise InterpreterError("KURWA ERROR: Klucz mapy musi być stringiem")

    @classmethod
    def _validate_map_keys(cls, entries) -> None:
        for key, _ in entries:
            cls._validate_map_key(key)

    def _delete_map_entry(self, map_value: RuntimeMap, key) -> None:
        self._validate_map_key(key)
        if key not in map_value.values:
            raise InterpreterError(f'KURWA BŁĄD: mapa nie zawiera klucza "{key}"')
        del map_value.values[key]

    @staticmethod
    def _validate_index(index, collection) -> int:
        if not isinstance(index, int) or isinstance(index, bool):
            raise InterpreterError("KURWA ERROR: Indeks listy musi być liczbą")
        if index < 0 or index >= len(collection):
            raise InterpreterError(f"KURWA ERROR: Indeks poza zakresem: {index}")
        return index

    @staticmethod
    def _validate_string_index(index, value: str, allow_end: bool = False) -> int:
        if not isinstance(index, int) or isinstance(index, bool):
            raise InterpreterError("KURWA ERROR: Indeks stringa musi być liczbą")
        upper_bound = len(value) if allow_end else len(value) - 1
        if index < 0 or index > upper_bound:
            raise InterpreterError(f"KURWA ERROR: Indeks stringa poza zakresem: {index}")
        return index

    @staticmethod
    def _builtin_length(arguments):
        value = arguments[0]
        if isinstance(value, str):
            return len(value)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, RuntimeMap):
            return len(value.values)
        raise InterpreterError("KURWA ERROR: 'ile_kurwa' wymaga stringa, listy lub mapy")

    @staticmethod
    def _require_strings(arguments, name: str):
        if not all(isinstance(value, str) for value in arguments):
            raise InterpreterError(f"KURWA ERROR: '{name}' wymaga stringów")

    @staticmethod
    def _builtin_upper(arguments):
        Interpreter._require_strings(arguments, "wielkie_kurwa")
        return arguments[0].upper()

    @staticmethod
    def _builtin_lower(arguments):
        Interpreter._require_strings(arguments, "male_kurwa")
        return arguments[0].lower()

    @staticmethod
    def _builtin_contains(arguments):
        Interpreter._require_strings(arguments, "zawiera_kurwa")
        return arguments[1] in arguments[0]

    @staticmethod
    def _builtin_replace(arguments):
        Interpreter._require_strings(arguments, "zamien_kurwa")
        text, old, new = arguments
        if old == "":
            raise InterpreterError("KURWA ERROR: 'zamien_kurwa' nie przyjmuje pustego szukanego fragmentu")
        return text.replace(old, new)

    @staticmethod
    def _builtin_find(arguments):
        Interpreter._require_strings(arguments, "znajdz_kurwa")
        return arguments[0].find(arguments[1])

    @staticmethod
    def _builtin_text(arguments):
        value = arguments[0]
        if isinstance(value, (int, float, str, bool)) or isinstance(value, (list, RuntimeMap)) or value is NO_VALUE:
            return str(value)
        raise InterpreterError(f"KURWA ERROR: 'tekst_kurwa' nie obsługuje typu {Interpreter._runtime_type(value)}")

    @staticmethod
    def _builtin_number(arguments):
        value = arguments[0]
        if Interpreter._is_integer(value):
            return value
        if isinstance(value, str):
            try:
                return float(value) if "." in value else int(value)
            except ValueError as error:
                raise InterpreterError(f"KURWA ERROR: Nie można zamienić stringa {value!r} na liczbę") from error
        raise InterpreterError(f"KURWA ERROR: 'liczba_kurwa' nie obsługuje typu {Interpreter._runtime_type(value)}")

    @staticmethod
    def _builtin_has_key(arguments):
        map_value, key = arguments
        if not isinstance(map_value, RuntimeMap):
            raise InterpreterError("KURWA ERROR: 'jest_kurwa' wymaga mapy")
        Interpreter._validate_map_key(key)
        return key in map_value.values

    @staticmethod
    def _stdlib_number(value, name: str):
        if not Interpreter._is_number(value):
            raise InterpreterError(
                f"KURWA ERROR: '{name}' wymaga number, otrzymano {Interpreter._runtime_type(value)}"
            )
        return value

    @staticmethod
    def _stdlib_abs(arguments):
        return abs(Interpreter._stdlib_number(arguments[0], "matematyka.abs_kurwa"))

    @staticmethod
    def _stdlib_power(arguments):
        left = Interpreter._stdlib_number(arguments[0], "matematyka.potega_kurwa")
        right = Interpreter._stdlib_number(arguments[1], "matematyka.potega_kurwa")
        return left ** right

    @staticmethod
    def _stdlib_sqrt(arguments):
        value = Interpreter._stdlib_number(arguments[0], "matematyka.pierwiastek_kurwa")
        if value < 0:
            raise InterpreterError("KURWA ERROR: pierwiastek_kurwa nie przyjmuje liczby ujemnej")
        return math.sqrt(value)

    @staticmethod
    def _stdlib_minimum(arguments):
        values = [Interpreter._stdlib_number(value, "matematyka.minimum_kurwa") for value in arguments]
        return min(values)

    @staticmethod
    def _stdlib_maximum(arguments):
        values = [Interpreter._stdlib_number(value, "matematyka.maksimum_kurwa") for value in arguments]
        return max(values)

    @staticmethod
    def _stdlib_round(arguments):
        return round(Interpreter._stdlib_number(arguments[0], "matematyka.zaokraglij_kurwa"))

    @staticmethod
    def _stdlib_random_integer(arguments):
        minimum, maximum = arguments
        if not Interpreter._is_integer(minimum) or not Interpreter._is_integer(maximum):
            raise InterpreterError("KURWA ERROR: losuj.liczba wymaga dwóch liczb całkowitych")
        if minimum > maximum:
            raise InterpreterError("KURWA ERROR: losuj.liczba wymaga min <= max")
        return random.randint(minimum, maximum)

    @staticmethod
    def _stdlib_random_float(arguments):
        minimum = Interpreter._stdlib_number(arguments[0], "losuj.ulamek")
        maximum = Interpreter._stdlib_number(arguments[1], "losuj.ulamek")
        if minimum > maximum:
            raise InterpreterError("KURWA ERROR: losuj.ulamek wymaga min <= max")
        return random.uniform(minimum, maximum)

    @staticmethod
    def _stdlib_random_element(arguments):
        values = arguments[0]
        if not isinstance(values, list):
            raise InterpreterError("KURWA ERROR: losuj.element wymaga listy")
        if not values:
            raise InterpreterError("KURWA ERROR: losuj.element nie działa na pustej liście")
        return random.choice(values)

    @staticmethod
    def _stdlib_text(arguments, name: str):
        if not isinstance(arguments[0], str):
            raise InterpreterError(f"KURWA ERROR: '{name}' wymaga stringa")
        return arguments[0]

    @staticmethod
    def _stdlib_trim(arguments):
        return Interpreter._stdlib_text(arguments, "tekst.oczysc").strip()

    @staticmethod
    def _stdlib_starts_with(arguments):
        text = Interpreter._stdlib_text(arguments, "tekst.zaczyna_sie")
        prefix = arguments[1]
        if not isinstance(prefix, str):
            raise InterpreterError("KURWA ERROR: 'tekst.zaczyna_sie' wymaga dwóch stringów")
        return text.startswith(prefix)

    @staticmethod
    def _stdlib_ends_with(arguments):
        text = Interpreter._stdlib_text(arguments, "tekst.konczy_sie")
        suffix = arguments[1]
        if not isinstance(suffix, str):
            raise InterpreterError("KURWA ERROR: 'tekst.konczy_sie' wymaga dwóch stringów")
        return text.endswith(suffix)

    @staticmethod
    def _stdlib_split(arguments):
        text = Interpreter._stdlib_text(arguments, "tekst.rozdziel")
        separator = arguments[1]
        if not isinstance(separator, str) or separator == "":
            raise InterpreterError("KURWA ERROR: 'tekst.rozdziel' wymaga niepustego separatora")
        return text.split(separator)

    @staticmethod
    def _stdlib_join(arguments):
        values, separator = arguments
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise InterpreterError("KURWA ERROR: 'tekst.polacz' wymaga listy stringów")
        if not isinstance(separator, str):
            raise InterpreterError("KURWA ERROR: 'tekst.polacz' wymaga stringowego separatora")
        return separator.join(values)

    @staticmethod
    def _stdlib_repeat(arguments):
        text, count = arguments
        if not isinstance(text, str) or not Interpreter._is_integer(count):
            raise InterpreterError("KURWA ERROR: 'tekst.powtorz' wymaga stringa i liczby całkowitej")
        if count < 0:
            raise InterpreterError("KURWA ERROR: 'tekst.powtorz' wymaga nieujemnej liczby")
        return text * count

    @staticmethod
    def _stdlib_timestamp(arguments):
        return time.time()

    @staticmethod
    def _stdlib_datetime(arguments):
        return datetime.now().isoformat(sep=" ", timespec="seconds")

    @staticmethod
    def _stdlib_sleep(arguments):
        milliseconds = arguments[0]
        if not Interpreter._is_integer(milliseconds) or milliseconds < 0:
            raise InterpreterError("KURWA ERROR: czas.uspij wymaga nieujemnej liczby całkowitej milisekund")
        time.sleep(milliseconds / 1000)
        return NO_VALUE

    def _stdlib_arguments(self, arguments):
        return list(self.program_arguments)

    @staticmethod
    def _stdlib_os(arguments):
        return platform.system()

    @staticmethod
    def _stdlib_cwd(arguments):
        return os.getcwd()

    @staticmethod
    def _stdlib_version(arguments):
        return LANGUAGE_VERSION

    @staticmethod
    def _stdlib_file_exists(arguments):
        path = Path(arguments[0])
        return path.exists()

    @staticmethod
    def _stdlib_read_text(arguments):
        file_path = Path(arguments[0])
        if not file_path.exists():
            raise InterpreterError(f"KURWA ERROR: plik.czytaj nie może odczytać nieistniejącego pliku: {file_path}")
        if file_path.is_dir():
            raise InterpreterError(f"KURWA ERROR: plik.czytaj wymaga pliku, nie katalogu: {file_path}")
        return file_path.read_text(encoding="utf-8")

    @staticmethod
    def _stdlib_write_text(arguments):
        file_path = Path(arguments[0])
        text = arguments[1]
        if not isinstance(text, str):
            raise InterpreterError("KURWA ERROR: plik.zapisz wymaga tekstu jako drugiego argumentu")
        if file_path.exists() and file_path.is_dir():
            raise InterpreterError(f"KURWA ERROR: plik.zapisz wymaga pliku, nie katalogu: {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text, encoding="utf-8")
        return True

    @staticmethod
    def _stdlib_append_text(arguments):
        file_path = Path(arguments[0])
        text = arguments[1]
        if not isinstance(text, str):
            raise InterpreterError("KURWA ERROR: plik.dopisz wymaga tekstu jako drugiego argumentu")
        if file_path.exists() and file_path.is_dir():
            raise InterpreterError(f"KURWA ERROR: plik.dopisz wymaga pliku, nie katalogu: {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(text)
        return True

    @staticmethod
    def _stdlib_delete_file(arguments):
        file_path = Path(arguments[0])
        if not file_path.exists():
            raise InterpreterError(f"KURWA ERROR: plik.usun nie może usunąć nieistniejącego pliku: {file_path}")
        if file_path.is_dir():
            raise InterpreterError(f"KURWA ERROR: plik.usun wymaga pliku, nie katalogu: {file_path}")
        file_path.unlink()
        return True

    @staticmethod
    def _stdlib_file_info(arguments):
        file_path = Path(arguments[0])
        if not file_path.exists():
            return RuntimeMap([
                ("rozmiar", 0),
                ("istnieje", False),
                ("czy_plik", False),
                ("czy_katalog", False),
            ])
        return RuntimeMap([
            ("rozmiar", file_path.stat().st_size),
            ("istnieje", True),
            ("czy_plik", file_path.is_file()),
            ("czy_katalog", file_path.is_dir()),
        ])

    @staticmethod
    def _stdlib_dir_exists(arguments):
        return Path(arguments[0]).is_dir()

    @staticmethod
    def _stdlib_make_dir(arguments):
        directory = Path(arguments[0])
        if directory.exists() and not directory.is_dir():
            raise InterpreterError(f"KURWA ERROR: katalog.utworz wymaga katalogu, nie pliku: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        return True

    @staticmethod
    def _stdlib_list_dir(arguments):
        directory = Path(arguments[0])
        if not directory.exists():
            raise InterpreterError(f"KURWA ERROR: katalog.lista nie może odczytać nieistniejącego katalogu: {directory}")
        if not directory.is_dir():
            raise InterpreterError(f"KURWA ERROR: katalog.lista wymaga katalogu, nie pliku: {directory}")
        return [entry.name for entry in sorted(directory.iterdir(), key=lambda entry: entry.name)]

    @staticmethod
    def _stdlib_path_join(arguments):
        left, right = arguments
        if not isinstance(left, str) or not isinstance(right, str):
            raise InterpreterError("KURWA ERROR: sciezka.polacz wymaga dwóch stringów")
        return os.path.join(left, right)

    @staticmethod
    def _stdlib_path_name(arguments):
        value = arguments[0]
        if not isinstance(value, str):
            raise InterpreterError("KURWA ERROR: sciezka.nazwa wymaga stringa")
        return os.path.basename(os.path.normpath(value)) or os.path.basename(value)

    @staticmethod
    def _stdlib_path_extension(arguments):
        value = arguments[0]
        if not isinstance(value, str):
            raise InterpreterError("KURWA ERROR: sciezka.rozszerzenie wymaga stringa")
        return Path(value).suffix

    @staticmethod
    def _stdlib_path_directory(arguments):
        value = arguments[0]
        if not isinstance(value, str):
            raise InterpreterError("KURWA ERROR: sciezka.katalog wymaga stringa")
        return str(Path(value).parent)

    @staticmethod
    def _stdlib_path_absolute(arguments):
        value = arguments[0]
        if not isinstance(value, str):
            raise InterpreterError("KURWA ERROR: sciezka.absolutna wymaga stringa")
        return str(Path(value).resolve())

    @classmethod
    def _stdlib_json_encode(cls, arguments):
        return cls._json_dump(arguments[0], pretty=False)

    @classmethod
    def _stdlib_json_pretty(cls, arguments):
        return cls._json_dump(arguments[0], pretty=True)

    @classmethod
    def _json_dump(cls, value, pretty: bool):
        try:
            converted = cls._to_json_value(value, set())
            return json.dumps(
                converted,
                ensure_ascii=False,
                allow_nan=False,
                indent=2 if pretty else None,
                separators=None if pretty else (",", ":"),
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise InterpreterError(f"KURWA ERROR: nie można skurwić wartości do JSON: {error}") from error

    @classmethod
    def _to_json_value(cls, value, active: set[int]):
        if value is NO_VALUE:
            return None
        if isinstance(value, bool) or isinstance(value, str) or value is None:
            return value
        if cls._is_number(value):
            return value
        if isinstance(value, list):
            identity = id(value)
            if identity in active:
                raise InterpreterError("KURWA ERROR: wykryto cykliczną strukturę podczas zapisu JSON")
            active.add(identity)
            try:
                return [cls._to_json_value(item, active) for item in value]
            finally:
                active.remove(identity)
        if isinstance(value, RuntimeMap):
            identity = id(value)
            if identity in active:
                raise InterpreterError("KURWA ERROR: wykryto cykliczną strukturę podczas zapisu JSON")
            active.add(identity)
            try:
                return {key: cls._to_json_value(item, active) for key, item in value.values.items()}
            finally:
                active.remove(identity)
        raise InterpreterError(
            f"KURWA ERROR: typ {cls._runtime_type(value)} nie może zostać zapisany jako JSON"
        )

    @classmethod
    def _stdlib_json_decode(cls, arguments):
        text = arguments[0]
        if not isinstance(text, str):
            raise InterpreterError("KURWA ERROR: dane.odkurw wymaga stringa JSON")
        try:
            return cls._from_json_value(
                json.loads(text, parse_constant=cls._reject_json_constant)
            )
        except json.JSONDecodeError as error:
            raise InterpreterError(
                f"KURWA ERROR: niepoprawny JSON w linii {error.lineno}, kolumnie {error.colno}: {error.msg}"
            ) from error
        except ValueError as error:
            raise InterpreterError(f"KURWA ERROR: niepoprawny JSON: {error}") from error

    @staticmethod
    def _reject_json_constant(value):
        raise ValueError(f"niedozwolona wartość {value}")

    @classmethod
    def _from_json_value(cls, value):
        if value is None:
            return NO_VALUE
        if isinstance(value, dict):
            return RuntimeMap((key, cls._from_json_value(item)) for key, item in value.items())
        if isinstance(value, list):
            return [cls._from_json_value(item) for item in value]
        return value

    @classmethod
    def _stdlib_json_write(cls, arguments):
        path, value = arguments
        if not isinstance(path, str):
            raise InterpreterError("KURWA ERROR: dane.zapisz wymaga ścieżki jako stringa")
        text = cls._json_dump(value, pretty=True)
        return cls._stdlib_write_text([path, text])

    @classmethod
    def _stdlib_json_read(cls, arguments):
        path = arguments[0]
        if not isinstance(path, str):
            raise InterpreterError("KURWA ERROR: dane.czytaj wymaga ścieżki jako stringa")
        text = cls._stdlib_read_text([path])
        return cls._stdlib_json_decode([text])

    @staticmethod
    def _stdlib_http_get(arguments):
        if not arguments:
            raise InterpreterError("KURWA ERROR: siec.wjeb wymaga adresu URL")
        url = arguments[0]
        params = arguments[1] if len(arguments) > 1 else None
        headers = arguments[2] if len(arguments) > 2 else None
        timeout = arguments[3] if len(arguments) > 3 else 10
        return Interpreter._http_request("GET", url, params=params, headers=headers, timeout=timeout)

    @staticmethod
    def _stdlib_http_post(arguments):
        if not arguments:
            raise InterpreterError("KURWA ERROR: siec.wyślij wymaga adresu URL")
        url = arguments[0]
        body = arguments[1] if len(arguments) > 1 else None
        headers = arguments[2] if len(arguments) > 2 else None
        timeout = arguments[3] if len(arguments) > 3 else 10
        return Interpreter._http_request("POST", url, body=body, headers=headers, timeout=timeout)

    @staticmethod
    def _stdlib_http_put(arguments):
        if not arguments:
            raise InterpreterError("KURWA ERROR: siec.wrzuć wymaga adresu URL")
        url = arguments[0]
        body = arguments[1] if len(arguments) > 1 else None
        headers = arguments[2] if len(arguments) > 2 else None
        timeout = arguments[3] if len(arguments) > 3 else 10
        return Interpreter._http_request("PUT", url, body=body, headers=headers, timeout=timeout)

    @staticmethod
    def _stdlib_http_delete(arguments):
        if not arguments:
            raise InterpreterError("KURWA ERROR: siec.wyjeb wymaga adresu URL")
        url = arguments[0]
        body = arguments[1] if len(arguments) > 1 else None
        headers = arguments[2] if len(arguments) > 2 else None
        timeout = arguments[3] if len(arguments) > 3 else 10
        return Interpreter._http_request("DELETE", url, body=body, headers=headers, timeout=timeout)

    @staticmethod
    def _stdlib_http_request(arguments):
        if len(arguments) < 2:
            raise InterpreterError("KURWA ERROR: siec.zjeb wymaga metody i adresu URL")
        method = arguments[0]
        url = arguments[1]
        body = arguments[2] if len(arguments) > 2 else None
        headers = arguments[3] if len(arguments) > 3 else None
        timeout = arguments[4] if len(arguments) > 4 else 10
        return Interpreter._http_request(method, url, body=body, headers=headers, timeout=timeout)

    @staticmethod
    def _http_request(method: str, url: str, params=None, body=None, headers=None, timeout=10):
        if not isinstance(url, str):
            raise InterpreterError("KURWA ERROR: siec wymaga poprawnego URL jako stringa")
        if not url.startswith(("http://", "https://")):
            raise InterpreterError("KURWA ERROR: niepoprawny URL: musi zaczynać się od http:// lub https://")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InterpreterError("KURWA ERROR: niepoprawny URL: brak hosta lub nieobsługiwany protokół")
        if timeout is None:
            timeout = 10
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
            raise InterpreterError("KURWA ERROR: timeout HTTP musi być liczbą dodatnią")
        if timeout <= 0:
            raise InterpreterError("KURWA ERROR: timeout HTTP musi być większy od zera")

        method = str(method).upper()
        if params is not None:
            if not isinstance(params, RuntimeMap):
                raise InterpreterError("KURWA ERROR: parametry URL muszą być mapą")
            query = urllib.parse.urlencode({str(key): str(value) for key, value in params.values.items()}, doseq=True)
            separator = "&" if parsed.query else "?"
            url = f"{url}{separator}{query}"
        payload = None
        header_map = {}
        if headers is not None:
            if not isinstance(headers, RuntimeMap):
                raise InterpreterError("KURWA ERROR: nagłówki HTTP muszą być mapą")
            header_map = {str(key): str(value) for key, value in headers.values.items()}

        if body is not None:
            if isinstance(body, str):
                payload = body.encode("utf-8")
                header_map.setdefault("Content-Type", "text/plain; charset=utf-8")
            elif isinstance(body, (RuntimeMap, list, int, float, bool)) or body is NO_VALUE:
                payload = Interpreter._json_dump(body, pretty=False).encode("utf-8")
                header_map.setdefault("Content-Type", "application/json; charset=utf-8")
            else:
                raise InterpreterError(f"KURWA ERROR: typ {Interpreter._runtime_type(body)} nie może zostać wysłany jako HTTP body")

        try:
            request = urllib.request.Request(url, data=payload, headers=header_map, method=method)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                return Interpreter._http_response_from_backend(
                    url=url,
                    status=getattr(response, "status", getattr(response, "code", 200)),
                    body=raw,
                    headers=dict(response.headers.items()),
                    success=getattr(response, "status", getattr(response, "code", 200)) < 400,
                )
        except urllib.error.HTTPError as error:
            return Interpreter._http_response_from_backend(
                url=url,
                status=error.code,
                body=error.read(),
                headers=dict(error.headers.items()),
                success=False,
            )
        except TimeoutError as error:
            raise InterpreterError(
                f"KURWA ERROR: timeout połączenia HTTP po {timeout} s"
            ) from error
        except (socket.gaierror, ConnectionResetError, ConnectionRefusedError, ssl.SSLError, OSError, ValueError) as error:
            if isinstance(error, socket.gaierror):
                raise InterpreterError(f"KURWA ERROR: błąd DNS/połączenia sieciowego: {error}") from error
            if isinstance(error, ConnectionRefusedError):
                raise InterpreterError(f"KURWA ERROR: połączenie odrzucone: {error}") from error
            if isinstance(error, ssl.SSLError):
                raise InterpreterError(f"KURWA ERROR: błąd HTTPS/TLS: {error}") from error
            raise InterpreterError(f"KURWA ERROR: połączenie sieciowe nie powiodło się: {error}") from error
        except urllib.error.URLError as error:
            reason = getattr(error, "reason", error)
            if isinstance(reason, TimeoutError):
                raise InterpreterError(
                    f"KURWA ERROR: timeout połączenia HTTP po {timeout} s"
                ) from error
            raise InterpreterError(f"KURWA ERROR: połączenie sieciowe nie powiodło się: {reason}") from error

    @staticmethod
    def _http_response_from_backend(url: str, status: int, body: bytes, headers: dict, success: bool):
        text = body.decode("utf-8", errors="replace")
        json_value = NO_VALUE
        content_type = ""
        if headers:
            for key, value in headers.items():
                if key.lower() == "content-type":
                    content_type = str(value).lower()
                    break
        if "json" in content_type and text:
            try:
                json_value = Interpreter._stdlib_json_decode([text])
            except InterpreterError:
                json_value = NO_VALUE
        return RuntimeHttpResponse(
            status_code=status,
            url=url,
            text=text,
            headers=headers,
            success=success,
            json_value=json_value,
        )

    @staticmethod
    def _is_integer(value) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def _is_number(value) -> bool:
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
