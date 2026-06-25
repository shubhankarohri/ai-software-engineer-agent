
import json
from pathlib import Path
from .models import AuditReport, Severity


SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🟢",
    Severity.INFO: "🔵",
}


class AuditReporter:

    def __init__(self, report: AuditReport):
        self.report = report

    def print_summary(self) -> None:
        r = self.report

        print(f"\n{'='*55}")
        print(f"  AUDIT REPORT — {r.repo_name}")
        print(f"{'='*55}")

        print(f"\n  Files analyzed : {r.total_files_analyzed}")
        print(f"  Total smells   : {r.total_smells}")

        print(f"\n  Severity breakdown:")
        print(f"    🔴 Critical : {r.critical_count}")
        print(f"    🟠 High     : {r.high_count}")
        print(f"    🟡 Medium   : {r.medium_count}")
        print(f"    🟢 Low      : {r.low_count}")

        if r.smell_distribution:
            print(f"\n  Smell types found:")
            for smell_type, count in sorted(
                r.smell_distribution.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                bar = "█" * min(count, 20)
                print(f"    {smell_type:<25} {bar} {count}")

        if r.most_problematic_files:
            print(f"\n  Most problematic files:")
            for fp, count, critical in r.most_problematic_files[:5]:
                short = fp.split("/")[-1]
                crit_str = f" ({critical} critical)" if critical else ""
                print(f"    {short:<35} {count} smells{crit_str}")

    def print_detailed(
        self,
        min_severity: Severity = Severity.HIGH,
    ) -> None:
        severity_order = [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]

        min_idx = severity_order.index(min_severity)

        print(f"\n{'='*55}")
        print(f"  DETAILED FINDINGS (≥ {min_severity.value})")
        print(f"{'='*55}")

        for file_result in self.report.files:
            relevant = [
                s
                for s in file_result.smells
                if severity_order.index(s.severity) <= min_idx
            ]

            if not relevant:
                continue

            short = file_result.file_path.split("/")[-1]

            print(f"\n📁 {short} ({file_result.lines_of_code} LOC)")

            for smell in sorted(
                relevant,
                key=lambda x: severity_order.index(x.severity),
            ):
                icon = SEVERITY_ICONS[smell.severity]

                print(
                    f"\n  {icon} [{smell.smell_type}] "
                    f"line {smell.line_start}"
                )
                print(f"     {smell.message}")
                print(f"     💡 {smell.suggestion}")

    def save_json(
        self,
        output_path: str = "data/audit_report.json",
    ) -> str:
        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "repo_name": self.report.repo_name,
            "total_files": self.report.total_files_analyzed,
            "total_smells": self.report.total_smells,
            "severity_counts": {
                "critical": self.report.critical_count,
                "high": self.report.high_count,
                "medium": self.report.medium_count,
                "low": self.report.low_count,
            },
            "smell_distribution": self.report.smell_distribution,
            "files": [
                {
                    "file": f.file_path,
                    "loc": f.lines_of_code,
                    "smells": [
                        {
                            "type": s.smell_type,
                            "severity": s.severity.value,
                            "entity": s.entity_name,
                            "line": s.line_start,
                            "message": s.message,
                            "suggestion": s.suggestion,
                            "metric": s.metric_value,
                        }
                        for s in f.smells
                    ],
                }
                for f in self.report.files
            ],
        }

        with open(output_path, "w") as f:
            json.dump(
                data,
                f,
                indent=2,
            )

        print(f"  ✓ Report saved: {output_path}")
        return output_path
