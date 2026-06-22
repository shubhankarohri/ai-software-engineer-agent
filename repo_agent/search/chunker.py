
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import ast


@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    module_name: str
    chunk_type: str
    name: str
    parent_class: Optional[str]
    source_code: str
    start_line: int
    end_line: int
    docstring: Optional[str]


class CodeChunker:

    def __init__(self, max_chunk_chars: int = 1500):
        self.max_chunk_chars = max_chunk_chars

    def chunk_file(self, file_path: str, module_name: str) -> list[CodeChunk]:
        try:
            source = Path(file_path).read_text(
                encoding="utf-8",
                errors="ignore"
            )
            lines = source.splitlines()
            tree = ast.parse(source)
        except Exception:
            return []

        chunks = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not self._is_method(node, tree):
                    chunk = self._make_function_chunk(
                        node,
                        lines,
                        file_path,
                        module_name,
                        parent_class=None,
                    )
                    if chunk:
                        chunks.append(chunk)

            elif isinstance(node, ast.ClassDef):
                class_chunk = self._make_class_chunk(
                    node,
                    lines,
                    file_path,
                    module_name,
                )
                if class_chunk:
                    chunks.append(class_chunk)

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_chunk = self._make_function_chunk(
                            item,
                            lines,
                            file_path,
                            module_name,
                            parent_class=node.name,
                        )
                        if method_chunk:
                            chunks.append(method_chunk)

        if not chunks:
            module_chunk = self._make_module_chunk(
                source,
                file_path,
                module_name,
            )
            if module_chunk:
                chunks.append(module_chunk)

        return chunks

    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in ast.walk(parent):
                    if node in parent.body:
                        return True
        return False

    def _extract_source(self, node, lines: list[str]) -> str:
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(lines[start:end])

    def _make_function_chunk(
        self,
        node,
        lines,
        file_path,
        module_name,
        parent_class,
    ) -> Optional[CodeChunk]:
        source = self._extract_source(node, lines)

        if not source.strip():
            return None

        prefix = f"{parent_class}." if parent_class else ""
        chunk_id = f"{module_name}::{prefix}{node.name}"
        chunk_type = "method" if parent_class else "function"

        return CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            module_name=module_name,
            chunk_type=chunk_type,
            name=node.name,
            parent_class=parent_class,
            source_code=source[:self.max_chunk_chars],
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
        )

    def _make_class_chunk(
        self,
        node,
        lines,
        file_path,
        module_name,
    ) -> Optional[CodeChunk]:
        start = node.lineno - 1
        end = min(node.lineno + 20, node.end_lineno or node.lineno)
        source = "\n".join(lines[start:end])

        if not source.strip():
            return None

        return CodeChunk(
            chunk_id=f"{module_name}::{node.name}",
            file_path=file_path,
            module_name=module_name,
            chunk_type="class",
            name=node.name,
            parent_class=None,
            source_code=source[:self.max_chunk_chars],
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
        )

    def _make_module_chunk(
        self,
        source,
        file_path,
        module_name,
    ) -> Optional[CodeChunk]:
        if not source.strip():
            return None

        return CodeChunk(
            chunk_id=f"{module_name}::__module__",
            file_path=file_path,
            module_name=module_name,
            chunk_type="module",
            name="__module__",
            parent_class=None,
            source_code=source[:self.max_chunk_chars],
            start_line=1,
            end_line=source.count("\n") + 1,
            docstring=None,
        )
