from itertools import combinations
from CAGP_Solver import Point, PolygonWithHoles, VisibilityPolygonCalculator, AVP_Arrangement, generate_solver_input, plot_polygon
import glob
import os
from pyrsistent import v
from tqdm import tqdm
import rustworkx as rx
import matplotlib.pyplot as plt
import distinctipy as distcolors

with open('/home/yanyan/PythonProjects/CAGP-Solver/agp2009a-simplerand/randsimple-20-1.pol') as f:
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
    assert len(linear_ring) == 20

vis_calculator = VisibilityPolygonCalculator(poly)
guards = {}
index = 0
avp_arr = None
visibility_list = []
for point in poly.outer_boundary().boundary():
    # if index > 10:
    #     break
    guards[index] = point
    if index == 0:
        visibility = PolygonWithHoles(vis_calculator.compute_visibility_polygon(point))
        visibility_list.append(visibility)
        avp_arr = AVP_Arrangement(visibility, {index})
    else:
        visibility = PolygonWithHoles(vis_calculator.compute_visibility_polygon(point))
        avp_arr2 = AVP_Arrangement(visibility, {index})
        visibility_list.append(visibility)
        avp_arr = avp_arr.overlay(avp_arr2)
    index += 1

witness_to_guards, guard_to_witnesses, light_guard_sets, witness_to_guards_cf, guard_to_witnesses_cf, all_guard_sets = avp_arr.get_shadow_witnesses_and_light_guard_sets(list(guards.keys()))
print(witness_to_guards)
print(guard_to_witnesses)
print(light_guard_sets)

fig, ax = plt.subplots()

shadow_avps, light_avps = avp_arr.get_shadow_and_light_avps()
avps = avp_arr.get_avps()
print(len(avps))
print(len(shadow_avps))
print(len(light_avps))  

index = 0
for polygon in avps:
    plot_polygon(polygon, ax=ax, color='none', edgecolor='black', alpha=0.5, zorder=0)
    index += 1

for polygon in shadow_avps:
    plot_polygon(polygon, ax=ax, color='red', edgecolor='black', alpha=0.5, zorder=1)

for polygon in light_avps:
    plot_polygon(polygon, ax=ax, color='blue', edgecolor='black', alpha=0.5, zorder=1)

for point in guards.values():
    plt.scatter(point.x(), point.y(), color='black', s=10, zorder=2, edgecolors='none')

plt.show()

# fig, ax = plt.subplots()
# colors = distcolors.get_colors(len(visibility_list))

# index = 0
# for polygon in visibility_list:
#     plot_polygon(polygon, ax=ax, color=colors[index], alpha=0.2, zorder=0)
#     index += 1

# plt.show()