import time
from pyvispoly import Point, PolygonWithHoles, plot_polygon
import solver_utils as solver_utils
from CAGPSolverMIP import CAGPSolverMIP
from CAGPSolverSAT import CAGPSolverSAT
from CAGPSolverCPSAT_MIP_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_MIP
from CAGPSolverCPSAT_SAT_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_SAT
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

# to parse simple polygons from Salzburg Benchmark
# G = nx.parse_graphml(lzma.open('/home/yanyan/PythonProjects/CAGP-Solver/db/sbgdb-20200507/polygons/random/fpg/fpg-poly_0000002500.graphml.xz').read())
# pos = {}
# for node in G.nodes(data=True):
#     node_location = tuple(node[1].values())
#     node_location = (float(node_location[0]), float(node_location[1]))
#     pos[node[0]] = node_location
# ring = convert_to_LinearRing(list(G.edges()), pos)
# poly = PolygonWithHoles(ring)

# to parse simple polygons from AGP2009 Benchmark
with open('/home/yanyan/PythonProjects/CAGP-Solver/agp2009a-simplerand/randsimple-2500-1.pol') as f:
    vertices = f.readline().split()
    vertices = vertices[1:]
    linear_ring = []
    for i in range(0, len(vertices), 2):
        x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
        y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
        linear_ring.append(Point(x, y))
    poly = PolygonWithHoles(linear_ring)

# to parse simple polygons from AGP2009 Benchmark with holes
# with open('/home/yanyan/PythonProjects/CAGP-Solver/simple-polygons-with-holes/g1_simple-simple_250:1000v-100h_2.pol') as f:
#     vertices = f.readline().split()
#     linear_rings = []
#     num_points = int(vertices.pop(0))
#     linear_ring = []
#     for _ in range(num_points):
#         x_str = vertices.pop(0).split('/')
#         x = int(x_str[0])/int(x_str[1])
#         y_str = vertices.pop(0).split('/')
#         y = int(y_str[0])/int(y_str[1])
#         linear_ring.append(Point(x, y))
#     linear_rings.append(linear_ring)  # Add outer boundary to linear_rings
#     num_holes = int(vertices.pop(0))  # Get the number of holes
#     for _ in range(num_holes):  # Repeat the process for each hole
#         num_points = int(vertices.pop(0))
#         linear_ring = []
#         for _ in range(num_points):
#             x_str = vertices.pop(0).split('/')
#             x = int(x_str[0])/int(x_str[1])
#             y_str = vertices.pop(0).split('/')
#             y = int(y_str[0])/int(y_str[1])
#             linear_ring.append(Point(x, y))
#         linear_rings.append(linear_ring)  # Add hole to linear_rings
#     poly = PolygonWithHoles(linear_rings[0], linear_rings[1:])

# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")
# plt.show()

print('Generating solver input:')
guards, guard_to_witnesses, initial_witnesses, all_witnesses, GC, G = solver_utils.generate_solver_input(poly, guards_on_holes=True)

print('Calculating greedy solution...')
greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)
print("number of colors in greedy solution: ", greedyColors)
print("number of guards in greedy solution: ", len(greedySolution))

print('Generating edge clique covers...')
start = time.time()
edge_clique_covers = solver_utils.generate_edge_clique_covers(GC, greedyColors)
end = time.time()
# print(edge_clique_covers)
print('Time to generate edge clique covers:', end - start, 'seconds')

# print('Creating MIP solver...')
# solverMIP = CAGPSolverMIP(greedyColors, poly, guard_to_witnesses, initial_witnesses, all_witnesses, G, edge_clique_covers, solution=greedySolution)
# print('Solving MIP...')
# solution = solverMIP.solve()
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))
# print('Average vertex degree:', (2 * len(GC.edge_indices())) / len(GC.node_indices()))

print('Creating CPSAT solver...')
solverCPSAT = CAGPSolverCPSAT_MIP(greedyColors, poly, guard_to_witnesses, initial_witnesses, all_witnesses, G, edge_clique_covers, solution=greedySolution)
print('Solving CPSAT...')
start = time.time()
solution = solverCPSAT.solve()
end = time.time()
print('Time to solve:', end - start, 'seconds')
# print([(guard, color) for guard, color in solution])
print(solver_utils.verify_solver_solution(solution, GC))

# print('Creating CPSAT solver...')
# solverCPSAT = CAGPSolverCPSAT_SAT(greedyColors, poly, guard_to_witnesses, initial_witnesses, all_witnesses, G, GC, None, solution=greedySolution)
# print('Solving CPSAT...')
# start = time.time()
# solution = solverCPSAT.solve()
# end = time.time()
# print('Time to solve:', end - start, 'seconds')
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))

# print('Creating SAT solver...')
# solverSAT = CAGPSolverSAT(greedyColors, poly, guard_to_witnesses, initial_witnesses, all_witnesses, G, GC, None, False, solution=greedySolution)
# print('Solving SAT...')
# start = time.time()
# solution = solverSAT.solve()
# end = time.time()
# print('Time to solve:', end - start, 'seconds')
# solverSAT.__del__()
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))

# print('Creating SAT solver...')
# solverSAT = CAGPSolverSAT(greedyColors, poly, guard_to_witnesses, initial_witnesses, all_witnesses, G, GC, None, True, solution=greedySolution)
# print('Solving SAT...')
# start = time.time()
# solution = solverSAT.solve()
# end = time.time()
# print('Time to solve:', end - start, 'seconds')
# solverSAT.__del__()
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))

# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")

# print('Plotting...')
# colors = distcolors.get_colors(len(guards))
# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")
# for s in solution:
#     for id, (point, visibility) in guards.items():
#         if s[0] == id:
#             plot_polygon(visibility, ax=ax, color=colors[s[1]], alpha=0.1)
#             plt.scatter(point.x(), point.y(), color='black', s=10)
# plt.show()