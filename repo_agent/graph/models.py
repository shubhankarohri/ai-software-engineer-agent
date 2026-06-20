
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeData:
    module_name: str
    file_path: str
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float = 0.0
    betweenness: float = 0.0
    lines_of_code: int = 0
    num_classes: int = 0
    num_functions: int = 0
    total_complexity: int = 0


@dataclass
class EdgeData:
    source: str
    target: str
    edge_type: str
    weight: int = 1


@dataclass
class GraphMetrics:
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
    is_dag: bool = True
    num_circular_dep_clusters: int = 0
    num_isolated_nodes: int = 0
    avg_in_degree: float = 0.0
    avg_out_degree: float = 0.0
    most_imported: list[tuple] = field(default_factory=list)
    most_complex_hubs: list[tuple] = field(default_factory=list)
    circular_dep_groups: list[list[str]] = field(default_factory=list)
