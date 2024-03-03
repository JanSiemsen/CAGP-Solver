from pyvispoly import Point, PolygonWithHoles, plot_polygon
import solver
from CAGPSolverMIP_integral import CAGPSolverMIP
from CAGPSolverSAT import CAGPSolverSAT
from GreedyCAGP2 import get_greedy_solution
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

# G = nx.parse_graphml(lzma.open('/home/yanyan/PythonProjects/CAGP-Solver/db/sbgdb-20200507/polygons/random/fpg/fpg-poly_0000002500.graphml.xz').read())
# pos = {}
# for node in G.nodes(data=True):
#     node_location = tuple(node[1].values())
#     node_location = (float(node_location[0]), float(node_location[1]))
#     pos[node[0]] = node_location
# ring = convert_to_LinearRing(list(G.edges()), pos)
# poly = PolygonWithHoles(ring)

with open('/home/yanyan/PythonProjects/CAGP-Solver/agp2009a-simplerand/randsimple-2500-1.pol') as f:
    vertices = f.readline().split()
    vertices = vertices[1:]
    linear_ring = []
    for i in range(0, len(vertices), 2):
        x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
        y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
        linear_ring.append(Point(x, y))
    poly = PolygonWithHoles(linear_ring)

# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")
# plt.show()

# print('Creating guard set...')
# guards = solver.generate_guard_set(poly)
# print('Creating witness set...')
# witnesses = solver.generate_witness_set(poly)

# print('Creating guard set...')
# guards = solver.generate_guard_set2(poly)

# print('Creating AVP arrangement...')
# avp = solver.generate_AVP_recursive2(list(guards.items()))

# print('Creating witness set...')
# initial_witnesses, remaining_witnesses = solver.generate_witness_set2(avp, len(guards))

# print('Creating visibility and full graph...')
# GC, G = solver.generate_visibility_and_full_graph(guards, witnesses)

# print('Creating visibility and full graph...')
# GC, G = solver.generate_visibility_and_full_graph2(guards, initial_witnesses)

print('Generating solver input:')
guards, initial_witnesses, remaining_witnesses, all_witnesses, GC, G = solver.generate_solver_input(poly)

print('Calculating greedy solution...')
greedyColors, greedySolution = get_greedy_solution(guards, all_witnesses, GC)
print("number of colors in greedy solution: ", greedyColors)
print("number of guards in greedy solution: ", len(greedySolution))

print('Generating edge clique covers...')
edge_clique_covers = solver.generate_edge_clique_covers(GC, greedyColors)

print('Creating MIP solver...')
solverMIP = CAGPSolverMIP(greedyColors, poly, guards, initial_witnesses, remaining_witnesses, G, edge_clique_covers, solution=greedySolution)
print('Solving MIP...')
solution = solverMIP.solve()
print([(guard, color) for guard, color in solution])
print(solver.verify_solver_solution(solution, GC))
print('Density of the graph:', (2 * len(GC.edge_indices())) / (len(GC.node_indices()) * (len(GC.node_indices()) - 1)))

# print('Creating SAT solver...')
# solverSAT = CAGPSolverSAT(len(greedySolution), poly, guards, witnesses, G)
# print('Solving SAT...')
# solution = solverSAT.solve()
# solverSAT.__del__()
# print([(G[guard], color) for guard, color in solution])
# print(solve.verify_solver_solution(solution, GC))
