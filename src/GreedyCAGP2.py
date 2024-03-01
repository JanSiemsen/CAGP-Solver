from pyvispoly import Point, PolygonWithHoles
import rustworkx as rx
from ISSolverMIP2 import ISSolverMIP

def get_greedy_solution(guards: dict[int, tuple[Point, PolygonWithHoles]], witnesses: dict[int, Point], G: rx.PyGraph) -> list[list[int]]:
    solution = []
    uncovered = list(witnesses.items())
    while (uncovered):
        weights = []
        for g_id, (g_point, g_polygon) in guards.items():
            weight = 0
            for w_id, w_point in uncovered:
                if g_polygon.contains(w_point):
                    weight += 1
            weights.append((g_id, weight))
        solver = ISSolverMIP(weights, G)
        independent_set = solver.solve()
        solution.append(independent_set)
        for guard in independent_set:
            for w_id, w_point in uncovered:
                if guards[guard][1].contains(w_point):
                    uncovered.remove((w_id, w_point))   
    return solution
