
import sqlite3
import json
from pathlib import Path
from .models import FileAnalysis, ClassInfo, FunctionInfo, ImportInfo


CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT UNIQUE NOT NULL,
    module_name     TEXT,
    lines_of_code   INTEGER,
    has_parse_error INTEGER DEFAULT 0,
    parse_error     TEXT
);

CREATE TABLE IF NOT EXISTS classes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER REFERENCES files(id),
    file_path       TEXT NOT NULL,
    name            TEXT NOT NULL,
    line_start      INTEGER,
    line_end        INTEGER,
    base_classes    TEXT,
    decorators      TEXT,
    docstring       TEXT,
    is_abstract     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS functions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER REFERENCES files(id),
    file_path       TEXT NOT NULL,
    name            TEXT NOT NULL,
    line_start      INTEGER,
    line_end        INTEGER,
    is_method       INTEGER DEFAULT 0,
    parent_class    TEXT,
    arguments       TEXT,
    return_annotation TEXT,
    decorators      TEXT,
    is_async        INTEGER DEFAULT 0,
    docstring       TEXT,
    complexity      INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS imports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id         INTEGER REFERENCES files(id),
    file_path       TEXT NOT NULL,
    module          TEXT NOT NULL,
    names           TEXT,
    is_from_import  INTEGER DEFAULT 0,
    is_relative     INTEGER DEFAULT 0,
    line_number     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_classes_file    ON classes(file_path);
CREATE INDEX IF NOT EXISTS idx_functions_file  ON functions(file_path);
CREATE INDEX IF NOT EXISTS idx_imports_module  ON imports(module);
CREATE INDEX IF NOT EXISTS idx_functions_class ON functions(parent_class);
"""


class ASTCache:

    def __init__(self, db_path: str = "data/cache/ast_cache.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self.conn.executescript(CREATE_TABLES_SQL)
        self.conn.commit()

    def is_cached(self, file_path: str) -> bool:
        row = self.conn.execute(
            "SELECT id FROM files WHERE file_path = ?", (file_path,)
        ).fetchone()
        return row is not None

    def store_file_analysis(self, analysis: FileAnalysis) -> None:
        with self.conn:
            cursor = self.conn.execute(
                """INSERT OR REPLACE INTO files
                   (file_path, module_name, lines_of_code, has_parse_error, parse_error)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    analysis.file_path,
                    analysis.module_name,
                    analysis.lines_of_code,
                    int(analysis.has_parse_error),
                    analysis.parse_error_message,
                )
            )
            file_id = cursor.lastrowid

            for cls in analysis.classes:
                self.conn.execute(
                    """INSERT INTO classes
                       (file_id, file_path, name, line_start, line_end,
                        base_classes, decorators, docstring, is_abstract)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id, cls.file_path, cls.name,
                        cls.line_start, cls.line_end,
                        json.dumps(cls.base_classes),
                        json.dumps(cls.decorators),
                        cls.docstring,
                        int(cls.is_abstract),
                    )
                )

            for fn in analysis.functions:
                args_data = [
                    {
                        "name": a.name,
                        "type": a.type_annotation,
                        "default": a.default_value,
                        "is_args": a.is_args,
                        "is_kwargs": a.is_kwargs,
                    }
                    for a in fn.arguments
                ]

                self.conn.execute(
                    """INSERT INTO functions
                       (file_id, file_path, name, line_start, line_end,
                        is_method, parent_class, arguments, return_annotation,
                        decorators, is_async, docstring, complexity)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id, fn.file_path, fn.name,
                        fn.line_start, fn.line_end,
                        int(fn.is_method), fn.parent_class,
                        json.dumps(args_data),
                        fn.return_annotation,
                        json.dumps(fn.decorators),
                        int(fn.is_async),
                        fn.docstring,
                        fn.complexity,
                    )
                )

            for imp in analysis.imports:
                self.conn.execute(
                    """INSERT INTO imports
                       (file_id, file_path, module, names,
                        is_from_import, is_relative, line_number)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id, imp.file_path, imp.module,
                        json.dumps(imp.names),
                        int(imp.is_from_import),
                        int(imp.is_relative),
                        imp.line_number,
                    )
                )

    def get_all_imports(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM imports").fetchall()
        return [dict(r) for r in rows]

    def get_all_classes(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM classes").fetchall()
        return [dict(r) for r in rows]

    def get_all_functions(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM functions ORDER BY complexity DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_most_complex_functions(self, limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM functions ORDER BY complexity DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        return {
            "total_files": self.conn.execute(
                "SELECT COUNT(*) FROM files"
            ).fetchone()[0],

            "total_classes": self.conn.execute(
                "SELECT COUNT(*) FROM classes"
            ).fetchone()[0],

            "total_functions": self.conn.execute(
                "SELECT COUNT(*) FROM functions"
            ).fetchone()[0],

            "total_imports": self.conn.execute(
                "SELECT COUNT(*) FROM imports"
            ).fetchone()[0],

            "parse_errors": self.conn.execute(
                "SELECT COUNT(*) FROM files WHERE has_parse_error=1"
            ).fetchone()[0],
        }

    def close(self) -> None:
        self.conn.close()
