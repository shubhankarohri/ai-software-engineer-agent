
import google.generativeai as genai
from .models import (
    FeatureImplementationPlan,
    ImplementationStep,
    Effort,
)

FEATURE_SYSTEM_PROMPT = """You are a senior software engineer \
who specializes in planning feature implementations.

You will be given:
1. A description of a feature to implement
2. Relevant source code from the existing codebase
3. The repository's tech stack and architecture

Your job is to produce a concrete implementation plan that:
- Specifies exactly which existing files to modify
- Specifies exactly which new files to create
- Lists implementation steps in the correct dependency order
- Identifies risks and edge cases
- Is realistic about effort

Format your response exactly like this:

SUMMARY:
[One paragraph overview of the implementation approach]

FILES TO MODIFY:
- [existing/file.py]&#58; [what changes]
- [another/file.py]&#58; [what changes]

FILES TO CREATE:
- [new/file.py]&#58; [purpose]

IMPLEMENTATION STEPS:
1. [First thing to do — be specific]
2. [Second step]
3. [Continue in dependency order]

RISKS:
- [Technical risk or edge case]
- [Another risk]

DEPENDENCIES:
- [External library needed]
- [Another dependency]

EFFORT: [LOW / MEDIUM / HIGH / EPIC]"""

EFFORT_MAP = {
    "LOW": Effort.LOW,
    "MEDIUM": Effort.MEDIUM,
    "HIGH": Effort.HIGH,
    "EPIC": Effort.EPIC,
}


class FeaturePlanner:

    def __init__(
        self,
        search_index,
        embedder,
        api_key: str,
        manifest: dict,
    ):
        self.search_index = search_index
        self.embedder = embedder
        self.manifest = manifest

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=FEATURE_SYSTEM_PROMPT,
        )

    def plan_feature(self, feature_description: str) -> FeatureImplementationPlan:
        print(f"  Planning: '{feature_description[:60]}...'")

        query_vec = self.embedder.embed_query(feature_description)
        results = self.search_index.search(query_vec, top_k=6)
        code_context = self._build_context(results)

        tech = self.manifest.get("tech_profile", {})
        tech_str = (
            f"Language: {tech.get('primary_language', 'Unknown')}\n"
            f"Frameworks: {', '.join(tech.get('frameworks', []))}\n"
            f"Entry points: {', '.join(self.manifest.get('entry_points', []))}"
        )

        prompt = f"""Repository tech stack:
{tech_str}

Feature to implement:
{feature_description}

Relevant existing code:
{code_context}

Generate a concrete implementation plan."""

        try:
            response = self.model.generate_content(prompt)
            ai_text = response.text
        except Exception as e:
            ai_text = f"Could not generate plan: {e}"

        return self._parse_response(feature_description, ai_text)

    def _build_context(self, results: list[dict]) -> str:
        parts = []
        for r in results[:4]:
            header = f"### {r['chunk_type']}: {r['name']} in {r['module']}"
            parts.append(f"{header}\n```python\n{r['source_preview']}\n```")
        return "\n\n".join(parts) if parts else "No relevant code found."

    def _parse_response(
        self, feature_desc: str, ai_text: str
    ) -> FeatureImplementationPlan:
        effort = Effort.MEDIUM
        for key, val in EFFORT_MAP.items():
            if f"EFFORT: {key}" in ai_text.upper():
                effort = val
                break

        summary = ""
        in_summary = False
        for line in ai_text.split("\n"):
            if "SUMMARY:" in line:
                in_summary = True
                continue
            if in_summary and line.strip() and not line.strip().startswith(
                ("FILES", "IMPL", "RISKS", "DEP", "EFFORT")
            ):
                summary += line.strip() + " "
            elif in_summary and line.strip().startswith(
                ("FILES", "IMPL", "RISKS", "DEP", "EFFORT")
            ):
                break

        files_to_modify = []
        in_modify = False
        for line in ai_text.split("\n"):
            if "FILES TO MODIFY:" in line:
                in_modify = True
                continue
            if in_modify and line.strip().startswith("-"):
                files_to_modify.append(line.strip("- ").strip())
            elif in_modify and not line.strip().startswith("-") and line.strip():
                if not line.strip()[0].isspace():
                    in_modify = False

        files_to_create = []
        in_create = False
        for line in ai_text.split("\n"):
            if "FILES TO CREATE:" in line:
                in_create = True
                continue
            if in_create and line.strip().startswith("-"):
                files_to_create.append(line.strip("- ").strip())
            elif in_create and not line.strip().startswith("-") and line.strip():
                if line.strip().startswith(
                    ("IMPL", "RISKS", "DEP", "EFFORT")
                ):
                    in_create = False

        steps = []
        in_steps = False
        step_num = 0
        for line in ai_text.split("\n"):
            if "IMPLEMENTATION STEPS:" in line:
                in_steps = True
                continue
            if in_steps and line.strip() and line.strip()[0].isdigit():
                step_num += 1
                steps.append(ImplementationStep(
                    order=step_num,
                    action=f"Step {step_num}",
                    file_path="",
                    description=line.strip(),
                ))
            elif in_steps and line.strip().startswith(
                ("RISKS", "DEP", "EFFORT")
            ):
                in_steps = False

        risks = []
        in_risks = False
        for line in ai_text.split("\n"):
            if "RISKS:" in line:
                in_risks = True
                continue
            if in_risks and line.strip().startswith("-"):
                risks.append(line.strip("- ").strip())
            elif in_risks and line.strip().startswith(("DEP", "EFFORT")):
                in_risks = False

        deps = []
        in_deps = False
        for line in ai_text.split("\n"):
            if "DEPENDENCIES:" in line:
                in_deps = True
                continue
            if in_deps and line.strip().startswith("-"):
                deps.append(line.strip("- ").strip())
            elif in_deps and line.strip().startswith("EFFORT"):
                in_deps = False

        return FeatureImplementationPlan(
            feature_description=feature_desc,
            summary=summary.strip(),
            effort=effort,
            files_to_modify=files_to_modify,
            files_to_create=files_to_create,
            steps=steps,
            risks=risks,
            dependencies=deps,
            ai_plan=ai_text,
        )
