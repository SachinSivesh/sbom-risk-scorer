"""Dependency graph construction using networkx."""

from dataclasses import dataclass, field
from typing import Optional
import networkx as nx
from app.parsers.base import ParsedDependency, ParsedEdge
from app.utils.logging import get_logger

logger = get_logger(__name__)

MAX_TRAVERSAL_DEPTH = 50


@dataclass
class GraphNode:
    """A node in the dependency graph for visualization."""
    id: str
    label: str
    ecosystem: str
    is_direct: bool
    risk_level: str = "NONE"


@dataclass
class GraphEdge:
    """An edge in the dependency graph."""
    from_id: str
    to_id: str


@dataclass
class DependencyGraph:
    """Complete dependency graph structure."""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    has_cycles: bool = False
    cycle_details: list[list[str]] = field(default_factory=list)


class GraphBuilder:
    """Builds a dependency graph from parsed SBOM data using networkx."""

    def build(
        self,
        dependencies: list[ParsedDependency],
        edges: list[ParsedEdge],
        root_ref: Optional[str] = None,
    ) -> DependencyGraph:
        """
        Build a dependency graph from parsed dependencies and edges.

        Args:
            dependencies: Normalized dependencies from SBOM parser.
            edges: Dependency relationship edges from SBOM parser.
            root_ref: The bom-ref of the root component (if known).

        Returns:
            DependencyGraph with nodes, edges, cycle info, and warnings.
        """
        result = DependencyGraph()

        if not dependencies:
            return result

        # Create networkx directed graph
        G = nx.DiGraph()

        # Build bom_ref → dependency map
        ref_map: dict[str, ParsedDependency] = {}
        for dep in dependencies:
            if dep.bom_ref:
                ref_map[dep.bom_ref] = dep
                G.add_node(dep.bom_ref)

        # Add edges in bulk for O(n+e) performance
        valid_edges = []
        for edge in edges:
            if edge.from_ref in ref_map and edge.to_ref in ref_map:
                valid_edges.append((edge.from_ref, edge.to_ref))
            elif edge.from_ref == root_ref and edge.to_ref in ref_map:
                # Edge from root to a dependency (root may not be in ref_map)
                valid_edges.append((edge.from_ref, edge.to_ref))
            else:
                result.warnings.append(f"DANGLING_EDGE: {edge.from_ref} → {edge.to_ref}")

        G.add_edges_from(valid_edges)

        # Detect cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                result.has_cycles = True
                result.cycle_details = [list(c) for c in cycles[:10]]  # Cap at 10
                result.warnings.append(f"CYCLE_DETECTED: {len(cycles)} cycle(s) found")
                logger.warning("Cycles detected in dependency graph", cycle_count=len(cycles))
        except Exception as e:
            logger.error("Error during cycle detection", error=str(e))

        # Build output nodes
        for dep in dependencies:
            node = GraphNode(
                id=dep.bom_ref or f"{dep.name}@{dep.version}",
                label=f"{dep.name}@{dep.version}",
                ecosystem=dep.ecosystem,
                is_direct=dep.is_direct,
            )
            result.nodes.append(node)

        # Build output edges (only valid ones)
        for from_ref, to_ref in valid_edges:
            # Skip edges from root since root isn't a node in the output
            if from_ref == root_ref and root_ref not in ref_map:
                continue
            result.edges.append(GraphEdge(from_id=from_ref, to_id=to_ref))

        return result

    def get_transitive_dependencies(
        self,
        dependencies: list[ParsedDependency],
        edges: list[ParsedEdge],
        root_ref: Optional[str],
        target_ref: str,
    ) -> list[str]:
        """
        Get all transitive dependencies of a specific node.
        Uses depth-limited BFS to prevent infinite loops.

        Returns:
            List of bom-refs that are transitive dependencies.
        """
        G = nx.DiGraph()

        ref_map = {dep.bom_ref: dep for dep in dependencies if dep.bom_ref}

        for edge in edges:
            if edge.from_ref in ref_map and edge.to_ref in ref_map:
                G.add_edge(edge.from_ref, edge.to_ref)

        # BFS with depth limit
        visited = set()
        queue = [(target_ref, 0)]
        result = []

        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > MAX_TRAVERSAL_DEPTH:
                continue
            visited.add(node)

            if node != target_ref:
                result.append(node)

            for successor in G.successors(node):
                if successor not in visited:
                    queue.append((successor, depth + 1))

        return result
