from pysat.solvers import Solver
import rustworkx as rx
from guard import Guard
from witness import Witness
from pyvispoly import PolygonWithHoles

class CAGPSolverSAT:
    
    def __init__(self, K: int, poly: PolygonWithHoles, guards: list[Guard], witnesses: list[Witness], G: rx.PyGraph, edge_clique_covers: list[list[list[str]]]) -> list[str]:
        self.G = G
        self.K = K
        self.poly = poly
        self.guards = guards
        self.witnesses = witnesses
        self.edge_clique_covers = edge_clique_covers
        self.solver = Solver(name='Gluecard4', with_proof=False)
        self.__make_vars()
        self.__add_witness_covering_constraints()
        self.__add_conflicting_guards_constraints()
        # self.__add_edge_clique_cover_constraints()

    def __make_vars(self):
        self.guard_to_var = {}
        self.var_to_guard = {}
        id = 1
        for guard in self.guards:
            for i in range(self.K):
                self.guard_to_var[(guard.id, i)] = id
                self.var_to_guard[id] = (guard.id, i)
                id += 1

    def __add_witness_covering_constraints(self):
        for witness in self.G.node_indices():
            if self.G[witness][0] == 'w':
                subset = []
                for guard in self.G.neighbors(witness):
                    for k in range(self.K):
                        subset.append((self.G[guard], k))
                self.solver.add_clause([self.guard_to_var[guard] for guard in subset])

    def __add_conflicting_guards_constraints(self):
        for e in self.G.edge_index_map().values():
            if self.G[e[0]][0] == 'g' and self.G[e[1]][0] == 'g':
                for k in range(self.K):
                    self.solver.add_clause([-self.guard_to_var[(self.G[e[0]], k)], -self.guard_to_var[(self.G[e[1]], k)]])

    # These constraints are being replaced by the conflicting guards constraints
    def __add_edge_clique_cover_constraints(self):
        for edge_clique in self.edge_clique_covers:
            self.solver.add_clause([self.guard_to_var[guard] for guard in edge_clique])

    def __deactivate_guards(self, color_lim: int):
        return [-self.guard_to_var[(guard.id, k)] for guard in self.guards for k in range(color_lim, self.K)]
    
    def __deactivated_guards(self, color_lim: int):
        return [(guard.id, k) for guard in self.guards for k in range(color_lim, self.K)]
    
    def __check_coverage(self, solution: list[int]):
        solution = [guard[0] for guard in solution]
        solution = list(set(solution))

        missing_area = [self.poly]
        for guard in solution:
            # get the coverage of the guard
            coverage = next((x.visibility for x in self.guards if x.id == guard), None)
            # remove the coverage from each polygon in the missing area
            missing_area = sum((poly.difference(coverage) for poly in missing_area), [])

        return missing_area

    def __solve(self, assumptions=None):
        self.solver.solve(assumptions=assumptions)
        if not self.solver.solve(assumptions=assumptions):
            print('No solution found')
            return None
        print('Solution found')
        return [self.var_to_guard[var] for var in self.solver.get_model() if var > 0]
    
    def solve(self, color_lim: int=0):
        if color_lim == 0:
            color_lim, solution = self.binary_search()
        else:
            solution = self.linear_search(color_lim)
        missing_area = self.__check_coverage(solution)
        while(missing_area):
            new_witnesses = []
            index = len(self.witnesses)
            for polygon in missing_area:
                new_witnesses.append(Witness(f'w{index}', polygon.interior_sample_points()[0]))

            for witness in new_witnesses:
                subset = []
                for guard in self.guards:
                    if guard.visibility.contains(witness.position):
                        for k in range(self.K):
                            subset.append((guard.id, k))
                self.solver.add_clause([self.guard_to_var[guard] for guard in subset])

            solution = self.linear_search(color_lim)
            missing_area = self.__check_coverage(solution)
        return solution

    def binary_search(self):
        lower = 1
        upper = self.K
        while lower < upper:
            mid = (lower + upper) // 2
            print(f'Checking for {mid} colors')
            solution = self.__solve(assumptions=self.__deactivate_guards(mid))
            if solution:
                upper = mid
            else:
                lower = mid + 1
        return lower, self.__solve(self.__deactivate_guards(lower))
    
    def linear_search(self, color_lim: int):
        print(f'Checking for {color_lim} colors')
        solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        while(solution and color_lim > 0):
            color_lim -= 1
            print(f'Checking for {color_lim} colors')
            solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        while(not solution and color_lim <= self.K):
            color_lim += 1
            print(f'Checking for {color_lim} colors')
            solution = self.__solve(assumptions=self.__deactivate_guards(color_lim))
        return self.__solve(assumptions=self.__deactivate_guards(color_lim))

    def __del__(self):
        """
        The solvers from python-sat need a special cleanup,
        which is not necessary for normal Python code.
        There seem to occur resource leaks when you leave this out,
        so it should be sufficient to let the solvers clean up at the garbage collection.
        """
        self.solver.delete()
