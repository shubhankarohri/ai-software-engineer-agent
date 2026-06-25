
import google.generativeai as genai
from .models import (
    RefactoringPlan,
    RefactoringStep,
    Priority,
    Effort,
)

REFACTORING_SYSTEM_PROMPT = """You are a senior software engineer specializing in code refactoring and software architecture.

You will be given:
1. A detected code smell with its metrics
2. The actual source code that has the smell

Your job is to produce a concrete, actionable refactoring plan.
Be specific — name the exact functions, classes, and files involved.
Do not give generic advice. Give step-by-step instructions a junior developer could follow.

Format your response exactly like this:

PROBLEM:
[One paragraph explaining what's wrong and why it matters]

STEPS:
1. [Concrete action]
2. [Next step]

AFFECTED FILES:
- [file path]

RISKS:
- [risk]

EFFORT: [LOW / MEDIUM / HIGH / EPIC]"""

SMELL_PRIORITY = {
    "high_complexity": Priority.P1,
    "god_class": Priority.P1,
    "long_method": Priority.P2,
    "deep_nesting": Priority.P2,
    "too_many_arguments": Priority.P2,
    "large_file": Priority.P3,
}

EFFORT_MAP = {
    "LOW": Effort.LOW,
    "MEDIUM": Effort.MEDIUM,
    "HIGH": Effort.HIGH,
    "EPIC": Effort.EPIC,
}


class RefactoringPlanner:

    def __init__(self, search_index, embedder, api_key: str):
        self.search_index = search_index
        self.embedder = embedder

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=REFACTORING_SYSTEM_PROMPT,
        )

    def plan_for_smell(self, smell: dict) -> RefactoringPlan:
        query = f"{smell['type']} {smell['entity']} {smell['message']}"
        query_vec = self.embedder.embed_query(query)
        results = self.search_index.search(query_vec, top_k=4)

        code_context = self._build_code_context(results, smell)

        prompt = f"""Detected smell: {smell['type'].upper()}
Severity: {smell['severity']}
Entity: {smell['entity']}
File: {smell['file']}
Line: {smell['line']}
Issue: {smell['message']}
Metric: {smell.get('metric', 'N/A')}

Source code context:
{code_context}

Generate a concrete refactoring plan."""

        try:
            response = self.model.generate_content(prompt)
            ai_text = response.text
        except Exception as e:
            ai_text = f"Could not generate plan: {e}"

        return self._parse_response(ai_text, smell)

    def plan_top_smells(self, audit_report, max_plans: int = 5):
        all_smells = []

        for file_result in audit_report.files:
            for smell in file_result.smells:
                all_smells.append({
                    "type": smell.smell_type,
                    "severity": smell.severity.value,
                    "entity": smell.entity_name,
                    "file": smell.file_path,
                    "line": smell.line_start,
                    "message": smell.message,
                    "metric": smell.metric_value,
                    "suggestion": smell.suggestion,
                })

        severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
        }

        all_smells.sort(
            key=lambda s: severity_order.get(s["severity"], 9)
        )

        seen = set()
        top_smells = []

        for smell in all_smells:
            key = (smell["type"], smell["entity"])

            if key not in seen:
                seen.add(key)
                top_smells.append(smell)

            if len(top_smells) >= max_plans:
                break

        print(f"  Generating plans for {len(top_smells)} smells...")

        plans = []

        for i, smell in enumerate(top_smells, 1):
            print(
                f"    [{i}/{len(top_smells)}] Planning: "
                f"{smell['type']} in {smell['entity']}"
            )

            plan = self.plan_for_smell(smell)
            plans.append(plan)

        return plans

    def _build_code_context(self, search_results, smell):
        if not search_results:
            return "No source code retrieved."

        parts = []

        for r in search_results[:3]:
            header = (
                f"### {r['chunk_type']}: "
                f"{r['name']} ({r['module']})"
            )

            parts.append(
                f"{header}\n```python\n"
                f"{r['source_preview']}\n```"
            )

        return "\n\n".join(parts)

    def _parse_response(self, ai_text, smell):
        effort = Effort.MEDIUM

        for effort_key, effort_val in EFFORT_MAP.items():
            if f"EFFORT: {effort_key}" in ai_text.upper():
                effort = effort_val
                break

        steps = []
        in_steps = False
        step_num = 0

        for line in ai_text.split("\n"):
            if line.strip().startswith("STEPS:"):
                in_steps = True
                continue

            if in_steps and line.strip() and line.strip()[0].isdigit():
                step_num += 1

                steps.append(
                    RefactoringStep(
                        order=step_num,
                        action=f"Step {step_num}",
                        description=line.strip(),
                        target_file=smell["file"],
                        target_entity=smell["entity"],
                    )
                )

            elif in_steps and line.strip().startswith(
                ("AFFECTED", "RISKS", "EFFORT")
            ):
                in_steps = False

        affected = []
        in_files = False

        for line in ai_text.split("\n"):
            if "AFFECTED FILES:" in line:
                in_files = True
                continue

            if in_files and line.strip().startswith("-"):
                affected.append(
                    line.strip("- ").strip()
                )

            elif in_files and line.strip().startswith(
                ("RISKS", "EFFORT")
            ):
                in_files = False

        risks = []
        in_risks = False

        for line in ai_text.split("\n"):
            if "RISKS:" in line:
                in_risks = True
                continue

            if in_risks and line.strip().startswith("-"):
                risks.append(
                    line.strip("- ").strip()
                )

            elif in_risks and line.strip().startswith("EFFORT"):
                in_risks = False

        return RefactoringPlan(
            smell_type=smell["type"],
            severity=smell["severity"],
            entity_name=smell["entity"],
            file_path=smell["file"],
            problem_summary=smell["message"],
            priority=SMELL_PRIORITY.get(
                smell["type"],
                Priority.P2,
            ),
            effort=effort,
            steps=steps,
            affected_files=affected,
            risks=risks,
            ai_explanation=ai_text,
        )
