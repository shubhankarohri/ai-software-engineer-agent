
import json
from pathlib import Path
from dataclasses import dataclass, field
from .scanner import ScanResult


@dataclass
class TechProfile:
    primary_language: str = "Unknown"
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    build_tools: list[str] = field(default_factory=list)
    config_files_found: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_ci: bool = False


EXTENSION_TO_LANGUAGE = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".cpp": "C++", ".c": "C", ".cs": "C#", ".swift": "Swift",
    ".kt": "Kotlin", ".scala": "Scala", ".r": "R", ".m": "MATLAB",
}

CONFIG_SIGNALS = {
    "pyproject.toml": ("Python", "pyproject"),
    "setup.py": ("Python", "setuptools"),
    "setup.cfg": ("Python", "setuptools"),
    "requirements.txt": ("Python", "pip"),
    "Pipfile": ("Python", "pipenv"),
    "poetry.lock": ("Python", "poetry"),
    "package.json": ("JavaScript", "npm"),
    "yarn.lock": ("JavaScript", "yarn"),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java", "gradle"),
    "go.mod": ("Go", "go modules"),
    "Cargo.toml": ("Rust", "cargo"),
    "Gemfile": ("Ruby", "bundler"),
    "Dockerfile": (None, "docker"),
    "docker-compose.yml": (None, "docker-compose"),
    ".github/workflows": (None, "github-actions"),
}

FRAMEWORK_IMPORT_SIGNALS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "tornado": "Tornado", "aiohttp": "aiohttp", "starlette": "Starlette",
    "sqlalchemy": "SQLAlchemy", "celery": "Celery",
    "pytest": "pytest", "unittest": "unittest",
    "react": "React", "vue": "Vue", "angular": "Angular",
    "express": "Express", "next": "Next.js",
}

ENTRY_POINT_NAMES = {
    "main.py", "app.py", "run.py", "server.py", "manage.py",
    "wsgi.py", "asgi.py", "index.py", "__main__.py",
    "index.js", "server.js", "app.js", "main.js",
    "index.ts", "main.ts",
}


class TechDetector:

    def __init__(self, scan_result: ScanResult):
        self.scan = scan_result
        self.root = Path(scan_result.repo_root)
        self._file_map = {f.path: f for f in scan_result.files}
        self._filenames = {Path(f.path).name for f in scan_result.files}
        self._all_paths = {f.path for f in scan_result.files}

    def detect(self) -> TechProfile:
        profile = TechProfile()

        self._detect_from_extensions(profile)
        self._detect_from_config_files(profile)
        self._detect_entry_points(profile)
        self._detect_frameworks_from_imports(profile)
        self._detect_test_suite(profile)
        self._detect_ci(profile)

        return profile

    def _detect_from_extensions(self, profile: TechProfile) -> None:
        lang_counts: dict[str, int] = {}

        for file_info in self.scan.files:
            if file_info.is_binary:
                continue
            lang = EXTENSION_TO_LANGUAGE.get(file_info.extension)
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

        if not lang_counts:
            return

        sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        profile.languages = [lang for lang, _ in sorted_langs]
        profile.primary_language = profile.languages[0]

    def _detect_from_config_files(self, profile: TechProfile) -> None:
        for config_name, (lang, tool) in CONFIG_SIGNALS.items():
            if config_name in self._all_paths or config_name in self._filenames:
                profile.config_files_found.append(config_name)
                profile.build_tools.append(tool)
                if lang and profile.primary_language == "Unknown":
                    profile.primary_language = lang

    def _detect_entry_points(self, profile: TechProfile) -> None:
        for file_info in self.scan.files:
            filename = Path(file_info.path).name
            if filename in ENTRY_POINT_NAMES:
                profile.entry_points.append(file_info.path)

    def _detect_frameworks_from_imports(self, profile: TechProfile) -> None:
        found_frameworks = set()

        for file_info in self.scan.files:
            if file_info.extension != ".py" or file_info.is_binary:
                continue
            if file_info.size_bytes > MAX_SCAN_SIZE:
                continue

            try:
                content = Path(file_info.absolute_path).read_text(
                    encoding="utf-8", errors="ignore"
                )
                content_lower = content.lower()
                for signal, framework in FRAMEWORK_IMPORT_SIGNALS.items():
                    if signal in content_lower:
                        found_frameworks.add(framework)
            except OSError:
                continue

        profile.frameworks = sorted(found_frameworks)

    def _detect_test_suite(self, profile: TechProfile) -> None:
        test_indicators = {"tests", "test", "spec", "__tests__"}
        for file_info in self.scan.files:
            parts = set(Path(file_info.path).parts)
            if parts & test_indicators:
                profile.has_tests = True
                return
            if Path(file_info.path).name.startswith("test_"):
                profile.has_tests = True
                return

    def _detect_ci(self, profile: TechProfile) -> None:
        ci_indicators = {".github", ".circleci", ".travis.yml", "Jenkinsfile"}
        for file_info in self.scan.files:
            parts = set(Path(file_info.path).parts)
            if parts & ci_indicators:
                profile.has_ci = True
                return


MAX_SCAN_SIZE = 500_000
