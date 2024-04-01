from ortools.sat.python import cp_model
import rustworkx as rx
from pyvispoly import PolygonWithHoles

class CAGPSolverCPSAT:

    def __init__(self, K: int, guard_to_witnesses: dict[int, set[int]], witness_to_guards: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], edge_clique_covers: list[list[list[int]]], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.K = K
        self.guard_to_witnesses = guard_to_witnesses
        self.witness_to_guards = witness_to_guards
        self.witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = cp_model.CpModel()

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__add_objective()
        # if solution:
        #     self.__provide_init_solution(solution)

    def __make_vars(self):
        self.color_vars = {k: self.model.NewBoolVar(f'k{k}') for k in range(self.K)}
        self.guard_vars = {(guard, k): self.model.NewBoolVar(f'{guard}k{k}') for guard in self.guard_to_witnesses.keys() for k in range(self.K)}

    def __add_witness_covering_constraints(self):
        for witness in self.witnesses:
            subset = []
            for guard in self.witness_to_guards[witness]:
                for k in range(self.K):
                    subset.append(self.guard_vars[(guard, k)])
            self.model.Add(sum(subset) >= 1)

    def __add_edge_clique_cover_constraints(self):
        color = 0
        for cover in self.edge_clique_covers:
            for clique in cover:
                self.model.Add(self.color_vars[color] >= sum(self.guard_vars[(guard, color)] for guard in clique))
            color += 1

    def __add_guard_coloring_constraints(self):
        for guard in self.guard_to_witnesses.keys():
            self.model.Add(sum(self.guard_vars[(guard, i)] for i in range(self.K)) <= 1)

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.Add(self.color_vars[k] >= self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.Add(sum(self.guard_vars[(guard, k)] for guard in self.guard_to_witnesses.keys()) >= sum(self.guard_vars[(guard, k + 1)] for guard in self.guard_to_witnesses.keys()))

    def __add_objective(self):
        self.model.Minimize(sum(self.color_vars.values()))

    def __provide_init_solution(self, solution: list[tuple[int, int]]):
        for (guard, color) in solution:
            self.model.Add(self.guard_vars[(guard, color)] == 1)
            self.model.Add(self.color_vars[color] == 1)

    def __check_coverage(self, solution: list[tuple[int, int]]):
        solution = [guard for guard, color in solution]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses
    
    def solve(self):
        solver = cp_model.CpSolver()
        # solver.parameters.log_search_progress = True
        status = solver.Solve(self.model)
        if status != cp_model.OPTIMAL:
            print('No solution found')
            return None
        
        missing_witnesses = self.__check_coverage([(guard, color) for guard, color in self.guard_vars.keys() if solver.Value(self.guard_vars[(guard, color)]) == 1])

        while(missing_witnesses):
            print('Adding new witnesses...')
            for witness in missing_witnesses:
                subset = []
                for guard in self.witness_to_guards[witness]:
                    for k in range(self.K):
                        subset.append(self.guard_vars[(guard, k)])
                self.model.Add(sum(subset) >= 1)
            status = solver.Solve(self.model)
            if status != cp_model.OPTIMAL:
                print('No solution found')
                return None
            missing_witnesses = self.__check_coverage([(guard, color) for guard, color in self.guard_vars.keys() if solver.Value(self.guard_vars[(guard, color)]) == 1])

        print('Solution with chromatic number:', solver.ObjectiveValue())
        return [(guard, color) for guard, color in self.guard_vars.keys() if solver.Value(self.guard_vars[(guard, color)]) == 1]