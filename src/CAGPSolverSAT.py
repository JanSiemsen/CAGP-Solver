from pysat.solvers import Solver
import rustworkx as rx
from guard import Guard
from witness import Witness
from pyvispoly import PolygonWithHoles

class CAGPSolverSAT:
    
    def __init__(self, K: int, poly: PolygonWithHoles, guards: list[Guard], witnesses: list[Witness], G: rx.PyGraph, edge_clique_covers: list[list[list[str]]], solution: list[list[Guard]]=None) -> list[str]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guards = guards
        self.witnesses = witnesses
        self.edge_clique_covers = edge_clique_covers
        self.solver = Solver(name='Gluecard4')
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
        self.color_vars = {i: self.solver.var() for i in range(self.K)}
        self.guard_vars = {(guard, i): self.solver.var() for guard in self.guards for i in range(self.K)}

    def __add_witness_covering_constraints(self):
        for witness in self.G.node_indices():
            if self.G[witness][0] == 'w':
                subset = []
                for guard in self.G.neighbors(witness):
                    for k in range(self.K):
                        subset.append((guard, k))
                self.solver.add_clause([self.guard_vars[guard] for guard in subset])

    def __add_edge_clique_cover_constraints(self):
        for edge_clique in self.edge_clique_covers:
            self.solver.add_clause([self.guard_vars[guard] for guard in edge_clique])

    def __add_guard_coloring_constraints(self):
        for guard in self.guards:
            for k in range(self.K):
                self.solver.add_clause([-self.guard_vars[(guard, k)], self.color_vars[k]])

    def __add_color_symmetry_constraints(self):
        for k in range(self.K - 1):
            self.solver.add_clause([-self.color_vars[k], self.color_vars[k + 1]])

    def __add_guard_symmetry_constraints(self):
        for guard in self.guards:
            for k in range(self.K - 1):
                self.solver.add_clause([-self.guard_vars[(guard, k)], self.guard_vars[(guard, k + 1)]])

    def solve(self):
        self.solver.solve()
        return [guard for guard in self.guards if any(self.solver.get_values([self.guard_vars[(guard, k)] for k in range(self.K)]))]