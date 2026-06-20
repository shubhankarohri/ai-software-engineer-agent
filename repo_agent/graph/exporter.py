
import json
import networkx as nx
from pathlib import Path


class GraphExporter:

    def __init__(self, graph: nx.DiGraph):
        self.G = graph

    def _sanitize_graph_for_graphml(self) -> nx.DiGraph:
        G_copy = self.G.copy()

        for _, data in G_copy.nodes(data=True):
            for key, val in list(data.items()):
                if isinstance(val, (list, dict)):
                    data[key] = json.dumps(val)

        for _, _, data in G_copy.edges(data=True):
            for key, val in list(data.items()):
                if isinstance(val, (list, dict)):
                    data[key] = json.dumps(val)

        return G_copy

    def to_graphml(self, path: str = "data/graphs/graph.graphml") -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        clean_graph = self._sanitize_graph_for_graphml()

        nx.write_graphml(clean_graph, path)

        print(f"  ✓ GraphML exported: {path}")
        return path

    def to_json(self, path: str = "data/graphs/graph.json") -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        data = nx.node_link_data(self.G)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"  ✓ JSON exported: {path}")
        return path

    def to_adjacency_report(
        self,
        path: str = "data/graphs/adjacency.txt"
    ) -> str:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(
                f"Dependency Graph: {self.G.graph.get('name', '')}\n"
            )
            f.write(
                f"Nodes: {self.G.number_of_nodes()} | "
                f"Edges: {self.G.number_of_edges()}\n\n"
            )

            for node in sorted(self.G.nodes()):
                deps = list(self.G.successors(node))
                importers = list(self.G.predecessors(node))

                f.write(f"{node}\n")

                if deps:
                    f.write(
                        f"  → imports:    {', '.join(deps)}\n"
                    )

                if importers:
                    f.write(
                        f"  ← imported by: {', '.join(importers)}\n"
                    )

                f.write("\n")

        print(f"  ✓ Adjacency report: {path}")
        return path
