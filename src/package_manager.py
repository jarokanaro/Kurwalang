"""Package manager for KURWA LANG v1.4.

This is intentionally small and local-first: it integrates with the existing
module resolver and keeps the runtime backend in Python. The package system is
built around a project manifest (`kurwa.pack`), a lock file (`kurwa.lock`),
and a local installation directory (`.kurwa_packages/`).
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PackageManagerError(Exception):
    """Raised for package manager issues."""


class VersionError(PackageManagerError):
    """Raised when a version is invalid."""


class DependencyError(PackageManagerError):
    """Raised when dependency constraints cannot be solved."""


class ManifestError(PackageManagerError):
    """Raised when manifest is missing or broken."""


class SecurityError(PackageManagerError):
    """Raised when a package would escape the project root."""


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        if not isinstance(value, str):
            raise VersionError("KURWA ERROR: wersja paczki musi być stringiem")
        parts = value.strip().split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise VersionError(f"KURWA ERROR: niepoprawna wersja paczki: {value}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "Version") -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)


@dataclass
class DependencySpec:
    name: str
    required: str

    def matches(self, version: str) -> bool:
        requested = version.strip()
        if requested.startswith("=="):
            return Version.parse(requested[2:]) == Version.parse(self.required)
        if requested.startswith(">="):
            return Version.parse(requested[2:]) >= Version.parse(self.required)
        if requested.startswith("<="):
            return Version.parse(requested[2:]) <= Version.parse(self.required)
        if requested.startswith(">"):
            return Version.parse(requested[1:]) > Version.parse(self.required)
        if requested.startswith("<"):
            return Version.parse(requested[1:]) < Version.parse(self.required)
        return Version.parse(requested) == Version.parse(self.required)


@dataclass
class PackageManifest:
    name: str
    version: str
    kurwa_version: str
    dependencies: dict[str, str]
    author: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PackageManifest":
        if not isinstance(data.get("nazwa"), str) or not data["nazwa"].strip():
            raise ManifestError("KURWA ERROR: manifest paczki ma brakujący klucz 'nazwa'")
        if not isinstance(data.get("wersja"), str) or not data["wersja"].strip():
            raise ManifestError("KURWA ERROR: manifest paczki ma brakujący klucz 'wersja'")
        version = data["wersja"]
        Version.parse(version)
        deps = data.get("zależności") or data.get("dependencies") or {}
        if not isinstance(deps, dict):
            raise ManifestError("KURWA ERROR: zależności w manifestcie muszą być mapą")
        kurwa_version = str(data.get("wymagana_wersja_kurwa") or data.get("kurwa_version") or "0.0.0")
        return cls(
            name=data["nazwa"],
            version=version,
            kurwa_version=kurwa_version,
            dependencies={str(k): str(v) for k, v in deps.items()},
            author=(data.get("autor") or data.get("author")),
            description=(data.get("opis") or data.get("description")),
            metadata=data.get("metadane") or data.get("metadata") or {},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "nazwa": self.name,
            "wersja": self.version,
            "wymagana_wersja_kurwa": self.kurwa_version,
            "zależności": self.dependencies,
        }
        if self.author is not None:
            payload["autor"] = self.author
        if self.description is not None:
            payload["opis"] = self.description
        if self.metadata:
            payload["metadane"] = self.metadata
        return payload


class LocalPackageSource:
    """Simple source that resolves packages from a local directory tree."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def resolve(self, package_name: str, version: str | None = None) -> Path:
        package_root = self.root / package_name
        if not package_root.exists():
            raise PackageManagerError(f"KURWA ERROR: nie znaleziono paczki lokalnej: {package_name}")
        if version is not None:
            candidate = package_root / version
            if candidate.exists():
                return candidate
        manifest_path = package_root / "kurwa.pack"
        if manifest_path.exists():
            return package_root
        raise PackageManagerError(f"KURWA ERROR: paczka {package_name} nie ma poprawnego manifestu")


class ProjectPackageManager:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root).resolve()
        self.manifest_path = self.project_root / "kurwa.pack"
        self.lockfile_path = self.project_root / "kurwa.lock"
        self.package_dir = self.project_root / ".kurwa_packages"

    def ensure_project(self) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.package_dir.mkdir(exist_ok=True)

    @property
    def manifest_exists(self) -> bool:
        return self.manifest_path.exists()

    def load_manifest(self) -> PackageManifest:
        if not self.manifest_path.exists():
            raise ManifestError("KURWA ERROR: brak manifestu projektu, uruchom 'kurwa init' najpierw")
        return self._parse_manifest_file(self.manifest_path)

    def save_manifest(self, manifest: PackageManifest) -> None:
        self.manifest_path.write_text(self._manifest_to_text(manifest), encoding="utf-8")

    def read_lockfile(self) -> dict[str, str]:
        if not self.lockfile_path.exists():
            return {}
        try:
            payload = json.loads(self.lockfile_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ManifestError("KURWA ERROR: lockfile ma nieprawidłowy format")
            return {str(key): str(value) for key, value in payload.items()}
        except json.JSONDecodeError as error:
            raise ManifestError(f"KURWA ERROR: uszkodzony lockfile: {error}") from error

    def write_lockfile(self, lock_data: dict[str, str]) -> None:
        ordered = {key: lock_data[key] for key in sorted(lock_data)}
        self.lockfile_path.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def init_project(self, name: str | None = None, version: str = "0.1.0") -> dict[str, Any]:
        self.ensure_project()
        if self.manifest_path.exists():
            raise ManifestError("KURWA ERROR: projekt już ma manifest, nie nadpisuję istniejących plików")
        project_name = (name or self.project_root.name).strip()
        if not project_name:
            raise ManifestError("KURWA ERROR: nazwa projektu nie może być pusta")
        manifest = PackageManifest(
            name=project_name,
            version=version,
            kurwa_version="1.12.0",
            dependencies={},
            description="Nowy projekt KURWA LANG",
            author="kurwa-team",
        )
        self.save_manifest(manifest)
        src_dir = self.project_root / "src"
        src_dir.mkdir(exist_ok=True)
        main_file = src_dir / "main.kurwa"
        if not main_file.exists():
            main_file.write_text(
                'program {\n    wypierdol "KURWA LANG v1.12"\n}\n',
                encoding="utf-8",
            )
        self.package_dir.mkdir(exist_ok=True)
        self.write_lockfile({})
        return manifest.to_dict()

    def install_local_package(self, source_path: Path, *, resolve_dependencies: bool = True) -> dict[str, Any]:
        source_raw = Path(source_path)
        if ".." in source_raw.parts:
            raise SecurityError("KURWA ERROR: ścieżka paczki nie może zawierać '..'")
        source_dir = source_raw.resolve()
        try:
            source_dir.relative_to(self.project_root)
        except ValueError as error:
            raise SecurityError("KURWA ERROR: paczka musi znajdować się wewnątrz katalogu projektu") from error
        if not source_dir.exists() or not source_dir.is_dir():
            raise PackageManagerError(f"KURWA ERROR: nie znaleziono katalogu paczki: {source_dir}")
        manifest_path = source_dir / "kurwa.pack"
        if not manifest_path.exists():
            raise ManifestError(f"KURWA ERROR: paczka w {source_dir} nie ma manifestu kurwa.pack")
        manifest = self._parse_manifest_file(manifest_path)
        if ".." in manifest.name or "/" in manifest.name or "\\" in manifest.name:
            raise SecurityError("KURWA ERROR: nazwa paczki nie może zawierać ścieżek")

        self._check_cycle(manifest.name, manifest.dependencies)
        for dep_name, dep_version in manifest.dependencies.items():
            self._check_dependency_is_compatible(dep_name, dep_version)

        target_dir = self.package_dir / manifest.name / manifest.version
        if target_dir.exists():
            shutil.rmtree(target_dir)

        self._ensure_safe_install(source_dir, target_dir)
        src_target = target_dir / "src"
        src_target.mkdir(parents=True, exist_ok=True)
        for child in source_dir.iterdir():
            if child.name in {".git", "__pycache__", ".kurwa_packages"}:
                continue
            if child.name in {"kurwa.pack", "kurwa.lock"}:
                continue
            dst = src_target / child.name
            if child.is_dir():
                shutil.copytree(child, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(child, dst)

        if resolve_dependencies:
            for dep_name, dep_version in manifest.dependencies.items():
                self.install_dependency(dep_name, dep_version)

        manifest_path_target = target_dir / "kurwa.pack"
        manifest_path_target.write_text(self._manifest_to_text(manifest), encoding="utf-8")
        lock_data = self.read_lockfile()
        lock_data[manifest.name] = manifest.version
        self.write_lockfile(lock_data)
        return manifest.to_dict()

    def install_dependency(self, package_name: str, requirement: str) -> None:
        package_ref = package_name.strip()
        if not package_ref:
            raise DependencyError("KURWA ERROR: nazwa zależności nie może być pusta")
        if package_ref.startswith(".") or package_ref.startswith("/"):
            raise SecurityError("KURWA ERROR: niebezpieczna ścieżka zależności")
        source_root = self.project_root / "packages"
        local_path = source_root / package_name
        if local_path.exists():
            self._check_dependency_is_compatible(package_name, requirement)
            if not (self.package_dir / package_name).exists():
                self.install_local_package(local_path)
            return
        installed_path = self.package_dir / package_ref
        for candidate in sorted(installed_path.glob("*"), reverse=True):
            if candidate.is_dir():
                manifest = self._parse_manifest_file(candidate / "kurwa.pack")
                if self._satisfies(manifest.version, requirement):
                    return
        raise DependencyError(
            f"KURWA ERROR: zależność {package_name} {requirement} nie została rozpoznana w lokalnym repozytorium"
        )

    def uninstall(self, package_name: str) -> None:
        package_dir = self.package_dir / package_name
        if not package_dir.exists():
            raise PackageManagerError(f"KURWA ERROR: paczka {package_name} nie jest zainstalowana")
        shutil.rmtree(package_dir)
        manifest = self.load_manifest()
        if package_name in manifest.dependencies:
            manifest.dependencies.pop(package_name)
            self.save_manifest(manifest)
        lock_data = self.read_lockfile()
        lock_data.pop(package_name, None)
        self.write_lockfile(lock_data)

    def list_installed(self) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        if not self.package_dir.exists():
            return results
        for package_dir in sorted(self.package_dir.iterdir()):
            if not package_dir.is_dir():
                continue
            for version_dir in sorted(package_dir.iterdir()):
                if not version_dir.is_dir():
                    continue
                manifest_path = version_dir / "kurwa.pack"
                if not manifest_path.exists():
                    continue
                manifest = self._parse_manifest_file(manifest_path)
                results.append({
                    "nazwa": manifest.name,
                    "wersja": manifest.version,
                    "źródło": str(version_dir),
                    "zależności": json.dumps(manifest.dependencies, ensure_ascii=False),
                })
        return results

    def update(self) -> dict[str, str]:
        lock_data = self.read_lockfile()
        if not lock_data:
            return {}
        for package_name, version in list(lock_data.items()):
            package_dir = self.package_dir / package_name
            if not package_dir.exists():
                continue
            newest = self._find_latest_installed_version(package_dir)
            if newest is not None:
                lock_data[package_name] = newest
        self.write_lockfile(lock_data)
        return lock_data

    def _parse_manifest_file(self, manifest_path: Path) -> PackageManifest:
        try:
            text = manifest_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ManifestError(f"KURWA ERROR: nie można odczytać manifestu: {error}") from error
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
        data: dict[str, Any] = {"zależności": {}}
        current_section = None
        for line in lines:
            if line.endswith(":") and line[:-1].strip().lower() in {"zależności", "dependencies"}:
                current_section = "zależności"
                continue
            if ":" not in line:
                if current_section == "zależności":
                    key, value = line.split(None, 1)
                    data["zależności"][key] = value.strip()
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in {"zależności", "dependencies"}:
                current_section = "zależności"
                data["zależności"] = {}
                continue
            if current_section == "zależności":
                data["zależności"][key] = value
            else:
                data[key] = value
        if not data.get("nazwa"):
            raise ManifestError("KURWA ERROR: uszkodzony manifest paczki: brak nazwy")
        if not data.get("wersja"):
            raise ManifestError("KURWA ERROR: uszkodzony manifest paczki: brak wersji")
        return PackageManifest.from_dict(data)

    def _manifest_to_text(self, manifest: PackageManifest) -> str:
        lines = [
            f"nazwa: {manifest.name}",
            f"wersja: {manifest.version}",
            f"wymagana_wersja_kurwa: {manifest.kurwa_version}",
        ]
        if manifest.author is not None:
            lines.append(f"autor: {manifest.author}")
        if manifest.description is not None:
            lines.append(f"opis: {manifest.description}")
        if manifest.metadata:
            lines.append("metadane:")
            for key, value in sorted(manifest.metadata.items()):
                lines.append(f"  {key}: {value}")
        if manifest.dependencies:
            lines.append("zależności:")
            for key, value in sorted(manifest.dependencies.items()):
                lines.append(f"  {key}: {value}")
        return "\n".join(lines) + "\n"

    def _ensure_safe_install(self, source_dir: Path, target_dir: Path) -> None:
        try:
            source_dir.relative_to(self.project_root)
        except ValueError as error:
            raise SecurityError("KURWA ERROR: zabezpieczona paczka nie może wyjść poza katalog projektu") from error
        target_dir.mkdir(parents=True, exist_ok=True)

    def _check_dependency_is_compatible(self, package_name: str, requirement: str) -> None:
        package_dir = self.package_dir / package_name
        if not package_dir.exists():
            return
        candidates = []
        for version_dir in sorted(package_dir.iterdir(), reverse=True):
            if not version_dir.is_dir():
                continue
            manifest_path = version_dir / "kurwa.pack"
            if manifest_path.exists():
                try:
                    manifest = self._parse_manifest_file(manifest_path)
                    candidates.append((Version.parse(manifest.version), manifest.version))
                except Exception:
                    continue
        if not candidates:
            return
        installed_version = max(candidates, key=lambda item: item[0])[1]
        if not self._satisfies(installed_version, requirement):
            raise DependencyError(
                f"KURWA ERROR: konflikt wersji zależności {package_name}: wymaga {requirement}, zainstalowano {installed_version}"
            )

    def _check_cycle(self, package_name: str, dependencies: dict[str, str], stack: list[str] | None = None) -> None:
        stack = stack or []
        if package_name in stack:
            cycle = " -> ".join(stack + [package_name])
            raise DependencyError(f"KURWA ERROR: cykl zależności wykryty: {cycle}")

        next_stack = stack + [package_name]
        for dep_name, _ in dependencies.items():
            manifest = self._resolve_dependency_manifest(dep_name)
            if manifest is None:
                continue
            if dep_name in next_stack:
                cycle = " -> ".join(next_stack + [dep_name])
                raise DependencyError(f"KURWA ERROR: cykl zależności wykryty: {cycle}")
            self._check_cycle(dep_name, manifest.dependencies, next_stack)

    def _resolve_dependency_manifest(self, package_name: str) -> PackageManifest | None:
        package_root = self.project_root / "packages" / package_name
        if package_root.exists():
            manifest_path = package_root / "kurwa.pack"
            if manifest_path.exists():
                try:
                    return self._parse_manifest_file(manifest_path)
                except Exception:
                    return None

        installed_root = self.package_dir / package_name
        if not installed_root.exists():
            return None

        versions = sorted(
            [child for child in installed_root.iterdir() if child.is_dir()],
            key=lambda item: Version.parse(item.name),
            reverse=True,
        )
        for version_dir in versions:
            manifest_path = version_dir / "kurwa.pack"
            if manifest_path.exists():
                try:
                    return self._parse_manifest_file(manifest_path)
                except Exception:
                    continue
        return None

    @staticmethod
    def _satisfies(version: str, requirement: str) -> bool:
        requirement = requirement.strip()
        required = Version.parse(version)
        if requirement.startswith("=="):
            return required == Version.parse(requirement[2:])
        if requirement.startswith(">="):
            return required >= Version.parse(requirement[2:])
        if requirement.startswith("<="):
            return required <= Version.parse(requirement[2:])
        if requirement.startswith(">"):
            return required > Version.parse(requirement[1:])
        if requirement.startswith("<"):
            return required < Version.parse(requirement[1:])
        return required == Version.parse(requirement)

    @staticmethod
    def _find_latest_installed_version(package_dir: Path) -> str | None:
        versions = []
        for candidate in package_dir.iterdir():
            if candidate.is_dir():
                try:
                    versions.append(str(Version.parse(candidate.name)))
                except VersionError:
                    continue
        if not versions:
            return None
        return max(versions, key=lambda item: Version.parse(item))


def find_project_root(start_path: Path | str | None) -> Path | None:
    current = Path(start_path).resolve() if start_path is not None else Path.cwd().resolve()
    while True:
        if (current / "kurwa.pack").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def install_project_package(project_root: Path | str, package_name: str | Path) -> dict[str, Any]:
    manager = ProjectPackageManager(project_root)
    source = Path(package_name)
    if source.exists():
        return manager.install_local_package(source)
    raise PackageManagerError(f"KURWA ERROR: nie znaleziono paczki do instalacji: {package_name}")
