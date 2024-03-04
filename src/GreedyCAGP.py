from pyvispoly import Point, PolygonWithHoles
import rustworkx as rx
from ISSolverMIP import ISSolverMIP

class HashablePoint:
    def __init__(self, point):
        self.point = point

    def __hash__(self):
        return hash((float(self.point.x()), float(self.point.y())))

    def __eq__(self, other):
        return float(self.point.x()) == float(other.point.x()) and float(self.point.y()) == float(other.point.y())

def get_greedy_solution(guards: dict[int, tuple[Point, PolygonWithHoles]], witnesses: list[Point], G: rx.PyGraph) -> tuple[int, set[(int, int)]]:
    solution = set()
    uncovered = set(HashablePoint(witness) for witness in witnesses)
    guard_to_witnesses = {g_id: {HashablePoint(w_point) for w_point in witnesses if g_vis.contains(w_point)} for g_id, (g_point, g_vis) in guards.items()}
    size = 0
    while uncovered:
        weights = [(g_id, len(witnesses & uncovered)) for g_id, witnesses in guard_to_witnesses.items()]
        solver = ISSolverMIP(weights, G)
        independent_set = solver.solve()
        for guard in independent_set:
            solution.add((guard, size))
            uncovered -= guard_to_witnesses[guard]
        size += 1
    return size, solution
