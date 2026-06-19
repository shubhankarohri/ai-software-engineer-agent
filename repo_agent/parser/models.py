
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImportInfo:
    file_path: str
    module: str
    names: list[str]
    is_from_import: bool
    is_relative: bool
    line_number: int


@dataclass
class ArgumentInfo:
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    is_args: bool = False
    is_kwargs: bool = False


@dataclass
class FunctionInfo:
    file_path: str
    name: str
    line_start: int
    line_end: int
    is_method: bool
    parent_class: Optional[str]
    arguments: list[ArgumentInfo] = field(default_factory=list)
    return_annotation: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    docstring: Optional[str] = None
    complexity: int = 1


@dataclass
class ClassInfo:
    file_path: str
    name: str
    line_start: int
    line_end: int
    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    is_abstract: bool = False


@dataclass
class FileAnalysis:
    file_path: str
    module_name: str
    lines_of_code: int
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    has_parse_error: bool = False
    parse_error_message: Optional[str] = None


@dataclass
class RepoAnalysis:
    repo_name: str
    total_python_files: int
    successfully_parsed: int
    failed_to_parse: int
    total_classes: int
    total_functions: int
    total_imports: int
    files: list[FileAnalysis] = field(default_factory=list)
