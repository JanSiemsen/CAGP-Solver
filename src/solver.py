from itertools import combinations
from pyvispoly import PolygonWithHoles, VisibilityPolygonCalculator, plot_polygon
from guard import Guard
from witness import Witness
import networkx as nx
import matplotlib.pyplot as plt

# This version uses the networkx library to create graphs

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

def generate_visibility_graph(guards: list[Guard]) -> nx.Graph:
    G = nx.Graph()

    for point1 in guards:
        for point2 in guards:
            if point1 == point2:
                continue
            # If the visibility of point1 is fully contained in the visibility of point2, add an edge between them
            if not point1.visibility.difference(point2.visibility):
                G.add_edge(point1.id, point2.id)
                continue
            # If the visibility of point1 minus the visibility of point1 is smaller than the visibility of point 1, add an edge between them
            if point1.visibility.difference(point2.visibility)[0].outer_boundary().area() < point1.visibility.outer_boundary().area():
                G.add_edge(point1.id, point2.id)

    # nx.draw_networkx(G, with_labels = True, pos=nx.kamada_kawai_layout(G))
    # plt.show()
    
    return G

def generate_covering_graph(guards: list[Guard], witnesses: list[Witness]) -> nx.Graph:
    G = nx.Graph()

    for witness in witnesses:
        for point in guards:
            if point.visibility.contains(witness.position):
                G.add_edge(point.id, witness.id)
    
    # nx.draw_networkx(G, with_labels = True, pos=nx.kamada_kawai_layout(G))
    # plt.show()
    
    return G

def generate_edge_clique_covers(G: nx.Graph, K: int) -> list[list[list[str]]]:
    edge_clique_covers = []

    # Construct a matching composed of K edges with the lowest sum of degrees of their vertices
    sorted_edges = iter(sorted(G.edges, key=lambda x: G.degree(x[0]) + G.degree(x[1])))
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
        edge_clique_cover = [clique]
        while len(uncovered_graph.edges) > 0:
            sorted_edges = iter(sorted(uncovered_graph.edges, key=lambda x: G.degree(x[0]) + G.degree(x[1])))
            clique = build_clique(next(sorted_edges), uncovered_graph)
            uncovered_graph.remove_edges_from(list(combinations(clique, 2)))
            edge_clique_cover.append(clique)
        edge_clique_covers.append(edge_clique_cover)

    return edge_clique_covers

def build_clique(e: (str, str), G: nx.Graph) -> list[list[str]]:
    clique = [e[0], e[1]]
    candidates = set(G[e[0]]) & set(G[e[1]])
    while len(candidates) > 0:
        v = candidates.pop()
        if all(v in G[u] for u in clique):
            candidates &= set(G[v])
            clique.append(v)
    return clique

# def add_wittnesses_to_visibility_graph(G: nx.Graph, guards: list[Guard], witnesses: list[Witness]) -> nx.Graph:
#     for witness in witnesses:
#         for point in guards:
#             if point.visibility.contains(witness.position):
#                 G.add_edge(point.id, witness.id)