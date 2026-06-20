
import json
import networkx as nx
from pathlib import Path
from .models import GraphMetrics, NodeData, EdgeData


class DependencyGraphBuilder:

    def __init__(self, cache, manifest: dict):
        self.cache = cache
        self.manifest = manifest
        self.repo_root = manifest["repository"]["root"]
        self.repo_name = manifest["repository"]["name"]
        self.graph = nx.DiGraph(name=self.repo_name)

    def build(self) -> nx.DiGraph:
        print("  [1/4] Adding module nodes...")
        self._add_module_nodes()

        print("  [2/4] Adding import edges...")
        self._add_import_edges()

        print("  [3/4] Adding inheritance edges...")
        self._add_inheritance_edges()

        print("  [4/4] Computing graph metrics...")
        self._attach_metrics()

        return self.graph

    def _add_module_nodes(self) -> None:
        all_files = self.cache.conn.execute(
            "SELECT * FROM files WHERE has_parse_error = 0"
        ).fetchall()

        all_classes = self.cache.get_all_classes()
        all_functions = self.cache.get_all_functions()

        class_counts = {}
        for cls in all_classes:
            class_counts[cls['file_path']] = class_counts.get(cls['file_path'], 0) + 1

        func_counts = {}
        method_counts = {}
        complexity_totals = {}
        for fn in all_functions:
            fp = fn['file_path']
            if fn['is_method']:
                method_counts[fp] = method_counts.get(fp, 0) + 1
            else:
                func_counts[fp] = func_counts.get(fp, 0) + 1
            complexity_totals[fp] = complexity_totals.get(fp, 0) + fn['complexity']
            for file_row in all_files:
    fp = file_row['file_path']
    node_id = file_row['module_name'] or fp

    for file_row in all_files:
    fp = file_row['file_path']
    node_id = file_row['module_name'] or fp

    # Skip test fixture stubs that shadow real library names
    if 'test_apps' in node_id or 'test_apps' in fp:
        continue

    self.graph.add_node(

    if 'test_apps' in node_id or 'test_apps' in fp:
        continue

        

            self.graph.add_node(
                node_id,
                file_path=fp,
                module_name=node_id,
                lines_of_code=file_row['lines_of_code'] or 0,
                num_classes=class_counts.get(fp, 0),
                num_functions=func_counts.get(fp, 0),
                num_methods=method_counts.get(fp, 0),
                total_complexity=complexity_totals.get(fp, 0),
                in_degree=0,
                out_degree=0,
                pagerank=0.0,
                betweenness=0.0,
            )

    def _add_import_edges(self) -> None:
        all_imports = self.cache.get_all_imports()
        node_set = set(self.graph.nodes)

        short_to_full = {}
        for node in node_set:
            short_name = node.split(".")[-1]
            short_to_full[short_name] = node

        edges_added = 0
        edges_skipped = 0

        for imp in all_imports:
            source_file = self.cache.conn.execute(
                "SELECT module_name FROM files WHERE file_path = ?",
                (imp['file_path'],)
            ).fetchone()

            if not source_file:
                continue

            source_node = source_file['module_name']
            if source_node not in node_set:
                continue

            target_node = self._resolve_import(
                imp['module'], node_set, short_to_full
            )

            if target_node and target_node != source_node:
                if self.graph.has_edge(source_node, target_node):
                    self.graph[source_node][target_node]['weight'] += 1
                else:
                    names = json.loads(imp['names']) if imp['names'] else []
                    self.graph.add_edge(
                        source_node,
                        target_node,
                        edge_type="import",
                        weight=1,
                        imported_names=names,
                        is_relative=bool(imp['is_relative']),
                    )
                    edges_added += 1
            else:
                edges_skipped += 1

        print(
            f"    Import edges added: {edges_added} | "
            f"External/unresolved: {edges_skipped}"
        )

    def _resolve_import(
    self,
    module_name: str,
    node_set: set,
    short_to_full: dict
) -> str | None:
    clean = module_name.lstrip(".")

    if clean in node_set:
        return clean

    for node in node_set:
        if "test_apps" in node or "fixtures" in node:
            continue
        if clean.startswith(node) or node.startswith(clean):
            return node

    last_part = clean.split(".")[-1]
    if last_part in short_to_full:
        candidate = short_to_full[last_part]
        if "test_apps" not in candidate and "fixtures" not in candidate:
            return candidate

    return None

    def _add_inheritance_edges(self) -> None:
        all_classes = self.cache.get_all_classes()
        node_set = set(self.graph.nodes)

        class_to_module = {}
        for cls in all_classes:
            source_file = self.cache.conn.execute(
                "SELECT module_name FROM files WHERE file_path = ?",
                (cls['file_path'],)
            ).fetchone()
            if source_file:
                class_to_module[cls['name']] = source_file['module_name']

        edges_added = 0
        for cls in all_classes:
            base_classes = json.loads(cls['base_classes'])
            if not base_classes:
                continue

            source_file = self.cache.conn.execute(
                "SELECT module_name FROM files WHERE file_path = ?",
                (cls['file_path'],)
            ).fetchone()
            if not source_file:
                continue

            source_node = source_file['module_name']

            for base in base_classes:
                base_clean = base.split(".")[-1]
                if base_clean in class_to_module:
                    target_node = class_to_module[base_clean]

                    if (
                        target_node in node_set
                        and target_node != source_node
                        and not self.graph.has_edge(source_node, target_node)
                    ):
                        self.graph.add_edge(
                            source_node,
                            target_node,
                            edge_type="inheritance",
                            weight=2,
                            child_class=cls['name'],
                            parent_class=base,
                        )
                        edges_added += 1

        print(f"    Inheritance edges added: {edges_added}")

    def _attach_metrics(self) -> None:
        if len(self.graph.nodes) == 0:
            return

        pagerank = nx.pagerank(self.graph, alpha=0.85)
        betweenness = nx.betweenness_centrality(self.graph)

        for node in self.graph.nodes:
            self.graph.nodes[node]['in_degree'] = self.graph.in_degree(node)
            self.graph.nodes[node]['out_degree'] = self.graph.out_degree(node)
            self.graph.nodes[node]['pagerank'] = round(
                pagerank.get(node, 0), 6
            )
            self.graph.nodes[node]['betweenness'] = round(
                betweenness.get(node, 0), 6
            )
