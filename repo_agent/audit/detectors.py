
import ast
import json

from .models import CodeSmell, Severity


COMPLEXITY_HIGH = 10
COMPLEXITY_CRITICAL = 20
FUNCTION_LINES_MEDIUM = 50
FUNCTION_LINES_HIGH = 100
CLASS_METHODS_HIGH = 15
CLASS_METHODS_CRITICAL = 25
NESTING_DEPTH_MEDIUM = 4
NESTING_DEPTH_HIGH = 6
FUNCTION_ARGS_MEDIUM = 5
FUNCTION_ARGS_HIGH = 8
FILE_LINES_MEDIUM = 300
FILE_LINES_HIGH = 500


class ComplexityDetector:

    def detect(self, cache, file_path: str) -> list[CodeSmell]:
        smells = []
        functions = cache.conn.execute(
            "SELECT * FROM functions WHERE file_path = ?",
            (file_path,)
        ).fetchall()

        for fn in functions:
            complexity = fn["complexity"]

            if complexity < COMPLEXITY_HIGH:
                continue

            if complexity >= COMPLEXITY_CRITICAL:
                severity = Severity.CRITICAL
                suggestion = (
                    f"Split '{fn['name']}' into smaller functions. "
                    f"Complexity {complexity} is unmaintainable. "
                    f"Target < {COMPLEXITY_HIGH} per function."
                )
            else:
                severity = Severity.HIGH
                suggestion = (
                    f"Consider refactoring '{fn['name']}' to reduce "
                    f"branching. Extract conditions into named functions."
                )

            parent = fn["parent_class"]
            entity = f"{parent}.{fn['name']}" if parent else fn["name"]

            smells.append(CodeSmell(
                smell_type="high_complexity",
                severity=severity,
                file_path=file_path,
                module_name=fn["file_path"],
                entity_name=entity,
                line_start=fn["line_start"],
                line_end=fn["line_end"],
                message=(
                    f"Function '{entity}' has cyclomatic complexity "
                    f"of {complexity} (threshold: {COMPLEXITY_HIGH})"
                ),
                metric_value=complexity,
                threshold=COMPLEXITY_HIGH,
                suggestion=suggestion,
            ))

        return smells


class LongMethodDetector:

    def detect(self, cache, file_path: str) -> list[CodeSmell]:
        smells = []

        functions = cache.conn.execute(
            "SELECT * FROM functions WHERE file_path = ?",
            (file_path,)
        ).fetchall()

        for fn in functions:
            length = (fn["line_end"] or 0) - (fn["line_start"] or 0)

            if length < FUNCTION_LINES_MEDIUM:
                continue

            severity = (
                Severity.HIGH
                if length >= FUNCTION_LINES_HIGH
                else Severity.MEDIUM
            )

            parent = fn["parent_class"]
            entity = f"{parent}.{fn['name']}" if parent else fn["name"]

            smells.append(CodeSmell(
                smell_type="long_method",
                severity=severity,
                file_path=file_path,
                module_name=fn["file_path"],
                entity_name=entity,
                line_start=fn["line_start"],
                line_end=fn["line_end"],
                message=(
                    f"'{entity}' is {length} lines long "
                    f"(threshold: {FUNCTION_LINES_MEDIUM})"
                ),
                metric_value=length,
                threshold=FUNCTION_LINES_MEDIUM,
                suggestion=(
                    f"Extract logical sections of '{entity}' into "
                    f"helper functions. Each function should do one thing."
                ),
            ))

        return smells


class GodClassDetector:

    def detect(self, cache, file_path: str) -> list[CodeSmell]:
        smells = []

        classes = cache.conn.execute(
            "SELECT * FROM classes WHERE file_path = ?",
            (file_path,)
        ).fetchall()

        for cls in classes:
            method_count = cache.conn.execute(
                "SELECT COUNT(*) FROM functions "
                "WHERE file_path = ? AND parent_class = ? AND is_method = 1",
                (file_path, cls["name"])
            ).fetchone()[0]

            if method_count < CLASS_METHODS_HIGH:
                continue

            severity = (
                Severity.CRITICAL
                if method_count >= CLASS_METHODS_CRITICAL
                else Severity.HIGH
            )

            smells.append(CodeSmell(
                smell_type="god_class",
                severity=severity,
                file_path=file_path,
                module_name=cls["file_path"],
                entity_name=cls["name"],
                line_start=cls["line_start"],
                line_end=cls["line_end"],
                message=(
                    f"Class '{cls['name']}' has {method_count} methods "
                    f"(threshold: {CLASS_METHODS_HIGH}). "
                    f"This is a God Class."
                ),
                metric_value=method_count,
                threshold=CLASS_METHODS_HIGH,
                suggestion=(
                    f"Apply Single Responsibility Principle. "
                    f"Split '{cls['name']}' into focused classes, "
                    f"each handling one concern."
                ),
            ))

        return smells


class DeepNestingDetector:

    def detect_in_source(
        self,
        source: str,
        file_path: str,
        module_name: str,
    ) -> list[CodeSmell]:

        smells = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            max_depth = self._max_nesting_depth(node)

            if max_depth < NESTING_DEPTH_MEDIUM:
                continue

            severity = (
                Severity.HIGH
                if max_depth >= NESTING_DEPTH_HIGH
                else Severity.MEDIUM
            )

            smells.append(CodeSmell(
                smell_type="deep_nesting",
                severity=severity,
                file_path=file_path,
                module_name=module_name,
                entity_name=node.name,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                message=(
                    f"'{node.name}' has nesting depth of {max_depth} "
                    f"(threshold: {NESTING_DEPTH_MEDIUM})"
                ),
                metric_value=max_depth,
                threshold=NESTING_DEPTH_MEDIUM,
                suggestion=(
                    "Use early returns and guard clauses to reduce nesting. "
                    "Extract deeply nested blocks into named functions."
                ),
            ))

        return smells

    def _max_nesting_depth(self, func_node: ast.FunctionDef) -> int:

        def _depth(node, current=0):
            nesting_nodes = (
                ast.If,
                ast.For,
                ast.While,
                ast.With,
                ast.Try,
                ast.ExceptHandler,
            )

            max_d = current

            for child in ast.iter_child_nodes(node):
                if isinstance(child, nesting_nodes):
                    max_d = max(max_d, _depth(child, current + 1))
                else:
                    max_d = max(max_d, _depth(child, current))

            return max_d

        return _depth(func_node)


class TooManyArgumentsDetector:

    def detect(self, cache, file_path: str) -> list[CodeSmell]:
        smells = []

        functions = cache.conn.execute(
            "SELECT * FROM functions WHERE file_path = ?",
            (file_path,)
        ).fetchall()

        for fn in functions:
            args = json.loads(fn["arguments"] or "[]")

            real_args = [
                a for a in args
                if not a.get("is_args") and not a.get("is_kwargs")
            ]

            arg_count = len(real_args)

            if arg_count < FUNCTION_ARGS_MEDIUM:
                continue

            severity = (
                Severity.HIGH
                if arg_count >= FUNCTION_ARGS_HIGH
                else Severity.MEDIUM
            )

            parent = fn["parent_class"]
            entity = f"{parent}.{fn['name']}" if parent else fn["name"]

            smells.append(CodeSmell(
                smell_type="too_many_arguments",
                severity=severity,
                file_path=file_path,
                module_name=fn["file_path"],
                entity_name=entity,
                line_start=fn["line_start"],
                line_end=fn["line_end"],
                message=(
                    f"'{entity}' has {arg_count} arguments "
                    f"(threshold: {FUNCTION_ARGS_MEDIUM})"
                ),
                metric_value=arg_count,
                threshold=FUNCTION_ARGS_MEDIUM,
                suggestion=(
                    f"Group related arguments into a dataclass or config "
                    f"object. Consider the Builder pattern for complex "
                    f"object construction."
                ),
            ))

        return smells


class LargeFileDetector:

    def detect(self, cache, file_path: str) -> list[CodeSmell]:
        file_row = cache.conn.execute(
            "SELECT * FROM files WHERE file_path = ?",
            (file_path,)
        ).fetchone()

        if not file_row:
            return []

        loc = file_row["lines_of_code"] or 0

        if loc < FILE_LINES_MEDIUM:
            return []

        severity = (
            Severity.HIGH
            if loc >= FILE_LINES_HIGH
            else Severity.MEDIUM
        )

        return [
            CodeSmell(
                smell_type="large_file",
                severity=severity,
                file_path=file_path,
                module_name=file_row["module_name"] or file_path,
                entity_name=file_path.split("/")[-1],
                line_start=1,
                line_end=loc,
                message=(
                    f"File has {loc} lines of code "
                    f"(threshold: {FILE_LINES_MEDIUM})"
                ),
                metric_value=loc,
                threshold=FILE_LINES_MEDIUM,
                suggestion=(
                    "Split this file into smaller, focused modules. "
                    "Each module should have a single, clear responsibility."
                ),
            )
        ]
