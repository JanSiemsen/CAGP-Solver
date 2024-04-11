import time
from pyvispoly import Point, PolygonWithHoles, plot_polygon
import solver_utils as solver_utils
from GreedyCAGP import get_greedy_solution
from CAGPSolverMIP import CAGPSolverMIP
from CAGPSolverSAT import CAGPSolverSAT
from CAGPSolverCPSAT_MIP_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_MIP
from CAGPSolverCPSAT_Mix_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_Mix
from CAGPSolverCPSAT_SAT_Formulation import CAGPSolverCPSAT as CAGPSolverCPSAT_SAT
from CFCAGPSolverMIP import CFCAGPSolverMIP
from CFCAGPSolverSAT import CFCAGPSolverSAT
import networkx as nx
import matplotlib.pyplot as plt
import distinctipy as distcolors
import lzma
from tqdm import tqdm

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
# G = nx.parse_graphml(lzma.open('/home/yanyan/PythonProjects/CAGP-Solver/db/sbgdb-20200507/polygons/random/fpg/fpg-poly_0000030000.graphml.xz').read())
# pos = {}
# for node in G.nodes(data=True):
#     node_location = tuple(node[1].values())
#     node_location = (float(node_location[0]), float(node_location[1]))
#     pos[node[0]] = node_location
# ring = convert_to_LinearRing(list(G.edges()), pos)
# poly = PolygonWithHoles(ring)

# to parse simple polygons from AGP2009 Benchmark
# with open('/home/yanyan/PythonProjects/CAGP-Solver/cagp_solver/mini_benchmark/agp2009a-simplerand/randsimple-500-3.pol') as f:
#     vertices = f.readline().split()
#     vertices = vertices[1:]
#     linear_ring = []
#     for i in range(0, len(vertices), 2):
#         x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
#         y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
#         linear_ring.append(Point(x, y))
#     poly = PolygonWithHoles(linear_ring)

# to parse simple polygons from AGP2009 Benchmark with holes
with open('/home/yanyan/PythonProjects/CAGP-Solver/simple-polygons-with-holes/g1_simple-simple_75:300v-30h_14.pol') as f:
    vertices = f.readline().split()
    linear_rings = []
    num_points = int(vertices.pop(0))
    linear_ring = []
    for _ in range(num_points):
        x_str = vertices.pop(0).split('/')
        x = int(x_str[0])/int(x_str[1])
        y_str = vertices.pop(0).split('/')
        y = int(y_str[0])/int(y_str[1])
        linear_ring.append(Point(x, y))
    linear_rings.append(linear_ring)  # Add outer boundary to linear_rings
    num_holes = int(vertices.pop(0))  # Get the number of holes
    for _ in range(num_holes):  # Repeat the process for each hole
        num_points = int(vertices.pop(0))
        linear_ring = []
        for _ in range(num_points):
            x_str = vertices.pop(0).split('/')
            x = int(x_str[0])/int(x_str[1])
            y_str = vertices.pop(0).split('/')
            y = int(y_str[0])/int(y_str[1])
            linear_ring.append(Point(x, y))
        linear_rings.append(linear_ring)  # Add hole to linear_rings
    poly = PolygonWithHoles(linear_rings[0], linear_rings[1:])

# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")
# plt.show()

print('Generating solver input:')
guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf, all_witnesses_cf = solver_utils.generate_solver_input(poly, guards_on_holes=True)

print('Calculating greedy solution...')
greedyColors, greedySolution = get_greedy_solution(guard_to_witnesses, all_witnesses, GC)
print("number of colors in greedy solution: ", greedyColors)
print("number of guards in greedy solution: ", len(greedySolution))

# print('Creating MIP solver...')
# CFsolverMIP = CFCAGPSolverMIP(greedyColors, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf, all_witnesses_cf, solution=greedySolution)
# print('Solving MIP...')
# solution = CFsolverMIP.solve()

# print(len(all_witnesses))
# print(len(all_witnesses_cf))
# print('Creating SAT solver...')
# CFsolverSAT = CFCAGPSolverSAT(greedyColors, guard_to_witnesses_cf, witness_to_guards_cf, all_witnesses_cf, all_witnesses_cf, solution=greedySolution)
# print('Solving SAT...')
# start = time.time()
# solution = CFsolverSAT.solve()
# end = time.time()
# CFsolverSAT.__del__()
# print('Time to solve:', end - start)

# print('Generating edge clique covers...')
# start = time.time()
# edge_clique_covers = solver_utils.generate_edge_clique_covers(GC, greedyColors)
# end = time.time()
# # print(edge_clique_covers)
# print('Time to generate edge clique covers:', end - start, 'seconds')

# print('Creating MIP solver...')
# solverMIP = CAGPSolverMIP(greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, edge_clique_covers, solution=greedySolution)
# print('Solving MIP...')
# solution = solverMIP.solve()
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))
# print('Average vertex degree:', (2 * len(GC.edge_indices())) / len(GC.node_indices()))

# print('Creating CPSAT solver...')
# solverCPSAT_MIP = CAGPSolverCPSAT_MIP(greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, edge_clique_covers, solution=greedySolution)
# print('Solving CPSAT...')
# start = time.time()
# num_colors, solution, iterations, number_of_witnesses, status = solverCPSAT_MIP.solve()
# end = time.time()
# print('Number of colors:', num_colors)
# print('Number of guards:', len(solution))
# print('Number of iterations:', iterations)
# print('Number of witnesses:', number_of_witnesses)
# print('Time to solve:', end - start, 'seconds')
# print('Status:', status)
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))

# print('Creating CPSAT solver...')
# solverCPSAT_Mix = CAGPSolverCPSAT_Mix(greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, solution=greedySolution)
# print('Solving CPSAT...')
# start = time.time()
# num_colors, solution, iterations, number_of_witnesses, status = solverCPSAT_Mix.solve()
# end = time.time()
# print('Number of colors:', num_colors)
# print('Number of guards:', len(solution))
# print('Number of iterations:', iterations)
# print('Number of witnesses:', number_of_witnesses)
# print('Time to solve:', end - start, 'seconds')
# print('Status:', status)
# # print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))
# unique_first_values = set([s[1] for s in solution])
# print("Unique first values:", unique_first_values)

print('Creating CPSAT solver...')
solverCPSAT_SAT = CAGPSolverCPSAT_SAT(greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, guard_color_constraints=True)
print('Solving CPSAT...')
start = time.time()
num_colors, solution, iterations, number_of_witnesses, status = solverCPSAT_SAT.solve()
end = time.time()
print('Number of colors:', num_colors)
print('Number of guards:', len(solution))
print('Number of iterations:', iterations)
print('Number of witnesses:', number_of_witnesses)
print('Time to solve:', end - start, 'seconds')
print('Status:', status)
# print([(guard, color) for guard, color in solution])
print(solver_utils.verify_solver_solution(solution, GC))

# print('Creating SAT solver...')
# solverSAT = CAGPSolverSAT(greedyColors, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, solver_name="Cadical103", guard_color_constraints=False, solution=greedySolution)
# print('Solving SAT...')
# start = time.time()
# num_colors, solution, iterations, number_of_witnesses, status = solverSAT.solve()
# end = time.time()
# print('Number of colors:', num_colors)
# print('Number of guards:', len(solution))
# print('Number of iterations:', iterations)
# print('Number of witnesses:', number_of_witnesses)
# print('Time to solve:', end - start, 'seconds')
# print('Status:', status)
# solverSAT.__del__()
# print([(guard, color) for guard, color in solution])
# print(solver_utils.verify_solver_solution(solution, GC))

# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey")

print('Plotting...')
colors = distcolors.get_colors(greedyColors)
fig, ax = plt.subplots()
plot_polygon(poly, ax=ax, color="lightgrey", zorder=0)
progress = tqdm(solution)
for s in solution:
    (point, visibility) = guards[s[0]]
    plot_polygon(visibility, ax=ax, color=colors[s[1]], alpha=0.2, zorder=0, linewidth=0.01)
    plt.scatter(point.x(), point.y(), color=colors[s[1]], s=10, zorder=1, edgecolors='none')
    progress.update()
progress.close()

plt.show()

# plt.savefig("polygon_solution_plot.png", dpi=1200)