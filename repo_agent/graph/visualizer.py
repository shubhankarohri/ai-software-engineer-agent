
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path


class GraphVisualizer:

    def __init__(self, graph: nx.DiGraph):
        self.G = graph

    def render_interactive(
        self,
        output_path: str = "data/graphs/dependency_graph.html",
        max_nodes: int = 80,
    ) -> str:
        from pyvis.network import Network

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        net = Network(
    height="750px",
    width="100%",
    directed=True,
    bgcolor="#1a1a2e",
    font_color="#e0e0e0",
    cdn_resources="in_line"

        )
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "centralGravity": 0.01,
              "springLength": 120,
              "springConstant": 0.08
            },
            "solver": "forceAtlas2Based",
            "stabilization": { "iterations": 150 }
          },
          "edges": {
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } },
            "smooth": { "type": "curvedCW", "roundness": 0.2 }
          },
          "interaction": { "hover": true, "tooltipDelay": 100 }
        }
        """)

        top_nodes = sorted(
            self.G.nodes(data=True),
            key=lambda x: x[1].get("pagerank", 0),
            reverse=True,
        )[:max_nodes]

        top_node_ids = {n for n, _ in top_nodes}

        max_complexity = max(
            (d.get("total_complexity", 0) for _, d in top_nodes),
            default=1,
        ) or 1

        for node_id, data in top_nodes:
            complexity = data.get("total_complexity", 0)
            pagerank = data.get("pagerank", 0)

            ratio = min(complexity / max_complexity, 1.0)

            r = int(255 * ratio)
            g = int(255 * (1 - ratio))

            color = f"#{r:02x}{g:02x}40"
            size = 10 + pagerank * 3000

            short_name = node_id.split(".")[-1]

            tooltip = (
                f"Module: {node_id}\n"
                f"In-degree: {data.get('in_degree', 0)}\n"
                f"Out-degree: {data.get('out_degree', 0)}\n"
                f"LOC: {data.get('lines_of_code', 0)}\n"
                f"Classes: {data.get('num_classes', 0)}\n"
                f"Functions: {data.get('num_functions', 0)}\n"
                f"Complexity: {complexity}\n"
                f"PageRank: {pagerank:.4f}"
            )

            net.add_node(
                node_id,
                label=short_name,
                title=tooltip,
                size=size,
                color=color,
                borderWidth=2,
            )

        for src, dst, edge_data in self.G.edges(data=True):
            if src in top_node_ids and dst in top_node_ids:
                color = (
                    "#4a9eff"
                    if edge_data.get("edge_type") == "import"
                    else "#ff6b6b"
                )

                net.add_edge(
                    src,
                    dst,
                    width=edge_data.get("weight", 1),
                    color=color,
                    title=edge_data.get("edge_type", "import"),
                )

        net.save_graph(output_path)

        print(f"  ✓ Interactive graph saved: {output_path}")
        return output_path

    def render_static(
        self,
        output_path: str = "data/graphs/dependency_graph.png",
        max_nodes: int = 40,
    ) -> str:

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        top_nodes = sorted(
            self.G.nodes(),
            key=lambda n: self.G.in_degree(n),
            reverse=True,
        )[:max_nodes]

        subgraph = self.G.subgraph(top_nodes)

        fig, ax = plt.subplots(1, 1, figsize=(18, 12))

        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")

        pos = nx.spring_layout(subgraph, k=2.5, seed=42)

        sizes = [
            300 + subgraph.in_degree(n) * 200
            for n in subgraph.nodes()
        ]

        complexities = [
            subgraph.nodes[n].get("total_complexity", 0)
            for n in subgraph.nodes()
        ]

        max_c = max(complexities) or 1

        nx.draw_networkx_nodes(
            subgraph,
            pos,
            node_size=sizes,
            node_color=complexities,
            cmap=plt.cm.RdYlGn_r,
            vmin=0,
            vmax=max_c,
            alpha=0.9,
            ax=ax,
        )

        nx.draw_networkx_edges(
            subgraph,
            pos,
            edge_color="#4a9eff",
            arrows=True,
            arrowsize=15,
            alpha=0.5,
            ax=ax,
        )

        labels = {
            n: n.split(".")[-1]
            for n in subgraph.nodes()
        }

        nx.draw_networkx_labels(
            subgraph,
            pos,
            labels=labels,
            font_size=7,
            font_color="white",
            ax=ax,
        )

        ax.set_title(
            f"Dependency Graph — {self.G.graph.get('name', 'Repository')} "
            f"(top {max_nodes} nodes by in-degree)",
            color="white",
            fontsize=14,
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

        print(f"  ✓ Static graph saved: {output_path}")
        return output_path
