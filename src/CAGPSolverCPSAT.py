from ortools.sat.python import cp_model
import rustworkx as rx
from guard import Guard
from witness import Witness
from pyvispoly import PolygonWithHoles

class CAGPSolverCPSAT:

    def __init__(self, K: int, poly: PolygonWithHoles, guards: list[Guard], witnesses: list[Witness], G: rx.PyGraph, edge_clique_covers: list[list[list[str]]], solution: list[list[Guard]]=None) -> list[str]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guards = guards
        self.witnesses = witnesses
        self.edge_clique_covers = edge_clique_covers
        self.model = cp_model.CpModel()
        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_edge_clique_cover_constraints()
        self.__add_guard_coloring_constraints()
        self.__add_color_symmetry_constraints()
        self.__add_guard_symmetry_constraints()
        self.__add_bottleneck_constraint()
        if solution:
            self.__provide_init_solution(solution)

    def __make_vars(self):
        self.color_vars = [self.model.NewBoolVar(f'k{i}') for i in range(self.K)]
        self.guard_vars = {(guard, i): self.model.NewBoolVar(f'{guard.id}k{i}') for guard in self.guards for i in range(self.K)}
        self.chromatic_number = self.model.NewIntVar(0, self.K, 'chromatic_number')

    def __add_witness_covering_constraints(self):
        for witness in self.G.node_indices():
            if self.G[witness][0] == 'w':
                subset = []
                for guard in self.G.neighbors(witness):
                    for k in range(self.K):
                        subset.append(self.guard_vars[(guard, k)])
                self.model.Add(sum(subset) >= 1)

    def __add_edge_clique_cover_constraints(self):
        for edge_clique in self.edge_clique_covers:
            self.model.Add(sum(self.guard_vars[(guard, i)] for guard in edge_clique for i in range(self.K)) >= 1)

    def __add_guard_coloring_constraints(self):
        for guard in self.guards:
            for k in range(self.K):
                self.model.Add(sum(self.guard_vars[(guard, i)] for i in range(self.K)) <= 1)

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.model.Add(self.color_vars[k] >= self.color_vars[k + 1])

    def __add_guard_symmetry_constraints(self):
        for guard in self.guards:
            for k in range(self.K - 1):
                self.model.Add(self.guard_vars[(guard, k)] >= self.guard_vars[(guard, k + 1)])

    def __add_bottleneck_constraint(self):
        self.model.Add(self.chromatic_number >= sum(self.color_vars))

    def __provide_init_solution(self, solution: list[list[Guard]]):
        for i, color in enumerate(solution):
            for guard in color:
                self.model.Add(self.guard_vars[(guard, i)] == 1)
            self.model.Add(self.color_vars[i] == 1)
    
    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        if status == cp_model.OPTIMAL:
            return [guard for guard in self.guards if any(solver.Value(self.guard_vars[(guard, k)]) for k in range(self.K))]
        else:
            return []