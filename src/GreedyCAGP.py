import rustworkx as rx
from ISSolverMIP import ISSolverMIP

def get_greedy_solution(guard_to_witnesses: dict[int, set[int]], initial_witnesses: list[int], G: rx.PyGraph) -> tuple[int, set[(int, int)]]:
    solution = set()
    uncovered = set(initial_witnesses)
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
