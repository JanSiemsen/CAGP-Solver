from itertools import combinations
from pyvispoly import PolygonWithHoles, VisibilityPolygonCalculator, AVP_Arrangement
from guard import Guard
from witness import Witness
import rustworkx as rx
from heapq import heappop, heappush
from collections import defaultdict

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

def generate_AVP_list(guards: list[Guard]) -> AVP_Arrangement:
    guards = guards.copy()
    avp = AVP_Arrangement(guards[0].visibility, {guards[0].id})
    guards.pop(0)
    for guard in guards:
        avp = avp.overlay(AVP_Arrangement(guard.visibility, {guard.id}))
    return avp

def generate_AVP_recursive(guards: list[Guard]) -> AVP_Arrangement:
    half = len(guards)//2
    leftHalf = guards[half:]
    rightHalf = guards[:half]
    if len(guards) == 1:
        return AVP_Arrangement(guards[0].visibility, {guards[0].id})
    else:
        return generate_AVP_recursive(leftHalf).overlay(generate_AVP_recursive(rightHalf))

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

'''
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
'''

def generate_visibility_and_full_graph(guards: list[Guard], witnesses: list[Witness]) -> rx.PyGraph:
    GC = rx.PyGraph()

    # Create dictionaries that map IDs to guards and witnesses
    guard_dict = {guard.id: guard for guard in guards}
    witness_dict = {witness.id: witness for witness in witnesses}

    for guard in guards:
        GC.add_node(guard.id)

    for guard1, guard2 in combinations(GC.node_indices(), 2):
        g1 = guard_dict[GC[guard1]]
        g2 = guard_dict[GC[guard2]]

        # if the intersection between two guards in not empty, add an edge between them
        if g1.visibility.do_intersect(g2.visibility):
            GC.add_edge(guard1, guard2, None)

    G = GC.copy()

    for witness in witnesses:
        G.add_node(witness.id)

    for witness in G.node_indices():
        if G[witness][0] == 'w':
            for guard in G.node_indices():
                if G[guard][0] == 'g':
                    w = witness_dict[G[witness]]
                    g = guard_dict[G[guard]]
                    if g.visibility.contains(w.position):
                        G.add_edge(guard, witness, None)
    
    return GC, G

'''
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

        # Build a priority queue of edges, with priority being the negative sum of degrees
        # We use negative values to get a max-heap, as Python's heapq module only provides a min-heap
        edge_queue = [(-uncovered_graph.degree(e[0]) - uncovered_graph.degree(e[1]), e) for e in uncovered_graph.edge_index_map().values()]
        heapify(edge_queue)

        while len(uncovered_graph.edge_indices()) > 0:

            # Get the edge with highest priority
            _, edge = heappop(edge_queue)

            # sorted_edges = iter(sorted(uncovered_graph.edge_index_map().values(), key=lambda x: G.degree(x[0]) + G.degree(x[1])))
            # clique = build_clique(next(sorted_edges), uncovered_graph)
            
            clique = build_clique(edge, uncovered_graph)
            uncovered_graph.remove_edges_from(list(combinations(clique, 2)))
            edge_clique_cover.append([G[v] for v in clique])

            # Update the priority queue
            edge_queue = [(-uncovered_graph.degree(x[0]) - uncovered_graph.degree(x[1]), x) for x in uncovered_graph.edge_index_map().values()]
            heapify(edge_queue)

        edge_clique_covers.append(edge_clique_cover)
    return edge_clique_covers
'''

def sort_edge(e: tuple[int, int]):
    return (min(e[0], e[1]), max(e[0], e[1]))

REMOVED = '<removed-task>'  # placeholder for a removed task

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
        edge_clique_cover = [clique]

        # Build a priority queue of edges, with priority being the negative sum of degrees
        edge_map = {sort_edge((e[0], e[1])): [-uncovered_graph.degree(e[0]) - uncovered_graph.degree(e[1]), sort_edge((e[0], e[1]))] for e in uncovered_graph.edge_index_map().values()}
        edge_queue = []
        for e in edge_map.values():
            heappush(edge_queue, e.copy())

        while len(uncovered_graph.edge_indices()) > 0:
            # Get the edge with highest priority
            while True:
                neg_degree, edge = heappop(edge_queue)
                if edge is not REMOVED:
                    current_neg_degree = -uncovered_graph.degree(edge[0]) - uncovered_graph.degree(edge[1])
                    if neg_degree == current_neg_degree:
                        break

            clique = build_clique(edge, uncovered_graph)
            edges_to_remove = list(combinations(clique, 2))
            uncovered_graph.remove_edges_from(edges_to_remove)
            edge_clique_cover.append(clique)

            # Mark the removed edges as "REMOVED" in the queue and keep track of the affected edges
            affected_edges = set()
            for e in edges_to_remove:
                e = (min(e[0], e[1]), max(e[0], e[1]))
                if e in edge_map:
                    edge_map[e][1] = REMOVED
                affected_edges.update([(n, e[0]) for n in G.neighbors(e[0])])
                affected_edges.update([(n, e[1]) for n in G.neighbors(e[1])])

            # Update the degrees in the queue for the affected edges
            for e in affected_edges:
                e = (min(e[0], e[1]), max(e[0], e[1]))
                if e in edge_map and edge_map[e][1] is not REMOVED:
                    edge_map[e][0] = -uncovered_graph.degree(e[0]) - uncovered_graph.degree(e[1])
                    heappush(edge_queue, edge_map[e].copy())
            
            # Reorder the queue
            # edge_queue = [e for e in edge_queue if e[1] is not REMOVED]
            # heapify(edge_queue)

        edge_clique_covers.append(edge_clique_cover)
    return edge_clique_covers
    
def build_clique(e: tuple[int, int], G: rx.PyGraph) -> list[list[str]]:
    clique = [e[0], e[1]]
    candidates = set(G.neighbors(e[0])) & set(G.neighbors(e[1]))
    while len(candidates) > 0:
        v = candidates.pop()
        if all(v in G.neighbors(u) for u in clique):
            candidates &= set(G.neighbors(v))
            clique.append(v)
    return clique

# This function verifies if all the set of guards with the same color have no edge between them
def verify_solver_solution(solution: list[(str, int)], G: rx.PyGraph) -> bool:

    # Group the guards by color
    color_groups = defaultdict(list)
    for vertex, color in solution:
        color_groups[color].append(vertex)

    # Check if the induced subgraph for each color group has no edges
    for color, vertices in color_groups.items():
        subgraph = G.subgraph(vertices)
        if len(subgraph.edge_indices()) > 0:
            return False

    return True