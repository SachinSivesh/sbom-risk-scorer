from app.resolvers.graph_builder import GraphBuilder
from app.parsers.base import ParsedDependency, ParsedEdge


def test_build_simple_graph():
    builder = GraphBuilder()

    deps = [
        ParsedDependency(name="A", version="1.0", bom_ref="A", is_direct=True),
        ParsedDependency(name="B", version="1.0", bom_ref="B"),
        ParsedDependency(name="C", version="1.0", bom_ref="C"),
    ]

    edges = [
        ParsedEdge(from_ref="A", to_ref="B"),
        ParsedEdge(from_ref="B", to_ref="C"),
    ]

    graph = builder.build(deps, edges, root_ref="root")

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.has_cycles is False
    assert len(graph.warnings) == 0


def test_cycle_detection():
    builder = GraphBuilder()

    deps = [
        ParsedDependency(name="A", version="1.0", bom_ref="A"),
        ParsedDependency(name="B", version="1.0", bom_ref="B"),
    ]

    edges = [
        ParsedEdge(from_ref="A", to_ref="B"),
        ParsedEdge(from_ref="B", to_ref="A"),
    ]

    graph = builder.build(deps, edges)

    assert graph.has_cycles is True
    assert "CYCLE_DETECTED" in graph.warnings[0]


def test_get_transitive_dependencies():
    builder = GraphBuilder()

    deps = [
        ParsedDependency(name="A", version="1.0", bom_ref="A"),
        ParsedDependency(name="B", version="1.0", bom_ref="B"),
        ParsedDependency(name="C", version="1.0", bom_ref="C"),
    ]

    edges = [
        ParsedEdge(from_ref="A", to_ref="B"),
        ParsedEdge(from_ref="B", to_ref="C"),
    ]

    transit = builder.get_transitive_dependencies(deps, edges, root_ref="root", target_ref="A")
    assert "B" in transit
    assert "C" in transit
    assert len(transit) == 2
