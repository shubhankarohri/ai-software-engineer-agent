
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileInfo:
    path: str
    absolute_path: str
    extension: str
    size_bytes: int
    is_binary: bool
    language: Optional[str] = None


@dataclass
class ScanResult:
    repo_name: str
    repo_root: str
    total_files: int = 0
    total_size_bytes: int = 0
    files: list[FileInfo] = field(default_factory=list)
    extension_counts: dict[str, int] = field(default_factory=dict)
    skipped_dirs: list[str] = field(default_factory=list)


IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".tox", ".mypy_cache",
    ".pytest_cache", "*.egg-info", ".idea", ".vscode",
    "migrations",
    "vendor",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".whl", ".pyc", ".pyo",
    ".db", ".sqlite", ".exe", ".dll", ".so", ".dylib",
    ".ttf", ".woff", ".woff2", ".eot", ".mp4", ".mp3",
}

MAX_FILE_SIZE_BYTES = 1_000_000


class RepoScanner:

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        if not self.repo_root.exists():
            raise FileNotFoundError(f"Repo root not found: {repo_root}")

    def _should_skip_dir(self, dir_name: str) -> bool:
        return dir_name in IGNORE_DIRS or dir_name.startswith(".")

    def _is_binary(self, extension: str) -> bool:
        return extension.lower() in BINARY_EXTENSIONS

    def scan(self) -> ScanResult:
        result = ScanResult(
            repo_name=self.repo_root.name,
            repo_root=str(self.repo_root),
        )

        for root, dirs, files in os.walk(self.repo_root):
            skipped = [d for d in dirs if self._should_skip_dir(d)]
            result.skipped_dirs.extend(skipped)
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]

            for filename in files:
                abs_path = Path(root) / filename
                rel_path = abs_path.relative_to(self.repo_root)
                extension = abs_path.suffix.lower()

                try:
                    size = abs_path.stat().st_size
                except OSError:
                    continue

                file_info = FileInfo(
                    path=str(rel_path),
                    absolute_path=str(abs_path),
                    extension=extension,
                    size_bytes=size,
                    is_binary=self._is_binary(extension),
                )

                result.files.append(file_info)
                result.total_files += 1
                result.total_size_bytes += size

                result.extension_counts[extension] = (
                    result.extension_counts.get(extension, 0) + 1
                )

        return result
