from ortools.sat.python import cp_model
import rustworkx as rx
from pyvispoly import PolygonWithHoles
from sympy import assuming

class CAGPSolverCPSAT:

    def __init__(self, K: int, poly: PolygonWithHoles, guard_to_witnesses: dict[int, set[int]], initial_witnesses: list[int], all_witnesses: set[int], G: rx.PyGraph, GC: rx.PyGraph, edge_clique_covers: list[list[list[int]]], solution: list[list[int]]=None) -> list[tuple[int, int]]:
        self.G = G
        self.GC = GC
        self.K = K
        self.poly = poly
        self.guard_to_witnesses = guard_to_witnesses
        self.witnesses = initial_witnesses
        self.all_witnesses = all_witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = cp_model.CpModel()

        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_conflicting_guards_constraints()
        self.__color_activation_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_objective()
        # self.__add_edge_clique_cover_constraints()
        # if solution:
        #     self.__provide_init_solution(solution)

    def __make_vars(self):
        self.color_vars = {k: self.model.NewBoolVar(f'k{k}') for k in range(self.K)}
        self.guard_vars = {(guard, k): self.model.NewBoolVar(f'{guard}k{k}') for guard in self.guard_to_witnesses.keys() for k in range(self.K)}

    def __add_witness_covering_constraints(self):
        for witness in self.witnesses:
            subset = []
            for guard in self.G.neighbors(witness):
                for k in range(self.K):
                    subset.append((guard, k))
            self.model.AddBoolOr([self.guard_vars[guard] for guard in subset])

    def __add_conflicting_guards_constraints(self):
        for e in self.GC.edge_index_map().values():
            for k in range(self.K):
                self.model.AddBoolOr([self.guard_vars[(e[0], k)].Not(), self.guard_vars[(e[1], k)].Not()])

    def __color_activation_constraints(self):
        for (guard, k), guard_var in self.guard_vars.items():
            self.model.AddBoolOr([self.color_vars[k], guard_var.Not()])

    def __add_guard_coloring_constraints(self):
        for guard in self.guard_to_witnesses.keys():
            self.model.AddAtMostOne([self.guard_vars[(guard, i)] for i in range(self.K)])

    # These constraints are being replaced by the conflicting guards constraints
    def __add_edge_clique_cover_constraints(self):
        color = 0
        for cover in self.edge_clique_covers:
            for clique in cover:
                self.model.Add(self.color_vars[color] >= sum(self.guard_vars[(guard, color)] for guard in clique))
            color += 1

    def __add_objective(self):
        self.model.Minimize(sum(self.color_vars.values()))
    
    def __check_coverage(self, solution: list[tuple[int, int]]):
        solution = [guard[0] for guard in solution]
        solution = list(set(solution))

        covered_witnesses = set()
        for guard in solution:
            covered_witnesses = covered_witnesses.union(self.guard_to_witnesses[guard])

        missing_witnesses = self.all_witnesses.difference(covered_witnesses)
        
        return missing_witnesses

    def solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
        status = solver.Solve(self.model, assumptions=None)
        if status != cp_model.OPTIMAL:
            print('No solution found')
            return None
        
        missing_witnesses = self.__check_coverage([(guard, color) for guard, color in self.guard_vars.keys() if solver.Value(self.guard_vars[(guard, color)]) == 1])

        while(missing_witnesses):
            print('Adding new witnesses...')
            for witness in missing_witnesses:
                subset = []
                for guard, witness_set in self.guard_to_witnesses.items():
                    if witness in witness_set:
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