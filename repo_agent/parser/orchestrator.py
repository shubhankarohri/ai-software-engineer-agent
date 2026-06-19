
import ast
from pathlib import Path
from .ast_visitor import CodeVisitor
from .cache import ASTCache
from .models import FileAnalysis, RepoAnalysis


class ParserOrchestrator:

    def __init__(self, manifest: dict, cache: ASTCache):
        self.manifest = manifest
        self.cache = cache
        self.repo_root = manifest["repository"]["root"]

    def _parse_file(self, file_path: str, absolute_path: str) -> FileAnalysis:
        try:
            source = Path(absolute_path).read_text(
                encoding="utf-8",
                errors="ignore"
            )
            source_lines = source.splitlines()
            tree = ast.parse(source, filename=file_path)

            visitor = CodeVisitor(
                file_path=file_path,
                source_lines=source_lines
            )
            visitor.visit(tree)

            return visitor.analysis

        except SyntaxError as e:
            return FileAnalysis(
                file_path=file_path,
                module_name=file_path,
                lines_of_code=0,
                has_parse_error=True,
                parse_error_message=f"SyntaxError at line {e.lineno}: {e.msg}",
            )

        except Exception as e:
            return FileAnalysis(
                file_path=file_path,
                module_name=file_path,
                lines_of_code=0,
                has_parse_error=True,
                parse_error_message=str(e),
            )

    def run(self, force_reparse: bool = False) -> RepoAnalysis:

        python_files = self.manifest.get("python_files", [])
        repo_root = Path(self.repo_root)

        analyses = []
        skipped = 0
        failed = 0

        print(f"  Processing {len(python_files)} Python files...")

        for i, rel_path in enumerate(python_files):

            abs_path = str(repo_root / rel_path)

            if not force_reparse and self.cache.is_cached(rel_path):
                skipped += 1
                continue

            analysis = self._parse_file(rel_path, abs_path)

            self.cache.store_file_analysis(analysis)
            analyses.append(analysis)

            if analysis.has_parse_error:
                failed += 1

            if (i + 1) % 20 == 0:
                print(
                    f"    [{i+1}/{len(python_files)}] parsed..."
                )

        stats = self.cache.get_stats()

        print(
            f"  ✓ Parsed: {len(analyses)} new files | "
            f"Cached: {skipped} | Errors: {failed}"
        )

        return RepoAnalysis(
            repo_name=self.manifest["repository"]["name"],
            total_python_files=len(python_files),
            successfully_parsed=(
                stats["total_files"] - stats["parse_errors"]
            ),
            failed_to_parse=stats["parse_errors"],
            total_classes=stats["total_classes"],
            total_functions=stats["total_functions"],
            total_imports=stats["total_imports"],
        )
