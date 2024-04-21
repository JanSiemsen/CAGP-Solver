from itertools import combinations
from CAGP_Solver import Point, PolygonWithHoles, generate_solver_input, plot_polygon
import glob
import os
from sympy import li
from tqdm import tqdm
import rustworkx as rx
import matplotlib.pyplot as plt

def generate_visibility_graph(guards) -> rx.PyGraph:
    G = rx.PyGraph()

    for guard in guards.keys():
        G.add_node(guard)

    for guard1, guard2 in combinations(G.node_indices(), 2):
        g1 = guards[G[guard1]]
        g2 = guards[G[guard2]]

        # if the intersection between two guards in not empty, add an edge between them
        if g1[1].do_intersect(g2[1]):
            G.add_edge(guard1, guard2, None)
    
    return G

with open('/home/yanyan/PythonProjects/CAGP-Solver/agp2009a-simplerand/randsimple-200-1.pol') as f:
    vertices = f.readline().split()
    vertices = vertices[1:]
    linear_ring = []
    seen_points = set()
    for i in range(0, len(vertices), 2):
        x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
        y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
        if (x, y) in seen_points:
            raise ValueError(f"Duplicate point: ({x}, {y})")
        seen_points.add((x, y))
        linear_ring.append(Point(x, y))
    poly = PolygonWithHoles(linear_ring)
    assert len(linear_ring) == 200

guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf, all_witnesses_cf, shadow_avps, light_avps, all_avps, light_guard_sets, all_guard_sets = generate_solver_input(poly, guards_on_holes=True)

GC0 = rx.PyGraph(multigraph=False)
GC1 = rx.PyGraph(multigraph=False)

for guard in guards.keys():
    GC0.add_node(guard)
    GC1.add_node(guard)

for guardset in light_guard_sets:
    print(guardset)
    for guard1, guard2 in combinations(guardset, 2):
        GC0.add_edge(guard1, guard2, None)


for guardset in all_guard_sets:
    for guard1, guard2 in combinations(guardset, 2):
        GC1.add_edge(guard1, guard2, None)

GC2 = generate_visibility_graph(guards)

# for witness_set in guard_to_witnesses.values():
#     print(witness_set)

# print('Plotting...')
# fig, ax = plt.subplots()
# plot_polygon(poly, ax=ax, color="lightgrey", zorder=0)
# for avp in shadow_avps:
#     plot_polygon(avp, ax=ax, color="red", alpha=0.2, zorder=0, linewidth=0.01)
# for avp in light_avps:
#     plot_polygon(avp, ax=ax, color="blue", alpha=0.2, zorder=0, linewidth=0.01)
# for avp in all_avps:
#     plot_polygon(avp, ax=ax, color="green", alpha=0.2, zorder=0, linewidth=0.01)

# plt.show()

# Calculate the graph density for GC
E_GC = len(GC.edge_indices())
V_GC = len(GC.node_indices())
density_GC = 2*E_GC/(V_GC*(V_GC-1)) if V_GC > 1 else 0

# Calculate the graph density for GC0
E_GC0 = len(GC0.edge_indices())
V_GC0 = len(GC0.node_indices())
density_GC0 = 2*E_GC0/(V_GC0*(V_GC0-1)) if V_GC0 > 1 else 0

# Calculate the graph density for GC1
E_GC1 = len(GC1.edge_indices())
V_GC1 = len(GC1.node_indices())
density_GC1 = 2*E_GC1/(V_GC1*(V_GC1-1)) if V_GC1 > 1 else 0

# Calculate the graph density for GC2
E_GC2 = len(GC2.edge_indices())
V_GC2 = len(GC2.node_indices())
density_GC2 = 2*E_GC2/(V_GC2*(V_GC2-1)) if V_GC2 > 1 else 0

print(f"Graph density for GC: {density_GC}")
print(f"Graph density for GC0: {density_GC0}")
print(f"Graph density for GC1: {density_GC1}")
print(f"Graph density for GC2: {density_GC2}")


# root_path = os.path.dirname(os.getcwd())
# relative_path = 'cagp_solver/benchmark_instances/final_benchmark_instances/agp2009a-simplerand/*.pol'
# print(os.path.join(root_path, relative_path))

# Initialize the dictionary
# graph_density_GC = {}
# graph_density_GC2 = {}
# progress = tqdm(glob.glob(os.path.join(root_path, relative_path)))
# for filename in glob.glob(os.path.join(root_path, relative_path)):
#     progress.update()
#     instance_name = os.path.splitext(os.path.basename(filename))[0]
    
#     with open(filename, "r") as file:
#         vertices = file.readline().split()
#         number_of_vertices = int(vertices.pop(0))
#         linear_ring = []
#         for i in range(0, len(vertices), 2):
#             x = int(vertices[i].split('/')[0])/int(vertices[i].split('/')[1])
#             y = int(vertices[i+1].split('/')[0])/int(vertices[i+1].split('/')[1])
#             linear_ring.append(Point(x, y))
#         poly = PolygonWithHoles(linear_ring)

#     guards, guard_to_witnesses, witness_to_guards, initial_witnesses, all_witnesses, GC, guard_to_witnesses_cf, witness_to_guards_cf, initial_witnesses_cf, all_witnesses_cf = generate_solver_input(poly, guards_on_holes=True)
#     GC2 = generate_visibility_graph(guards)

#     # Calculate the graph density
#     E = len(GC.edge_indices())
#     V = len(GC.node_indices())
#     density_GC = 2*E/(V*(V-1)) if V > 1 else 0

#     # Calculate the graph density for GC2
#     E_GC2 = len(GC2.edge_indices())
#     V_GC2 = len(GC2.node_indices())
#     density_GC2 = 2*E_GC2/(V_GC2*(V_GC2-1)) if V_GC2 > 1 else 0

#     # Add the densities to the lists for the number of guards
#     graph_density_GC.setdefault(len(guards), []).append(density_GC)
#     graph_density_GC2.setdefault(len(guards), []).append(density_GC2)
# progress.close()

# # Calculate the average density for each number of guards
# average_graph_density_GC = {k: sum(v) / len(v) for k, v in graph_density_GC.items()}
# average_graph_density_GC2 = {k: sum(v) / len(v) for k, v in graph_density_GC2.items()}

# print("Average graph density for GC:")
# for k, v in average_graph_density_GC.items():
#     print(f"Number of vertices: {k}, Average graph density: {v}")

# print("Average graph density for GC2:")
# for k, v in average_graph_density_GC2.items():
#     print(f"Number of vertices: {k}, Average graph density: {v}")