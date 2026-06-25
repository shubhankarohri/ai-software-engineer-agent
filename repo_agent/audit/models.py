
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeSmell:
    smell_type: str
    severity: Severity
    file_path: str
    module_name: str
    entity_name: str
    line_start: int
    line_end: int
    message: str
    metric_value: float
    threshold: float
    suggestion: str


@dataclass
class FileAuditResult:
    file_path: str
    module_name: str
    lines_of_code: int
    smells: list[CodeSmell] = field(default_factory=list)
    maintainability_index: float = 0.0
    avg_complexity: float = 0.0

    @property
    def smell_count(self) -> int:
        return len(self.smells)

    @property
    def critical_count(self) -> int:
        return sum(
            1
            for s in self.smells
            if s.severity == Severity.CRITICAL
        )

    @property
    def high_count(self) -> int:
        return sum(
            1
            for s in self.smells
            if s.severity == Severity.HIGH
        )


@dataclass
class AuditReport:
    repo_name: str
    total_files_analyzed: int = 0
    total_smells: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    files: list[FileAuditResult] = field(default_factory=list)
    smell_distribution: dict = field(default_factory=dict)
    most_problematic_files: list[tuple] = field(default_factory=list)
