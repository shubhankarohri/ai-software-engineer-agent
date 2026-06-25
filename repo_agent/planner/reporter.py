
import json
from pathlib import Path
from .models import RefactoringPlan, FeatureImplementationPlan


PRIORITY_ICONS = {"p0": "🚨", "p1": "🔴", "p2": "🟠", "p3": "🟡"}
EFFORT_ICONS = {"low": "⚡", "medium": "🔧", "high": "🏗️", "epic": "🚀"}


class PlanReporter:

    def print_refactoring_plan(self, plan: RefactoringPlan) -> None:
        p_icon = PRIORITY_ICONS.get(plan.priority.value, "•")
        e_icon = EFFORT_ICONS.get(plan.effort.value, "•")

        print(f"\n{'='*60}")
        print(f"{p_icon} REFACTORING PLAN — {plan.smell_type.upper()}")
        print(f"{'='*60}")
        print(f"  Entity   : {plan.entity_name}")
        print(f"  File     : {plan.file_path}")
        print(f"  Severity : {plan.severity}")
        print(f"  Priority : {plan.priority.value.upper()}")
        print(f"  Effort   : {e_icon} {plan.effort.value.upper()}")
        print(f"\n  Problem:")
        print(f"  {plan.problem_summary}")

        if plan.steps:
            print(f"\n  Steps:")
            for step in plan.steps:
                print(f"    {step.description}")

        if plan.affected_files:
            print(f"\n  Affected files:")
            for f in plan.affected_files:
                print(f"    - {f}")

        if plan.risks:
            print(f"\n  ⚠️  Risks:")
            for r in plan.risks:
                print(f"    - {r}")

    def print_feature_plan(self, plan: FeatureImplementationPlan) -> None:
        e_icon = EFFORT_ICONS.get(plan.effort.value, "•")

        print(f"\n{'='*60}")
        print(f"🛠️  FEATURE PLAN")
        print(f"{'='*60}")
        print(f"  Feature  : {plan.feature_description}")
        print(f"  Effort   : {e_icon} {plan.effort.value.upper()}")

        if plan.summary:
            print(f"\n  Summary:")
            print(f"  {plan.summary[:300]}")

        if plan.files_to_modify:
            print(f"\n  📝 Files to modify:")
            for f in plan.files_to_modify:
                print(f"    - {f}")

        if plan.files_to_create:
            print(f"\n  ✨ Files to create:")
            for f in plan.files_to_create:
                print(f"    - {f}")

        if plan.steps:
            print(f"\n  Implementation steps:")
            for step in plan.steps:
                print(f"    {step.description}")

        if plan.risks:
            print(f"\n  ⚠️  Risks:")
            for r in plan.risks:
                print(f"    - {r}")

        if plan.dependencies:
            print(f"\n  📦 Dependencies needed:")
            for d in plan.dependencies:
                print(f"    - {d}")

    def save_json(
        self,
        refactoring_plans: list,
        feature_plans: list,
        output_path: str = "data/planning_report.json"
    ) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        data = {
            "refactoring_plans": [
                {
                    "smell_type": p.smell_type,
                    "severity": p.severity,
                    "entity": p.entity_name,
                    "file": p.file_path,
                    "priority": p.priority.value,
                    "effort": p.effort.value,
                    "steps": [s.description for s in p.steps],
                    "affected_files": p.affected_files,
                    "risks": p.risks,
                    "full_plan": p.ai_explanation,
                }
                for p in refactoring_plans
            ],
            "feature_plans": [
                {
                    "feature": p.feature_description,
                    "summary": p.summary,
                    "effort": p.effort.value,
                    "files_to_modify": p.files_to_modify,
                    "files_to_create": p.files_to_create,
                    "steps": [s.description for s in p.steps],
                    "risks": p.risks,
                    "full_plan": p.ai_plan,
                }
                for p in feature_plans
            ],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  ✓ Planning report saved: {output_path}")
        return output_path
