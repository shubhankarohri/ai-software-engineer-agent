
import json
import networkx as nx


class MermaidGenerator:

    def __init__(self, graph: nx.DiGraph, cache):
        self.G = graph
        self.cache = cache

    def dependency_flowchart(self, max_nodes: int = 20) -> str:

        top_nodes = sorted(
            self.G.nodes(),
            key=lambda n: self.G.in_degree(n),
            reverse=True
        )[:max_nodes]
        top_set = set(top_nodes)

        lines = ["graph LR"]
        lines.append("")

        for node in top_nodes:
            short = node.split(".")[-1]
            in_deg = self.G.in_degree(node)
            data = self.G.nodes[node]
            complexity = data.get("total_complexity", 0)

            if in_deg > 8:
                lines.append(f'    {short}["{short}"]:::hub')
            elif complexity > 50:
                lines.append(f'    {short}["{short}"]:::complex')
            else:
                lines.append(f'    {short}["{short}"]')

        lines.append("")

        seen_edges = set()
        for src, dst in self.G.edges():
            if src in top_set and dst in top_set:
                src_short = src.split(".")[-1]
                dst_short = dst.split(".")[-1]
                edge_key = (src_short, dst_short)
                if edge_key not in seen_edges:
                    lines.append(f"    {src_short} --> {dst_short}")
                    seen_edges.add(edge_key)

        lines.append("")
        lines.append("    classDef hub fill:#9b2335,stroke:#ff6b6b,color:#fff")
        lines.append("    classDef complex fill:#b5862a,stroke:#ffd700,color:#fff")

        return "\n".join(lines)

    def class_hierarchy_chart(self) -> str:

        all_classes = self.cache.get_all_classes()
        lines = ["classDiagram"]

        for cls in all_classes:
            name = cls["name"]
            bases = json.loads(cls["base_classes"])
            methods = []

            class_methods = self.cache.conn.execute(
                """
                SELECT name, return_annotation
                FROM functions
                WHERE parent_class = ?
                AND is_method = 1
                LIMIT 5
                """,
                (name,),
            ).fetchall()

            for m in class_methods:
                ret = m["return_annotation"] or ""
                methods.append(f"        +{m['name']}() {ret}")

            if methods:
                lines.append(f"    class {name}{{")
                lines.extend(methods)
                lines.append("    }")

            for base in bases:
                base_clean = base.split(".")[-1]
                if base_clean not in (
                    "object",
                    "ABC",
                    "Exception",
                    "BaseException",
                    "dict",
                    "list",
                ):
                    lines.append(f"    {base_clean} <|-- {name}")

        return "\n".join(lines)

    def save_to_readme_snippet(
        self,
        output_path: str = "data/graphs/mermaid_diagrams.md"
    ) -> str:
        """Save all Mermaid diagrams as a Markdown file."""
        dep_chart = self.dependency_flowchart()
        class_chart = self.class_hierarchy_chart()

        # Build string manually to avoid backtick conflicts inside f-strings
        fence = "```"
        content = "# Architecture Diagrams — Auto-Generated\n\n"
        content += "## Module Dependencies\n\n"
        content += f"{fence}mermaid\n{dep_chart}\n{fence}\n\n"
        content += "## Class Hierarchy\n\n"
        content += f"{fence}mermaid\n{class_chart}\n{fence}\n"

        with open(output_path, "w") as f:
            f.write(content)

        print(f"  ✓ Mermaid diagrams saved: {output_path}")
        return output_path
