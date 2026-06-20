
import networkx as nx
from .models import GraphMetrics


class GraphAnalyzer:

    def __init__(self, graph: nx.DiGraph):
        self.G = graph

    def compute_metrics(self) -> GraphMetrics:
        metrics = GraphMetrics()

        if not self.G.nodes:
            return metrics

        metrics.total_nodes = self.G.number_of_nodes()
        metrics.total_edges = self.G.number_of_edges()
        metrics.density = round(nx.density(self.G), 6)

        in_degrees = [d for _, d in self.G.in_degree()]
        out_degrees = [d for _, d in self.G.out_degree()]

        metrics.avg_in_degree = round(
            sum(in_degrees) / len(in_degrees) if in_degrees else 0,
            2,
        )
        metrics.avg_out_degree = round(
            sum(out_degrees) / len(out_degrees) if out_degrees else 0,
            2,
        )

        sccs = list(nx.strongly_connected_components(self.G))
        circular = [list(scc) for scc in sccs if len(scc) > 1]

        metrics.is_dag = len(circular) == 0
        metrics.num_circular_dep_clusters = len(circular)
        metrics.circular_dep_groups = circular

        metrics.num_isolated_nodes = len(list(nx.isolates(self.G)))

        metrics.most_imported = sorted(
            [(n, self.G.in_degree(n)) for n in self.G.nodes],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        metrics.most_complex_hubs = sorted(
            [
                (
                    n,
                    self.G.nodes[n].get("pagerank", 0),
                    self.G.nodes[n].get("total_complexity", 0),
                )
                for n in self.G.nodes
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return metrics

    def find_god_modules(self, min_functions: int = 15) -> list[dict]:
        gods = []

        for node, data in self.G.nodes(data=True):
            total_fns = (
                data.get("num_functions", 0)
                + data.get("num_methods", 0)
            )

            if total_fns >= min_functions:
                gods.append(
                    {
                        "module": node,
                        "total_functions": total_fns,
                        "imported_by": self.G.in_degree(node),
                        "complexity": data.get("total_complexity", 0),
                        "pagerank": data.get("pagerank", 0),
                    }
                )

        return sorted(
            gods,
            key=lambda x: x["total_functions"],
            reverse=True,
        )

    def find_bridge_modules(
        self,
        min_betweenness: float = 0.05,
    ) -> list[dict]:
        bridges = []

        for node, data in self.G.nodes(data=True):
            betweenness = data.get("betweenness", 0)

            if betweenness >= min_betweenness:
                bridges.append(
                    {
                        "module": node,
                        "betweenness": betweenness,
                        "in_degree": self.G.in_degree(node),
                        "out_degree": self.G.out_degree(node),
                    }
                )

        return sorted(
            bridges,
            key=lambda x: x["betweenness"],
            reverse=True,
        )

    def get_dependency_chain(self, module: str) -> dict:
        if module not in self.G:
            return {
                "error": f"Module '{module}' not in graph"
            }

        ancestors = nx.ancestors(self.G, module)
        descendants = nx.descendants(self.G, module)

        return {
            "module": module,
            "depended_on_by": sorted(ancestors),
            "depends_on": sorted(descendants),
            "direct_importers": list(
                self.G.predecessors(module)
            ),
            "direct_dependencies": list(
                self.G.successors(module)
            ),
        }
