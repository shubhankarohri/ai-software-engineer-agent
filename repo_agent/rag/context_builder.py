
from dataclasses import dataclass

CHARS_PER_TOKEN = 4
MAX_CONTEXT_TOKENS = 6000
MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN


@dataclass
class BuiltContext:
    context_text: str
    chunks_used: int
    total_chars: int
    sources: list[str]


class ContextBuilder:

    def build(self, search_results: list[dict]) -> BuiltContext:
        if not search_results:
            return BuiltContext(
                context_text="No relevant code found.",
                chunks_used=0,
                total_chars=0,
                sources=[],
            )

        seen_chunks = set()
        context_parts = []
        sources = []
        total_chars = 0

        for result in search_results:
            chunk_id = result["chunk_id"]

            if chunk_id in seen_chunks:
                continue

            seen_chunks.add(chunk_id)

            chunk_text = self._format_chunk(result)

            if total_chars + len(chunk_text) > MAX_CONTEXT_CHARS:
                break

            context_parts.append(chunk_text)
            sources.append(chunk_id)
            total_chars += len(chunk_text)

        return BuiltContext(
            context_text="\n\n".join(context_parts),
            chunks_used=len(context_parts),
            total_chars=total_chars,
            sources=sources,
        )

    def _format_chunk(self, result: dict) -> str:
        location = (
            f"{result['module']} "
            f"(line {result['start_line']}-{result['end_line']})"
        )

        chunk_type = result["chunk_type"]
        name = result["name"]
        parent = result.get("parent_class")

        if parent:
            header = f"### {chunk_type}: {parent}.{name} | {location}"
        else:
            header = f"### {chunk_type}: {name} | {location}"

        lines = [header]

        if result.get("docstring"):
            lines.append(f"# {result['docstring']}")

        lines.extend([
            "```python",
            result["source_preview"],
            "```",
        ])

        return "\n".join(lines)
