
import json
from collections import defaultdict
from pathlib import Path

import graphviz
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx


class DiagramGenerator:

    def __init__(self, graph: nx.DiGraph, cache, manifest: dict):
        self.G = graph
        self.cache = cache
        self.manifest = manifest
        self.repo_name = manifest["repository"]["name"]
        Path("data/graphs").mkdir(parents=True, exist_ok=True)

    def module_dependency_diagram(
        self,
        max_nodes: int = 30,
        output_path: str = "data/graphs/module_deps",
    ) -> str:

        dot = graphviz.Digraph(
            name=f"{self.repo_name} — Module Dependencies",
            format="png",
        )

        dot.attr(
            rankdir="LR",
            bgcolor="#1a1a2e",
            fontname="Helvetica",
            fontcolor="white",
            pad="0.5",
            nodesep="0.4",
            ranksep="1.2",
        )

        dot.attr(
            "node",
            shape="box",
            style="filled,rounded",
            fontname="Helvetica",
            fontsize="10",
            fontcolor="white",
            margin="0.2,0.1",
        )

        dot.attr(
            "edge",
            color="#4a9eff",
            arrowsize="0.7",
            penwidth="1.2",
        )

        top_nodes = sorted(
            self.G.nodes(data=True),
            key=lambda x: x[1].get("pagerank", 0),
            reverse=True,
        )[:max_nodes]

        top_ids = {n for n, _ in top_nodes}

        max_complexity = max(
            (d.get("total_complexity", 0) for _, d in top_nodes),
            default=1,
        ) or 1

        for node_id, data in top_nodes:
            complexity = data.get("total_complexity", 0)
            ratio = min(complexity / max_complexity, 1.0)

            if ratio < 0.33:
                color = "#2d6a4f"
            elif ratio < 0.66:
                color = "#b5862a"
            else:
                color = "#9b2335"

            short = node_id.split(".")[-1]
            in_deg = data.get("in_degree", 0)
            loc = data.get("lines_of_code", 0)

            dot.node(
                node_id,
                label=f"{short}\n{loc} LOC | {in_deg} importers",
                fillcolor=color,
            )

        for src, dst, data in self.G.edges(data=True):
            if src in top_ids and dst in top_ids:
                color = (
                    "#4a9eff"
                    if data.get("edge_type") == "import"
                    else "#ff6b6b"
                )
                dot.edge(src, dst, color=color)

        dot.render(output_path, cleanup=True)

        final_path = output_path + ".png"
        print(f"  ✓ Module dependency diagram: {final_path}")

        return final_path

    def class_hierarchy_diagram(
        self,
        output_path: str = "data/graphs/class_hierarchy.png",
    ) -> str:

        all_classes = self.cache.get_all_classes()

        if not all_classes:
            print("  No classes found — skipping hierarchy diagram")
            return ""

        H = nx.DiGraph()
        class_to_file = {}

        for cls in all_classes:
            name = cls["name"]
            bases = json.loads(cls["base_classes"])
            file_short = cls["file_path"].split("/")[-1].replace(".py", "")

            class_to_file[name] = file_short
            H.add_node(name, file=file_short)

            for base in bases:
                base = base.split(".")[-1]
                if base not in {
                    "object",
                    "ABC",
                    "Exception",
                    "BaseException",
                    "dict",
                    "list",
                }:
                    H.add_edge(name, base)

        H.remove_nodes_from(list(nx.isolates(H)))

        if H.number_of_nodes() == 0:
            print("  No inheritance relationships found")
            return ""

        fig, ax = plt.subplots(figsize=(16, 10))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        try:
            pos = nx.nx_agraph.graphviz_layout(H, prog="dot")
        except Exception:
            pos = nx.spring_layout(H, k=3, seed=42)

        files = list(set(class_to_file.values()))

        colors = plt.cm.Set3(
            [i / max(len(files), 1) for i in range(len(files))]
        )

        file_colors = {
            f: colors[i]
            for i, f in enumerate(files)
        }

        node_colors = [
            file_colors.get(H.nodes[n].get("file", ""), "#4a9eff")
            for n in H.nodes
        ]
        
        nx.draw_networkx_nodes(
            H,
            pos,
            node_color=node_colors,
            node_size=1500,
            alpha=0.9,
            ax=ax,
        )

        nx.draw_networkx_edges(
            H,
            pos,
            edge_color="#ff6b6b",
            arrows=True,
            arrowsize=20,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            ax=ax,
        )

        nx.draw_networkx_labels(
            H,
            pos,
            font_size=8,
            font_color="white",
            font_weight="bold",
            ax=ax,
        )

        legend = [
            mpatches.Patch(color=file_colors[f], label=f)
            for f in files[:8]
        ]

        ax.legend(
            handles=legend,
            loc="upper left",
            fontsize=7,
            facecolor="#2a2a4e",
            labelcolor="white",
        )

        ax.set_title(
            f"Class Hierarchy — {self.repo_name}",
            color="white",
            fontsize=14,
            pad=15,
        )

        ax.axis("off")

        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
            facecolor="#1a1a2e",
        )
        plt.close()

        print(f"  ✓ Class hierarchy diagram: {output_path}")

        return output_path

    def layer_architecture_diagram(
        self,
        output_path: str = "data/graphs/layer_architecture.png",
    ) -> str:

        layers = defaultdict(list)

        for node, data in self.G.nodes(data=True):
            layer = self._classify_layer(
                node.split(".")[-1].lower(),
                data,
            )
            layers[layer].append((node, data))

        layer_order = [
            "entry",
            "core",
            "data",
            "utilities",
            "tests",
            "other",
        ]

        labels = {
            "entry": "Entry Points",
            "core": "Core Logic",
            "data": "Data Layer",
            "utilities": "Utilities",
            "tests": "Tests",
            "other": "Other",
        }

        colors = {
            "entry": "#e63946",
            "core": "#457b9d",
            "data": "#2d6a4f",
            "utilities": "#b5862a",
            "tests": "#6a0572",
            "other": "#4a4a6a",
        }

        fig, ax = plt.subplots(figsize=(18, 10))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        active = [l for l in layer_order if layers[l]]
        width = 1 / len(active) if active else 1

        for i, layer in enumerate(active):
            nodes = layers[layer][:12]
            color = colors[layer]
            center = (i + 0.5) * width

            rect = mpatches.FancyBboxPatch(
                (i * width + 0.01, 0.05),
                width - 0.02,
                0.85,
                boxstyle="round,pad=0.01",
                linewidth=2,
                edgecolor=color,
                facecolor=color + "22",
                transform=ax.transAxes,
            )

            ax.add_patch(rect)

            ax.text(
                center,
                0.94,
                labels[layer],
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=color,
            )

            total = len(nodes)

            for j, (node, data) in enumerate(nodes):
                y = 0.82 - j * (0.72 / max(total, 1))

                ax.text(
                    center,
                    y,
                    f"{node.split('.')[-1]}\n({data.get('lines_of_code',0)} LOC)",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white",
                    bbox=dict(
                        boxstyle="round,pad=0.3",
                        facecolor=color + "88",
                        edgecolor=color,
                    ),
                )

        ax.set_title(
            f"Layer Architecture — {self.repo_name}",
            color="white",
            fontsize=16,
            pad=20,
        )

        ax.axis("off")

        plt.tight_layout()
        plt.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
            facecolor="#1a1a2e",
        )
        plt.close()

        print(f"  ✓ Layer architecture diagram: {output_path}")

        return output_path

    def _classify_layer(self, module_short: str, data: dict) -> str:

        entry = {
            "app",
            "main",
            "cli",
            "wsgi",
            "asgi",
            "run",
            "server",
            "manage",
        }

        data_layer = {
            "model",
            "models",
            "db",
            "database",
            "session",
            "sessions",
            "cache",
            "schema",
        }

        utils = {
            "util",
            "utils",
            "helper",
            "helpers",
            "common",
            "shared",
            "mixin",
            "base",
            "globals",
            "typing",
            "exceptions",
        }

        tests = {
            "test",
            "tests",
            "conftest",
            "fixture",
            "spec",
            "mock",
        }

        if any(x in module_short for x in tests):
            return "tests"

        if any(x in module_short for x in entry):
            return "entry"

        if any(x in module_short for x in data_layer):
            return "data"

        if any(x in module_short for x in utils):
            return "utilities"

        if (
            data.get("total_complexity", 0) > 30
            or data.get("in_degree", 0) > 5
        ):
            return "core"

        return "other"
