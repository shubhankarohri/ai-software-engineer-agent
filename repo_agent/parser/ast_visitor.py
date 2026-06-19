
import ast
from pathlib import Path
from typing import Optional
from .models import (
    ImportInfo, ArgumentInfo, FunctionInfo,
    ClassInfo, FileAnalysis
)


class CodeVisitor(ast.NodeVisitor):

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.analysis = FileAnalysis(
            file_path=file_path,
            module_name=self._path_to_module(file_path),
            lines_of_code=len(source_lines),
        )
        self._current_class: Optional[str] = None

    def _path_to_module(self, path: str) -> str:
        return path.replace("/", ".").replace("\\", ".").removesuffix(".py")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            info = ImportInfo(
                file_path=self.file_path,
                module=alias.name,
                names=[alias.asname or alias.name],
                is_from_import=False,
                is_relative=False,
                line_number=node.lineno,
            )
            self.analysis.imports.append(info)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        is_relative = node.level > 0
        if is_relative:
            dots = "." * node.level
            module = dots + module

        names = [alias.name for alias in node.names]

        info = ImportInfo(
            file_path=self.file_path,
            module=module,
            names=names,
            is_from_import=True,
            is_relative=is_relative,
            line_number=node.lineno,
        )
        self.analysis.imports.append(info)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        base_classes = self._extract_base_classes(node)
        decorators = self._extract_decorators(node)
        docstring = ast.get_docstring(node)

        is_abstract = any(
            b in ("ABC", "ABCMeta") for b in base_classes
        ) or any(
            d in ("abstractmethod",) for d in decorators
        )

        class_info = ClassInfo(
            file_path=self.file_path,
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            base_classes=base_classes,
            decorators=decorators,
            docstring=docstring,
            is_abstract=is_abstract,
        )

        previous_class = self._current_class
        self._current_class = node.name

        self.generic_visit(node)

        class_info.methods = [
            f for f in self.analysis.functions
            if f.parent_class == node.name
        ]

        self._current_class = previous_class

        self.analysis.classes.append(class_info)

    def _extract_base_classes(self, node: ast.ClassDef) -> list[str]:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id}.{base.attr}")
            elif isinstance(base, ast.Subscript):
                if isinstance(base.value, ast.Name):
                    bases.append(base.value.id)
        return bases

    def _extract_decorators(self, node) -> list[str]:
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"{dec.value.id}.{dec.attr}")
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    decorators.append(f"{dec.func.value.id}.{dec.func.attr}")
                elif isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
        return decorators

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node, is_async=True)

    def _process_function(self, node, is_async: bool) -> None:
        args = self._extract_arguments(node.args)
        decorators = self._extract_decorators(node)
        docstring = ast.get_docstring(node)
        complexity = self._compute_complexity(node)

        return_annotation = None
        if node.returns:
            return_annotation = ast.unparse(node.returns)

        func_info = FunctionInfo(
            file_path=self.file_path,
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            is_method=self._current_class is not None,
            parent_class=self._current_class,
            arguments=args,
            return_annotation=return_annotation,
            decorators=decorators,
            is_async=is_async,
            docstring=docstring,
            complexity=complexity,
        )
        self.analysis.functions.append(func_info)

        self.generic_visit(node)

    def _extract_arguments(self, args: ast.arguments) -> list[ArgumentInfo]:
        result = []

        num_args = len(args.args)
        num_defaults = len(args.defaults)
        default_offset = num_args - num_defaults

        for i, arg in enumerate(args.args):
            if arg.arg == "self" or arg.arg == "cls":
                continue

            annotation = None
            if arg.annotation:
                annotation = ast.unparse(arg.annotation)

            default = None
            default_index = i - default_offset
            if default_index >= 0:
                default = ast.unparse(args.defaults[default_index])

            result.append(ArgumentInfo(
                name=arg.arg,
                type_annotation=annotation,
                default_value=default,
            ))

        if args.vararg:
            annotation = ast.unparse(args.vararg.annotation) if args.vararg.annotation else None
            result.append(ArgumentInfo(
                name=args.vararg.arg,
                type_annotation=annotation,
                is_args=True,
            ))

        if args.kwarg:
            annotation = ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None
            result.append(ArgumentInfo(
                name=args.kwarg.arg,
                type_annotation=annotation,
                is_kwargs=True,
            ))

        return result

    def _compute_complexity(self, node: ast.FunctionDef) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (
                ast.If, ast.For, ast.While, ast.ExceptHandler,
                ast.With, ast.Assert, ast.comprehension,
            )):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
