"""Python-side extension model for KURWA LANG v1.7 EXT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Extension:
    """Definition for a KURWA LANG extension loaded from a Python file."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    functions: dict[str, Callable[..., Any]] = field(default_factory=dict)
    author: str | None = None
    capabilities: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "nazwa_kurwa": self.name,
            "wersja_kurwa": self.version,
            "opis_kurwa": self.description,
            "autor_kurwa": self.author or "nieznany",
            "mozliwosci_kurwa": list(self.capabilities),
        }


class ExtensionRegistrationError(RuntimeError):
    """Raised when an extension is invalid or conflicts with the runtime."""


class ExtensionLoadError(RuntimeError):
    """Raised when a Python extension cannot be loaded safely."""


class ExtensionRuntimeError(RuntimeError):
    """Raised when an extension function fails during execution."""


class ExtensionRegistry:
    """Central registry for trusted local KURWA-language extensions."""

    def __init__(self):
        self._extensions: dict[str, dict[str, Any]] = {}

    def register(self, extension: Extension):
        if not extension.name or not extension.name.strip():
            raise ExtensionRegistrationError("KURWA ERROR: nazwa rozszerzenia nie może być pusta")
        if extension.name in self._extensions:
            raise ExtensionRegistrationError(f"KURWA ERROR: rozszerzenie {extension.name} jest już zarejestrowane")
        if extension.name in {"ile_kurwa", "zajeb_moduł", "wjebaj", "zlap_kurwa"}:
            raise ExtensionRegistrationError("KURWA ERROR: nazwa rozszerzenia nie może zastąpić zarezerwowanej funkcji runtime")
        self._extensions[extension.name] = {
            "name": extension.name,
            "version": extension.version,
            "description": extension.description,
            "author": extension.author,
            "capabilities": list(extension.capabilities),
            "functions": dict(extension.functions),
        }

    def get(self, name: str):
        if name not in self._extensions:
            raise ExtensionRegistrationError(f"KURWA ERROR: nie znaleziono rozszerzenia {name}")
        return self._extensions[name]

    def has(self, name: str) -> bool:
        return name in self._extensions

    def list_names(self) -> list[str]:
        return sorted(self._extensions)

    def unregister(self, name: str):
        if name not in self._extensions:
            raise ExtensionRegistrationError(f"KURWA ERROR: rozszerzenie {name} nie jest załadowane")
        del self._extensions[name]


def safe_to_kurwa(value):
    """Convert a Python value into a KURWA runtime-compatible value."""
    if value is None:
        return "brak_wyniku"
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [safe_to_kurwa(item) for item in value]
    if isinstance(value, tuple):
        return [safe_to_kurwa(item) for item in value]
    if isinstance(value, dict):
        from src.interpreter import RuntimeMap

        return RuntimeMap((str(key), safe_to_kurwa(item)) for key, item in value.items())
    if hasattr(value, "as_map"):
        return value.as_map()
    raise TypeError(f"KURWA ERROR: typ {type(value).__name__} nie jest bezpieczny dla KURWA runtime")


def safe_from_kurwa(value):
    """Convert a runtime value into a Python scalar for extension code."""
    from src.interpreter import RuntimeMap, NO_VALUE

    if value is NO_VALUE:
        return None
    if isinstance(value, RuntimeMap):
        return {key: safe_from_kurwa(item) for key, item in value.values.items()}
    if isinstance(value, list):
        return [safe_from_kurwa(item) for item in value]
    return value
