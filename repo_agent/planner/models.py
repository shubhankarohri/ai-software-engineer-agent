
from dataclasses import dataclass, field
from enum import Enum


class Effort(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EPIC = "epic"


class Priority(Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass
class RefactoringStep:
    order: int
    action: str
    description: str
    target_file: str
    target_entity: str


@dataclass
class RefactoringPlan:
    smell_type: str
    severity: str
    entity_name: str
    file_path: str
    problem_summary: str
    priority: Priority
    effort: Effort
    steps: list[RefactoringStep] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    ai_explanation: str = ""


@dataclass
class ImplementationStep:
    order: int
    action: str
    file_path: str
    description: str
    is_new_file: bool = False


@dataclass
class FeatureImplementationPlan:
    feature_description: str
    summary: str
    effort: Effort
    files_to_modify: list[str] = field(default_factory=list)
    files_to_create: list[str] = field(default_factory=list)
    steps: list[ImplementationStep] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    ai_plan: str = ""


@dataclass
class PlanningReport:
    repo_name: str
    refactoring_plans: list[RefactoringPlan] = field(default_factory=list)
    feature_plans: list[FeatureImplementationPlan] = field(default_factory=list)
    total_tech_debt_score: float = 0.0
    priority_order: list[str] = field(default_factory=list)
