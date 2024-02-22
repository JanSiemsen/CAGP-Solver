from itertools import combinations
from pyvispoly import PolygonWithHoles, VisibilityPolygonCalculator
from guard import Guard
from witness import Witness
import rustworkx as rx
from itertools import combinations

# This version uses the rustworkx library to create graphs

def generate_guard_set(polygon: PolygonWithHoles) -> list[Guard]:
    vis_calculator = VisibilityPolygonCalculator(polygon)
    guards = []
    index = 0
    for point in polygon.outer_boundary().boundary():
        guards.append(Guard(f'g{index}', point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point))))
        index += 1
    return guards

def generate_witness_set(polygon: PolygonWithHoles)-> list[Witness]:
    witnesses = []
    index = 0
    for point in polygon.outer_boundary().boundary():
        witnesses.append(Witness(f'w{index}', point))
        index += 1
    return witnesses

def generate_visibility_graph(guards: list[Guard]) -> rx.PyGraph:
    G = rx.PyGraph()

    for guard in guards:
        G.add_node(guard.id)

    for guard1, guard2 in combinations(G.node_indices(), 2):
        g1 = next((x for x in guards if x.id == G[guard1]), None)
        g2 = next((x for x in guards if x.id == G[guard2]), None)

        # if the intersection between two guards in not empty, add an edge between them
        if g1.visibility.intersection(g2.visibility):
            G.add_edge(guard1, guard2, None)
    
    return G

def generate_covering_graph(guards: list[Guard], witnesses: list[Witness]) -> rx.PyGraph:
    G = rx.PyGraph()

    for guard in guards:
        G.add_node(guard.id)

    for witness in witnesses:
        G.add_node(witness.id)

    for witness in G.node_indices():
        if G[witness][0] == 'w':
            for guard in G.node_indices():
                if G[guard][0] == 'g':
                    w = next((x for x in witnesses if x.id == G[witness]), None)
                    g = next((x for x in guards if x.id == G[guard]), None)
                    if g.visibility.contains(w.position):
                        G.add_edge(guard, witness, None)
    
    return G

def generate_visibility_and_full_graph(guards: list[Guard], witnesses: list[Witness]) -> rx.PyGraph:
    GC = rx.PyGraph()

    for guard in guards:
        GC.add_node(guard.id)

    for guard1, guard2 in combinations(GC.node_indices(), 2):
        g1 = next((x for x in guards if x.id == GC[guard1]), None)
        g2 = next((x for x in guards if x.id == GC[guard2]), None)

        # if the intersection between two guards in not empty, add an edge between them
        if g1.visibility.intersection(g2.visibility):
            GC.add_edge(guard1, guard2, None)

    G = GC.copy()

    for witness in witnesses:
        G.add_node(witness.id)

    for witness in G.node_indices():
        if G[witness][0] == 'w':
            for guard in G.node_indices():
                if G[guard][0] == 'g':
                    w = next((x for x in witnesses if x.id == G[witness]), None)
                    g = next((x for x in guards if x.id == G[guard]), None)
                    if g.visibility.contains(w.position):
                        G.add_edge(guard, witness, None)
    
    return GC, G

def generate_edge_clique_covers(G: rx.PyGraph, K: int) -> list[list[list[str]]]:
    edge_clique_covers = []

    # Construct a matching composed of K edges with the lowest sum of degrees of their vertices
    sorted_edges = iter(sorted(G.edge_index_map().values(), key=lambda x: G.degree(x[0]) + G.degree(x[1])))
    matching = []
    covered_vertices = set()
    for i in range(K):
        edge = next(sorted_edges)
        while(edge[0] in covered_vertices or edge[1] in covered_vertices):
            edge = next(sorted_edges)
        matching.append(edge)
        covered_vertices.add(edge[0])
        covered_vertices.add(edge[1])
    
    # Construct a clique cover for each edge in the matching
    for i in range(K):
        clique = build_clique(matching[i], G)
        uncovered_graph = G.copy()
        uncovered_graph.remove_edges_from(list(combinations(clique, 2)))
        edge_clique_cover = [[G[v] for v in clique]]
        while len(uncovered_graph.edge_indices()) > 0:
            sorted_edges = iter(sorted(uncovered_graph.edge_index_map().values(), key=lambda x: G.degree(x[0]) + G.degree(x[1])))
            clique = build_clique(next(sorted_edges), uncovered_graph)
            uncovered_graph.remove_edges_from(list(combinations(clique, 2)))
            edge_clique_cover.append([G[v] for v in clique])
        edge_clique_covers.append(edge_clique_cover)
    return edge_clique_covers

def build_clique(e: tuple[str, str], G: rx.PyGraph) -> list[list[str]]:
    clique = [e[0], e[1]]
    candidates = set(G.neighbors(e[0])) & set(G.neighbors(e[1]))
    while len(candidates) > 0:
        v = candidates.pop()
        if all(v in G.neighbors(u) for u in clique):
            candidates &= set(G.neighbors(v))
            clique.append(v)
    return clique