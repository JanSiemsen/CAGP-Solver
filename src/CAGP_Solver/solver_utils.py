from functools import partial
from itertools import combinations
from ._cgal_bindings import Point, PolygonWithHoles, VisibilityPolygonCalculator, AVP_Arrangement
import rustworkx as rx
from heapq import heappop, heappush
from collections import defaultdict
from multiprocessing import Pool
from tqdm import tqdm

# This version uses the rustworkx library to create graphs
    
def generate_AVP_recursive(guards: list[tuple[int, tuple[Point, PolygonWithHoles]]], progress: tqdm) -> AVP_Arrangement:
    half = len(guards)//2
    leftHalf = guards[:half]
    rightHalf = guards[half:]
    if len(guards) == 1:
        progress.update(1)
        return AVP_Arrangement(guards[0][1][1], {guards[0][0]})
    else:
        return generate_AVP_recursive(leftHalf, progress=progress).overlay(generate_AVP_recursive(rightHalf, progress=progress))

def generate_solver_input(polygon: PolygonWithHoles):
    GC = rx.PyGraph(multigraph=False)

    print('Creating guard set...')
    vis_calculator = VisibilityPolygonCalculator(polygon)
    guards = {}
    progress = tqdm(polygon.outer_boundary().boundary())
    for point in polygon.outer_boundary().boundary():
        index = GC.add_node(None)
        guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
        progress.update()
    progress.close()
    progress = tqdm(total=len(polygon.holes()))
    for hole in polygon.holes():
        for point in hole.boundary():
            index = GC.add_node(None)
            guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
        progress.update()
    progress.close()

    print('Creating AVP arrangement...')
    progress = tqdm(total=len(guards))
    avp = generate_AVP_recursive(list(guards.items()), progress=progress)
    progress.refresh()
    progress.close()
    witness_to_guards, guard_to_witnesses, light_guard_sets, witness_to_guards_cf, guard_to_witnesses_cf, all_guard_sets = avp.get_shadow_witnesses_and_light_guard_sets(len(guards))

    print('Creating visibility graph...')
    progress = tqdm(total=len(light_guard_sets))
    for guard_set in light_guard_sets:
        for g1, g2 in combinations(guard_set, 2):
            GC.add_edge(g1, g2, None)
        progress.update()
    progress.close()

    print('Creating witness set...')
    all_witnesses = sorted(witness_to_guards.keys(), key=lambda x: len(witness_to_guards[x]))
    initial_witnesses = all_witnesses[:len(guards)]

    return guards, guard_to_witnesses, witness_to_guards, initial_witnesses, set(all_witnesses), GC

def generate_solver_input_cf(polygon: PolygonWithHoles, guards_on_holes: bool=True):
    GC = rx.PyGraph(multigraph=False)

    print('Creating guard set...')
    vis_calculator = VisibilityPolygonCalculator(polygon)
    guards = {}
    progress = tqdm(polygon.outer_boundary().boundary())
    for point in polygon.outer_boundary().boundary():
        index = GC.add_node(None)
        guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
        progress.update()
    progress.close()
    progress = tqdm(total=len(polygon.holes()))
    for hole in polygon.holes():
        for point in hole.boundary():
            index = GC.add_node(None)
            guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
        progress.update()
    progress.close()

    print('Creating AVP arrangement...')
    progress = tqdm(total=len(guards))
    avp = generate_AVP_recursive(list(guards.items()), progress=progress)
    progress.refresh()
    progress.close()
    witness_to_guards, guard_to_witnesses, light_guard_sets, witness_to_guards_cf, guard_to_witnesses_cf, all_guard_sets = avp.get_shadow_witnesses_and_light_guard_sets(len(guards))

    print('Creating visibility graph...')
    progress = tqdm(total=len(light_guard_sets))
    for guard_set in light_guard_sets:
        for g1, g2 in combinations(guard_set, 2):
            GC.add_edge(g1, g2, None)
        progress.update()
    progress.close()

    print('Creating initial witnesses and all witnesses for conflict-free...')
    all_witnesses_cf = sorted(witness_to_guards_cf.keys(), key=lambda x: len(witness_to_guards_cf[x]), reverse=True)
    initial_witnesses_cf_desc = all_witnesses_cf[:len(guards)]
    all_witnesses_cf = sorted(witness_to_guards_cf.keys(), key=lambda x: len(witness_to_guards_cf[x]), reverse=False)
    initial_witnesses_cf_asc = all_witnesses_cf[:len(guards)]

    return guards, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf_desc, initial_witnesses_cf_asc, set(all_witnesses_cf), guard_to_witnesses, set(list(witness_to_guards.keys())), GC

def generate_shadow_and_light_polygons(polygon: PolygonWithHoles, guards_on_holes: bool=True):
    GC = rx.PyGraph(multigraph=False)

    print('Creating guard set...')
    vis_calculator = VisibilityPolygonCalculator(polygon)
    guards = {}
    progress = tqdm(polygon.outer_boundary().boundary())
    for point in polygon.outer_boundary().boundary():
        index = GC.add_node(None)
        guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
        progress.update()
    progress.close()
    if guards_on_holes:
        progress = tqdm(total=len(polygon.holes()))
        for hole in polygon.holes():
            for point in hole.boundary():
                index = GC.add_node(None)
                guards[index] = (point, PolygonWithHoles(vis_calculator.compute_visibility_polygon(point)))
            progress.update()
        progress.close()

    print('Creating AVP arrangement...')
    progress = tqdm(total=len(guards))
    avp = generate_AVP_recursive(list(guards.items()), progress=progress)
    progress.refresh()
    progress.close()

    shadow_avps, light_avps = avp.get_shadow_and_light_avps()

    all_avps = avp.get_avps()

    return shadow_avps, light_avps, all_avps

def sort_edge(e: tuple[int, int]):
    return (min(e[0], e[1]), max(e[0], e[1]))

REMOVED = '<removed-task>'  # placeholder for a removed task

def generate_edge_clique_covers(G: rx.PyGraph, K: int) -> list[list[list[int]]]:
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
    with Pool() as p:
        func = partial(construct_clique_cover, G)
        edge_clique_covers = p.map(func, matching[:K])

    return edge_clique_covers

def construct_clique_cover(G: rx.PyGraph, edge: tuple[int, int]) -> list[list[int]]:
    uncovered_graph = G.copy()
    clique = build_clique(edge, G)
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

    return edge_clique_cover

def build_clique(e: tuple[int, int], G: rx.PyGraph) -> list[int]:
    clique = [e[0], e[1]]
    candidates = set(G.neighbors(e[0])) & set(G.neighbors(e[1]))
    while len(candidates) > 0:
        v = max(candidates, key=lambda v: sum(1 for u in G.neighbors(v) if u not in clique))
        candidates &= set(G.neighbors(v))
        clique.append(v)
    return clique

# This function verifies if all the set of guards with the same color have no edge between them
def verify_solver_solution(solution: list[(int, int)], G: rx.PyGraph) -> bool:

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

def verify_solver_solution_cf(solution: list[(int, int)], witness_to_guards: dict) -> bool:
    for witness, guards in witness_to_guards.items():
        guard_colors = [color for g, color in solution if g in guards]
        if any(guard_colors.count(color) == 1 for color in guard_colors):
            continue
        return False
    return True
