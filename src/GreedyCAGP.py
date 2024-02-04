from guard import Guard
from witness import Witness
import rustworkx as rx
from ISSolverMIP2 import ISSolverMIP

def get_greedy_solution(guards: list[Guard], witnesses: list[Witness], G: rx.PyGraph) -> list[list[Guard]]:
    solution = []
    uncovered = witnesses
    while (uncovered):
        weights = []
        for guard in guards:
            weight = 0
            for witness in uncovered:
                if guard.visibility.contains(witness.position):
                    weight += 1
            weights.append((guard, weight))
        solver = ISSolverMIP(weights, G)
        independent_set = solver.solve()
        solution.append(independent_set)
        for guard in independent_set:
            for witness in uncovered:
                if guard.visibility.contains(witness.position):
                    uncovered.remove(witness)
    return solution
