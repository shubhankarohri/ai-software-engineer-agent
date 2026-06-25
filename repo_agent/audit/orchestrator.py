
from pathlib import Path
from collections import Counter

from .models import AuditReport, FileAuditResult, Severity
from .detectors import (
    ComplexityDetector,
    LongMethodDetector,
    GodClassDetector,
    DeepNestingDetector,
    TooManyArgumentsDetector,
    LargeFileDetector,
)


class AuditOrchestrator:

    def __init__(self, cache, manifest: dict):
        self.cache = cache
        self.manifest = manifest
        self.repo_name = manifest["repository"]["name"]
        self.repo_root = Path(manifest["repository"]["root"])

        self.detectors = {
            "complexity": ComplexityDetector(),
            "long_method": LongMethodDetector(),
            "god_class": GodClassDetector(),
            "too_many_args": TooManyArgumentsDetector(),
            "large_file": LargeFileDetector(),
        }

        self.nesting_detector = DeepNestingDetector()

    def run(self) -> AuditReport:

        report = AuditReport(repo_name=self.repo_name)

        python_files = self.manifest.get("python_files", [])

        print(f"  Analyzing {len(python_files)} files...")

        for rel_path in python_files:
            abs_path = str(self.repo_root / rel_path)

            file_result = self._audit_file(
                rel_path,
                abs_path,
            )

            if file_result.smell_count > 0:
                report.files.append(file_result)

            report.total_files_analyzed += 1
            report.total_smells += file_result.smell_count

        all_smells = [
            smell
            for file_result in report.files
            for smell in file_result.smells
        ]

        severity_counts = Counter(
            smell.severity
            for smell in all_smells
        )

        report.critical_count = severity_counts.get(
            Severity.CRITICAL,
            0,
        )

        report.high_count = severity_counts.get(
            Severity.HIGH,
            0,
        )

        report.medium_count = severity_counts.get(
            Severity.MEDIUM,
            0,
        )

        report.low_count = severity_counts.get(
            Severity.LOW,
            0,
        )

        report.smell_distribution = dict(
            Counter(
                smell.smell_type
                for smell in all_smells
            )
        )

        report.most_problematic_files = sorted(
            [
                (
                    file_result.file_path,
                    file_result.smell_count,
                    file_result.critical_count,
                )
                for file_result in report.files
            ],
            key=lambda x: (x[2], x[1]),
            reverse=True,
        )[:10]

        return report

    def _audit_file(
        self,
        rel_path: str,
        abs_path: str,
    ) -> FileAuditResult:

        file_row = self.cache.conn.execute(
            "SELECT * FROM files WHERE file_path = ?",
            (rel_path,),
        ).fetchone()

        loc = file_row["lines_of_code"] if file_row else 0
        module = file_row["module_name"] if file_row else rel_path

        result = FileAuditResult(
            file_path=rel_path,
            module_name=module,
            lines_of_code=loc,
        )

        for detector in self.detectors.values():
            try:
                smells = detector.detect(
                    self.cache,
                    rel_path,
                )

                result.smells.extend(smells)

            except Exception:
                pass

        try:
            source = Path(abs_path).read_text(
                encoding="utf-8",
                errors="ignore",
            )

            nesting_smells = self.nesting_detector.detect_in_source(
                source,
                rel_path,
                module,
            )

            result.smells.extend(nesting_smells)

        except Exception:
            pass

        return result
