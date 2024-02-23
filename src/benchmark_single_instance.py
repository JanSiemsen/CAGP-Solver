from pyvispoly import Point, PolygonWithHoles, plot_polygon
import solver2
from CAGPSolverMIP import CAGPSolverMIP
from CAGPSolverSAT import CAGPSolverSAT
from GreedyCAGP import get_greedy_solution
import networkx as nx
import matplotlib.pyplot as plt
import distinctipy as distcolors
import lzma

def convert_to_LinearRing(edges: list, pos: dict) -> list[Point]:
    ring = []
    cur_point = next(iter(pos))
    while len(pos):
        x, y = pos.pop(cur_point)
        ring.append(Point(x, y))
        cur_edge = [edge for edge in edges if edge[0] == cur_point or edge[1] == cur_point][0]
        cur_point = cur_edge[0] if cur_edge[1] == cur_point else cur_edge[1]
        edges.remove(cur_edge)
    return ring

G = nx.parse_graphml(lzma.open('/home/yanyan/PythonProjects/CAGP-Solver/db/sbgdb-20200507/polygons/random/fpg/fpg-poly_0000000100.graphml.xz').read())
pos = {}
for node in G.nodes(data=True):
    node_location = tuple(node[1].values())
    node_location = (float(node_location[0]), float(node_location[1]))
    pos[node[0]] = node_location

ring = convert_to_LinearRing(list(G.edges()), pos)
poly = PolygonWithHoles(ring)

print('Creating guard set...')
guards = solver2.generate_guard_set(poly)
print('Creating witness set...')
witnesses = solver2.generate_witness_set(poly)

print('Creating visibility and full graph...')
GC, G = solver2.generate_visibility_and_full_graph(guards, witnesses)

print('Calculating greedy solution...')
greedySolution = get_greedy_solution(guards, witnesses, GC)
print("size of greedy solution: ", len(greedySolution))

print('Generating edge clique covers...')
edge_clique_covers = solver2.generate_edge_clique_covers(GC, len(greedySolution))

'''
print('Creating MIP solver...')
solverMIP = CAGPSolverMIP(len(greedySolution), poly, guards, witnesses, G, edge_clique_covers)
print('Solving MIP...')
solution = solverMIP.solve()
print(solution)

print('Creating SAT solver...')
solverSAT = CAGPSolverSAT(len(greedySolution), poly, guards, witnesses, G, None)
print('Solving SAT...')
solution = solverSAT.solve()
print(solution)
solverSAT.__del__()
'''
