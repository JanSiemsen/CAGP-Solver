from pyvispoly import FieldNumber, Point, Polygon, PolygonWithHoles, VisibilityPolygonCalculator, plot_polygon
from guard import Guard
from witness import Witness
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

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

def generate_visibility_graph(guards: list[Guard], witnesses: list[Witness]) -> nx.Graph:
    G = nx.Graph()

    for point1 in guards:
        for point2 in guards:
            if point1 == point2:
                continue
            print(point1.id, point2.id)
            if not point1.visibility.difference(point2.visibility):
                G.add_edge(point1.id, point2.id)
                continue
            if point1.visibility.difference(point2.visibility)[0].outer_boundary().area() < point1.visibility.outer_boundary().area():
                G.add_edge(point1.id, point2.id)

    for witness in witnesses:
        for point in guards:
            if point.visibility.contains(witness.position):
                G.add_edge(point.id, witness.id)

    nx.draw_networkx(G, with_labels = True, pos=nx.kamada_kawai_layout(G))
    plt.show()
    return G